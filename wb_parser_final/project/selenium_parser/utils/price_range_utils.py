
# selenium_parser/utils/price_range_utils.py
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By

# Range and step settings
target_min_count = 5000  # desired minimum number of products in the range
target_max_count = 6000  # desired maximum number of products in the range
min_step = 0.1           # minimum step for changing the boundary (in RUB)

def get_products_count(driver):
    """Extracts the number of products from the current page."""
    try:
        # First, let's try to find the element with the product count
        count_elements = driver.find_elements(By.XPATH, "//h1/following-sibling::p[contains(@class, 'goods-count')] | "
                                                    "//div[contains(@class, 'catalog-title')]//span[contains(text(), 'товар')] | "
                                                    "//h1[contains(text(), 'товар')]")
        
        for element in count_elements:
            text = element.text.strip()
            # Search for a number in the text (it might be in the format "143 816 products")
            import re
            match = re.search(r'(\d[\d\s]*)\s*товар', text)
            if match:
                # Remove all non-digit characters and convert to a number
                count_str = re.sub(r'[^\d]', '', match.group(1))
                try:
                    return int(count_str)
                except (ValueError, AttributeError):
                    continue
        
        # If not found in standard places, try to find the number on the page
        page_text = driver.page_source
        matches = re.findall(r'(\d[\d\s]*) товар', page_text)
        if matches:
            try:
                return int(matches[0].replace(' ', ''))
            except (ValueError, AttributeError):
                pass
                
        # If nothing is found, return None
        return None
        
    except Exception as e:
        print(f"Error getting product count: {e}")
        return None


def find_suitable_upper(driver, base_url, lower_price):
    """
    Selects an upper price boundary (in RUB) for a given lower_price,
    so that the number of products is between target_min_count and target_max_count.
    Returns a tuple (upper_price, count) or (None, None) if a suitable range could not be found.
    """
    # Initial boundaries for the search
    low_price = lower_price
    # Initial maximum (upper boundary) - we'll take it either from base_url (if upper is specified there), or a very large number
    import re
    upper_match = re.search(r'priceU=\d+%3B(\d+)', base_url)
    if upper_match:
        # priceU is specified in kopecks, convert to rubles
        max_upper_price = int(upper_match.group(1)) / 100.0
    else:
        max_upper_price = 10000000.0  # 10 million RUB (default value if not specified)
    high_price = max_upper_price

    suitable_upper = None
    suitable_count = None

    # Perform a binary search on the upper price boundary
    # Define a function to load the page with the current range and get the product count
    def load_and_count(lower, upper):
        # Form the URL with the specified price range
        lower_param = int(lower * 100)
        upper_param = int(upper * 100)
        url = re.sub(r'priceU=\d+%3B\d+', f'priceU={lower_param}%3B{upper_param}', base_url)
        driver.get(url)
        try:
            # Wait until the product count (or the products themselves) appear on the page
            WebDriverWait(driver, 10).until(lambda d: get_products_count(d) is not None)
        except Exception:
            pass
        count = get_products_count(driver)
        return count

    # Get the total number of products for the initial maximum limit
    total_count = load_and_count(low_price, high_price)
    if total_count is None:
        print("Failed to get the number of products for the initial range.")
        return None, None
    # If the total number of products is already below the minimum threshold (meaning the whole category has < 5000 products)
    # Return the current upper limit as suitable (all products) and the count.
    if total_count < target_min_count:
        return high_price, total_count

    # Otherwise, start selecting the upper boundary
    # Range of upper values: [low_price, high_price]
    left = low_price
    right = high_price

    while left <= right:
        mid = (left + right) / 2.0
        count = load_and_count(low_price, mid)
        if count is None:
            # If we failed to get the count (unexpected parsing error), stop the search
            break
        # Check if we are in the desired range
        if target_min_count <= count <= target_max_count:
            suitable_upper = mid
            suitable_count = count
            break
        # If there are too many products, decrease the upper boundary
        if count > target_max_count:
            suitable_upper = mid  # remember the current mid as the last one that gives >6000
            right = mid - 0.1  # decrease the upper limit, step 0.1 RUB
        else:
            # If there are too few products, increase the upper boundary
            left = mid + 0.1
        # If the search interval has narrowed to the minimum step
        if (right - left) < min_step:
            # Exit the loop, further refinement is pointless
            break

    # Round the upper price down to the nearest 0.1 RUB (to avoid capturing extra products at the boundary value)
    if suitable_upper is not None:
        suitable_upper = round(suitable_upper, 2)
        # Re-get the exact number of products for the rounded upper value
        final_count = load_and_count(low_price, suitable_upper)
        suitable_count = final_count if final_count is not None else suitable_count

    return suitable_upper, suitable_count
