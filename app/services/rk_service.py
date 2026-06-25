from sqlalchemy.orm import Session
from sqlalchemy import select, func
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException, status
from typing import Optional

from app.models.rk import RK
from app.schemas.rk import RKCreate, RKUpdate


class RKService:

    @staticmethod
    def get_all(
        db: Session,
        skip: int = 0,
        limit: int = 1000,
        type_rk: Optional[str] = None,
        search: Optional[str] = None,
    ) -> tuple[int, list[RK]]:
        q = db.query(RK).filter(RK.is_active == True)
        if type_rk:
            q = q.filter(RK.type_rk == type_rk)
        if search:
            s = f"%{search}%"
            q = q.filter(RK.rk_id.ilike(s) | RK.address.ilike(s))
        total = q.count()
        items = q.order_by(RK.num).offset(skip).limit(limit).all()
        return total, items

    @staticmethod
    def get_by_id(db: Session, rk_id: str) -> RK:
        rk = db.query(RK).filter(RK.rk_id == rk_id, RK.is_active == True).first()
        if not rk:
            raise HTTPException(status_code=404, detail=f"RK {rk_id} not found")
        return rk

    @staticmethod
    def get_by_pk(db: Session, pk: int) -> RK:
        rk = db.query(RK).filter(RK.id == pk).first()
        if not rk:
            raise HTTPException(status_code=404, detail="RK not found")
        return rk

    @staticmethod
    def create(db: Session, data: RKCreate) -> RK:
        rk = RK(**data.model_dump())
        db.add(rk)
        try:
            db.flush()
            db.refresh(rk)
            return rk
        except IntegrityError:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"RK {data.rk_id} already exists"
            )

    @staticmethod
    def update(db: Session, pk: int, data: RKUpdate) -> RK:
        rk = RKService.get_by_pk(db, pk)
        for key, value in data.model_dump(exclude_unset=True).items():
            setattr(rk, key, value)
        db.flush()
        db.refresh(rk)
        return rk

    @staticmethod
    def delete(db: Session, pk: int) -> None:
        rk = RKService.get_by_pk(db, pk)
        rk.is_active = False
        db.flush()

    @staticmethod
    def update_files(
        db: Session,
        pk: int,
        photo_path: Optional[str] = None,
        scheme_path: Optional[str] = None,
        passport_path: Optional[str] = None,
    ) -> RK:
        rk = RKService.get_by_pk(db, pk)
        if photo_path is not None:
            rk.photo_path = photo_path
        if scheme_path is not None:
            rk.scheme_path = scheme_path
        if passport_path is not None:
            rk.passport_path = passport_path
        db.flush()
        db.refresh(rk)
        return rk

    @staticmethod
    def get_stats(db: Session) -> dict:
        total = db.query(func.count(RK.id)).filter(RK.is_active == True).scalar()
        rows = db.query(RK.type_rk, func.count(RK.id)).filter(
            RK.is_active == True).group_by(RK.type_rk).all()
        by_type = {row[0]: row[1] for row in rows}
        with_passport = db.query(func.count(RK.id)).filter(
            RK.is_active == True, RK.passport_path.isnot(None)).scalar()
        return {
            "total": total,
            "by_type": by_type,
            "with_passport": with_passport,
            "without_passport": total - with_passport,
        }

    @staticmethod
    def get_map_data(db: Session) -> list[dict]:
        rks = db.query(RK).filter(RK.is_active == True).order_by(RK.num).all()
        return [
            {
                "id": rk.id,
                "rk_id": rk.rk_id,
                "num": rk.num,
                "address": rk.address,
                "type_adv": rk.type_adv or "",
                "type_rk": rk.type_rk,
                "size": rk.size or "",
                "area": rk.area or "",
                "lat": rk.lat,
                "lon": rk.lon,
                "note": (rk.note or "")[:200],
                "has_passport": bool(rk.passport_path),
                "passport_path": rk.passport_path or None,
                "has_photo": bool(rk.photo_path),
            }
            for rk in rks
        ]