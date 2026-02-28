FROM python:3.11-slim

WORKDIR /app

COPY services/enricher/requirements.txt .
RUN pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu && \
    pip install --no-cache-dir -r requirements.txt

COPY shared/ ./shared/
COPY data_contracts/ ./data_contracts/
COPY services/enricher/ ./services/enricher/

CMD ["python", "-m", "services.enricher.main"]
