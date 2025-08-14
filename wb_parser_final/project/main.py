import os
import sys
from urllib.parse import urlparse, parse_qs, urlencode
from selenium_parser.parsers.wildberries_price_range_parser import WildberriesPriceRangeParser

def prepare_url(url):
    """Подготавливает URL для парсинга, добавляя необходимые параметры."""
    print(f"Подготовка URL: {url}")
    parsed = urlparse(url)

    # Получаем базовый URL без параметров запроса
    base_url = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"

    # Парсим существующие параметры запроса
    params = parse_qs(parsed.query)

    # Обновляем нашими параметрами
    params.update({
        'sort': ['popular'],
        'page': ['1'],
        'priceU': ['100;1000000000']  # от 1 до 1 млн рублей
    })

    # Пересобираем URL
    new_query = urlencode(params, doseq=True)
    result = f"{base_url}?{new_query}"
    print(f"Подготовленный URL: {result}")
    return result

def main():
    print("=== Парсер Wildberries ===\n")

    # URL для теста по умолчанию
    default_url = "https://www.wildberries.ru/catalog/obuv/detskaya"

    # Получаем URL из командной строки или используем по умолчанию
    if len(sys.argv) > 1:
        url = sys.argv[1]
    else:
        url = input(f"Введите URL категории Wildberries [по умолчанию: {default_url}]: ").strip()
        if not url:
            url = default_url
            print(f"Используется URL по умолчанию: {url}")

    try:
        # Подготавливаем URL
        start_url = prepare_url(url)

        # Создаем выходную директорию
        os.makedirs("output", exist_ok=True)

        # Запускаем парсер
        print("\nЗапуск парсера...")
        parser = WildberriesPriceRangeParser(start_url)
        parser.run()
        print("\nПарсинг успешно завершен!")

    except KeyboardInterrupt:
        print("\nПарсинг прерван пользователем.")
        sys.exit(1)
    except Exception as e:
        print(f"\nПроизошла ошибка: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
