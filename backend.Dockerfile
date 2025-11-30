FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y libpq-dev gcc

COPY PrimeGift/backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY PrimeGift/backend/ .

RUN chmod +x start.sh

CMD ["./start.sh"]

