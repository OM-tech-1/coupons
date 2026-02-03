FROM python:3.12-slim

WORKDIR /app

# Install system dependencies (needed for psycopg2-binary, though slim usually has enough for binary, 
# sometimes gcc/libpq-dev are needed if building from source. keeping it simple for now as we use binary)
# RUN apt-get update && apt-get install -y gcc libpq-dev && rm -rf /var/lib/apt/lists/*

COPY ./requirements.txt /app/requirements.txt

RUN pip install --no-cache-dir --upgrade -r /app/requirements.txt

COPY ./app /app/app

# Expose port 8000
EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
