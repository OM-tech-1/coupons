FROM python:3.12-slim

WORKDIR /app

# Install system dependencies (needed for psycopg2-binary, though slim usually has enough for binary, 
# sometimes gcc/libpq-dev are needed if building from source. keeping it simple for now as we use binary)
# RUN apt-get update && apt-get install -y gcc libpq-dev && rm -rf /var/lib/apt/lists/*

COPY ./requirements.txt /app/requirements.txt

RUN pip install --no-cache-dir --upgrade -r /app/requirements.txt

COPY ./app /app/app
COPY ./gunicorn.conf.py /app/gunicorn.conf.py

COPY ./create_admin.py /app/create_admin.py
COPY ./scripts /app/scripts

# Expose port 8000
EXPOSE 8000

# Use Gunicorn with multiple workers for production
# Verify/Create admin on startup if env vars are present
CMD ["sh", "-c", "python create_admin.py && gunicorn app.main:app -c gunicorn.conf.py"]
