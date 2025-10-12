FROM python:3.11-slim

WORKDIR /app
COPY lab1.py /app/
COPY client.py /app/
COPY content/ /app/content/

RUN mkdir -p /app/downloads
EXPOSE 8000

RUN useradd -m appuser && chown -R appuser:appuser /app
USER appuser

CMD ["python3", "lab1.py", "content"]