import time
import re
import os
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager

from selenium_parser import settings
from selenium_parser.utils.price_range_utils import find_suitable_upper, target_min_count, target_max_count
from selenium_parser.parsers.wildberries_parser_v2 import parse_products_from_page
from selenium_parser.utils.clickhouse_insert import insert_product_if_new  # 👈 ClickHouse integration


class WildberriesPriceRangeParser:
    def __init__(self, start_url):
        self.start_url = start_url
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")

        selenium_remote_url = os.getenv("SELENIUM_REMOTE_URL")
        if selenium_remote_url:
            print(f"🔌 Connecting to remote Selenium at {selenium_remote_url}")
            self.driver = webdriver.Remote(
                command_executor=selenium_remote_url,
                options=chrome_options
            )
        else:
            print("🚀 Starting local Selenium driver")
            # Check for CHROMEDRIVER_PATH in settings for local development
            try:
                driver_path = settings.CHROMEDRIVER_PATH
            except AttributeError:
                driver_path = None

            if driver_path:
                service = ChromeService(executable_path=driver_path)
                self.driver = webdriver.Chrome(service=service, options=chrome_options)
            else:
                # If no path is set, use webdriver-manager
                service = ChromeService(ChromeDriverManager().install())
                self.driver = webdriver.Chrome(service=service, options=chrome_options)

        self.driver.implicitly_wait(5)

        # Base domain
        from urllib.parse import urlparse
        parts = urlparse(self.start_url)
        self.base_domain = f"{parts.scheme}://{parts.netloc}"

    def run(self):
        driver = self.driver
        start_url = self.start_url
        seen_links = set()

        driver.get(start_url)
        time.sleep(2)

        # Extract category from URL
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

        print(f"📦 Category: {category_name}")

        lower_match = re.search(r'priceU=(\d+)%3B\d+', start_url)
        current_lower = int(lower_match.group(1)) / 100.0 if lower_match else 1.0

        block_num = 1
        while True:
            print(f"\n🔎 Range #{block_num} with lower bound {current_lower:.2f} RUB...")
            upper_price, count = find_suitable_upper(driver, start_url, current_lower)
            if upper_price is None:
                print("❌ Failed to select a range. Exiting.")
                break

            lower_param = int(current_lower * 100)
            upper_param = int(upper_price * 100)
            range_url = re.sub(r'priceU=\d+%3B\d+', f'priceU={lower_param}%3B{upper_param}', start_url)
            print(f"📊 Collecting: {current_lower:.2f} – {upper_price:.2f} RUB.")

            driver.get(range_url)
            time.sleep(2)
            page_number = 1

            while True:
                print("📜 Scrolling page...")
                while True:
                    driver.execute_script("window.scrollBy(0, 450);")
                    time.sleep(0.25)
                    new_height = driver.execute_script("return window.pageYOffset + window.innerHeight")
                    total_height = driver.execute_script("return document.body.scrollHeight")
                    if new_height >= total_height - 10:
                        break
                time.sleep(1)

                html = driver.page_source
                products = parse_products_from_page(html, self.base_domain, category_name)
                new_count = 0

                for p in products:
                    if p["link"] not in seen_links:
                        insert_product_if_new(p)  # 👈 Insert into ClickHouse
                        seen_links.add(p["link"])
                        new_count += 1

                print(f"📄 Page {page_number}: +{new_count} new")

                try:
                    next_btn = driver.find_element(By.LINK_TEXT, "Next page")
                    time.sleep(1)
                    next_btn.click()
                    page_number += 1
                    time.sleep(2)
                except NoSuchElementException:
                    break

            current_lower = upper_price
            block_num += 1

        driver.quit()
        print(f"✅ Collection finished. Total new products: {len(seen_links)}")


# 🆕 Function to be called via FastAPI or main.py
def run_price_range_parser(url: str, step: float = 5000, max_products: int = 6000):
    parser = WildberriesPriceRangeParser(start_url=url)
    parser.run()
