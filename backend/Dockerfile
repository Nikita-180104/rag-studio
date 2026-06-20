FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy and install python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend source files
COPY . .

# Configure PYTHONPATH to locate src directory modules
ENV PYTHONPATH=src

# Expose Hugging Face Spaces default port
EXPOSE 7860

# Start Uvicorn ASGI server
CMD ["uvicorn", "src.api:app", "--host", "0.0.0.0", "--port", "7860"]
