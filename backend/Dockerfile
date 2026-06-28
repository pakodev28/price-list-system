FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# uv for fast, reproducible installs
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

WORKDIR /app

# Install dependencies into the system environment (no venv inside the image).
RUN uv pip install --system \
    "django>=5.0,<5.2" djangorestframework django-environ django-filter \
    drf-spectacular django-cors-headers "psycopg[binary]" "celery[redis]" \
    redis python-calamine rapidfuzz openai gunicorn model2vec numpy \
    pytest pytest-django factory-boy

# Bake the multilingual embedding model into the image so the first match
# isn't blocked on a download.
RUN python -c "from model2vec import StaticModel; \
    StaticModel.from_pretrained('minishlab/potion-multilingual-128M')"

COPY . .

RUN chmod +x entrypoint.sh
ENTRYPOINT ["./entrypoint.sh"]
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
