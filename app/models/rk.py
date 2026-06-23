from sqlalchemy import Column, Integer, String, Float, Text, DateTime, Boolean
from sqlalchemy.sql import func
from app.database import Base

class RK(Base):
    __tablename__ = "rk"

    id          = Column(Integer, primary_key=True, index=True)
    rk_id       = Column(String(20), unique=True, nullable=False, index=True, comment="№ РК (Б1, С12, Д3...)")
    num         = Column(Integer, nullable=False, comment="№ п/п в реестре")

    # Основные данные
    address     = Column(String(500), nullable=False, comment="Местоположение")
    type_adv    = Column(String(100), default="Наружная реклама", comment="Тип рекламной конструкции")
    type_rk     = Column(String(100), nullable=False, comment="Вид РК (Билборд, Сити-формат...)")
    size        = Column(String(50), comment="Высота*ширина*кол-во сторон")
    area        = Column(String(20), comment="Общая площадь м2")
    compliance  = Column(String(200), default="ИТ", comment="Соответствие документам тер. планирования")
    legal_doc   = Column(String(200), comment="Правоустанавливающий документ")
    note        = Column(Text, comment="Примечание")

    # Координаты
    lat         = Column(Float, nullable=False, comment="Широта WGS84")
    lon         = Column(Float, nullable=False, comment="Долгота WGS84")
    msk_x       = Column(String(30), comment="Координата X МСК")
    msk_y       = Column(String(30), comment="Координата Y МСК")

    # Файлы
    photo_path    = Column(String(300), comment="Путь к фото объекта")
    scheme_path   = Column(String(300), comment="Путь к схеме расположения")
    passport_path = Column(String(300), comment="Путь к PDF паспорту")

    # Мета
    is_active   = Column(Boolean, default=True)
    created_at  = Column(DateTime(timezone=True), server_default=func.now())
    updated_at  = Column(DateTime(timezone=True), onupdate=func.now())

    def __repr__(self):
        return f"<RK {self.rk_id}: {self.address[:40]}>"
