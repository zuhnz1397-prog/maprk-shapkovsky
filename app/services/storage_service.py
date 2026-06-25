# -*- coding: utf-8 -*-
import httpx
from app.config import settings


def upload_passport(rk_id: str, pdf_bytes: bytes) -> str:
    """Upload passport PDF to Supabase Storage via REST API, return public URL."""
    if not settings.SUPABASE_URL or not settings.SUPABASE_SERVICE_KEY:
        raise ValueError("SUPABASE_URL and SUPABASE_SERVICE_KEY must be set")

    bucket = settings.SUPABASE_BUCKET
    path = f"{rk_id}.pdf"
    url = f"{settings.SUPABASE_URL}/storage/v1/object/{bucket}/{path}"
    headers = {
        "Authorization": f"Bearer {settings.SUPABASE_SERVICE_KEY}",
        "Content-Type": "application/pdf",
        "x-upsert": "true",
    }

    with httpx.Client(timeout=60) as client:
        resp = client.post(url, content=pdf_bytes, headers=headers)
        if resp.status_code not in (200, 201):
            raise RuntimeError(f"Supabase upload failed: {resp.status_code} {resp.text}")

    public_url = f"{settings.SUPABASE_URL}/storage/v1/object/public/{bucket}/{path}"
    return public_url
