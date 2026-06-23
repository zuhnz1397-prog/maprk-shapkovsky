from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, delete
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException, status
from typing import Optional

from app.models.rk import RK
from app.schemas.rk import RKCreate, RKUpdate

class RKService:

    @staticmethod
    async def get_all(
        db: AsyncSession,
        skip: int = 0,
        limit: int = 1000,
        type_rk: Optional[str] = None,
        search: Optional[str] = None,
    ) -> tuple[int, list[RK]]:
        q = select(RK).where(RK.is_active == True)

        if type_rk:
            q = q.where(RK.type_rk == type_rk)
        if search:
            s = f"%{search}%"
            q = q.where(RK.rk_id.ilike(s) | RK.address.ilike(s))

        total_q = select(func.count()).select_from(q.subquery())
        total = (await db.execute(total_q)).scalar_one()

        q = q.order_by(RK.num).offset(skip).limit(limit)
        result = await db.execute(q)
        return total, result.scalars().all()

    @staticmethod
    async def get_by_id(db: AsyncSession, rk_id: str) -> RK:
        result = await db.execute(
            select(RK).where(RK.rk_id == rk_id, RK.is_active == True)
        )
        rk = result.scalar_one_or_none()
        if not rk:
            raise HTTPException(status_code=404, detail=f"РК {rk_id} не найдена")
        return rk

    @staticmethod
    async def get_by_pk(db: AsyncSession, pk: int) -> RK:
        result = await db.execute(select(RK).where(RK.id == pk))
        rk = result.scalar_one_or_none()
        if not rk:
            raise HTTPException(status_code=404, detail="РК не найдена")
        return rk

    @staticmethod
    async def create(db: AsyncSession, data: RKCreate) -> RK:
        rk = RK(**data.model_dump())
        db.add(rk)
        try:
            await db.flush()
            await db.refresh(rk)
            return rk
        except IntegrityError:
            await db.rollback()
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"РК с номером {data.rk_id} уже существует"
            )

    @staticmethod
    async def update(db: AsyncSession, pk: int, data: RKUpdate) -> RK:
        rk = await RKService.get_by_pk(db, pk)
        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(rk, key, value)
        await db.flush()
        await db.refresh(rk)
        return rk

    @staticmethod
    async def delete(db: AsyncSession, pk: int) -> None:
        rk = await RKService.get_by_pk(db, pk)
        rk.is_active = False  # Soft delete
        await db.flush()

    @staticmethod
    async def update_files(
        db: AsyncSession,
        pk: int,
        photo_path: Optional[str] = None,
        scheme_path: Optional[str] = None,
        passport_path: Optional[str] = None,
    ) -> RK:
        rk = await RKService.get_by_pk(db, pk)
        if photo_path is not None:
            rk.photo_path = photo_path
        if scheme_path is not None:
            rk.scheme_path = scheme_path
        if passport_path is not None:
            rk.passport_path = passport_path
        await db.flush()
        await db.refresh(rk)
        return rk

    @staticmethod
    async def get_stats(db: AsyncSession) -> dict:
        total = (await db.execute(
            select(func.count()).select_from(RK).where(RK.is_active == True)
        )).scalar_one()

        rows = (await db.execute(
            select(RK.type_rk, func.count(RK.id))
            .where(RK.is_active == True)
            .group_by(RK.type_rk)
        )).all()
        by_type = {row[0]: row[1] for row in rows}

        with_passport = (await db.execute(
            select(func.count()).select_from(RK)
            .where(RK.is_active == True, RK.passport_path.isnot(None))
        )).scalar_one()

        return {
            "total": total,
            "by_type": by_type,
            "with_passport": with_passport,
            "without_passport": total - with_passport,
        }

    @staticmethod
    async def get_map_data(db: AsyncSession) -> list[dict]:
        """Оптимизированный запрос только нужных полей для карты"""
        result = await db.execute(
            select(RK).where(RK.is_active == True).order_by(RK.num)
        )
        rks = result.scalars().all()
        return [
            {
                "id":      rk.id,
                "rk_id":  rk.rk_id,
                "num":    rk.num,
                "address": rk.address,
                "type_adv": rk.type_adv or "",
                "type_rk":  rk.type_rk,
                "size":   rk.size or "",
                "area":   rk.area or "",
                "lat":    rk.lat,
                "lon":    rk.lon,
                "note":   (rk.note or "")[:200],
                "has_passport": bool(rk.passport_path),
                "has_photo":    bool(rk.photo_path),
            }
            for rk in rks
        ]
