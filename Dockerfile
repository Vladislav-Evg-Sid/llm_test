FROM python:3.11-slim

WORKDIR /app

# COPY requirements.txt .
COPY req.txt .
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

COPY net_debug.py .

# EXPOSE 8000

# CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
# CMD ["python", "./app/llm.py"]
CMD ["python", "./net_debug.py"]
