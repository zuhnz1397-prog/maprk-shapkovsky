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
from app.services.storage_service import upload_passport as storage_upload_passport
from app.utils.auth import get_current_admin
from app.config import settings

router = APIRouter(prefix="/rk", tags=["rk"])


# ─── Публичные endpoints (карта) ─────────────────────────────────────────────

@router.get("/map", summary="Все РК для карты (лёгкий JSON)")
async def get_map_data(db: AsyncSession = Depends(get_db)):
    """Оптимизированный endpoint — только нужные поля для отображения на карте"""
    return RKService.get_map_data(db)


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
    total, items = RKService.get_all(db, skip, limit, type_rk, search)
    return {"total": total, "items": items}


@router.get("/stats", response_model=StatsOut, summary="Статистика")
async def get_stats(
    db: AsyncSession = Depends(get_db),
    _: str = Depends(get_current_admin),
):
    return RKService.get_stats(db)


# ─── Экспорт документов (должны быть ДО /{pk} чтобы FastAPI не матчил "export" как int) ──

@router.get("/export/pdf", summary="Экспорт реестра в PDF")
async def export_pdf(
    db: AsyncSession = Depends(get_db),
    _: str = Depends(get_current_admin),
):
    _, rks = RKService.get_all(db, limit=10000)
    pdf_bytes = generate_registry_pdf(rks)
    filename = f"reestr_RK_Shpakovsky_{__import__('datetime').date.today()}.pdf"
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
    _, rks = RKService.get_all(db, limit=10000)
    docx_bytes = generate_registry_docx(rks)
    filename = f"reestr_RK_Shpakovsky_{__import__('datetime').date.today()}.docx"
    return Response(
        content=docx_bytes,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'}
    )


@router.get("/{pk}", response_model=RKOut, summary="Одна РК по id")
async def get_rk(
    pk: int,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(get_current_admin),
):
    return RKService.get_by_pk(db, pk)


@router.post("/", response_model=RKOut, status_code=201, summary="Создать РК")
async def create_rk(
    data: RKCreate,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(get_current_admin),
):
    return RKService.create(db, data)


@router.put("/{pk}", response_model=RKOut, summary="Обновить данные РК")
async def update_rk(
    pk: int,
    data: RKUpdate,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(get_current_admin),
):
    return RKService.update(db, pk, data)


@router.delete("/{pk}", status_code=204, summary="Удалить РК (soft delete)")
async def delete_rk(
    pk: int,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(get_current_admin),
):
    RKService.delete(db, pk)


# ─── Загрузка файлов ─────────────────────────────────────────────────────────

@router.post("/{pk}/photo", response_model=RKOut, summary="Загрузить фото объекта")
async def upload_photo(
    pk: int,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    _: str = Depends(get_current_admin),
):
    path = await save_photo(file)
    return RKService.update_files(db, pk, photo_path=path)


@router.post("/{pk}/scheme", response_model=RKOut, summary="Загрузить схему расположения")
async def upload_scheme(
    pk: int,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    _: str = Depends(get_current_admin),
):
    path = await save_scheme(file)
    return RKService.update_files(db, pk, scheme_path=path)


@router.post("/{pk}/passport/upload", response_model=RKOut, summary="Загрузить оригинальный PDF паспорта")
async def upload_passport_pdf(
    pk: int,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    _: str = Depends(get_current_admin),
):
    rk = RKService.get_by_pk(db, pk)
    pdf_bytes = await file.read()
    public_url = storage_upload_passport(rk.rk_id, pdf_bytes)
    rk = RKService.update_files(db, pk, passport_path=public_url)
    return rk


@router.get("/{pk}/passport/pdf", summary="Паспорт одной РК в PDF")
async def download_passport(
    pk: int,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(get_current_admin),
):
    rk = RKService.get_by_pk(db, pk)
    pdf_bytes = generate_passport_pdf(rk)
    filename = f"паспорт_{rk.rk_id}.pdf"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'}
    )
