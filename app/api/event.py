from datetime import datetime
from fastapi import APIRouter, HTTPException
from google.cloud import bigquery

router = APIRouter()
BQ = bigquery.Client(project="bci-backend")
TABLE_ID = "bci-backend.huddle_data.events"

@router.post("/event")
async def create_event(payload: dict):
    # minimal validation
    if "event_type" not in payload:
        raise HTTPException(status_code=400, detail="event_type is required")

    row = {
        "ts": datetime.utcnow().isoformat(),
        "event_type": payload.get("event_type"),
        "mobility":   payload.get("mobility"),
        "sleep_hours": payload.get("sleep_hours"),
    }
    errors = BQ.insert_rows_json(TABLE_ID, [row])
    if errors:
        raise HTTPException(status_code=500, detail=str(errors))
    return {"status": "ok"}
