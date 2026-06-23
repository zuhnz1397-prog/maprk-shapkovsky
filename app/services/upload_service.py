import uuid
import aiofiles
from pathlib import Path
from fastapi import UploadFile, HTTPException
from PIL import Image
import io

from app.config import settings

ALLOWED_IMAGE = {"image/jpeg", "image/png", "image/webp"}
ALLOWED_DOCS  = {"image/jpeg", "image/png", "application/pdf"}


async def save_upload(
    file: UploadFile,
    dest_dir: Path,
    allowed_types: set[str],
    max_size: int = None,
) -> str:
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=400,
            detail=f"Недопустимый тип файла: {file.content_type}. "
                   f"Разрешены: {', '.join(allowed_types)}"
        )

    content = await file.read()

    if max_size and len(content) > max_size:
        raise HTTPException(
            status_code=413,
            detail=f"Файл слишком большой. Максимум: {max_size // 1024 // 1024} МБ"
        )

    # Генерируем уникальное имя
    ext = Path(file.filename).suffix.lower() or ".jpg"
    filename = f"{uuid.uuid4().hex}{ext}"
    file_path = dest_dir / filename

    # Для изображений — сжимаем до разумного размера
    if file.content_type in ALLOWED_IMAGE:
        content = _resize_image(content, max_width=1920, quality=85)

    async with aiofiles.open(file_path, "wb") as f:
        await f.write(content)

    return str(file_path)


def _resize_image(content: bytes, max_width: int = 1920, quality: int = 85) -> bytes:
    try:
        img = Image.open(io.BytesIO(content))
        if img.mode in ("RGBA", "P"):
            img = img.convert("RGB")
        if img.width > max_width:
            ratio = max_width / img.width
            new_h = int(img.height * ratio)
            img = img.resize((max_width, new_h), Image.LANCZOS)
        out = io.BytesIO()
        img.save(out, format="JPEG", quality=quality, optimize=True)
        return out.getvalue()
    except Exception:
        return content  # Если не удалось — возвращаем оригинал


async def save_photo(file: UploadFile) -> str:
    return await save_upload(
        file, settings.PHOTOS_DIR, ALLOWED_IMAGE, settings.MAX_UPLOAD_SIZE
    )

async def save_scheme(file: UploadFile) -> str:
    return await save_upload(
        file, settings.SCHEMES_DIR, ALLOWED_DOCS, settings.MAX_UPLOAD_SIZE
    )

async def save_passport(file: UploadFile) -> str:
    return await save_upload(
        file, settings.PASSPORTS_DIR, ALLOWED_DOCS, settings.MAX_UPLOAD_SIZE
    )
