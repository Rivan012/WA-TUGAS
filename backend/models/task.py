from typing import Optional

from pydantic import BaseModel


class Task(BaseModel):
    nama: str
    matkul: str
    deadline: str
    catatan: str
    user_id: str
    group_id: Optional[str] = None
    status: str = "belum"