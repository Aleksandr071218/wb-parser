import os
from celery import Celery
from selenium_parser.parsers.wildberries_price_range_parser import run_price_range_parser

# Get broker and backend URLs from environment variables, with defaults for local dev
broker_url = os.getenv('CELERY_BROKER_URL', 'redis://localhost:6379/0')
result_backend_url = os.getenv('CELERY_RESULT_BACKEND', 'redis://localhost:6379/0')

# Create a Celery instance
# The first argument is the name of the current module, important for auto-discovery of tasks.
celery = Celery(
    __name__,
    broker=broker_url,
    backend=result_backend_url
)

# Optional: Configure Celery settings
celery.conf.update(
    task_track_started=True,
    result_expires=3600,  # Store results for 1 hour
    # It might be useful to define a specific queue if you expand later
    # task_default_queue='default',
)

@celery.task(name='create_parsing_task')
def create_parsing_task(url: str, step: float, max_products: int):
    """
    Celery task to run the Wildberries parser in the background.
    """
    print(f"Received parsing task for URL: {url}")
    try:
        # This function contains the entire parsing logic
        run_price_range_parser(url=url, step=step, max_products=max_products)
        return {'status': 'Completed', 'url': url}
    except Exception as e:
        # Log the exception for debugging
        print(f"Task failed for URL {url}: {e}")
        # Re-raising the exception will mark the task as FAILED in Celery
        # and store the traceback in the result backend.
        raise
