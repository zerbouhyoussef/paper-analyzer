import os
import sys
import time
from contextlib import asynccontextmanager

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

import uvicorn
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from prometheus_client import make_asgi_app

from services.api.config import Config
from services.api.metrics import REQUEST_LATENCY, REQUEST_COUNT, APP_INFO
from services.api.routes.health import router as health_router
from services.api.routes.papers import router as papers_router, store


@asynccontextmanager
async def lifespan(_app: FastAPI):
    APP_INFO.info({"version": "0.1.0", "environment": os.getenv("ENVIRONMENT", "dev")})
    store.load_papers()
    yield


app = FastAPI(
    title="Paper Analyzer API",
    description="REST API for browsing and searching analyzed academic papers",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def metrics_middleware(request: Request, call_next) -> Response:
    start = time.perf_counter()
    response = await call_next(request)
    elapsed = time.perf_counter() - start

    path = request.url.path
    if not path.startswith("/metrics"):
        labels = {
            "method": request.method,
            "endpoint": path,
            "status": str(response.status_code),
        }
        REQUEST_LATENCY.labels(**labels).observe(elapsed)
        REQUEST_COUNT.labels(**labels).inc()

    return response


metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)

app.include_router(health_router)
app.include_router(papers_router)

if __name__ == "__main__":
    uvicorn.run("services.api.main:app", host=Config.HOST, port=Config.PORT, reload=True)
