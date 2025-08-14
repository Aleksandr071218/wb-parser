# Use an official Python runtime as a parent image
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file into the container at /app
COPY project/requirements.txt .

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code from the 'project' directory
COPY project/ .

# Expose the port the app runs on
EXPOSE 8000

# Define the command to run the application
# Note: We refer to 'api:app' because the WORKDIR is /app, where api.py is located.
CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8000"]
