FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY bot/ bot/
COPY data/ data/
COPY app.py .

ENV PYTHONUNBUFFERED=1
ENV PORT=8080

CMD ["python", "app.py"]
