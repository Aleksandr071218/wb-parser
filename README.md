# WB-Parser

A powerful Python-based parser for Wildberries, with smart price range filtering, full page scrolling, pagination, and ClickHouse integration for storing extracted product data. The project features an asynchronous API for non-blocking task management.

## Features

- Automatically adjusts price ranges to bypass the 6000-item limit
- Parses all pages of a category
- **Asynchronous API:** Start parsing jobs without waiting for them to complete.
- **Task Status Tracking:** Check the status and results of parsing jobs.
- Scrolls to the bottom of each page to load dynamic content
- Stores data in ClickHouse
- Deploys as a containerized service with Docker Compose.

---

## Running with Docker (Recommended)

This project is designed to run with Docker and Docker Compose, which simplifies setup and deployment.

### Prerequisites

- [Docker](https://docs.docker.com/get-docker/)
- [Docker Compose](https://docs.docker.com/compose/install/)

### Quick Start

1.  **Clone the repository and navigate to the directory.**

2.  **Build and start the services:**
    From the `wb-parser-final` directory, run:
    ```bash
    docker-compose up --build -d
    ```
    This command will build and start all services (app, worker, selenium, redis, clickhouse) in detached mode.

3.  **Run the parser via API:**
    Once the services are running, you can trigger the parser by sending a request to the API as described in the "API Usage" section below.

4.  **Shutting down:**
    To stop all running services, run:
    ```bash
    docker-compose down
    ```

---

## API Usage

The application uses an asynchronous API. You first submit a job, which returns a `task_id`. You can then use this ID to check the status of the job.

### 1. Submit a Parsing Task

- **Endpoint:** `POST /parse`
- **Method:** `POST`
- **Body:** A JSON object with the URL and optional parameters.
  ```json
  {
    "url": "https://www.wildberries.ru/catalog/obuv/muzhskaya/kedy-i-krossovki",
    "step": 5000,
    "max_products": 6000
  }
  ```

**Example `curl` command:**
```bash
curl -X POST "http://localhost:8000/parse" \
-H "Content-Type: application/json" \
-d '{"url": "https://www.wildberries.ru/catalog/obuv/muzhskaya/kedy-i-krossovki"}'
```

**Successful Response (202 Accepted):**
The API will immediately respond with a task ID.
```json
{
  "task_id": "a1b2c3d4-e5f6-7890-1234-567890abcdef",
  "status": "Accepted"
}
```

### 2. Check Task Status

- **Endpoint:** `GET /tasks/{task_id}`
- **Method:** `GET`

**Example `curl` command:**
```bash
curl http://localhost:8000/tasks/a1b2c3d4-e5f6-7890-1234-567890abcdef
```

**Response:**
The response will show the current status of the task (`PENDING`, `STARTED`, `SUCCESS`, `FAILURE`). If the task is complete, the `result` field will be populated.
```json
{
  "task_id": "a1b2c3d4-e5f6-7890-1234-567890abcdef",
  "status": "SUCCESS",
  "result": {
    "status": "Completed",
    "url": "https://www.wildberries.ru/catalog/obuv/muzhskaya/kedy-i-krossovki"
  }
}
```
If the task failed, the `result` will contain error information.

---

## Local Development (Alternative)

### System Requirements

- Python 3.8+
- Google Chrome & `chromedriver`
- **Redis Server**
- **ClickHouse Instance**

### Setup

1.  **Install dependencies:**
    ```bash
    pip install -r project/requirements.txt
    ```

2.  **Configure Environment:**
    Ensure you have running instances of Redis and ClickHouse. Set the following environment variables if they are not running on default ports on localhost:
    - `CLICKHOUSE_HOST`, `CLICKHOUSE_PORT`, etc.
    - `CELERY_BROKER_URL`, `CELERY_RESULT_BACKEND`

3.  **Run the API server:**
    ```bash
    uvicorn project.api:app --reload
    ```
4.  **Run the Celery worker:**
    In a separate terminal, run:
    ```bash
    celery -A project.celery_app.celery worker --loglevel=info
    ```
