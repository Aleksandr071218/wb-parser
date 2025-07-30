
import os
import sys
from urllib.parse import urlparse, parse_qs, urlencode
from selenium_parser.parsers.wildberries_price_range_parser import WildberriesPriceRangeParser

def prepare_url(url):
    """Prepare URL for parsing by adding necessary parameters."""
    print(f"Preparing URL: {url}")
    parsed = urlparse(url)
    
    # Get base URL without query parameters
    base_url = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
    
    # Parse existing query parameters
    params = parse_qs(parsed.query)
    
    # Update with our parameters
    params.update({
        'sort': ['popular'],
        'page': ['1'],
        'priceU': ['100;1000000000']  # from 1 RUB to 1M RUB
    })
    
    # Rebuild the URL
    new_query = urlencode(params, doseq=True)
    result = f"{base_url}?{new_query}"
    print(f"Prepared URL: {result}")
    return result

def main():
    print("=== Wildberries Parser ===\n")
    
    # Default test URL
    default_url = "https://www.wildberries.ru/catalog/obuv/detskaya"
    
    # Get URL from command line or use default
    if len(sys.argv) > 1:
        url = sys.argv[1]
    else:
        url = input(f"Enter Wildberries category URL [default: {default_url}]: ").strip()
        if not url:
            url = default_url
            print(f"Using default URL: {url}")
    
    try:
        # Prepare the URL
        start_url = prepare_url(url)
        
        # Create output directory
        os.makedirs("output", exist_ok=True)
        
        # Run the parser
        print("\nStarting parser...")
        parser = WildberriesPriceRangeParser(start_url)
        parser.run()
        print("\nParsing completed successfully!")
        
    except KeyboardInterrupt:
        print("\nParsing interrupted by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\nAn error occurred: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
