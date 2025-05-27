from fastapi import FastAPI
import logging

from app.api import summary as summary_api
from app.api import huddle_ui
from app.api import event as event_api
from app.api.analysis import router as analysis_router

logging.basicConfig(level=logging.INFO)

app = FastAPI(title="BCI Core")

app.include_router(huddle_ui.router)
app.include_router(event_api.router)
app.include_router(summary_api.router)
app.include_router (analysis_router)

DEFAULT_ERROR = "TEST_ERROR_ALERT"

@app.get("/test-error", status_code=500)
async def test_error():
    logging.error(DEFAULT_ERROR)
    return {"detail": "Error logged"}
