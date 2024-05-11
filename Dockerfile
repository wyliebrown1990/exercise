# Syntax directive to use Docker Buildx. This line is optional and depends on your Docker setup.
# syntax=docker/dockerfile:1.3-labs

FROM --platform=linux/amd64 python:3.8-slim

WORKDIR /app

# Install system dependencies (if needed)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libc6-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY ./app/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY ./app .

# Expose the port used by your application
EXPOSE 5001

# Run the application
CMD ["gunicorn", "--workers=3", "--bind=0.0.0.0:5001", "app:app"]
