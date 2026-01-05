from fastapi import Depends
from sqlalchemy.orm import Session
from app.db.db_session import SessionLocal

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
