FROM python:3.11-slim

WORKDIR /app

COPY services/ingestor/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY shared/ ./shared/
COPY data_contracts/ ./data_contracts/
COPY services/ingestor/ ./services/ingestor/

CMD ["python", "-m", "services.ingestor.main"]
