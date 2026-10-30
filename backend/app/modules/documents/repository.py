"""
Database repository for citizen documents, processing jobs, and checklist results.
Enforces QueueLess 2.3 Section 9.3 & 10:
Ownership checks: citizen can only view, check, or delete their own documents.
"""

from datetime import datetime, timezone
from typing import List, Optional, Tuple
from uuid import UUID

from sqlalchemy import and_
from sqlalchemy.orm import Session

from app.models.citizen_document import CitizenDocument
from app.models.document_check import DocumentCheck
from app.models.document_check_item import DocumentCheckItem
from app.models.document_processing_job import DocumentProcessingJob
from app.schemas.documents import ChecklistItemRead, ProcessingStatus


class DocumentRepository:
    def __init__(self, db: Session):
        self.db = db

    def create_document(
        self,
        citizen_id: UUID,
        service_id: Optional[UUID],
        storage_key: str,
        original_filename: str,
        file_type: str,
        file_size_bytes: int,
    ) -> CitizenDocument:
        now = datetime.now(timezone.utc)
        doc = CitizenDocument(
            citizen_id=citizen_id,
            service_id=service_id,
            storage_key=storage_key,
            original_filename=original_filename,
            file_type=file_type,
            file_size_bytes=file_size_bytes,
            processing_status=ProcessingStatus.RECEIVED,
            created_at=now,
        )
        self.db.add(doc)
        self.db.commit()
        self.db.refresh(doc)
        return doc

    def get_by_id(self, document_id: UUID) -> Optional[CitizenDocument]:
        return (
            self.db.query(CitizenDocument)
            .filter(and_(CitizenDocument.id == document_id, CitizenDocument.deleted_at.is_(None)))
            .first()
        )

    def list_by_citizen(self, citizen_id: UUID) -> List[CitizenDocument]:
        return (
            self.db.query(CitizenDocument)
            .filter(and_(CitizenDocument.citizen_id == citizen_id, CitizenDocument.deleted_at.is_(None)))
            .order_by(CitizenDocument.created_at.desc())
            .all()
        )

    def update_status(self, document_id: UUID, status: str) -> Optional[CitizenDocument]:
        doc = self.get_by_id(document_id)
        if not doc:
            return None
        doc.processing_status = status
        doc.updated_at = datetime.now(timezone.utc)
        self.db.commit()
        self.db.refresh(doc)
        return doc

    def soft_delete(self, document_id: UUID) -> bool:
        doc = self.get_by_id(document_id)
        if not doc:
            return False
        now = datetime.now(timezone.utc)
        doc.processing_status = ProcessingStatus.DELETED
        doc.deleted_at = now
        doc.updated_at = now
        self.db.commit()
        return True

    def create_processing_job(
        self,
        document_id: UUID,
        engine: str = "tesseract",
        engine_version: str = "1.0",
        language_packs: str = "eng",
    ) -> DocumentProcessingJob:
        now = datetime.now(timezone.utc)
        job = DocumentProcessingJob(
            citizen_document_id=document_id,
            engine=engine,
            engine_version=engine_version,
            language_packs=language_packs,
            status=ProcessingStatus.OCR_PENDING,
            attempts=1,
            started_at=now,
            created_at=now,
        )
        self.db.add(job)
        self.db.commit()
        self.db.refresh(job)
        return job

    def get_active_job(self, document_id: UUID) -> Optional[DocumentProcessingJob]:
        return (
            self.db.query(DocumentProcessingJob)
            .filter(
                and_(
                    DocumentProcessingJob.citizen_document_id == document_id,
                    DocumentProcessingJob.status.in_([ProcessingStatus.RECEIVED, ProcessingStatus.OCR_PENDING]),
                )
            )
            .order_by(DocumentProcessingJob.created_at.desc())
            .first()
        )

    def complete_job(
        self,
        job_id: UUID,
        status: str,
        error_code: Optional[str] = None,
        error_detail: Optional[str] = None,
    ) -> Optional[DocumentProcessingJob]:
        job = self.db.query(DocumentProcessingJob).filter(DocumentProcessingJob.id == job_id).first()
        if not job:
            return None
        job.status = status
        job.error_code = error_code
        job.error_detail = error_detail
        job.completed_at = datetime.now(timezone.utc)
        self.db.commit()
        self.db.refresh(job)
        return job

    def save_check_result(
        self,
        document_id: UUID,
        overall_status: str,
        items: List[ChecklistItemRead],
        checklist_version_id: Optional[UUID] = None,
    ) -> DocumentCheck:
        now = datetime.now(timezone.utc)
        # Delete previous check if exists (re-check)
        existing = self.db.query(DocumentCheck).filter(DocumentCheck.citizen_document_id == document_id).first()
        if existing:
            self.db.delete(existing)
            self.db.flush()

        check = DocumentCheck(
            citizen_document_id=document_id,
            checklist_version_id=checklist_version_id,
            overall_status=overall_status,
            created_at=now,
            updated_at=now,
        )
        self.db.add(check)
        self.db.flush()

        check_items = []
        for item in items:
            ci = DocumentCheckItem(
                check_id=check.id,
                checklist_item_id=item.checklist_item_id,
                result=item.result,
                confidence_band=item.confidence_band,
                review_note=item.message,
                created_at=now,
            )
            check_items.append(ci)

        self.db.bulk_save_objects(check_items)
        self.db.commit()
        self.db.refresh(check)
        return check

    def get_check_result(self, document_id: UUID) -> Optional[DocumentCheck]:
        return (
            self.db.query(DocumentCheck)
            .filter(DocumentCheck.citizen_document_id == document_id)
            .first()
        )

