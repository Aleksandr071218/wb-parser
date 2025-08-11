import time
import re
import os
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException, WebDriverException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
from tenacity import retry, stop_after_attempt, wait_fixed, retry_if_exception_type

from selenium_parser import settings
from selenium_parser.utils.price_range_utils import find_suitable_upper
from selenium_parser.parsers.wildberries_parser_v2 import parse_products_from_page
from selenium_parser.utils.clickhouse_insert import insert_product_if_new
from logging_config import get_logger

logger = get_logger(__name__)


class WildberriesPriceRangeParser:
    def __init__(self, start_url):
        self.start_url = start_url
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")

        selenium_remote_url = os.getenv("SELENIUM_REMOTE_URL")
        if selenium_remote_url:
            logger.info(f"Connecting to remote Selenium at {selenium_remote_url}")
            self.driver = webdriver.Remote(
                command_executor=selenium_remote_url,
                options=chrome_options
            )
        else:
            logger.info("Starting local Selenium driver")
            try:
                driver_path = settings.CHROMEDRIVER_PATH
            except AttributeError:
                driver_path = None

            if driver_path:
                service = ChromeService(executable_path=driver_path)
                self.driver = webdriver.Chrome(service=service, options=chrome_options)
            else:
                service = ChromeService(ChromeDriverManager().install())
                self.driver = webdriver.Chrome(service=service, options=chrome_options)

        self.driver.implicitly_wait(5)

        from urllib.parse import urlparse
        parts = urlparse(self.start_url)
        self.base_domain = f"{parts.scheme}://{parts.netloc}"

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_fixed(2),
        retry=retry_if_exception_type(WebDriverException),
        before_sleep=lambda retry_state: logger.warning(f"Retrying driver.get() attempt {retry_state.attempt_number}...")
    )
    def get_with_retry(self, url: str):
        self.driver.get(url)

    def run(self):
        start_url = self.start_url
        seen_links = set()

        logger.info(f"Starting parsing for URL: {start_url}")
        self.get_with_retry(start_url)
        time.sleep(2)

        from urllib.parse import urlparse, unquote
        path = urlparse(start_url).path
        if path.endswith("/"):
            path = path[:-1]

        if "/catalog/" in path:
            cat_path = path.split("/catalog/")[1]
            category_name = unquote(cat_path.replace("/", "_"))
        else:
            cat_path = path.strip("/")
            category_name = unquote(cat_path.replace("/", "_"))

        logger.info(f"Target category: {category_name}")

        lower_match = re.search(r'priceU=(\d+)%3B\d+', start_url)
        current_lower = int(lower_match.group(1)) / 100.0 if lower_match else 1.0

        block_num = 1
        while True:
            logger.info(f"Searching for price range #{block_num} with lower bound {current_lower:.2f} RUB...")
            upper_price, count = find_suitable_upper(self.driver, start_url, current_lower)
            if upper_price is None:
                logger.warning("Failed to select a suitable price range. Exiting.")
                break

            lower_param = int(current_lower * 100)
            upper_param = int(upper_price * 100)
            range_url = re.sub(r'priceU=\d+%3B\d+', f'priceU={lower_param}%3B{upper_param}', start_url)
            logger.info(f"Collecting products in range: {current_lower:.2f} – {upper_price:.2f} RUB.")

            self.get_with_retry(range_url)
            time.sleep(2)
            page_number = 1

            while True:
                logger.info(f"Scrolling page {page_number}...")
                while True:
                    self.driver.execute_script("window.scrollBy(0, 450);")
                    time.sleep(0.25)
                    new_height = self.driver.execute_script("return window.pageYOffset + window.innerHeight")
                    total_height = self.driver.execute_script("return document.body.scrollHeight")
                    if new_height >= total_height - 10:
                        break
                time.sleep(1)

                html = self.driver.page_source
                products = parse_products_from_page(html, self.base_domain, category_name)
                new_count = 0

                for p in products:
                    if p["link"] not in seen_links:
                        insert_product_if_new(p)
                        seen_links.add(p["link"])
                        new_count += 1

                logger.info(f"Page {page_number}: found {new_count} new products.")

                try:
                    next_btn = self.driver.find_element(By.LINK_TEXT, "Next page")
                    time.sleep(1)
                    next_btn.click()
                    page_number += 1
                    time.sleep(2)
                except NoSuchElementException:
                    logger.info("No 'Next page' button found. End of category range.")
                    break

            current_lower = upper_price
            block_num += 1

        self.driver.quit()
        logger.info(f"Collection finished. Total unique products found: {len(seen_links)}")


def run_price_range_parser(url: str, step: float = 5000, max_products: int = 6000):
    parser = WildberriesPriceRangeParser(start_url=url)
    parser.run()
