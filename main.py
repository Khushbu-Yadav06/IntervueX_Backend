from database.connection import Base, engine
from database import models
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routers.interviews import router as interview_router
from routers.resume import router as resume_router
from routers.auth import router as auth_router

app = FastAPI(
    title="AI Interview Preparation API",
    description="Backend for AI-powered interview preparation",
    version="1.0.0"
)

Base.metadata.create_all(bind=engine)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:5173",
        "http://127.0.0.1:5173"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def home():
    return {
        "message": "Welcome to AI Interview Preparation Backend"
    }


@app.get("/api/health/")
def health_check():
    return {
        "status": "success",
        "message": "Backend is running successfully"
    }


app.include_router(interview_router)
app.include_router(resume_router)
app.include_router(auth_router)
