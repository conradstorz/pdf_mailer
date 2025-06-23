
FROM python:3.11-slim

RUN apt-get update && apt-get install -y curl && apt-get clean
RUN curl -Ls https://astral.sh/uv/install.sh | bash

WORKDIR /app

COPY pyproject.toml /app/
RUN --mount=type=cache,target=/root/.cache/uv uv sync --no-install-project

COPY . /app/
RUN uv pip install --editable .

EXPOSE 8000
CMD ["./uvicorn_start.sh"]
