# -*- coding: utf-8 -*-
from supabase import create_client, Client
from app.config import settings


def get_supabase() -> Client:
    return create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_KEY)


def upload_passport(rk_id: str, pdf_bytes: bytes) -> str:
    """Upload passport PDF to Supabase Storage, return public URL."""
    sb = get_supabase()
    path = f"{rk_id}.pdf"
    bucket = settings.SUPABASE_BUCKET

    # Remove old file if exists
    try:
        sb.storage.from_(bucket).remove([path])
    except Exception:
        pass

    sb.storage.from_(bucket).upload(
        path,
        pdf_bytes,
        {"content-type": "application/pdf", "upsert": "true"},
    )

    result = sb.storage.from_(bucket).get_public_url(path)
    return result
