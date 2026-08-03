from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..db import get_db
from ..models import ModelInfo
from ..providers.registry import list_models

router = APIRouter(prefix="/api/models", tags=["models"])


@router.get("", response_model=list[ModelInfo])
def get_models(db: Session = Depends(get_db)):
    return list_models(db)
