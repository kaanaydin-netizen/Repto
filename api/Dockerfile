FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000
# Shell-form zodat $PORT (Railway injecteert deze) expandeert; valt terug op 8000 lokaal
CMD uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}
