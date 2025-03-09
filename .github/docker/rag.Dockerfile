FROM python:3.11

WORKDIR /code

COPY libs libs/
COPY projects/rag/ml_hub projects/rag/ml_hub/
COPY projects/rag/tests projects/rag/tests
COPY projects/rag/poetry.lock projects/rag/
COPY projects/rag/pyproject.toml projects/rag/
COPY projects/rag/README.md projects/rag/

WORKDIR /code/projects/rag/


ENV POETRY_VERSION=1.5.1
ENV PORT=8080
EXPOSE $PORT

# Add build arguments
ARG ML_HUB_SERVICE_ACC
ARG ENVIRONMENT

# Project initialization :
RUN pip install "poetry==$POETRY_VERSION"
RUN poetry config virtualenvs.create false \
    && poetry install --no-interaction --no-ansi


CMD gunicorn --worker-class uvicorn.workers.UvicornWorker --workers 9 --worker-connections 4000 --bind 0.0.0.0:$PORT  --timeout 0 --preload rag.main:app
