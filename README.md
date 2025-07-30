WB-Parser
A robust Python-based web scraper for Wildberries that dynamically adjusts price filters to bypass product limits, paginates through all available items, extracts product links and details, and stores the data in ClickHouse for further analysis.
Wildberries Parser

A powerful Python-based parser for Wildberries, with smart price range filtering, full page scrolling, pagination, and ClickHouse integration for storing extracted product data.



Features

- Automatically adjusts price ranges to bypass the 6000-item limit
- Parses all pages of a category
- Scrolls to the bottom of each page to load dynamic content
- Extracts product links using `BeautifulSoup`
- Stores data in ClickHouse
- Flexible configuration and easy to scale



Quick Start

Install dependencies
pip install -r requirements.txt
 
 
System Requirements
Python: Version 3.8 or higher
Google Chrome: Installed on your system
ChromeDriver
