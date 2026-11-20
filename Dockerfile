FROM python:3.11-slim

WORKDIR /app

COPY pyproject.toml .
RUN pip install --no-cache-dir -e .

COPY . .

EXPOSE 8000 9000

CMD ["uvicorn", "sample_api.main:app", "--host", "0.0.0.0", "--port", "8000"]
