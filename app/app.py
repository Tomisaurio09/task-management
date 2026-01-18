from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.dependencies import get_db
import sqlalchemy as sa
from fastapi.middleware.cors import CORSMiddleware
from app.db.db_session import Base, engine
from app import models 
import os

app = FastAPI(
    title="Task Management API",
    version="1.0.0",
    description="Backend estilo Trello con FastAPI + SQLAlchemy + PostgreSQL"
)

ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


from app.api import auth, projects, boards, tasks
app.include_router(auth.router, prefix="/auth")
app.include_router(projects.router, prefix="/projects")
app.include_router(boards.router, prefix="/projects/{project_id}/boards")
app.include_router(tasks.router, prefix="/projects/{project_id}/boards/{board_id}/tasks")


@app.get("/")
def root():
    return {"message": "Task Management API is running!"}

@app.get("/health")
def health_check(db: Session = Depends(get_db)):
    """
    Health check endpoint para monitoring/orchestration (Docker, Kubernetes, etc.)
    Verifica que la API esté corriendo Y que la BD esté accesible.
    """
    try:
        # Intenta hacer una query simple a la BD
        db.execute(sa.text("SELECT 1"))
        return {
            "status": "healthy",
            "database": "connected"
        }
    except Exception as e:
        # Si falla la BD, retorna 503 Service Unavailable
        raise HTTPException(
            status_code=503, 
            detail=f"Database unavailable: {str(e)}"
        )