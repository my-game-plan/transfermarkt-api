from fastapi import APIRouter

from app.schemas import staff as schemas
from app.services.staff.profile import TransfermarktStaffProfile

router = APIRouter()


@router.get("/{staff_id}/profile", response_model=schemas.StaffProfile, response_model_exclude_defaults=True)
def get_staff_profile(staff_id: str) -> dict:
    tfmkt = TransfermarktStaffProfile(staff_id=staff_id)
    staff_profile = tfmkt.get_staff_profile()
    return staff_profile
