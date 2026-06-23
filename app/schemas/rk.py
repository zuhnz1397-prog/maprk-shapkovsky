from pydantic import BaseModel, Field, field_validator
from typing import Optional
from datetime import datetime

class RKBase(BaseModel):
    rk_id:      str         = Field(..., min_length=1, max_length=20,  description="№ РК")
    num:        int         = Field(..., ge=1,                          description="№ п/п")
    address:    str         = Field(..., min_length=5, max_length=500,  description="Адрес")
    type_adv:   str         = Field(default="Наружная реклама",         description="Тип")
    type_rk:    str         = Field(..., min_length=1, max_length=100,  description="Вид РК")
    size:       Optional[str] = Field(None, max_length=50,              description="Размер")
    area:       Optional[str] = Field(None, max_length=20,              description="Площадь м²")
    compliance: Optional[str] = Field(default="ИТ",                    description="Соответствие")
    legal_doc:  Optional[str] = Field(None, max_length=200,             description="Правоустанавл. документ")
    note:       Optional[str] = Field(None,                             description="Примечание")
    lat:        float        = Field(..., ge=43.0, le=47.0,             description="Широта")
    lon:        float        = Field(..., ge=40.0, le=44.0,             description="Долгота")
    msk_x:      Optional[str] = Field(None, max_length=30)
    msk_y:      Optional[str] = Field(None, max_length=30)

    @field_validator("type_rk")
    @classmethod
    def validate_type_rk(cls, v):
        allowed = {
            "Билборд", "Сити-формат", "Билборд динамика",
            "Цифровой билборд", "Афиша", "Панель-кронштейн",
            "Остановочный пункт", "Настенный щит", "Прочее"
        }
        if v not in allowed:
            raise ValueError(f"Вид РК должен быть одним из: {', '.join(sorted(allowed))}")
        return v

class RKCreate(RKBase):
    pass

class RKUpdate(BaseModel):
    address:    Optional[str]   = None
    type_adv:   Optional[str]   = None
    type_rk:    Optional[str]   = None
    size:       Optional[str]   = None
    area:       Optional[str]   = None
    compliance: Optional[str]   = None
    legal_doc:  Optional[str]   = None
    note:       Optional[str]   = None
    lat:        Optional[float] = None
    lon:        Optional[float] = None
    msk_x:      Optional[str]   = None
    msk_y:      Optional[str]   = None

class RKOut(RKBase):
    id:             int
    photo_path:     Optional[str] = None
    scheme_path:    Optional[str] = None
    passport_path:  Optional[str] = None
    is_active:      bool
    created_at:     datetime
    updated_at:     Optional[datetime] = None

    model_config = {"from_attributes": True}

class RKMapOut(BaseModel):
    """Лёгкая схема для карты — только нужные поля"""
    id:     int
    rk_id:  str
    num:    int
    address: str
    type_adv: str
    type_rk: str
    size:   Optional[str]
    area:   Optional[str]
    lat:    float
    lon:    float
    note:   Optional[str]
    has_passport: bool
    has_photo:    bool

    model_config = {"from_attributes": True}

class RKListResponse(BaseModel):
    total:  int
    items:  list[RKOut]

class StatsOut(BaseModel):
    total:          int
    by_type:        dict[str, int]
    with_passport:  int
    without_passport: int
