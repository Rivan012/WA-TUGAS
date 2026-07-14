from datetime import datetime
from typing import Optional

from google import genai
from pydantic import BaseModel, Field
import json

from backend.config import GOOGLE_AI_API_KEY

_client = genai.Client(api_key=GOOGLE_AI_API_KEY) if GOOGLE_AI_API_KEY else None


class ParsedTask(BaseModel):
    nama: str = Field(description="Nama/judul tugas")
    matkul: str = Field(description="Nama mata kuliah/pelajaran")
    deadline: str = Field(
        description="Deadline dalam format ISO 8601 lengkap, contoh: 2026-07-20T20:00:00"
    )
    catatan: Optional[str] = Field(
        default="", description="Catatan tambahan jika ada, kosongkan jika tidak ada"
    )


def parse_task_ai(text: str) -> dict:
    """
    Ekstrak field tugas (nama, matkul, deadline, catatan) dari teks bebas
    menggunakan Gemini. Melempar Exception kalau gagal, biar caller bisa
    fallback ke parser manual.
    """
    if _client is None:
        raise RuntimeError("GOOGLE_AI_API_KEY belum diset")

    now = datetime.now()

    prompt = f"""
            Sekarang: {now.isoformat()}

            Ekstrak JSON dengan field:
            - nama
            - matkul
            - deadline (ISO8601)
            - catatan

            Jika jam tidak ada gunakan 23:59.
            Jika tahun tidak ada gunakan {now.year}.

            Pesan:
            {text}
            """

    response = _client.models.generate_content(
        model="gemini-3.5-flash",
        contents=prompt,
        config={
            "response_mime_type": "application/json",
            "response_json_schema": ParsedTask.model_json_schema(),
            "thinking_config": {"thinking_level": "minimal"},
        },
    )
    # parsed = json.loads(response.text)


    parsed = ParsedTask.model_validate_json(response.text)

    return {
        "nama": parsed.nama.strip(),
        "matkul": parsed.matkul.strip(),
        "deadline": parsed.deadline.strip(),
        "catatan": (parsed.catatan or "").strip(),
    }