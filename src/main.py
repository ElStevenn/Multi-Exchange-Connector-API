# main.py
# Author: Pau Mateu
# Developer Email: paumat17@gmail.com

from fastapi import FastAPI, HTTPException, Request, BackgroundTasks
import asyncio

from app.database import crud
from app.schemas import *


app = FastAPI(
    title="Bitget API",
    summary="In this API you'll find everything about "
)

@app.post("/add_new_user", description="", tags=["tag"])
async def add_new_user():
    return {}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host='0.0.0.0', port=8001)