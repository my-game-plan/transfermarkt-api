from datetime import date
from typing import Optional

from app.schemas.base import AuditMixin, TransfermarktBaseModel


class Absence(TransfermarktBaseModel):
    season: str
    reason: str
    competition: Optional[str]
    competition_id: Optional[str]
    from_date: Optional[date]
    until_date: Optional[date]
    days: Optional[int]
    games_missed: Optional[int]
    games_missed_clubs: list[str]


class PlayerAbsences(TransfermarktBaseModel, AuditMixin):
    id: str
    page_number: int
    last_page_number: int
    absences: list[Absence]
