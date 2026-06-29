import logging

import uvicorn
from fastapi import FastAPI

from app.api.routes import router
from app.core.logging import setup_logging
from app.database.db import engine
from app.database.models import Base

setup_logging()
logger = logging.getLogger(__name__)

app = FastAPI(title="Campaign Decision Assistant")

Base.metadata.create_all(bind=engine)

app.include_router(router)


@app.on_event("startup")
async def on_startup() -> None:
    logger.info("Campaign Decision Assistant started")


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
