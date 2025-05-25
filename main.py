from fastapi import FastAPI
import logging

from app.api import summary as summary_api

logging.basicConfig(level=logging.INFO)

app = FastAPI(title="BCI Core")
app.include_router(summary_api.router)

DEFAULT_ERROR = "TEST_ERROR_ALERT"


@app.get("/test-error", status_code=500)
async def test_error():
    logging.error(DEFAULT_ERROR)
    return {"detail": "Error logged"}
