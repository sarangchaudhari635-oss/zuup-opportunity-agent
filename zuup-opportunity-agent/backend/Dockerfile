FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright browsers for scraping
RUN playwright install chromium --with-deps

# Copy source code
COPY . .

# Expose port
EXPOSE 8000

# Default command (overridden by docker-compose for different services)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
