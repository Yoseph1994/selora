FROM python:3.13-slim

WORKDIR /app

# Prevent Python from writing .pyc and enable unbuffered output
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Create volume directories for persistent database and uploads
RUN mkdir -p data/receipts data/products_images

EXPOSE 8000

CMD ["python", "main.py"]

