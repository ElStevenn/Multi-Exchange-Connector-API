from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding
from fastapi.security import OAuth2PasswordBearer
from fastapi import HTTPException, Depends
from datetime import datetime, timedelta
from typing import Annotated
from uuid import UUID
import base64, jwt

from src.config import PUBLIC_KEY, PRIVATE_KEY, JWT_SECRET_KEY

ALGORITHM = "HS256"
TOKEN_EXPIRE_DAYS = 30

#  - - - - - BEABER TOKEN - - - - - 
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

def encode_session_token(user_id: str):
    expiration = datetime.utcnow() + timedelta(days=TOKEN_EXPIRE_DAYS)
    payload = {
        "sub": user_id,  
        "exp": expiration 
    }
    token = jwt.encode(payload, JWT_SECRET_KEY, algorithm=ALGORITHM)
    return token


def decode_session_token(token: str):
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        return user_id
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=401, 
            detail="Session has expired",
            headers={"WWW-Authenticate": "Bearer"}
            )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=401,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"}  
        )

async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)]):
    user_id = decode_session_token(token)
    return UUID(user_id)


async def get_user_id(token: Annotated[str, Depends(oauth2_scheme)]):
    # Get user id only
    user_id = decode_session_token(token)
    return user_id


async def get_current_active_user(
        current_user_credentials: Annotated[tuple[dict, str], Depends(get_user_id)]
    ):
    user_id = current_user_credentials  
    return user_id

async def get_current_active_account(
        current_user_credentials: Annotated[tuple[dict, str], Depends(get_user_id)]
):
    """Get user and all its credentials for its main account"""
    from src.app.database.crud import get_main_account, get_account_credentials

    # Get main account
    user_id = current_user_credentials
    main_account_id, proxy_ip = await get_main_account(user_id=user_id)
    
    # Get account credentials
    account_api_keys = await get_account_credentials(account_id=main_account_id)

    return user_id, proxy_ip, account_api_keys['apikey'], account_api_keys['secret_key'], account_api_keys['passphrase']

# - - - - - ENCRYPTION - - - - - 
def encrypt_data(plain_text: str) -> str:
    encrypted = PUBLIC_KEY.encrypt(
        plain_text.encode(),
        # Optimal Asymmetric Encryption Padding
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None
        )
    )
    return base64.b64encode(encrypted).decode('utf-8')

def decrypt_data(encrypted_data: str) -> str:
    decrypt_data = PRIVATE_KEY.decrypt(
        base64.b64decode(encrypted_data.encode('utf8')),
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None
        )
    )
    return decrypt_data.decode('utf-8')


def security_testing():
    encrypted_apikey = ""
    encrypted_passphrase = ""

    decrypted_apikey = decrypt_data(encrypted_apikey); print("APIKEY -> ", decrypted_apikey)
    decrypted_passphrase = decrypt_data(encrypted_passphrase); print("PASSPHRASE -> ", decrypted_passphrase)

if __name__ == "__main__":
    security_testing()
    # # Example to encrypt
    # plain_text = "password123"
    # encrypted_password = encrypt_data(plain_text)
    # print("encrypted password", encrypted_password)

    # Example to decypt
    res = decrypt_data("XX8JskEVnCO3vb8WlRhpE8c+houpMdFspQLSfjOFMgQX8Foe+WGpGG7GVPLl3+mjOMGf0oHqd2nGjRmt5zbhXou5WvcS1QvPA1igX2+RHeSLlmmRKo0ye7wbMmjj9Ly04oinJR5McW7Zk1nXI6dwN5hPu58nedGXWpjU2PSTrH3HAjppv+g+Rkhq8NfTpppFnwXkIxhUDkVrVpELihF3zkL1mC3+XH1K09uUJRlF56bg3GBQbDuY8ngBoL523jeX4heG1ctLcWoEWyAib9YPPw3XdHfhM4slxszyAGEIpVKnDpbnUpfuWYItUSUYSEeS9f24P9R9rFg+TMFFtlSWDw==")
    print(res)