"""
Citizen Document Service.
Orchestrates file upload validation, private object storage, OCR processing,
category inference, and versioned checklist comparison.
"""

import logging
from typing import List, Optional
from uuid import UUID, uuid4

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.modules.documents.repository import DocumentRepository
from app.schemas.documents import (
    ChecklistItemRead,
    ChecklistItemResult,
    CitizenDocumentList,
    CitizenDocumentRead,
    DocumentCheckResult,
    DocumentDeleteResponse,
    DocumentUploadResponse,
    ProcessingStatus,
)
from app.services.ocr.category_classifier import CategoryClassifier
from app.services.ocr.checklist_matcher import ChecklistItemDefinition, ChecklistMatcher
from app.services.ocr.engine_adapter import OCREngineAdapter
from app.services.ocr.file_safety import FileSafetyChecker
from app.services.ocr.file_validation import FileValidationError, FileValidator
from app.services.ocr.readiness_report import ReadinessReportGenerator
from app.services.ocr.storage import PrivateStorage
from app.services.ocr.tesseract_engine import TesseractEngine
from app.services.ocr.text_normalizer import TextNormalizer

logger = logging.getLogger(__name__)


class DocumentService:
    def __init__(
        self,
        db: Session,
        storage: Optional[PrivateStorage] = None,
        ocr_engine: Optional[OCREngineAdapter] = None,
    ):
        self.db = db
        self.repo = DocumentRepository(db)
        self.storage = storage or PrivateStorage()
        self.ocr_engine = ocr_engine or TesseractEngine()

    def upload_document(
        self,
        file_bytes: bytes,
        original_filename: str,
        service_id: Optional[UUID],
        citizen_id: UUID,
        checklist_version_id: Optional[UUID] = None,
    ) -> DocumentUploadResponse:
        """
        Validates file, securely saves it to private storage, registers in DB,
        and initiates asynchronous/immediate readiness check.
        """
        # 1. Validation
        try:
            info = FileValidator.validate_upload(original_filename, file_bytes)
            FileSafetyChecker.scan_bytes(file_bytes, info.extension)
        except (FileValidationError, Exception) as exc:
            logger.warning("Upload validation failed for %s: %s", original_filename, exc)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"code": "FILE_VALIDATION_FAILED", "message": str(exc)},
            )

        # 2. Generate UUID and persist privately
        doc_id = uuid4()
        storage_key = self.storage.save(
            citizen_id=citizen_id,
            document_id=doc_id,
            original_filename=info.filename,
            file_bytes=file_bytes,
        )

        # 3. Create document record in PostgreSQL
        doc = self.repo.create_document(
            citizen_id=citizen_id,
            service_id=service_id,
            storage_key=storage_key,
            original_filename=info.filename,
            file_type=info.extension.lstrip("."),
            file_size_bytes=info.size_bytes,
        )

        # 4. Trigger OCR check immediately (or queue for background)
        try:
            self.process_document(doc.id, citizen_id, checklist_version_id=checklist_version_id)
        except Exception as exc:
            logger.error("Initial OCR processing failed for doc %s: %s", doc.id, exc)

        return DocumentUploadResponse(
            document_id=doc.id,
            processing_status=doc.processing_status,
            file_name=doc.original_filename,
            message="Upload received. Preliminary document readiness check completed.",
        )

    def list_documents(self, citizen_id: UUID) -> CitizenDocumentList:
        """Returns safe metadata for documents owned by the citizen."""
        docs = self.repo.list_by_citizen(citizen_id)
        items = [
            CitizenDocumentRead(
                document_id=d.id,
                file_name=d.original_filename,
                service_id=d.service_id,
                processing_status=d.processing_status,
                created_at=d.created_at,
            )
            for d in docs
        ]
        return CitizenDocumentList(items=items, total=len(items))

    def process_document(
        self,
        document_id: UUID,
        citizen_id: UUID,
        checklist_version_id: Optional[UUID] = None,
    ) -> DocumentCheckResult:
        """
        Executes OCR extraction, text normalization, category inference,
        and checklist matching.
        """
        doc = self.repo.get_by_id(document_id)
        if not doc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"code": "NOT_FOUND", "message": "Document not found."},
            )

        if doc.citizen_id != citizen_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={"code": "FORBIDDEN", "message": "Access to another citizen's document is forbidden."},
            )

        # Update status to OCR_PENDING
        self.repo.update_status(document_id, ProcessingStatus.OCR_PENDING)
        job = self.repo.create_processing_job(
            document_id=document_id,
            engine=self.ocr_engine.engine_name(),
        )

        try:
            # 1. Read file bytes from storage
            file_bytes = self.storage.get(doc.storage_key)

            # 2. Extract text via OCR
            ocr_res = self.ocr_engine.extract_text(file_bytes, doc.file_type)

            # 3. Normalize text
            normalized = TextNormalizer.normalize_text(ocr_res.text)

            # 4. Infer category
            cat_res = CategoryClassifier.classify(normalized)

            # 5. Resolve checklist items for service
            checklist_items = self._resolve_service_checklist(doc.service_id)

            # 6. Match checklist items
            matched_items = ChecklistMatcher.match_checklist(
                category_result=cat_res,
                checklist_items=checklist_items,
                checklist_version_id=checklist_version_id,
            )

            # 7. Generate readiness report
            report = ReadinessReportGenerator.generate_report(
                document_id=document_id,
                processing_status=ProcessingStatus.OCR_COMPLETE,
                items=matched_items,
                checklist_version_id=checklist_version_id,
            )

            # 8. Persist results
            self.repo.save_check_result(
                document_id=document_id,
                overall_status=report.overall_status,
                items=matched_items,
                checklist_version_id=checklist_version_id,
            )
            self.repo.complete_job(job.id, status=ProcessingStatus.OCR_COMPLETE)
            self.repo.update_status(document_id, ProcessingStatus.OCR_COMPLETE)

            return report

        except Exception as exc:
            logger.error("OCR check failed for document %s: %s", document_id, exc)
            self.repo.complete_job(job.id, status=ProcessingStatus.OCR_FAILED, error_detail=str(exc))
            self.repo.update_status(document_id, ProcessingStatus.OCR_FAILED)

            return ReadinessReportGenerator.generate_report(
                document_id=document_id,
                processing_status=ProcessingStatus.OCR_FAILED,
                items=[],
                checklist_version_id=checklist_version_id,
            )

    def get_check_result(self, document_id: UUID, citizen_id: UUID) -> DocumentCheckResult:
        """Retrieves existing preliminary readiness report for citizen's document."""
        doc = self.repo.get_by_id(document_id)
        if not doc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"code": "NOT_FOUND", "message": "Document not found."},
            )

        if doc.citizen_id != citizen_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={"code": "FORBIDDEN", "message": "Access to another citizen's document is forbidden."},
            )

        check = self.repo.get_check_result(document_id)
        if not check:
            # If not yet checked, run check
            return self.process_document(document_id, citizen_id)

        items = [
            ChecklistItemRead(
                checklist_item_id=ci.checklist_item_id,
                label=ChecklistMatcher.DEFAULT_CATEGORY_LABELS.get(str(ci.checklist_item_id), "Required Document"),
                result=ci.result,
                confidence_band=ci.confidence_band,
                message=ci.review_note,
            )
            for ci in (check.items or [])
        ]

        return ReadinessReportGenerator.generate_report(
            document_id=document_id,
            processing_status=doc.processing_status,
            items=items,
            checklist_version_id=check.checklist_version_id,
        )

    def delete_document(self, document_id: UUID, citizen_id: UUID) -> DocumentDeleteResponse:
        """Deletes document and derived data per retention policy."""
        doc = self.repo.get_by_id(document_id)
        if not doc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"code": "NOT_FOUND", "message": "Document not found."},
            )

        if doc.citizen_id != citizen_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={"code": "FORBIDDEN", "message": "Cannot delete another citizen's document."},
            )

        # Delete physical file from private storage
        self.storage.delete(doc.storage_key)

        # Soft delete record in DB
        self.repo.soft_delete(document_id)

        return DocumentDeleteResponse(
            document_id=document_id,
            status="DELETED",
            message="Document and extracted data removed according to retention policy.",
        )

    def _resolve_service_checklist(self, service_id: Optional[UUID]) -> List[ChecklistItemDefinition]:
        """Provides default government service checklist requirements."""
        # Standard checklist for Nadakacheri / Citizen Services
        return [
            ChecklistItemDefinition(
                id=UUID("11111111-1111-1111-1111-111111111111"),
                label="Identity Proof (Aadhaar Card)",
                target_category="AADHAAR_CARD",
                is_mandatory=True,
            ),
            ChecklistItemDefinition(
                id=UUID("22222222-2222-2222-2222-222222222222"),
                label="Voter Identity Card (EPIC)",
                target_category="VOTER_ID",
                is_mandatory=False,
            ),
            ChecklistItemDefinition(
                id=UUID("33333333-3333-3333-3333-333333333333"),
                label="Residential / Domicile Certificate",
                target_category="RESIDENTIAL_CERTIFICATE",
                is_mandatory=True,
            ),
        ]

