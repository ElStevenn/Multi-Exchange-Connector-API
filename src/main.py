from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
import asyncio

from src.app.database import crud
from src.app.security import encrypt_data
from src.app.schemas import *
from src.app.proxy import BrightProxy

app = FastAPI(
    title="Bitget API",
    summary="In this API you'll find everything about Bitget API integration."
)

origins = [
    "http://0.0.0.0:80",
    "http://localhost:8000",
    "http://3.143.209.3/",
    
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


proxy_manager = BrightProxy()

# AUTHENTICATION (Public - Accessible from Frontend)
@app.post("/auth/register", description="### Register a new account", tags=["User Authentication"])
async def add_new_account(request_body: RegisterUser):
    """
    Registers a new user account with Bitget API credentials.
    """

    # Test credentials and see if it works

    # Save encrypted credentials
    
    return {"message": "Account registered successfully"}

@app.post("/auth/login", description="### Login to an account", tags=["User Authentication"])
async def login_account(request_body: LoginUser):
    """
    Logs in a user and validates the provided API credentials.
    """

    return {"message": "Login successful"}

@app.get("/proxy/public-ip", description="### Retrives the public IP address of the static proxy\n\nThis is then used to connect with the Bitget API", tags=["User Authentication"])
async def get_proxy_ip():
    
    ip = await proxy_manager.select_ip()

    return {'proxy_ip': ip}

@app.post("/auth/refresh-token", description="### Refresh access token", tags=["User Authentication"])
async def refresh_token():
    """
    Refreshes an expired access token (if applicable for frontend sessions).
    """

    return {"message": "Token refreshed successfully"}

# ACCOUNT MANAGEMENT (Public - Accessible from Frontend)
@app.get("/accounts/{user_id}", description="### Get account info for a user", tags=["Account Management"])
async def get_account_info(user_id: str):
    """
    Retrieves account information for a given user.
    """

    return {"user_id": user_id, "message": "Account info retrieved"}

@app.delete("/accounts/remove/{account_id}", description="### Remove API credentials", tags=["Account Management"])
async def delete_user_credentials(account_id: str):
    """
    Removes the API credentials associated with the given account ID.
    """

    return {"message": f"API credentials for account {account_id} removed"}

# TRADING OPERATIONS (Internal - Accessed by APIs in the same VPC)
@app.post("/trades/open", description="### Open multiple trading operations", tags=["Trading Operations"])
async def open_trades(request_body: TradeRequest):
    """
    Opens trades for multiple users simultaneously.
    """
 
    return {"message": "Trades opened successfully"}

@app.post("/trades/close", description="### Close multiple trade operations", tags=["Trading Operations"])
async def close_trades(request_body: CloseTradeRequest):
    """
    Closes trades for multiple users simultaneously.
    """

    return {"message": "Trades closed successfully"}

@app.post("/trades/schedule", description="### Schedule multiple trade operations", tags=["Trading Operations"])
async def schedule_multiple_trades(request_body: ScheduledTradeRequest, background_tasks: BackgroundTasks):
    """
    Schedules trades for multiple users with a specific closing time.
    """
    # Add task to background to process scheduling
    background_tasks.add_task(
        schedule_close_trades,
        request_body=request_body
    )
    return {"message": "Trades scheduled successfully"}

# Background task to schedule trade closing
async def schedule_close_trades(request_body: ScheduledTradeRequest):
    """
    Handles the scheduled closing of trades.
    """
    await asyncio.sleep(request_body.time_to_close)  # Simulated delay for scheduling
    # Logic to close trades
    return

# TRADING CONFIGURATION (Internal - Accessed by APIs in the same VPC)
@app.post("/risk-management/set", description="### Set trading configuration", tags=["Trading Configuration"])
async def set_risk_management(request_body: SetRiskManagementRequest):
    """
    Sets risk management configurations for a user's account.
    """
    # Store risk configuration in database
    return {"message": "Risk management configuration saved"}

@app.get("/risk-management/{user_id}", description="### Get current risk management from Bitget account", tags=["Trading Configuration"])
async def get_risk_management(user_id: str):
    """
    Retrieves the risk management settings for a user's account.
    """
    # Fetch risk configuration from database
    return {"user_id": user_id, "message": "Risk management settings retrieved"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host='0.0.0.0', port=8001)