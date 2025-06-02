FROM python:alpine

WORKDIR /workspace

RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc build-essential librdkafka-dev netcat && \
    rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir poetry pre-commit