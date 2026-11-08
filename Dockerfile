# ==============================================================================
# Dockerfile: Production-Ready Container for SRU Blockchain E-Voting System
# ==============================================================================
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Install system build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install python dependencies
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY . /app/

# Collect static assets for WhiteNoise
RUN python manage.py collectstatic --noinput

# Run migrations and seed genesis mining info
RUN python manage.py migrate

EXPOSE 8000

CMD ["gunicorn", "Election.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "3", "--timeout", "120"]

