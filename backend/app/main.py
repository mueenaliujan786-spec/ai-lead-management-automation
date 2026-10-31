from fastapi import Depends, FastAPI, HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.database import get_db
from app.routers import leads

app = FastAPI(title="AI Lead Management API", version="0.1.0")

app.include_router(leads.router)


@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.get("/health/db")
def database_health_check(db: Session = Depends(get_db)):
    try:
        db.execute(text("SELECT 1"))
    except Exception:
        # Never show internal error details to the outside world.
        raise HTTPException(status_code=503, detail="Database unavailable")
    return {"status": "ok", "database": "connected"}