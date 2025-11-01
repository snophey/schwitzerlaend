FROM python:3.11-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# If your app imports local modules, copy the whole project (not just main.py)
COPY . .

# Secrets path will now be /app/secrets/ (as your code logs suggest)
EXPOSE 8000

# Bind to all interfaces in the container
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
