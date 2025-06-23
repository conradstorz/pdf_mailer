
from pathlib import Path
from loguru import logger
import pandas as pd
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter

from your_module import process_simple_summary_csv
from app.gmail_sender import send_pdf_via_email

logger.add("/logs/csv_pdf_printer.log", rotation="1 week", retention="4 weeks")
TO_EMAIL = "your_email@gmail.com"

def generate_pdf(df: pd.DataFrame, out_path: Path):
    c = canvas.Canvas(str(out_path), pagesize=letter)
    width, height = letter
    x, y = 60, height - 40
    line_height = 14
    for i, col in enumerate(df.columns):
        c.drawString(x + i * 100, y, str(col))
    y -= line_height
    for _, row in df.iterrows():
        for i, val in enumerate(row):
            c.drawString(x + i * 100, y, str(val)[:15])
        y -= line_height
        if y < 40:
            c.showPage()
            y = height - 40
    c.save()

def process_and_send_email(csv_path: Path) -> str:
    df = process_simple_summary_csv(csv_path)
    if df.empty:
        return "No data to process."
    pdf_path = csv_path.with_suffix(".pdf")
    generate_pdf(df, pdf_path)
    send_pdf_via_email(pdf_path, TO_EMAIL)
    return f"PDF sent to {TO_EMAIL}"
