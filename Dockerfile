FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# System deps (psycopg3 / pillow / etc. safe baseline)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    netcat-openbsd \
    && rm -rf /var/lib/apt/lists/*

# Install python deps
COPY requirements.txt /app/requirements.txt
RUN pip install --upgrade pip && pip install -r /app/requirements.txt

# Copy project
COPY . /app

# Create dirs for static/media (nginx will serve static, media optional)
RUN mkdir -p /app/staticfiles /app/media

# Default command (web). Worker/beat override in compose
CMD ["sh", "-c", "python manage.py migrate && python manage.py collectstatic --noinput && gunicorn -c gunicorn.conf.py config.wsgi:application"]