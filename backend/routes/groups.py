from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from backend.services import group_service
from backend.services.auth_service import get_current_user

router = APIRouter(prefix="/api/groups", tags=["groups"])


class RegisterGroupRequest(BaseModel):
    jid: str
    name: str = ""


class SetActiveRequest(BaseModel):
    active: bool


@router.get("")
def get_groups(username: str = Depends(get_current_user)):
    return {"groups": group_service.list_groups()}


@router.post("")
def register_group(data: RegisterGroupRequest, username: str = Depends(get_current_user)):
    try:
        group = group_service.register_group(data.jid, data.name, username)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {"success": True, "group": group}


@router.patch("/{jid}/active")
def set_group_active(jid: str, data: SetActiveRequest, username: str = Depends(get_current_user)):
    try:
        group = group_service.set_active(jid, data.active)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return {"success": True, "group": group}


@router.delete("/{jid}")
def remove_group(jid: str, username: str = Depends(get_current_user)):
    try:
        group_service.delete_group(jid)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return {"success": True}
