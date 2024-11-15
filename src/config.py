import os
from dotenv import load_dotenv

load_dotenv()



# BRIGHT DATA API
BRIGHTDATA_API_TOKEN = os.getenv('BRIGHTDATA_API_TOKEN', 'brightdata-api-token')
