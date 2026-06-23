from fastapi import APIRouter, Depends, Query, UploadFile, File, HTTPException
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from pathlib import Path

from app.database import get_db
from app.schemas.rk import RKCreate, RKUpdate, RKOut, RKListResponse, StatsOut
from app.services.rk_service import RKService
from app.services.upload_service import save_photo, save_scheme, save_passport
from app.services.export_service import (
    generate_registry_pdf, generate_registry_docx, generate_passport_pdf
)
from app.utils.auth import get_current_admin
from app.config import settings

router = APIRouter(prefix="/rk", tags=["rk"])


# ─── Публичные endpoints (карта) ─────────────────────────────────────────────

@router.get("/map", summary="Все РК для карты (лёгкий JSON)")
async def get_map_data(db: AsyncSession = Depends(get_db)):
    """Оптимизированный endpoint — только нужные поля для отображения на карте"""
    return await RKService.get_map_data(db)


# ─── Endpoints с авторизацией (админка) ──────────────────────────────────────

@router.get("/", response_model=RKListResponse, summary="Список всех РК")
async def list_rk(
    skip:    int = Query(0, ge=0),
    limit:   int = Query(100, ge=1, le=1000),
    type_rk: Optional[str] = Query(None, description="Фильтр по виду РК"),
    search:  Optional[str] = Query(None, description="Поиск по № или адресу"),
    db: AsyncSession = Depends(get_db),
    _: str = Depends(get_current_admin),
):
    total, items = await RKService.get_all(db, skip, limit, type_rk, search)
    return {"total": total, "items": items}


@router.get("/stats", response_model=StatsOut, summary="Статистика")
async def get_stats(
    db: AsyncSession = Depends(get_db),
    _: str = Depends(get_current_admin),
):
    return await RKService.get_stats(db)


@router.get("/{rk_id}", response_model=RKOut, summary="Одна РК по номеру")
async def get_rk(
    rk_id: str,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(get_current_admin),
):
    return await RKService.get_by_id(db, rk_id)


@router.post("/", response_model=RKOut, status_code=201, summary="Создать РК")
async def create_rk(
    data: RKCreate,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(get_current_admin),
):
    rk = await RKService.create(db, data)
    # Автоматически генерируем паспорт без фото
    passport_bytes = generate_passport_pdf(rk)
    passport_path = settings.PASSPORTS_DIR / f"{rk.rk_id}.pdf"
    passport_path.write_bytes(passport_bytes)
    rk = await RKService.update_files(db, rk.id, passport_path=str(passport_path))
    return rk


@router.put("/{pk}", response_model=RKOut, summary="Обновить данные РК")
async def update_rk(
    pk: int,
    data: RKUpdate,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(get_current_admin),
):
    rk = await RKService.update(db, pk, data)
    # Перегенерируем паспорт
    passport_bytes = generate_passport_pdf(rk)
    passport_path = settings.PASSPORTS_DIR / f"{rk.rk_id}.pdf"
    passport_path.write_bytes(passport_bytes)
    rk = await RKService.update_files(db, pk, passport_path=str(passport_path))
    return rk


@router.delete("/{pk}", status_code=204, summary="Удалить РК (soft delete)")
async def delete_rk(
    pk: int,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(get_current_admin),
):
    await RKService.delete(db, pk)


# ─── Загрузка файлов ─────────────────────────────────────────────────────────

@router.post("/{pk}/photo", response_model=RKOut, summary="Загрузить фото объекта")
async def upload_photo(
    pk: int,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    _: str = Depends(get_current_admin),
):
    path = await save_photo(file)
    rk = await RKService.update_files(db, pk, photo_path=path)
    # Перегенерируем паспорт с фото
    passport_bytes = generate_passport_pdf(rk)
    passport_path = settings.PASSPORTS_DIR / f"{rk.rk_id}.pdf"
    passport_path.write_bytes(passport_bytes)
    rk = await RKService.update_files(db, pk, passport_path=str(passport_path))
    return rk


@router.post("/{pk}/scheme", response_model=RKOut, summary="Загрузить схему расположения")
async def upload_scheme(
    pk: int,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    _: str = Depends(get_current_admin),
):
    path = await save_scheme(file)
    rk = await RKService.update_files(db, pk, scheme_path=path)
    # Перегенерируем паспорт со схемой
    passport_bytes = generate_passport_pdf(rk)
    passport_path = settings.PASSPORTS_DIR / f"{rk.rk_id}.pdf"
    passport_path.write_bytes(passport_bytes)
    rk = await RKService.update_files(db, pk, passport_path=str(passport_path))
    return rk


# ─── Экспорт документов ──────────────────────────────────────────────────────

@router.get("/export/pdf", summary="Экспорт реестра в PDF")
async def export_pdf(
    db: AsyncSession = Depends(get_db),
    _: str = Depends(get_current_admin),
):
    _, rks = await RKService.get_all(db, limit=10000)
    pdf_bytes = generate_registry_pdf(rks)
    filename = f"реестр_РК_Шпаковский_{__import__('datetime').date.today()}.pdf"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'}
    )


@router.get("/export/docx", summary="Экспорт реестра в Word")
async def export_docx(
    db: AsyncSession = Depends(get_db),
    _: str = Depends(get_current_admin),
):
    _, rks = await RKService.get_all(db, limit=10000)
    docx_bytes = generate_registry_docx(rks)
    filename = f"реестр_РК_Шпаковский_{__import__('datetime').date.today()}.docx"
    return Response(
        content=docx_bytes,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'}
    )


@router.get("/{pk}/passport/pdf", summary="Паспорт одной РК в PDF")
async def download_passport(
    pk: int,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(get_current_admin),
):
    rk = await RKService.get_by_pk(db, pk)
    pdf_bytes = generate_passport_pdf(rk)
    filename = f"паспорт_{rk.rk_id}.pdf"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'}
    )
