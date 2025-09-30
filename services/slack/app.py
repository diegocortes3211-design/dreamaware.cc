from fastapi import FastAPI
from services.slack.roo_tasks import router as roo_router

app = FastAPI(title="Dreamaware Slack Service")

app.include_router(roo_router)

# Optional: Add a root endpoint for health checks
@app.get("/")
def read_root():
    return {"status": "ok", "service": "slack"}