FROM python:3.12

ADD requirements.txt /tmp/requirements.txt

RUN pip install -r /tmp/requirements.txt

ENV DATABASE_URI=postgresql+asyncpg://admin:admin@postgres/MicroBlogProd

COPY __init__.py /app/backend/
COPY src/ /app/backend/src

WORKDIR /app

CMD ["uvicorn", "backend.src.main:app", "--host", "0.0.0.0", "--port", "8080"]