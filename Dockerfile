FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# SQLite db lives in a mounted volume so it survives container rebuilds
VOLUME ["/app/data"]

CMD ["python", "-m", "bot.main"]