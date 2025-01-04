# src/app/celery/run.py
import sys

if len(sys.argv) > 1 and sys.argv[1] == "test":
    from src.app.celery.tasks import fetch_user_assets_concurrently
else:
    from app.celery.tasks import fetch_user_assets_concurrently

def main():
    result = fetch_user_assets_concurrently.delay()
    print("Task ID:", result.id)

if __name__ == "__main__":
    main()
