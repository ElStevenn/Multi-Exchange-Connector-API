from fastapi import FastAPI, HTTPException, BackgroundTasks, Response, Depends, Query
from fastapi.middleware.cors import CORSMiddleware
from typing import Annotated, Optional
import asyncio

from src.app.database import crud
from src.app.security import encrypt_data, get_current_active_user, get_current_active_account
from src.app.schemas import *
from src.app.proxy import BrightProxy
from src.app.exchanges.bitget_layer import BitgetLayerConnection
from src.app.exchanges.exchange_utils import validate_account

app = FastAPI(
    title="Multi-Exchange Connector API",
    description="The **Multi-Exchange Connector API** provides a unified interface for managing cryptocurrency trading accounts and operations across multiple exchanges. It enables users to securely register, authenticate, and manage API credentials, retrieve account balances and assets, execute trades, and configure risk management settings. With support for dynamic proxy management and seamless integration, this API is designed to enhance trading workflows and ensure secure, efficient access to various exchanges."
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
@app.post("/auth/register/{user_id}", description="### Register a new account\n\n**IMPORTANT**API Connection Only works with HMAC Signature, so use HMAC only", tags=["User Authentication"])
async def add_new_account( user_id: str,request_body: RegisterUser):
    # user_id: Annotated[tuple[dict, str], Depends(get_current_active_user)],
    proxy = await BrightProxy.create()

    # Validate Proxy IP and get account ID
    account_information, account_id = await validate_account(
        exchange='bitget',
        proxy=proxy,
        apikey=request_body.apikey,
        secret_key=request_body.secret_key,
        passphrase=request_body.passphrase,
        proxy_ip=request_body.ip,
    )
    # account_id = account_information.get('userId')

    # Register new account
    await crud.register_new_account(
        user_id=user_id,
        account_id=account_id,
        email=request_body.email,
        account_name=request_body.account_name,
        account_type='sub-account',
        proxy_ip=request_body.ip
    )

    # Add user credentials
    await crud.add_user_credentials(
        account_id=account_id,
        encrypted_apikey=encrypt_data(request_body.apikey) if request_body.apikey else None,
        encrypted_secretkey=encrypt_data(request_body.secret_key) if request_body.secret_key else None,
        encrypted_passphrase=encrypt_data(request_body.passphrase) if request_body.passphrase else None,

    )

    return account_information

@app.post("/auth/login", description="### Login to an account", tags=["User Authentication"])
async def login_account(request_body: LoginUser):

    return {"message": "Login successful"}

@app.get("/proxy/public-ip", description="### Retrives the public IP address of the static proxy\n\nThis is then used to connect with the Bitget API", tags=["User Authentication"])
async def get_proxy_ip(user_id: Annotated[tuple[dict, str], Depends(get_current_active_user)]):
    
    # Validate User
    user = await crud.get_user_data(user_id=user_id)

    if not user:
        raise HTTPException(status_code=401, detail="You have no permissions to get the public IP")
    
    ip = await proxy_manager.select_ip()
    return {'proxy_ip': ip}

@app.post("/auth/refresh-token", description="### Refresh access token", tags=["User Authentication"])
async def refresh_token():

    return {"message": "Token refreshed successfully"}

# ACCOUNT MANAGEMENT (Public - Accessible from Frontend)
@app.get("/accounts/{user_id}", description="### Get accounts asociated to user", tags=["Account Management"])
async def get_account_info(user_id: str):
    proxy = await BrightProxy.create()

    return {"user_id": user_id, "message": "Account info retrieved"}

@app.get("/accounts/assets", description="### Get account assets", tags=["Account Management"])
async def get_account_assets(credentials: Annotated[tuple[str, str, str, str, str], Depends(get_current_active_account)], account_id: str):
    _, proxy_ip, apikey, secret_key, passphrase = credentials
    proxy = await BrightProxy.create()
    
    bitget_account = BitgetLayerConnection(
        api_key=apikey,
        api_secret_key=secret_key,
        passphrase=passphrase,
        proxy=proxy,
        ip=proxy_ip
    )

    assets = bitget_account.account_assets()

    return assets

@app.get("/accounts/balance/{account_id}/{user_id}", description="### Get total balance of the account", tags=["Account Management"])
async def get_account_balance(account_id: str, user_id: str):
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
    proxy = await BrightProxy.create()


    return {"message": "Trades scheduled successfully"}


# FUTURES
@app.get("/futures/assets", description="Get subaccount assets", tags=["Futures"])
async def get_futures_assets():
    proxy = await BrightProxy.create()

    return {}

@app.get("/futures/balance/{account_id}/{user_id}", description="Get total balance in future wa", tags=["Futures"])
async def get_future_total_balance():
    proxy = await BrightProxy.create()

    return {}

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