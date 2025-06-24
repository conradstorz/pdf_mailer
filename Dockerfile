FROM python:3.11-slim

RUN apt-get update && apt-get install -y curl && apt-get clean \
    && curl -Ls https://astral.sh/uv/install.sh | bash

ENV PATH="/root/.local/bin:$PATH"

WORKDIR /app

COPY pyproject.toml /app/
COPY src /app/src
COPY uvicorn_start.sh /app/
RUN chmod +x /app/uvicorn_start.sh

# 👇 This line installs your project + uvicorn as a backup
RUN /root/.local/bin/uv pip install --system --editable . \
 && /root/.local/bin/uv pip install --system uvicorn

CMD ["/app/uvicorn_start.sh"]
