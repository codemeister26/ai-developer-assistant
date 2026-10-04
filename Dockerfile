FROM python:3.12-slim

WORKDIR /app

# psycopg2 (source wala) ko compiler chahiye. Image mein build tools rakhne ke
# bajaye binary wheel use karte hain — chhoti image, tezi se build.
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir psycopg2-binary \
    && grep -v '^psycopg2==' requirements.txt > docker-requirements.txt \
    && pip install --no-cache-dir -r docker-requirements.txt

COPY alembic.ini .
COPY alembic/ ./alembic/
COPY app/ ./app/

EXPOSE 8000

# Schema Alembic banata hai, isliye server se pehle migrations chalao
CMD ["sh", "-c", "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000"]
