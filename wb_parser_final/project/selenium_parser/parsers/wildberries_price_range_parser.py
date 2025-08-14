import time
import re
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

from selenium_parser import settings
from selenium_parser.utils.price_range_utils import find_suitable_upper
from selenium_parser.parsers.wildberries_parser_v2 import parse_products_from_page
from selenium_parser.utils.clickhouse_insert import insert_product_if_new  # 👈 Интеграция с ClickHouse


class WildberriesPriceRangeParser:
    def __init__(self, start_url):
        self.start_url = start_url
        chrome_options = Options()
        # chrome_options.add_argument("--headless")  # Вы можете включить headless-режим позже
        if settings.CHROMEDRIVER_PATH:
            self.driver = webdriver.Chrome(settings.CHROMEDRIVER_PATH, options=chrome_options)
        else:
            self.driver = webdriver.Chrome(options=chrome_options)
        self.driver.implicitly_wait(5)

        # Базовый домен
        from urllib.parse import urlparse
        parts = urlparse(self.start_url)
        self.base_domain = f"{parts.scheme}://{parts.netloc}"

    def run(self):
        driver = self.driver
        start_url = self.start_url
        seen_links = set()

        driver.get(start_url)
        time.sleep(2)

        # Извлекаем категорию из URL
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

        print(f"📦 Категория: {category_name}")

        lower_match = re.search(r'priceU=(\d+)%3B\d+', start_url)
        current_lower = int(lower_match.group(1)) / 100.0 if lower_match else 1.0

        block_num = 1
        while True:
            print(f"\n🔎 Диапазон #{block_num} с нижней границей {current_lower:.2f} RUB...")
            upper_price, count = find_suitable_upper(driver, start_url, current_lower)
            if upper_price is None:
                print("❌ Не удалось подобрать диапазон. Выход.")
                break

            lower_param = int(current_lower * 100)
            upper_param = int(upper_price * 100)
            range_url = re.sub(r'priceU=\d+%3B\d+', f'priceU={lower_param}%3B{upper_param}', start_url)
            print(f"📊 Сбор: {current_lower:.2f} – {upper_price:.2f} RUB.")

            driver.get(range_url)
            time.sleep(2)
            page_number = 1

            while True:
                print("📜 Прокрутка страницы...")
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
                        insert_product_if_new(p)  # 👈 Вставляем в ClickHouse
                        seen_links.add(p["link"])
                        new_count += 1

                print(f"📄 Страница {page_number}: +{new_count} новых")

                try:
                    # Ищем кнопку "Следующая страница" по классу, чтобы избежать проблем с локализацией
                    next_btn = driver.find_element(By.XPATH, "//*[contains(@class, 'pagination-next')]")
                    time.sleep(1)
                    next_btn.click()
                    page_number += 1
                    time.sleep(2)
                except NoSuchElementException:
                    break

            current_lower = upper_price
            block_num += 1

        driver.quit()
        print(f"✅ Сбор завершен. Всего новых товаров: {len(seen_links)}")


# 🆕 Функция для вызова через FastAPI или main.py
def run_price_range_parser(url: str, step: float = 5000, max_products: int = 6000):
    parser = WildberriesPriceRangeParser(start_url=url)
    parser.run()
