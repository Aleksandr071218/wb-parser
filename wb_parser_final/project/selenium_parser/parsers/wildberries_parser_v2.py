# selenium_parser/parsers/wildberries_parser_v2.py
from bs4 import BeautifulSoup
from urllib.parse import urlparse

def parse_products_from_page(html, base_domain, category_name):
    """
    Parses the HTML of a Wildberries catalog page and extracts all product links.
    :param html: The HTML code of the page (fully loaded with all products).
    :param base_domain: The base domain of the site (e.g., 'https://global.wildberries.ru'),
                        used to form the full URL.
    :param category_name: The name of the category to save in the data.
    :return: A list of dictionaries {"category": category, "link": link, "article": article}.
    """
    soup = BeautifulSoup(html, "html.parser")
    products = []
    # Find all links to product cards by the presence of 'detail.aspx' in href
    product_links = soup.find_all("a", href=lambda href: href and "detail.aspx" in href)
    for a in product_links:
        href = a.get("href")
        if not href:
            continue
        # Form the full URL: if the link is relative (starts with '/'), add the domain
        if href.startswith("/"):
            full_link = base_domain + href
        elif href.startswith("http"):
            full_link = href
        else:
            # In case of other link formats, skip
            continue
        
        # Extract the article from the link
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
