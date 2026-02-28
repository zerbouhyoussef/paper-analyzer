FROM python:3.11-slim

WORKDIR /app

COPY services/validator/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY shared/ ./shared/
COPY data_contracts/ ./data_contracts/
COPY services/validator/ ./services/validator/

CMD ["python", "-m", "services.validator.main"]
