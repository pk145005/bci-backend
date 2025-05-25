from fastapi import APIRouter
from google.cloud import bigquery

router = APIRouter()
BQ = bigquery.Client(project="bci-backend")

SQL = """
SELECT
  huddles_24h, workouts_24h, mobility_yes_24h, avg_sleep_24h,
  huddles_7d,  workouts_7d,  mobility_yes_7d,  avg_sleep_7d
FROM `bci-backend.huddle_data.summary_mv`
"""

@router.get("/summary")
async def summary():
    row = list(BQ.query(SQL).result())[0]
    return {
        "last_24h": {
            "huddles": row.huddles_24h,
            "workouts": row.workouts_24h,
            "mobility_yes": row.mobility_yes_24h,
            "avg_sleep_hours": float(row.avg_sleep_24h)
        },
        "last_7d": {
            "huddles": row.huddles_7d,
            "workouts": row.workouts_7d,
            "mobility_yes": row.mobility_yes_7d,
            "avg_sleep_hours": float(row.avg_sleep_7d)
        }
    }
