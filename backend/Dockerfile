FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY main.py .

# Copy SSL certificates if they exist
COPY ssl/ /app/ssl/ 2>/dev/null || true

EXPOSE 8080

CMD ["python", "main.py"]
