FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    libpq-dev gcc \
        && rm -rf /var/lib/apt/lists/*

        COPY requirements.txt .
        RUN pip install --no-cache-dir -r requirements.txt

        COPY . .

        RUN mkdir -p static/uploads/photos static/uploads/schemes static/uploads/passports

        EXPOSE 8000

        CMD sh -c "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"
