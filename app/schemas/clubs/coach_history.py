from datetime import date
from typing import Optional

from app.schemas.base import AuditMixin, TransfermarktBaseModel


class ClubCoach(TransfermarktBaseModel):
    id: str
    name: str
    date_of_birth: Optional[date] = None
    citizenship: list[str] = []
    appointed: Optional[date] = None
    until: Optional[date] = None
    matches: Optional[int] = None
    ppm: Optional[float] = None


class ClubCoachHistory(TransfermarktBaseModel, AuditMixin):
    id: str
    coaches: list[ClubCoach]
