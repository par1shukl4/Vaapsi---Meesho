from fastapi import FastAPI

from backend.api.routes import router
from backend.core.config import get_settings


settings = get_settings()

app = FastAPI(
    title=settings.service_name,
    version=settings.version,
    description="Agentic NDR and RTO resolution platform for Indian social commerce.",
)
app.include_router(router)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "service": settings.service_name, "version": settings.version}
