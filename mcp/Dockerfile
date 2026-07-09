FROM python:3.14.6-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app.py ./app.py
COPY client.py ./client.py
COPY tools.py ./tools.py
COPY resources.py ./resources.py
COPY server.py ./server.py

RUN adduser --system --uid 1001 --no-create-home quiz
USER quiz

ENV QUIZ_APP_URL=http://quiz
ENV MCP_PORT=8000
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

EXPOSE 8000

CMD ["python", "server.py"]
