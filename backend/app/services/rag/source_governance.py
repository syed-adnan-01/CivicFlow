"""
RAG Source Governance Service.
Enforces the source lifecycle, verification requirements, scope boundaries,
and critical restrictions (such as the PSI Training notice scope).
"""

import hashlib
import logging
from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

from app.schemas.knowledge_document import VerificationStatus

logger = logging.getLogger(__name__)

# Specific notice identifiers / scope markers with restricted usage
RESTRICTED_PSI_TRAINING_KEYWORD = "psi training"
RESTRICTED_INCOME_CERT_KEYWORD = "income certificate"


class SourceGovernanceError(Exception):
    """Raised when a source governance or verification rule is violated."""
    pass


class SourceScopeError(SourceGovernanceError):
    """Raised when a source is applied outside its verified scope."""
    pass


class SourceGovernance:
    """
    Enforces rules for source onboarding, manual verification, and query scoping.
    """

    @staticmethod
    def compute_content_hash(text: str) -> str:
        """Computes a canonical SHA-256 hash of source content to detect changes."""
        normalized = " ".join(text.split())
        return hashlib.sha256(normalized.encode("utf-8")).hexdigest()

    @staticmethod
    def validate_verification_transition(
        current_status: str,
        new_status: str,
        reviewer_id: Optional[UUID],
        review_notes: Optional[str],
    ) -> None:
        """
        Validates transitions between UNVERIFIED, VERIFIED, STALE, and INACTIVE.
        A source cannot become VERIFIED without reviewer metadata.
        """
        valid_statuses = {
            VerificationStatus.UNVERIFIED,
            VerificationStatus.VERIFIED,
            VerificationStatus.STALE,
            VerificationStatus.INACTIVE,
        }

        if new_status not in valid_statuses:
            raise SourceGovernanceError(f"Invalid verification status: {new_status}")

        if new_status == VerificationStatus.VERIFIED:
            if not reviewer_id:
                raise SourceGovernanceError("A source cannot be marked VERIFIED without a reviewer ID.")
            if not review_notes or len(review_notes.strip()) < 5:
                raise SourceGovernanceError("Verification notes are required when marking a source as VERIFIED.")

    @staticmethod
    def is_source_retrievable(verification_status: str, active: bool) -> bool:
        """
        Only VERIFIED and active sources are permitted to support authoritative retrieval.
        UNVERIFIED, STALE, or INACTIVE sources must never be used.
        """
        return verification_status == VerificationStatus.VERIFIED and active is True

    @staticmethod
    def validate_service_scope_compatibility(source_scope: str, requested_service_name: Optional[str]) -> bool:
        """
        Ensures a source's documented scope matches the requested service.
        Critical Rule (Section 7.3): The PSI Training notice (Directorate of Minorities, 6 Oct 2020)
        is candidate ONLY for PSI Training document verification, NEVER for general Income Certificate.
        """
        if not source_scope or not requested_service_name:
            return True

        scope_lower = source_scope.lower()
        service_lower = requested_service_name.lower()

        # Check PSI training notice restriction
        if RESTRICTED_PSI_TRAINING_KEYWORD in scope_lower:
            if RESTRICTED_INCOME_CERT_KEYWORD in service_lower and RESTRICTED_PSI_TRAINING_KEYWORD not in service_lower:
                logger.warning(
                    "Scope mismatch: PSI Training source '%s' cannot be used for '%s'",
                    source_scope,
                    requested_service_name,
                )
                return False

        return True

