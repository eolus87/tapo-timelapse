FROM python:3.11-slim-bookworm

RUN apt-get update && apt-get install -y --no-install-recommends \
        libglib2.0-0 \
        libgl1 \
    && rm -rf /var/lib/apt/lists/*

RUN pip install pipenv

WORKDIR /app
COPY Pipfile Pipfile.lock ./
RUN pipenv install --system --deploy

COPY camera/ ./camera/
COPY config/ ./config/
COPY storage/ ./storage/
COPY main.py .
COPY config.yaml .

CMD ["python", "main.py"]
