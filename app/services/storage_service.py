# -*- coding: utf-8 -*-
import httpx
from app.config import settings

_TR = {
    'А': 'A', 'Б': 'B', 'В': 'V', 'Г': 'G', 'Д': 'D', 'Е': 'E', 'Ё': 'Yo',
    'Ж': 'Zh', 'З': 'Z', 'И': 'I', 'Й': 'J', 'К': 'K', 'Л': 'L', 'М': 'M',
    'Н': 'N', 'О': 'O', 'П': 'P', 'Р': 'R', 'С': 'S', 'Т': 'T', 'У': 'U',
    'Ф': 'F', 'Х': 'Kh', 'Ц': 'Ts', 'Ч': 'Ch', 'Ш': 'Sh', 'Щ': 'Shch',
    'Ъ': '', 'Ы': 'Y', 'Ь': '', 'Э': 'E', 'Ю': 'Yu', 'Я': 'Ya',
    'а': 'a', 'б': 'b', 'в': 'v', 'г': 'g', 'д': 'd', 'е': 'e', 'ё': 'yo',
    'ж': 'zh', 'з': 'z', 'и': 'i', 'й': 'j', 'к': 'k', 'л': 'l', 'м': 'm',
    'н': 'n', 'о': 'o', 'п': 'p', 'р': 'r', 'с': 's', 'т': 't', 'у': 'u',
    'ф': 'f', 'х': 'kh', 'ц': 'ts', 'ч': 'ch', 'ш': 'sh', 'щ': 'shch',
    'ъ': '', 'ы': 'y', 'ь': '', 'э': 'e', 'ю': 'yu', 'я': 'ya',
}


def _translit(s: str) -> str:
    """Б1 → B1, О-20 → O-20, Пр3 → Pr3 (ASCII-only for Supabase Storage keys)."""
    return ''.join(_TR.get(c, c) for c in s)


def upload_passport(rk_id: str, pdf_bytes: bytes) -> str:
    """Upload passport PDF to Supabase Storage via REST API, return public URL."""
    if not settings.SUPABASE_URL or not settings.SUPABASE_SERVICE_KEY:
        raise ValueError("SUPABASE_URL and SUPABASE_SERVICE_KEY must be set")

    bucket = settings.SUPABASE_BUCKET
    # Supabase Storage rejects non-ASCII keys — transliterate to Latin
    latin_name = _translit(rk_id) + ".pdf"
    url = f"{settings.SUPABASE_URL}/storage/v1/object/{bucket}/{latin_name}"
    headers = {
        "Authorization": f"Bearer {settings.SUPABASE_SERVICE_KEY}",
        "Content-Type": "application/pdf",
        "x-upsert": "true",
    }

    with httpx.Client(timeout=60) as client:
        resp = client.post(url, content=pdf_bytes, headers=headers)
        if resp.status_code not in (200, 201):
            raise RuntimeError(f"Supabase upload failed: {resp.status_code} {resp.text}")

    public_url = f"{settings.SUPABASE_URL}/storage/v1/object/public/{bucket}/{latin_name}"
    return public_url
