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

This project includes a lightweight FastAPI server that exposes an HTTP API for controlling the Wildberries parser remotely. It allows external tools—such as frontend clients, cron jobs, or scripts—to trigger the parsing process dynamically by sending HTTP requests. The main purpose of the FastAPI integration is to provide a clean and flexible interface for passing category URLs without modifying the code manually.

The core endpoint is POST /parse, which accepts a JSON payload containing a Wildberries category URL. When this endpoint is called, it initializes the WildberriesPriceRangeParser with the given URL and starts the entire parsing process: scrolling pages, collecting product links, and saving results to ClickHouse. This makes it easy to launch the parser on demand or integrate it into automated workflows.

To use the API, first start the FastAPI server by running:
uvicorn project.api:app --reload
Then, send a POST request to http://localhost:8000/parse with a JSON body like:
{
  "url": "https://www.wildberries.ru/catalog/obuv/muzhskaya/kedy-i-krossovki"
}
You can use tools like Postman, curl, or any HTTP client to interact with the API.

The API logic is implemented in project/api.py, and depends on fastapi and uvicorn, which can be installed via:
pip install fastapi uvicorn
This setup provides a scalable and extensible foundation for remote control, integration with external systems, or deployment in Dockerized environments with API endpoints.

