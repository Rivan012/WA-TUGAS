from fastapi import APIRouter
from pydantic import BaseModel

from backend.commands import (
    tambah,
    list,
    selesai,
    hapus,
    help
)

router = APIRouter()


class IncomingMessage(BaseModel):
    from_number: str
    message: str


@router.post("/webhook")
def webhook(data: IncomingMessage):

    text = data.message.strip()

    if text.startswith("/tambah"):
        return {"reply": tambah.execute(data.from_number, text)}

    elif text.startswith("/list"):
        return {"reply": list.execute(data.from_number)}

    elif text.startswith("/selesai"):
        return {"reply": selesai.execute(text)}

    elif text.startswith("/hapus"):
        return {"reply": hapus.execute(text)}

    else:
        return {"reply": help.execute()}