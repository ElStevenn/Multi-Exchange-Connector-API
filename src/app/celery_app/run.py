# src/app/celery/run.py
import sys

if len(sys.argv) > 1 and sys.argv[1] == "test":
    from src.app.celery_app.tasks import fetch_user_assets_concurrently
else:
    from app.celery_app.tasks import fetch_user_assets_concurrently

def main():
    result = fetch_user_assets_concurrently.apply_async(queue='once_off_queue')
    print("Task ID:", result.id)

if __name__ == "__main__":
    main()
