from dotenv import load_dotenv
load_dotenv()

import logging
from fastapi import FastAPI

from app.api.huddle_ui    import router as huddle_ui_router
from app.api.event        import router as event_router
from app.api.summary      import router as summary_router
from app.api.analysis     import router as analysis_router
from app.api.run_analysis import router as run_analysis_router

logging.basicConfig(level=logging.INFO)

app = FastAPI(title="BCI Core")

app.include_router(huddle_ui_router)
app.include_router(event_router)
app.include_router(summary_router)
app.include_router(analysis_router)
app.include_router(run_analysis_router)

DEFAULT_ERROR = "TEST_ERROR_ALERT"

@app.get("/test-error", status_code=500)
async def test_error():
    logging.error(DEFAULT_ERROR)
    return {"detail": "Error logged"}
