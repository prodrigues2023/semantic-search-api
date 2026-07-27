FROM python:3.12-slim

WORKDIR /app

COPY pyproject.toml ./
COPY src ./src
COPY console ./console
COPY corpus ./corpus
COPY relevance ./relevance

RUN pip install --no-cache-dir .

EXPOSE 8000

CMD ["uvicorn", "search_api.main:app", "--host", "0.0.0.0", "--port", "8000"]
