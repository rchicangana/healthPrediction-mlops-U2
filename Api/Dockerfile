# Use a Python base image
FROM python:3.10-slim 

# 1. Set the working directory
WORKDIR /app

# 2. Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 3. Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 4. Copy the application code
COPY app.py .
COPY templates/ templates/

# 5. Create directory for model
RUN mkdir -p /tmp

# 6. Expose the port
EXPOSE 5000

# 7. Define the command to run the application
# El modelo se descargará en tiempo de ejecución desde S3
CMD ["python3", "app.py"]