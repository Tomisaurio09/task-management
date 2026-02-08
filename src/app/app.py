from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.exceptions_handlers import setup_exception_handlers
from app.api import auth, projects, boards, tasks

app = FastAPI(
    title="Task Management API",
    version="1.0.0",
    description="Backend estilo Trello con FastAPI + SQLAlchemy + PostgreSQL",
    debug=settings.DEBUG,
)

setup_exception_handlers(app)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(auth.router, prefix="/auth")
app.include_router(projects.router, prefix="/projects")
app.include_router(boards.router, prefix="/projects/{project_id}/boards")
app.include_router(tasks.router, prefix="/projects/{project_id}/boards/{board_id}/tasks")


@app.get("/")
def root():
    return {"message": "Task Management API is running!"}

@app.get("/health")
def health_check():
    return {"status": "healthy"}