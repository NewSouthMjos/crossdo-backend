FROM python:3.11-slim-bookworm

# Define complementary software versions
ENV POETRY_VERSION 1.5.1

# Set python-specific environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/app \
    POETRY_VIRTUALENVS_CREATE=1 \
    POETRY_VIRTUALENVS_IN_PROJECT=1

WORKDIR /app

# Install poetry and dependencies
RUN apt update && \
    apt install -y curl make && \
    pip install poetry==$POETRY_VERSION

COPY ./app ./app
COPY ./bin ./bin
COPY ./pyproject.toml ./poetry.lock ./
RUN poetry install

ENTRYPOINT ["poetry", "run", "serve"]
