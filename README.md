# WB-Parser

A powerful Python-based parser for Wildberries, with smart price range filtering, full page scrolling, pagination, and ClickHouse integration for storing extracted product data.

## Features

- Automatically adjusts price ranges to bypass the 6000-item limit
- Parses all pages of a category
- Scrolls to the bottom of each page to load dynamic content
- Extracts product links using `BeautifulSoup`
- Stores data in ClickHouse
- Deploys as a containerized service with a remote-control API

---

## Running with Docker (Recommended)

This project is designed to run with Docker and Docker Compose, which simplifies setup and deployment.

### Prerequisites

- [Docker](https://docs.docker.com/get-docker/)
- [Docker Compose](https://docs.docker.com/compose/install/)

### Quick Start

1.  **Clone the repository:**
    ```bash
    git clone <repository-url>
    cd wb-parser-final
    ```

2.  **Build and start the services:**
    From the `wb-parser-final` directory, run:
    ```bash
    docker-compose up --build
    ```
    This command will build the Docker image for the application, download the necessary images for Selenium and ClickHouse, and start all services.

3.  **Run the parser via API:**
    Once the services are running, you can trigger the parser by sending a request to the API.

4.  **Shutting down:**
    To stop all running services, press `Ctrl+C` in the terminal, and then run:
    ```bash
    docker-compose down
    ```

---

## API Usage

The application exposes a FastAPI server for remote control.

- **Endpoint:** `GET /parse/`
- **URL:** `http://localhost:8000/parse/`

**Parameters:**
- `url` (required): The full URL to a Wildberries category.
- `step` (optional, default: 5000): The price step for range adjustments.
- `max_products` (optional, default: 6000): The product limit to stay under.

**Example using `curl`:**
```bash
curl -X GET "http://localhost:8000/parse/?url=https://www.wildberries.ru/catalog/obuv/muzhskaya/kedy-i-krossovki"
```

---

## Local Development (Alternative)

If you prefer to run the application without Docker, you can set it up locally.

### System Requirements

- Python 3.8+
- Google Chrome
- `chromedriver` (or use `webdriver-manager` which is included in `requirements.txt`)

### Setup

1.  **Install dependencies:**
    ```bash
    pip install -r project/requirements.txt
    ```

2.  **Configure ClickHouse:**
    Ensure you have a running ClickHouse instance and update the connection details in `project/selenium_parser/utils/clickhouse_insert.py` or set the corresponding environment variables (`CLICKHOUSE_HOST`, `CLICKHOUSE_PORT`, etc.).

3.  **Run the API server:**
    ```bash
    uvicorn project.api:app --reload
    ```
The server will be available at `http://localhost:8000`.
