FROM python:3.14-slim

ENV DEBIAN_FRONTEND=noninteractive

WORKDIR /app
COPY . .

RUN apt update && \
    apt install -y proot && \
    rm -rf /var/lib/apt/lists/* && \
    pip install -U pip && pip install --no-cache-dir -e ".[dev]"

ENTRYPOINT ["python", "-m", "pd_compose"]
CMD ["--help"]
