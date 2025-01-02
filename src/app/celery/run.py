# src/app/celery/run.py

from src.app.celery.tasks import fetch_user_assets_concurrently

def main():
    result = fetch_user_assets_concurrently.delay()
    print("Task ID:", result.id)

if __name__ == "__main__":
    main()
