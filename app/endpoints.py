
from fastapi import APIRouter, UploadFile, File
from fastapi.responses import HTMLResponse, PlainTextResponse
from pathlib import Path
from app.pdf_processor import process_and_send_email

router = APIRouter()

@router.get("/", response_class=HTMLResponse)
async def upload_page():
    return Path("app/templates/upload.html").read_text()

@router.post("/upload")
async def handle_upload(file: UploadFile = File(...)):
    saved_path = Path("/tmp") / file.filename
    with saved_path.open("wb") as f:
        f.write(await file.read())

    try:
        result = process_and_send_email(saved_path)
        return PlainTextResponse(f"✅ {result}")
    except Exception as e:
        return PlainTextResponse(f"❌ Error: {e}", status_code=500)
