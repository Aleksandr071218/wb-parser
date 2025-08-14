import os
from clickhouse_connect import get_client
from clickhouse_connect.driver.exceptions import ClickHouseError
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from logging_config import get_logger

logger = get_logger(__name__)

@retry(
    stop=stop_after_attempt(5),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    retry=retry_if_exception_type(Exception), # A more specific exception like ConnectionError would be better
    before_sleep=lambda retry_state: logger.warning(f"Retrying ClickHouse connection attempt {retry_state.attempt_number}...")
)
def get_clickhouse_client():
    """Establishes a connection to ClickHouse, with retries."""
    client = get_client(
        host=os.getenv('CLICKHOUSE_HOST', 'localhost'),
        port=int(os.getenv('CLICKHOUSE_PORT', 8123)),
        username=os.getenv('CLICKHOUSE_USER', 'default'),
        password=os.getenv('CLICKHOUSE_PASSWORD', ''),
        database=os.getenv('CLICKHOUSE_DB', 'wildberries_data')
    )
    logger.info(f"Connecting to ClickHouse at {os.getenv('CLICKHOUSE_HOST', 'localhost')}:{os.getenv('CLICKHOUSE_PORT', 8123)}")
    client.ping()
    logger.info("ClickHouse connection successful.")
    return client

# Initialize client with retries
try:
    client = get_clickhouse_client()
except Exception as e:
    logger.error("Failed to connect to ClickHouse after multiple retries.", exc_info=True)
    client = None


def parse_category_levels(category_raw: str):
    if not category_raw:
        return "", [None, None, None, None]
    parts = category_raw.split('_')
    category = parts[-1]
    levels = [None, None, None, None]
    for i, part in enumerate(reversed(parts)):
        if i < 4:
            levels[i] = part
    return category, levels

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=6),
    retry=retry_if_exception_type(ClickHouseError),
    before_sleep=lambda retry_state: logger.warning(f"Retrying DB insert for article {retry_state.args[0].get('article', 'N/A')}, attempt {retry_state.attempt_number}...")
)
def insert_product_if_new(data: dict):
    if not client:
        logger.error("ClickHouse client not available. Skipping insert.")
        return

    article = data.get("article", "")
    if not article:
        logger.warning("Skipped insert: no article provided.", extra={"data": data})
        return

    try:
        result = client.query(
            "SELECT count() FROM wildberries_products_parsed WHERE article = %(article)s",
            parameters={'article': article}
        )
        existing = result.result_rows[0][0] if result.result_rows else 0

        if existing > 0:
            logger.debug(f"Article {article} already exists. Skipping.")
            return
    except ClickHouseError as check_e:
        logger.error(f"Error checking existence of article {article}. Retrying...", exc_info=True)
        raise # Re-raise to trigger tenacity retry
    except Exception as e:
        logger.error(f"Non-retryable error checking existence of article {article}.", exc_info=True)
        return # Do not proceed with insert

    category_raw = data.get("category", "")
    if category_raw:
        category, (category_l1, category_l2, category_l3, category_l4) = parse_category_levels(category_raw)
    else:
        category, category_l1, category_l2, category_l3, category_l4 = "", "", "", "", ""

    insert_data = (
        article,
        data.get("link", ""),
        category_raw,
        category,
        category_l1,
        category_l2,
        category_l3,
        category_l4
    )

    try:
        client.insert(
            table='wildberries_products_parsed',
            data=[insert_data],
            column_names=['article', 'product_url', 'category_raw', 'category', 'category_l1', 'category_l2', 'category_l3', 'category_l4']
        )
        logger.info(f"Successfully inserted article {article}.")
    except ClickHouseError as e:
        logger.error(f"Failed to insert product {article}. Retrying...", exc_info=True)
        raise # Re-raise to trigger tenacity retry
    except Exception as e:
        logger.error(f"Non-retryable error inserting product {article}.", exc_info=True, extra={"insert_data": insert_data})
        # Do not re-raise, just log and fail for this item
