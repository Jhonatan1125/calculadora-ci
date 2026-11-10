FROM python:3.13.2-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    HISTORIAL_DATA_FILE=/data/historial.json \
    HISTORIAL_PORT=5001

RUN mkdir -p /data

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY service.py .

VOLUME ["/data"]

EXPOSE 5001

CMD ["python", "service.py"]
