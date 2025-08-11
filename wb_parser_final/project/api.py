from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, HttpUrl
from celery.result import AsyncResult
from typing import Any
from logging_config import setup_logging, get_logger

# Import the celery app instance to get task results
from celery_app import celery, create_parsing_task

# Setup logging for the API
setup_logging()
logger = get_logger(__name__)

app = FastAPI(
    title="Wildberries Parser API",
    description="An API to trigger and manage parsing tasks for Wildberries categories.",
    version="2.0.0"
)

# --- Pydantic Models ---

class ParseRequest(BaseModel):
    url: HttpUrl
    step: float = 5000
    max_products: int = 6000

class TaskResponse(BaseModel):
    task_id: str
    status: str

class StatusResponse(BaseModel):
    task_id: str
    status: str
    result: Any | None = None

# --- API Endpoints ---

@app.post("/parse", response_model=TaskResponse, status_code=202)
def submit_parsing_task(request: ParseRequest):
    """
    Queues a new parsing task for a given Wildberries category URL.

    This endpoint accepts the request and immediately returns a task ID
    without waiting for the parsing to complete.
    """
    logger.info(f"Received parsing request for URL: {request.url}")
    task = create_parsing_task.delay(
        url=str(request.url),
        step=request.step,
        max_products=request.max_products
    )
    logger.info(f"Task {task.id} created for URL: {request.url}")
    return {"task_id": task.id, "status": "Accepted"}


@app.get("/tasks/{task_id}", response_model=StatusResponse)
def get_task_status(task_id: str):
    """
    Retrieves the status and result of a background task.
    """
    logger.debug(f"Checking status for task ID: {task_id}")
    task_result = AsyncResult(task_id, app=celery)

    if not task_result:
        raise HTTPException(status_code=404, detail="Task not found")

    result = task_result.result
    if task_result.failed():
        result = {
            "error": str(task_result.result),
            "traceback": task_result.traceback
        }

    return {
        "task_id": task_id,
        "status": task_result.status,
        "result": result
    }
