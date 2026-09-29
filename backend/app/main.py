from contextlib import asynccontextmanager

from fastapi import FastAPI, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.database import dispose_engine, engine
from app.error_handlers import unhandled_exception_handler
from app.logging_config import configure_logging
from app.middleware import RequestContextMiddleware

configure_logging()

SERVICE_NAME = "livestock-intelligence-api"

@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    dispose_engine()

app = FastAPI(
    title="Livestock Intelligence API",
    version="0.1.0",
    description="Backend foundation for the Livestock Intelligence & Early-Warning System.",
    lifespan=lifespan,
)


app.add_exception_handler(Exception, unhandled_exception_handler)
app.add_middleware(RequestContextMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
def health() -> dict[str, str]:
    return {
        "status": "ok",
        "service": SERVICE_NAME,
    }


@app.get("/ready")
def readiness() -> JSONResponse:
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
    except SQLAlchemyError:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "status": "unavailable",
                "service": SERVICE_NAME,
            },
        )

    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "status": "ready",
            "service": SERVICE_NAME,
        },
    )
