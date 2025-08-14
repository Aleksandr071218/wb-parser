# selenium_parser/parsers/wildberries_parser_v2.py
from bs4 import BeautifulSoup
from urllib.parse import urlparse

def parse_products_from_page(html, base_domain, category_name):
    """
    Парсит HTML-код страницы каталога Wildberries и извлекает все ссылки на товары.
    :param html: HTML-код страницы (полностью загруженной со всеми товарами).
    :param base_domain: Базовый домен сайта (например, 'https://global.wildberries.ru'),
                        используется для формирования полного URL-адреса.
    :param category_name: Название категории для сохранения в данных.
    :return: Список словарей {"category": category, "link": link, "article": article}.
    """
    soup = BeautifulSoup(html, "html.parser")
    products = []
    # Находим все ссылки на карточки товаров по наличию 'detail.aspx' в href
    product_links = soup.find_all("a", href=lambda href: href and "detail.aspx" in href)
    for a in product_links:
        href = a.get("href")
        if not href:
            continue
        # Формируем полный URL: если ссылка относительная (начинается с '/'), добавляем домен
        if href.startswith("/"):
            full_link = base_domain + href
        elif href.startswith("http"):
            full_link = href
        else:
            # В случае других форматов ссылок, пропускаем
            continue

        # Извлекаем артикул из ссылки
        import re
        article_match = re.search(r'/catalog/(\d+)/detail\.aspx', full_link)
        article = article_match.group(1) if article_match else ""

        product = {
            "category": category_name,
            "link": full_link,
            "article": article
        }
        products.append(product)
    return products
