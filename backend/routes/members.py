from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from backend.services import member_service
from backend.services.auth_service import get_current_user

router = APIRouter(prefix="/api/members", tags=["members"])


class RegisterMemberRequest(BaseModel):
    phone: str
    name: str = ""


class SetActiveRequest(BaseModel):
    active: bool


@router.get("")
def get_members(username: str = Depends(get_current_user)):
    return {"members": member_service.list_members()}


@router.post("")
def register_member(data: RegisterMemberRequest, username: str = Depends(get_current_user)):
    try:
        member = member_service.register_member(data.phone, data.name, username)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {"success": True, "member": member}


@router.patch("/{phone}/active")
def set_member_active(phone: str, data: SetActiveRequest, username: str = Depends(get_current_user)):
    try:
        member = member_service.set_active(phone, data.active)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return {"success": True, "member": member}


@router.delete("/{phone}")
def remove_member(phone: str, username: str = Depends(get_current_user)):
    try:
        member_service.delete_member(phone)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return {"success": True}
