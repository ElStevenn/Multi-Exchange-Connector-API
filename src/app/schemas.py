from pydantic import BaseModel, EmailStr, UUID4
from typing import Optional, Literal, List


"""Authentication"""
class RegisterUser(BaseModel):
    email: EmailStr
    apikey: str
    secret_key: Optional[str] = None
    passphrase: str
    given_ip: str
    
class LoginUser(BaseModel):
    email: EmailStr
    apikey: str
    secret_key: Optional[str] = None
    passphrase: str

"""Managment"""
class AccountInfoResponse(BaseModel):
    account_id: UUID4
    user_id: UUID4
    type: str
    email: str
    created_at: str

class RemoveAccountResponse(BaseModel):
    account_id: UUID4
    message: str

"""Operations"""
class TradeRequest(BaseModel):
    user_ids: List[UUID4]
    symbol: str
    side: Literal['buy', 'sell'] # adapt this to the bitget api
    size: float
    leverage: int

class CloseTradeRequest(BaseModel):
    user_ids: List[UUID4]
    symbol: str

class ScheduledTradeRequest(BaseModel):
    user_ids: List[UUID4]
    symbol: str
    side: str
    size: float
    leverage: int
    time_to_close: int  # in seconds

class TradeResponse(BaseModel):
    user_id: UUID4
    trade_id: str
    status: str
    error: Optional[str] = None


"""Risk  Management """
class SetRiskManagementRequest(BaseModel):
    user_id: UUID4
    max_drawdown: float
    stop_loss: float
    take_profit: float
    leverage_limit: float

class RiskManagementResponse(BaseModel):
    user_id: UUID4
    max_drawdown: float
    stop_loss: float
    take_profit: float
    leverage_limit: float
    daily_loss_limit: Optional[float]

