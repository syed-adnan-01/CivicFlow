README for synthetic_documents/

Place synthetic (fake) PDF/JPEG/PNG test files here for OCR testing.

Rules:
- NO real Aadhaar numbers, PAN numbers, or identity documents.
- NO real people's names, photos or addresses.
- Use clearly fake/fictional data: "Test Citizen", "123 Synthetic Lane", etc.
- Label each file with what it represents, e.g.:
    synthetic_photo_id_clear.pdf
    synthetic_photo_id_blurry.jpg
    synthetic_address_proof_rotated.pdf
    synthetic_unsupported_format.bmp   (for rejection testing)

These files are used by:
    tests/unit/test_file_validation.py
    tests/unit/test_ocr_normalization.py
    tests/integration/test_document_pipeline.py

Do NOT commit real documents even anonymized ones.

