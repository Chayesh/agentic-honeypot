from fastapi import FastAPI
from app.routes.webhook import router

app = FastAPI(title="Agentic Honeypot")

app.include_router(router)

@app.get("/")
def health():
    return {"status": "ok"}
