from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models import Feedback
from backend.schemas import FeedbackCreateRequest

router = APIRouter()


def serialize_feedback(entry: Feedback) -> dict:
    return {
        "id": entry.id,
        "playerName": entry.player_name,
        "rating": entry.rating,
        "message": entry.message,
        "createdAt": entry.created_at.isoformat() if entry.created_at else None,
    }


@router.get("/api/feedback")
async def api_list_feedback(db: Session = Depends(get_db)) -> JSONResponse:
    entries = db.query(Feedback).order_by(Feedback.created_at.desc()).limit(100).all()
    return JSONResponse([serialize_feedback(entry) for entry in entries])


@router.post("/api/feedback")
async def api_create_feedback(payload: FeedbackCreateRequest, db: Session = Depends(get_db)) -> JSONResponse:
    player_name = payload.player_name.strip()
    message = payload.message.strip()
    if not player_name:
        raise HTTPException(status_code=400, detail="Player name is required.")

    entry = Feedback(player_name=player_name[:60], rating=payload.rating, message=message[:1000])
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return JSONResponse(serialize_feedback(entry))
