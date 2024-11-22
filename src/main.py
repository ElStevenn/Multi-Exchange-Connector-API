from fastapi import FastAPI, HTTPException, BackgroundTasks, Response, Depends
from fastapi.middleware.cors import CORSMiddleware
from typing import Annotated
import asyncio

from src.app.database import crud
from src.app.security import encrypt_data, get_current_active_user
from src.app.schemas import *
from src.app.proxy import BrightProxy
from src.app.bitget_layer import BitgetLayerConnection

app = FastAPI(
    title="Bitget API",
    summary="In this API you'll find everything about Bitget API integration."
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


proxy_manager = BrightProxy()

# AUTHENTICATION (Public - Accessible from Frontend)
@app.post("/auth/register", description="### Register a new account\n\n**IMPORTANT**API Connection Only works with HMAC Signature, so use HMAC only", tags=["User Authentication"])
async def add_new_account(user_id: Annotated[tuple[dict, str], Depends(get_current_active_user)], request_body: RegisterUser):


    proxy = await BrightProxy.create()
    bitget_account = BitgetLayerConnection(
        api_key=request_body.apikey,
        api_secret_key=request_body.secret_key,
        passphrase=request_body.passphrase,
        proxy=proxy,
        ip=request_body.ip
    )

    # Validate Proxy IP and get account ID
    account_information = await bitget_account.get_account_information()
    account_id = account_information.get('userId')

    # Register new account
    await crud.register_new_account(
        user_id=user_id,
        account_id=account_id,
        email=request_body.email,
        account_name=request_body.account_name,
        account_type=None,
        proxy_ip=request_body.ip
    )

    # Add user credentials
    await crud.add_user_credentials(
        account_id=account_id,
        encrypted_apikey=encrypt_data(request_body.apikey),
        encrypted_secretkey=encrypt_data(request_body.secret_key),
        encrypted_passphrase=encrypt_data(request_body.passphrase)
    )

    return account_information

@app.post("/auth/login", description="### Login to an account", tags=["User Authentication"])
async def login_account(request_body: LoginUser):

    return {"message": "Login successful"}

@app.get("/proxy/public-ip", description="### Retrives the public IP address of the static proxy\n\nThis is then used to connect with the Bitget API", tags=["User Authentication"])
async def get_proxy_ip():
    
    ip = await proxy_manager.select_ip()

    return {'proxy_ip': ip}

@app.post("/auth/refresh-token", description="### Refresh access token", tags=["User Authentication"])
async def refresh_token():

    return {"message": "Token refreshed successfully"}

# ACCOUNT MANAGEMENT (Public - Accessible from Frontend)
@app.get("/accounts/{user_id}", description="### Get account info for a user", tags=["Account Management"])
async def get_account_info(user_id: str):
    proxy = await BrightProxy.create()

    return {"user_id": user_id, "message": "Account info retrieved"}

@app.get("/accounts/assets/{user_id}", description="Get account assets", tags=["Account Management"])
async def get_account_assets(user_id: str):
    proxy = await BrightProxy.create()
    

    return {}

@app.delete("/accounts/remove/{account_id}", description="### Remove API credentials", tags=["Account Management"])
async def delete_user_credentials(account_id: str):


    return {"message": f"API credentials for account {account_id} removed"}

# TRADING OPERATIONS (Internal - Accessed by APIs in the same VPC)
@app.post("/trades/open", description="### Open multiple trading operations", tags=["Trading Operations"])
async def open_trades(request_body: TradeRequest):
    proxy = await BrightProxy.create()

 
    return {"message": "Trades opened successfully"}

@app.post("/trades/close", description="### Close multiple trade operations", tags=["Trading Operations"])
async def close_trades(request_body: CloseTradeRequest):
    proxy = await BrightProxy.create()

    return {"message": "Trades closed successfully"}

@app.post("/trades/schedule", description="### Schedule multiple trade operations", tags=["Trading Operations"])
async def schedule_multiple_trades(request_body: ScheduledTradeRequest, background_tasks: BackgroundTasks):
    # Add task to background to process scheduling
    background_tasks.add_task(
        schedule_close_trades,
        request_body=request_body
    )
    return {"message": "Trades scheduled successfully"}

# Background task to schedule trade closing
async def schedule_close_trades(request_body: ScheduledTradeRequest):
    await asyncio.sleep(request_body.time_to_close)  # Simulated delay for scheduling
    # Logic to close trades
    return

# TRADING CONFIGURATION (Internal - Accessed by APIs in the same VPC)
@app.post("/risk-management/set", description="### Set trading configuration", tags=["Trading Configuration"])
async def set_risk_management(request_body: SetRiskManagementRequest):
    
    # Store risk configuration in database
    return {"message": "Risk management configuration saved"}

@app.get("/risk-management/{user_id}", description="### Get current risk management from Bitget account", tags=["Trading Configuration"])
async def get_risk_management(user_id: str):
    # Fetch risk configuration from database
    return {"user_id": user_id, "message": "Risk management settings retrieved"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host='0.0.0.0', port=8001)