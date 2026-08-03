from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..db import get_db
from ..models import EvaluateRequest, EvaluateResponse
from ..services.evaluate import run_evaluation

router = APIRouter(prefix="/api/evaluate", tags=["evaluate"])


@router.post("", response_model=EvaluateResponse)
def evaluate(body: EvaluateRequest, db: Session = Depends(get_db)):
    try:
        return run_evaluation(
            db,
            dataset_id=body.dataset_id,
            base_model=body.base_model,
            adapter_id=body.adapter_id,
            split=body.split,
        )
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc
