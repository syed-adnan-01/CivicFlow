"""
Generates valid synthetic PDF and JPEG document fixtures for local demo and test pipelines.
Contains ONLY fictitious demo data; never contains real citizen PII.
"""

import io
import os
import sys

# Ensure pillow is available
from PIL import Image, ImageDraw, ImageFont


def create_synthetic_pdf(filepath: str, text_lines: list):
    # Minimal valid single-page PDF with text stream
    stream_content = "BT\n/F1 12 Tf\n50 750 Td\n"
    for line in text_lines:
        safe_line = line.replace("(", "\\(").replace(")", "\\)")
        stream_content += f"({safe_line}) Tj\nT*\n"
    stream_content += "ET"
    stream_bytes = stream_content.encode("latin1")

    pdf_content = (
        b"%PDF-1.4\n"
        b"1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n"
        b"2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n"
        b"3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >>\nendobj\n"
        b"4 0 obj\n<< /Length " + str(len(stream_bytes)).encode("latin1") + b" >>\nstream\n"
        + stream_bytes + b"\nendstream\nendobj\n"
        b"5 0 obj\n<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>\nendobj\n"
        b"xref\n0 6\n0000000000 65535 f \n0000000009 00000 n \n0000000058 00000 n \n0000000115 00000 n \n"
        + f"{240:010d} 00000 n \n".encode("latin1")
        + f"{320 + len(stream_bytes):010d} 00000 n \n".encode("latin1")
        + b"trailer\n<< /Size 6 /Root 1 0 R >>\nstartxref\n"
        + f"{390 + len(stream_bytes)}".encode("latin1") + b"\n%%EOF"
    )

    with open(filepath, "wb") as f:
        f.write(pdf_content)
    print(f"Created synthetic PDF: {filepath}")


def create_synthetic_jpeg(filepath: str, text_lines: list):
    # Create clean image with PIL
    img = Image.new("RGB", (600, 400), color=(250, 250, 250))
    draw = ImageDraw.Draw(img)

    y = 30
    for line in text_lines:
        draw.text((40, y), line, fill=(20, 20, 20))
        y += 35

    img.save(filepath, "JPEG", quality=90)
    print(f"Created synthetic JPEG: {filepath}")


def main():
    target_dir = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "tests",
        "fixtures",
        "synthetic_documents",
    )
    os.makedirs(target_dir, exist_ok=True)

    # 1. Synthetic Aadhaar PDF
    create_synthetic_pdf(
        os.path.join(target_dir, "synthetic_aadhaar_card.pdf"),
        [
            "Government of India",
            "Unique Identification Authority of India (UIDAI)",
            "Mera Aadhaar, Meri Pehchan",
            "Name: Demo Citizen Kumar",
            "DOB: 15/08/1990  |  Gender: Male",
            "1234 5678 9012",
            "Address: 123 Synthetic Street, Bengaluru - 560001",
        ],
    )

    # 2. Synthetic Voter ID JPEG
    create_synthetic_jpeg(
        os.path.join(target_dir, "synthetic_voter_id.jpg"),
        [
            "ELECTION COMMISSION OF INDIA",
            "ELECTOR PHOTO IDENTITY CARD",
            "EPIC NO: ABC1234567",
            "Elector Name: Demo Citizen Kumar",
            "Father Name: Sample Kumar",
            "Constituency: 154 - Rajajinagar",
        ],
    )

    # 3. Synthetic Residential Proof PDF
    create_synthetic_pdf(
        os.path.join(target_dir, "synthetic_residential_proof.pdf"),
        [
            "Government of Karnataka - Revenue Department",
            "Office of the Tahasildar, Bengaluru North",
            "DOMICILE AND RESIDENTIAL CERTIFICATE",
            "This is to certify that Shri Demo Citizen Kumar",
            "is residing at Bengaluru for the period of 10 years.",
            "Issued for Nadakacheri Citizen Service requirements.",
        ],
    )


if __name__ == "__main__":
    main()

