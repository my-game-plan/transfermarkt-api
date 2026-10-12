from datetime import date
from typing import Optional

from app.schemas.base import AuditMixin, TransfermarktBaseModel


class StaffAssistantOf(TransfermarktBaseModel):
    id: Optional[str] = None
    name: Optional[str] = None
    games: Optional[int] = None


class StaffAppointment(TransfermarktBaseModel):
    club_id: Optional[str] = None
    club_name: Optional[str] = None
    role: Optional[str] = None
    appointed: Optional[date] = None
    until: Optional[date] = None
    matches: Optional[int] = None
    ppm: Optional[float] = None
    assistant_of: list[StaffAssistantOf] = []


class StaffProfile(TransfermarktBaseModel, AuditMixin):
    id: str
    name: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    date_of_birth: Optional[date] = None
    place_of_birth: Optional[str] = None
    citizenship: list[str] = []
    coaching_licence: Optional[str] = None
    player_id: Optional[str] = None
    current_club_id: Optional[str] = None
    current_club_name: Optional[str] = None
    current_role: Optional[str] = None
    history: list[StaffAppointment]
