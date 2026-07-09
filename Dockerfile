FROM python:3.14.6-slim

WORKDIR /app

COPY requirements.txt requirements-dev.txt pyproject.toml ./
RUN pip install --no-cache-dir -r requirements.txt

COPY src/ ./src/
COPY mkdocs.yml ./
COPY docs/ ./docs/

RUN pip install --no-cache-dir -r requirements-dev.txt \
    && mkdocs build \
    && rm -rf docs/ mkdocs.yml

RUN useradd --system --uid 1001 --no-create-home quiz \
    && mkdir -p /app/data \
    && chown -R quiz:quiz /app

USER quiz

ENV QUIZ_DB=/app/data/quiz.db
ENV PORT=8080

EXPOSE 8080

CMD ["gunicorn", "src.api.main:app", \
     "--bind", "0.0.0.0:8080", \
     "--workers", "2", \
     "--worker-class", "uvicorn.workers.UvicornWorker", \
     "--timeout", "30"]
