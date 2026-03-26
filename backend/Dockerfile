FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Default port (overridden by platform)
ENV PORT=5001
EXPOSE $PORT

# Run with gunicorn
CMD gunicorn main:app --bind 0.0.0.0:$PORT --workers 2 --timeout 120 --keep-alive 5
