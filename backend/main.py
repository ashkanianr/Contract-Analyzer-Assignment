"""FastAPI app: Contract Analyzer API."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.api.routes import router
from backend.config import API_PREFIX

app = FastAPI(
    title="Contract Analyzer API",
    description="Upload a PDF contract, get structured compliance analysis (Table 1).",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(router, prefix=API_PREFIX)


@app.get("/")
def root():
    return {"message": "Contract Analyzer API", "docs": "/docs", "health": f"{API_PREFIX}/health", "analyze": f"{API_PREFIX}/analyze"}
