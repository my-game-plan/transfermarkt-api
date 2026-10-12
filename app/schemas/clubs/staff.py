from datetime import date
from typing import Optional

from app.schemas.base import AuditMixin, TransfermarktBaseModel


class ClubStaffMember(TransfermarktBaseModel):
    id: str
    name: str
    section: str
    role: Optional[str] = None
    age: Optional[int] = None
    citizenship: list[str] = []
    appointed: Optional[date] = None
    contract_expires: Optional[date] = None
    last_club_id: Optional[str] = None
    last_club_name: Optional[str] = None


class ClubStaff(TransfermarktBaseModel, AuditMixin):
    id: str
    staff: list[ClubStaffMember]
