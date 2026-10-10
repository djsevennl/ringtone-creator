FROM python:3.12-slim
RUN apt-get update && apt-get install -y --no-install-recommends ffmpeg ca-certificates && rm -rf /var/lib/apt/lists/*
RUN pip install --no-cache-dir fastapi uvicorn yt-dlp
WORKDIR /app
COPY experiments/blitz-audio/server.py /app/server.py
ENV PORT=8080
EXPOSE 8080
CMD ["sh","-c","uvicorn server:app --host 0.0.0.0 --port ${PORT:-8080}"]
