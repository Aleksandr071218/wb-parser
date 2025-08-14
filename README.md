# WB-Parser

A powerful Python-based parser for Wildberries, with smart price range filtering, full page scrolling, pagination, and ClickHouse integration for storing extracted product data. The project features an asynchronous API for non-blocking task management and is covered by an automated test suite.

## Features

- Automatically adjusts price ranges to bypass the 6000-item limit
- **Asynchronous API:** Start parsing jobs without waiting for them to complete.
- **Task Status Tracking:** Check the status and results of parsing jobs.
- **Structured Logging:** All operations are logged with context for easier debugging.
- **Resilient:** Automatically retries on transient network or database errors.
- **Tested:** Includes a suite of unit and integration tests using `pytest`.
- Deploys as a containerized service with Docker Compose.
- Stores data in ClickHouse.

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
    This command will build and start all services in detached mode.

3.  **Run the parser via API:**
    Use the API as described in the "API Usage" section below.

4.  **Shutting down:**
    To stop all running services, run:
    ```bash
    docker-compose down
    ```

---

## Testing

The project includes a test suite using `pytest`.

### Running the Tests

1.  **Install all dependencies (including testing libraries):**
    ```bash
    pip install -r project/requirements.txt
    ```

2.  **Run the test suite:**
    From the root directory (`wb-parser-final`), run:
    ```bash
    PYTHONPATH=project pytest tests/
    ```
    This command sets the `PYTHONPATH` so that the tests can correctly import the application modules and then runs `pytest` on the `tests` directory.

---

## API Usage

The application uses an asynchronous API. You first submit a job, which returns a `task_id`. You can then use this ID to check the status of the job.

### 1. Submit a Parsing Task

- **Endpoint:** `POST /parse`
... (rest of the file is the same)

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
    Set environment variables if your services are not on localhost.

3.  **Run the API server:**
    ```bash
    uvicorn project.api:app --reload
    ```
4.  **Run the Celery worker:**
    In a separate terminal, run:
    ```bash
    celery -A project.celery_app.celery worker --loglevel=info
    ```
