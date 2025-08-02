# main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from api.routes import router as api_router
from modules.ai_agent.agentv2 import RAGAgent
import os

app = FastAPI()
app.include_router(api_router, prefix="/api")       # Existing API routes


# CORS config: allow React dev and any OAuth callbacks
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
