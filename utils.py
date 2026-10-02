"""Shared helpers."""

import hashlib
import re
from typing import Optional


HEX64 = re.compile(r"^(0x)?[a-fA-F0-9]{64}$")


def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def normalize_document_hash(value: Optional[str]) -> Optional[str]:
    if not value or not value.strip():
        return None
    cleaned = value.strip().lower()
    if cleaned.startswith("0x"):
        cleaned = cleaned[2:]
    if not HEX64.match(cleaned):
        raise ValueError("Document hash must be 64 hexadecimal characters (SHA-256).")
    return cleaned


def validate_registration_payload(data: dict) -> dict:
    required = [
        "property_number",
        "survey_number",
        "owner_name",
        "location",
        "area",
        "property_type",
    ]
    missing = [f for f in required if not str(data.get(f, "")).strip()]
    if missing:
        raise ValueError(f"Missing required fields: {', '.join(missing)}")

    try:
        area = int(data["area"])
    except (TypeError, ValueError) as exc:
        raise ValueError("Area must be a positive integer.") from exc
    if area <= 0:
        raise ValueError("Area must be a positive integer.")

    doc_hash = None
    if data.get("document_hash"):
        doc_hash = normalize_document_hash(str(data["document_hash"]))

    return {
        "property_number": str(data["property_number"]).strip(),
        "survey_number": str(data["survey_number"]).strip(),
        "owner_name": str(data["owner_name"]).strip(),
        "location": str(data["location"]).strip(),
        "area": area,
        "property_type": str(data["property_type"]).strip(),
        "document_hash": doc_hash,
    }
