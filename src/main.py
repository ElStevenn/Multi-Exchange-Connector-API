from typing import Annotated, Optional
from datetime import datetime, timedelta, timezone as tz
import asyncio, json

from fastapi import FastAPI, HTTPException, BackgroundTasks, Response, Depends, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from src.app.database import crud
from src.app.database.database import get_all_tables
from src.app.security import encrypt_data, get_current_active_user, get_current_active_account
from src.app.schemas import (
    RegisterUser,
    LoginUser,
    TradeRequest,
    CloseTradeRequest,
    ScheduledTradeRequest,
    SetRiskManagementRequest,
)
from src.app.proxy import BrightProxy
from src.app.exchanges.bitget_layer import BitgetLayerConnection
from src.app.exchanges.exchange_utils import validate_account, get_account_balance_

from src.config import DOMAIN

app = FastAPI(
    title="Multi-Exchange Connector API",
    description=(
        "The **Multi-Exchange Connector API** provides a unified interface for managing "
        "cryptocurrency trading accounts and operations across multiple exchanges. It "
        "enables users to securely register, authenticate, and manage API credentials, "
        "retrieve account balances and assets, execute trades, and configure risk "
        "management settings. With support for dynamic proxy management and seamless "
        "integration, this API is designed to enhance trading workflows and ensure "
        "secure, efficient access to various exchanges."
    ),
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost", "http://localhost:8001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ------------------------------------------------------------------------------
# AUTHENTICATION (Public - Accessible from Frontend)
# ------------------------------------------------------------------------------
@app.post(
    "/auth/register",
    description=(
        "### Register a new account\n\n"
        "**IMPORTANT**\n"
        "API Connection Only works with HMAC Signature, so use HMAC only"
    ),
    tags=["User Authentication"],
)
async def add_new_account(
    user_id: Annotated[tuple[dict, str], Depends(get_current_active_user)],
    request_body: RegisterUser,
    response: Response,
):
    proxy = await BrightProxy.create()

    # Validate Proxy IP and get account ID
    account_id, permissions = await validate_account(
        exchange=request_body.exchange,
        proxy=proxy,
        apikey=request_body.apikey,
        secret_key=request_body.secret_key,
        passphrase=request_body.passphrase,
        proxy_ip=request_body.ip,
    )

    # Register new account
    await crud.register_new_account(
        user_id=user_id,
        account_id=account_id,
        email=request_body.email,
        account_name=request_body.account_name,
        permissions=permissions,
        account_type=None,
        proxy_ip=request_body.ip,
    )

    # Add user credentials
    await crud.add_user_credentials(
        account_id=account_id,
        encrypted_apikey=encrypt_data(request_body.apikey) if request_body.apikey else None,
        encrypted_secretkey=encrypt_data(request_body.secret_key) if request_body.secret_key else None,
        encrypted_passphrase=encrypt_data(request_body.passphrase) if request_body.passphrase else None,
        exchange=request_body.exchange,
    )

    # Get available accounts
    accounts = await crud.get_accounts(user_id=user_id)

    response.set_cookie(
        key="accounts",
        value=json.dumps(
            [{"account_id": acc["id"], "account_name": acc["account_name"]} for acc in accounts]
        ),
        expires=(datetime.now(tz.utc) + timedelta(days=30)).strftime("%a, %d %b %Y %H:%M:%S GMT"),
        path="/",
        domain=".pauservices.top" if DOMAIN else None,
        httponly=False,
        samesite="Lax",
        secure=False,  # Turn this into True when using HTTPS
    )

    return JSONResponse(
        content={"account_id": account_id, "message": "Account registered successfully"},
        status_code=201,
    )


@app.post("/auth/login", description="### Login to an account", tags=["User Authentication"])
async def login_account(request_body: LoginUser):
    return {"message": "Login successful"}


@app.get("/proxy/public-ip",description=("### Retrieves the public IP address of the static proxy\n\n""This is then used to connect with the Bitget API"), tags=["User Authentication"])
async def get_proxy_ip(user_id: Annotated[tuple[dict, str], Depends(get_current_active_user)]):
    proxy = await BrightProxy.create()

    # Validate User
    user = await crud.get_user_data(user_id=user_id)
    if not user:
        raise HTTPException(
            status_code=401,
            detail="You don't have permissions to get the public IP",
        )

    ip = await proxy.select_ip()
    return {"proxy_ip": ip}


@app.post("/auth/refresh-token", description="### Refresh access token", tags=["User Authentication"])
async def refresh_token():
    return {"message": "Token refreshed successfully"}


# ------------------------------------------------------------------------------
# ACCOUNT MANAGEMENT (Public - Accessible from Frontend)
# ------------------------------------------------------------------------------

#
# Balance
#

@app.get("/balance/overview/{account_id}", description="### Get total assets of all accounts", tags=["Balance"])
async def get_total_assets(user_id: str, account_id: Optional[str] = "all"):
    proxy = await BrightProxy.create()

    # Fetch user accounts
    accounts = await crud.get_accounts(user_id=user_id)

    if not accounts:
        raise HTTPException(status_code=404, detail="No accounts found for this user.")

    # Filter accounts if a specific account ID is provided
    if account_id != "all":
        accounts = [acc for acc in accounts if acc["id"] == account_id]
        if not accounts:
            raise HTTPException(status_code=404, detail=f"No account found with ID: {account}")

    # Fetch account balances
    final_result = {
        "total": 0.0,
        "accounts": {}
    }

    for account in accounts:
        account_information = await crud.get_account(account_id=account["id"])
        credentials = await crud.get_account_credentials(account_id=account["id"])

        balance = await get_account_balance_(
            account_id=account["id"],
            exchange=credentials["exchange"],
            proxy=proxy,
            apikey=credentials.get("apikey"),
            secret_key=credentials.get("secret_key"),
            passphrase=credentials.get("passphrase"),
            proxy_ip=account_information.get("proxy_ip"),
        )
        print("Balance response", balance)

        # Aggregate balances
        final_result["total"] += balance["total"]

        for account_type, amount in balance["accounts"].items():
            if account_type in final_result["accounts"]:
                final_result["accounts"][account_type] += amount
            else:
                final_result["accounts"][account_type] = amount

    return final_result

        


#
# Assets
#

@app.get("/assets/list", description="### Retrive a list of assets per exchange", tags=["Assets"])
async def get_assets_overview(user_id: Annotated[tuple[str, str], Depends(get_current_active_user)]):
    proxy = await BrightProxy.create()



    return {}

@app.get("/assets/history/{user_id}/{account}", description="### Get historical asset data for the chart", tags=["Assets"])
async def get_assets_history(account: str, user_id: Annotated[tuple[str, str], Depends(get_current_active_user)]):
    proxy = await BrightProxy.create()


    return {}

#
# 3) GENERIC ROUTE for all accounts under {user_id}
#
@app.get("/accounts/{user_id}", description="### Get accounts associated to user", tags=["Account Management"])
async def get_account_info(user_id: str):
    proxy = await BrightProxy.create()
    # (sample response for demonstration)
    return {"user_id": user_id, "message": "Account info retrieved"}


@app.put("/accounts/main-account/{account_id}",  description="Set main account", tags=["Account Management"])
async def set_main_account(
    account_id: str,
    user_info: Annotated[tuple[dict, str], Depends(get_current_active_user)],
):
    proxy = await BrightProxy.create()
    # Logic to set main account
    return {}


@app.get("/accounts/balance/{account_id}",description="### Get total balance of an explicit account",tags=["Account Management"])
async def get_account_balance_by_id(account_id: str):
    proxy = await BrightProxy.create()
    # Return balance for this specific account
    return {}


# ------------------------------------------------------------------------------
# TRADING OPERATIONS (Internal - Accessed by APIs in the same VPC)
# ------------------------------------------------------------------------------
@app.post("/trades/open", description="### Open multiple trading operations", tags=["Trading Operations"])
async def open_trades(request_body: TradeRequest):
    proxy = await BrightProxy.create()
    # Logic to open trades
    return {"message": "Trades opened successfully"}


@app.post("/trades/close", description="### Close multiple trade operations", tags=["Trading Operations"])
async def close_trades(request_body: CloseTradeRequest):
    proxy = await BrightProxy.create()
    # Logic to close trades
    return {"message": "Trades closed successfully"}


@app.post("/trades/schedule", description="### Schedule multiple trade operations", tags=["Trading Operations"])
async def schedule_multiple_trades(request_body: ScheduledTradeRequest, background_tasks: BackgroundTasks):
    proxy = await BrightProxy.create()
    # Logic to schedule trades
    return {"message": "Trades scheduled successfully"}


# ------------------------------------------------------------------------------
# TRADING CONFIGURATION (Internal - Accessed by APIs in the same VPC)
# ------------------------------------------------------------------------------
@app.post("/risk-management/set", description="### Set trading configuration", tags=["Trading Configuration"])
async def set_risk_management(request_body: SetRiskManagementRequest):
    # Store risk configuration in the database
    return {"message": "Risk management configuration saved"}


@app.get("/risk-management/{user_id}", description="### Get current risk management from Bitget account", tags=["Trading Configuration"])
async def get_risk_management(user_id: str):
    # Fetch risk configuration from database
    return {"user_id": user_id, "message": "Risk management settings retrieved"}


# ------------------------------------------------------------------------------
# SPOT
# ------------------------------------------------------------------------------
@app.get("/spot/assets", description="Get subaccount assets", tags=["Spot"])
async def get_spot_assets():
    proxy = await BrightProxy.create()
    # Logic to retrieve spot assets
    return {}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
