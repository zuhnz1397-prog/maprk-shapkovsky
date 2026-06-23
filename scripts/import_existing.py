"""
Скрипт импорта существующих 734 РК из JSON в базу данных.
Запуск: python scripts/import_existing.py --json rk_final.json
"""
import asyncio
import json
import argparse
import sys
from pathlib import Path

# Добавляем корень проекта в путь
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from app.models.rk import RK
from app.database import Base
from app.config import settings

TYPE_MAP = {
    "Билборд":            "Билборд",
    "Сити-формат":        "Сити-формат",
    "Билборд динамика":   "Билборд динамика",
    "Цифровой билборд":   "Цифровой билборд",
    "Афиша":              "Афиша",
    "Панель-кронштейн":   "Панель-кронштейн",
    "Остановочный пункт": "Остановочный пункт",
    "Настенный щит":      "Настенный щит",
    "Прочее":             "Прочее",
}

async def import_data(json_path: str):
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    SessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    with open(json_path, encoding="utf-8") as f:
        data = json.load(f)

    print(f"Загружено {len(data)} записей из {json_path}")

    async with SessionLocal() as session:
        created = 0
        skipped = 0
        for item in data:
            # Проверяем, не существует ли уже
            from sqlalchemy import select
            exists = await session.execute(
                select(RK.id).where(RK.rk_id == item["id"])
            )
            if exists.scalar_one_or_none():
                skipped += 1
                continue

            rk = RK(
                rk_id     = item["id"],
                num       = item.get("n", 0),
                address   = item.get("a", ""),
                type_adv  = item.get("tip", "Наружная реклама"),
                type_rk   = TYPE_MAP.get(item.get("vid", ""), "Прочее"),
                size      = item.get("s", ""),
                area      = item.get("ar", ""),
                note      = item.get("nt", ""),
                lat       = float(item["lat"]),
                lon       = float(item["lon"]),
                msk_x     = item.get("mx", ""),
                msk_y     = item.get("my", ""),
                is_active = True,
            )
            session.add(rk)
            created += 1

            if created % 100 == 0:
                await session.flush()
                print(f"  Импортировано {created}...")

        await session.commit()
        print(f"\nГотово! Создано: {created}, пропущено (дубли): {skipped}")

    await engine.dispose()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", required=True, help="Путь к JSON файлу с данными РК")
    args = parser.parse_args()
    asyncio.run(import_data(args.json))
