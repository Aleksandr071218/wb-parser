# selenium_parser/utils/price_range_utils.py
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By

# Настройки диапазона и шага
target_min_count = 5000  # желаемое минимальное количество товаров в диапазоне
target_max_count = 6000  # желаемое максимальное количество товаров в диапазоне
min_step = 0.1           # минимальный шаг для изменения границы (в рублях)

def get_products_count(driver):
    """Извлекает количество товаров с текущей страницы."""
    try:
        # Сначала попробуем найти элемент с количеством товаров
        count_elements = driver.find_elements(By.XPATH, "//h1/following-sibling::p[contains(@class, 'goods-count')] | "
                                                    "//div[contains(@class, 'catalog-title')]//span[contains(text(), 'товар')] | "
                                                    "//h1[contains(text(), 'товар')]")

        for element in count_elements:
            text = element.text.strip()
            # Ищем число в тексте (может быть в формате "143 816 товаров")
            import re
            match = re.search(r'(\d[\d\s]*)\s*товар', text)
            if match:
                # Удаляем все нецифровые символы и преобразуем в число
                count_str = re.sub(r'[^\d]', '', match.group(1))
                try:
                    return int(count_str)
                except (ValueError, AttributeError):
                    continue

        # Если не найдено в стандартных местах, попробуем найти число на странице
        page_text = driver.page_source
        matches = re.findall(r'(\d[\d\s]*) товар', page_text)
        if matches:
            try:
                return int(matches[0].replace(' ', ''))
            except (ValueError, AttributeError):
                pass

        # Если ничего не найдено, возвращаем None
        return None

    except Exception as e:
        print(f"Ошибка при получении количества товаров: {e}")
        return None


def find_suitable_upper(driver, base_url, lower_price):
    """
    Подбирает верхнюю границу цены (в рублях) для заданной lower_price,
    чтобы количество товаров находилось между target_min_count и target_max_count.
    Возвращает кортеж (upper_price, count) или (None, None), если подходящий диапазон не найден.
    """
    # Начальные границы для поиска
    low_price = lower_price
    # Начальный максимум (верхняя граница) - берем его либо из base_url (если там указан upper), либо очень большое число
    import re
    upper_match = re.search(r'priceU=\d+%3B(\d+)', base_url)
    if upper_match:
        # priceU указан в копейках, конвертируем в рубли
        max_upper_price = int(upper_match.group(1)) / 100.0
    else:
        max_upper_price = 10000000.0  # 10 миллионов рублей (значение по умолчанию)
    high_price = max_upper_price

    suitable_upper = None
    suitable_count = None

    # Выполняем бинарный поиск по верхней границе цены
    # Определяем функцию для загрузки страницы с текущим диапазоном и получения количества товаров
    def load_and_count(lower, upper):
        # Формируем URL с указанным диапазоном цен
        lower_param = int(lower * 100)
        upper_param = int(upper * 100)
        url = re.sub(r'priceU=\d+%3B\d+', f'priceU={lower_param}%3B{upper_param}', base_url)
        driver.get(url)
        try:
            # Ждем, пока на странице не появится количество товаров (или сами товары)
            WebDriverWait(driver, 10).until(lambda d: get_products_count(d) is not None)
        except Exception:
            pass
        count = get_products_count(driver)
        return count

    # Получаем общее количество товаров для начального максимального предела
    total_count = load_and_count(low_price, high_price)
    if total_count is None:
        print("Не удалось получить количество товаров для начального диапазона.")
        return None, None
    # Если общее количество товаров уже ниже минимального порога (т.е. вся категория имеет < 5000 товаров)
    # Возвращаем текущий верхний предел как подходящий (все товары) и количество.
    if total_count < target_min_count:
        return high_price, total_count

    # В противном случае, начинаем подбор верхней границы
    # Диапазон верхних значений: [low_price, high_price]
    left = low_price
    right = high_price

    while left <= right:
        mid = (left + right) / 2.0
        count = load_and_count(low_price, mid)
        if count is None:
            # Если не удалось получить количество (неожиданная ошибка парсинга), прекращаем поиск
            break
        # Проверяем, находимся ли мы в нужном диапазоне
        if target_min_count <= count <= target_max_count:
            suitable_upper = mid
            suitable_count = count
            break
        # Если товаров слишком много, уменьшаем верхнюю границу
        if count > target_max_count:
            suitable_upper = mid  # запоминаем текущий mid как последний, который дает >6000
            right = mid - 0.1  # уменьшаем верхний предел, шаг 0.1 руб
        else:
            # Если товаров слишком мало, увеличиваем верхнюю границу
            left = mid + 0.1
        # Если интервал поиска сузился до минимального шага
        if (right - left) < min_step:
            # Выходим из цикла, дальнейшее уточнение бессмысленно
            break

    # Округляем верхнюю цену вниз до ближайших 0.1 руб (чтобы не захватить лишние товары на граничном значении)
    if suitable_upper is not None:
        suitable_upper = round(suitable_upper, 2)
        # Повторно получаем точное количество товаров для округленного верхнего значения
        final_count = load_and_count(low_price, suitable_upper)
        suitable_count = final_count if final_count is not None else suitable_count

    return suitable_upper, suitable_count
