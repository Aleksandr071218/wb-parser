import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
import sys
import os

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# We need to import the app from the project
from project.api import app

@pytest_asyncio.fixture
async def async_client():
    """
    Provides an asynchronous client for making requests to the FastAPI app.
    """
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        yield client

@pytest.mark.asyncio
async def test_submit_parsing_task_success(async_client: AsyncClient, mocker):
    """
    Tests successful submission of a parsing task.
    """
    # Mock the Celery task where it's looked up (in the api module)
    mock_task = mocker.patch('project.api.create_parsing_task.delay')
    # Configure the mock to have an 'id' attribute, just like a real Celery task result
    mock_task.return_value.id = "fake-task-id-123"

    payload = {"url": "https://www.wildberries.ru/catalog/elektronika"}
    response = await async_client.post("/parse", json=payload)

    assert response.status_code == 202
    data = response.json()
    assert data["task_id"] == "fake-task-id-123"
    assert data["status"] == "Accepted"
    # Ensure our mock was called once with the correct arguments
    mock_task.assert_called_once_with(
        url="https://www.wildberries.ru/catalog/elektronika",
        step=5000,
        max_products=6000
    )

@pytest.mark.asyncio
async def test_get_task_status_success(async_client: AsyncClient, mocker):
    """
    Tests retrieving the status of a successfully completed task.
    """
    # Mock the AsyncResult class to simulate a finished task
    mock_async_result = mocker.patch('project.api.AsyncResult')
    mock_instance = mock_async_result.return_value
    mock_instance.status = "SUCCESS"
    mock_instance.result = {"status": "Completed", "url": "some_url"}
    mock_instance.failed.return_value = False

    response = await async_client.get("/tasks/fake-task-id-123")

    assert response.status_code == 200
    data = response.json()
    assert data["task_id"] == "fake-task-id-123"
    assert data["status"] == "SUCCESS"
    assert data["result"]["status"] == "Completed"

@pytest.mark.asyncio
async def test_get_task_status_pending(async_client: AsyncClient, mocker):
    """
    Tests retrieving the status of a pending task.
    """
    # Mock the AsyncResult class to simulate a pending task
    mock_async_result = mocker.patch('project.api.AsyncResult')
    mock_instance = mock_async_result.return_value
    mock_instance.status = "PENDING"
    mock_instance.result = None
    mock_instance.failed.return_value = False

    response = await async_client.get("/tasks/fake-task-id-456")

    assert response.status_code == 200
    data = response.json()
    assert data["task_id"] == "fake-task-id-456"
    assert data["status"] == "PENDING"
    assert data["result"] is None

@pytest.mark.asyncio
async def test_get_task_status_failed(async_client: AsyncClient, mocker):
    """
    Tests retrieving the status of a failed task.
    """
    # Mock the AsyncResult class to simulate a failed task
    mock_async_result = mocker.patch('project.api.AsyncResult')
    mock_instance = mock_async_result.return_value
    mock_instance.status = "FAILURE"
    mock_instance.result = "Something went wrong"
    mock_instance.traceback = "Traceback details..."
    mock_instance.failed.return_value = True

    response = await async_client.get("/tasks/fake-task-id-789")

    assert response.status_code == 200
    data = response.json()
    assert data["task_id"] == "fake-task-id-789"
    assert data["status"] == "FAILURE"
    assert "error" in data["result"]
    assert "traceback" in data["result"]
