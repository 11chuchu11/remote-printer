FROM python:3.12-slim

RUN apt-get update && apt-get install -y cups-client && rm -rf /var/lib/apt/lists/*
RUN pip install --no-cache-dir python-telegram-bot==21.* pypdf==6.*

COPY . /app/
WORKDIR /app
RUN mkdir -p /data

CMD ["python", "bot.py"]
