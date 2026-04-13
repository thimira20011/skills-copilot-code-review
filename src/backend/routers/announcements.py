"""
Endpoints for managing school announcements.
"""

from datetime import date, datetime
from typing import Any, Dict, List, Optional

from bson import ObjectId
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from ..database import announcements_collection, teachers_collection

router = APIRouter(
    prefix="/announcements",
    tags=["announcements"],
)


class AnnouncementPayload(BaseModel):
    """Payload for creating or updating an announcement."""

    message: str
    expiration_date: str
    start_date: Optional[str] = None


def _parse_date(date_text: str, field_name: str) -> date:
    try:
        return datetime.strptime(date_text, "%Y-%m-%d").date()
    except ValueError:
        raise HTTPException(status_code=400, detail=f"{field_name} must use YYYY-MM-DD format")


def _serialize_announcement(doc: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "id": str(doc["_id"]),
        "message": doc["message"],
        "start_date": doc.get("start_date"),
        "expiration_date": doc["expiration_date"],
        "created_at": doc.get("created_at"),
        "updated_at": doc.get("updated_at"),
    }


def _validate_teacher(teacher_username: Optional[str]) -> None:
    if not teacher_username:
        raise HTTPException(status_code=401, detail="Authentication required")

    teacher = teachers_collection.find_one({"_id": teacher_username})
    if not teacher:
        raise HTTPException(status_code=401, detail="Invalid user")


def _validate_payload(payload: AnnouncementPayload) -> Dict[str, Any]:
    message = payload.message.strip()
    if not message:
        raise HTTPException(status_code=400, detail="Message is required")

    if len(message) > 280:
        raise HTTPException(status_code=400, detail="Message cannot exceed 280 characters")

    expiration_date = _parse_date(payload.expiration_date, "expiration_date")

    start_date = None
    if payload.start_date:
        start_date = _parse_date(payload.start_date, "start_date")

    if start_date and start_date > expiration_date:
        raise HTTPException(status_code=400, detail="start_date cannot be after expiration_date")

    return {
        "message": message,
        "start_date": start_date.isoformat() if start_date else None,
        "expiration_date": expiration_date.isoformat(),
    }


@router.get("", response_model=List[Dict[str, Any]])
@router.get("/", response_model=List[Dict[str, Any]])
def get_active_announcements() -> List[Dict[str, Any]]:
    """Return all currently active announcements for public display."""
    today = date.today().isoformat()
    query = {
        "$and": [
            {"expiration_date": {"$gte": today}},
            {
                "$or": [
                    {"start_date": None},
                    {"start_date": {"$exists": False}},
                    {"start_date": {"$lte": today}},
                ]
            },
        ]
    }

    docs = announcements_collection.find(query).sort("expiration_date", 1)
    return [_serialize_announcement(doc) for doc in docs]


@router.get("/manage", response_model=List[Dict[str, Any]])
def get_all_announcements(teacher_username: Optional[str] = Query(None)) -> List[Dict[str, Any]]:
    """Return all announcements for the management dialog (authenticated users only)."""
    _validate_teacher(teacher_username)
    docs = announcements_collection.find({}).sort("created_at", -1)
    return [_serialize_announcement(doc) for doc in docs]


@router.post("/manage", response_model=Dict[str, Any])
def create_announcement(
    payload: AnnouncementPayload,
    teacher_username: Optional[str] = Query(None),
) -> Dict[str, Any]:
    """Create a new announcement (authenticated users only)."""
    _validate_teacher(teacher_username)
    validated_payload = _validate_payload(payload)

    now = datetime.utcnow().isoformat()
    record = {
        "message": validated_payload["message"],
        "start_date": validated_payload["start_date"],
        "expiration_date": validated_payload["expiration_date"],
        "created_at": now,
        "updated_at": now,
    }

    result = announcements_collection.insert_one(record)
    created = announcements_collection.find_one({"_id": result.inserted_id})
    return _serialize_announcement(created)


@router.put("/manage/{announcement_id}", response_model=Dict[str, Any])
def update_announcement(
    announcement_id: str,
    payload: AnnouncementPayload,
    teacher_username: Optional[str] = Query(None),
) -> Dict[str, Any]:
    """Update an existing announcement (authenticated users only)."""
    _validate_teacher(teacher_username)

    if not ObjectId.is_valid(announcement_id):
        raise HTTPException(status_code=404, detail="Announcement not found")

    validated_payload = _validate_payload(payload)
    result = announcements_collection.update_one(
        {"_id": ObjectId(announcement_id)},
        {
            "$set": {
                "message": validated_payload["message"],
                "start_date": validated_payload["start_date"],
                "expiration_date": validated_payload["expiration_date"],
                "updated_at": datetime.utcnow().isoformat(),
            }
        },
    )

    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Announcement not found")

    updated = announcements_collection.find_one({"_id": ObjectId(announcement_id)})
    return _serialize_announcement(updated)


@router.delete("/manage/{announcement_id}")
def delete_announcement(
    announcement_id: str,
    teacher_username: Optional[str] = Query(None),
) -> Dict[str, str]:
    """Delete an existing announcement (authenticated users only)."""
    _validate_teacher(teacher_username)

    if not ObjectId.is_valid(announcement_id):
        raise HTTPException(status_code=404, detail="Announcement not found")

    result = announcements_collection.delete_one({"_id": ObjectId(announcement_id)})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Announcement not found")

    return {"message": "Announcement deleted"}
