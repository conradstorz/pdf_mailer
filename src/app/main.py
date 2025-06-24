
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from app.endpoints import router

app = FastAPI()
app.include_router(router)
app.mount("/static", StaticFiles(directory="src/app/templates"), name="static")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], allow_methods=["*"], allow_headers=["*"]
)
