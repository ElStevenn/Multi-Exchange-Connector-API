import os
from dotenv import load_dotenv
from cryptography.hazmat.primitives import serialization
from typing import Literal
import base64

load_dotenv()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# BRIGHT DATA API
BRIGHTDATA_API_TOKEN = os.getenv('BRIGHTDATA_API_TOKEN', 'brightdata-api-token')


# DATABASE
DB_HOST = os.getenv('DB_HOST', '0.0.0.0')
DB_NAME = os.getenv('DB_NAME', 'db-name')
DB_USER = os.getenv('DB_USER', 'db-user')
DB_PASS = os.getenv('DB_PASS', 'db-pass')


# SECURITY
def load_public_key(path):
    absolute_path = os.path.join(BASE_DIR, path)
    with open(absolute_path, 'rb') as public_key_file:
        public_key = serialization.load_pem_public_key(public_key_file.read())
    return public_key

def load_private_key(path):
    absolute_path = os.path.join(BASE_DIR, path)
    with open(absolute_path, 'rb') as private_key_file:
        private_key = serialization.load_pem_private_key(
            private_key_file.read(),
            password=None  
        )
    return private_key

PUBLIC_KEY = load_public_key('security/public_key.pem')
PRIVATE_KEY = load_private_key('security/private_key.pem')
JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'your-jwt-secret-key')

AVARIABLE_EXCHANGES = ['bitget', 'binance']