FROM python:3.12-slim

WORKDIR /app

ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app
COPY docs ./docs

EXPOSE 8501

CMD ["streamlit", "run", "app/web_ui.py", "--server.address", "0.0.0.0", "--server.port", "8501"]
