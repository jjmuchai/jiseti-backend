# Use official Python 3.11 image
FROM python:3.11.9-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set working directory
WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

# Copy entire project
COPY . .

# Expose port
EXPOSE 5000

# Start the app
CMD ["gunicorn", "app:app", "--bind", "0.0.0.0:5000"]
