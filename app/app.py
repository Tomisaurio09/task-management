from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.db.db_session import Base, engine
from app import models # registra los modelos

app = FastAPI(
    title="Task Management API",
    version="1.0.0",
    description="Backend estilo Trello con FastAPI + SQLAlchemy + PostgreSQL"
)

# Middlewares (ejemplo CORS)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # en dev, luego restringís
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Crear tablas automáticamente (solo en dev, en prod usar Alembic)
Base.metadata.create_all(bind=engine)

# Routers (cuando los tengas)
#from app.api import users, projects, boards, tasks, auth
# app.include_router(users.router, prefix="/users")
# app.include_router(projects.router, prefix="/projects")
# app.include_router(boards.router, prefix="/boards")
# app.include_router(tasks.router, prefix="/tasks")
from app.api import auth
app.include_router(auth.router, prefix="/auth")

@app.get("/")
def root():
    return {"message": "Task Management API is running!"}
