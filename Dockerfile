FROM python:3.11-slim

ENV PLAYWRIGHT_BROWSERS_PATH=/ms-playwright

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt && \
    PLAYWRIGHT_BROWSERS_PATH=/ms-playwright playwright install-deps chromium && \
    PLAYWRIGHT_BROWSERS_PATH=/ms-playwright playwright install chromium

COPY . .

# Ensure SQLite database directory exists
RUN mkdir -p /app/database

EXPOSE 8000
CMD ["sh", "-c", "uvicorn api.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
