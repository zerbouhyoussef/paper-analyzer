FROM python:3.11-slim

RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    poppler-utils \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY services/extractor/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY shared/ ./shared/
COPY data_contracts/ ./data_contracts/
COPY services/extractor/ ./services/extractor/

CMD ["python", "-m", "services.extractor.main"]
