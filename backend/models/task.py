from pydantic import BaseModel


class Task(BaseModel):
    nama: str
    matkul: str
    deadline: str
    catatan: str
    user_id: str
    status: str = "belum"