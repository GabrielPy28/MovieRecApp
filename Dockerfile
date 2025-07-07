# Dockerfile for the movie recommendation system based on PySpark

# Use an official Python base image optimized for production
FROM python:3.11-slim

# Container metadata
LABEL maintainer="Gabriel Piñero <gabrielparenas27@gmail.com>"
LABEL version="1.1.0"
LABEL description="Intelligent movie recommendation system using machine learning with PySpark"
LABEL org.opencontainers.image.source="https://github.com/GabrielPy28/MovieRec"
LABEL org.opencontainers.image.licenses="MIT"

# Environment variables for configuration
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies:
# - OpenJDK 17 (required by PySpark)
# - gcc (for compiling Python dependencies)
# - Basic troubleshooting tools
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    openjdk-17-jre-headless \
    gcc \
    python3-dev \
    procps \ 
    net-tools \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Set environment variables for Java and Spark
ENV JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64 

ENV PATH="${JAVA_HOME}/bin:${PATH}" \
    PYSPARK_PYTHON=python3 \
    PYSPARK_DRIVER_PYTHON=python3 \
    SPARK_HOME=/usr/local/lib/python3.11/site-packages/pyspark

# Working directory in the container
WORKDIR /app

# Install Python dependencies
COPY requirements.txt .

RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt && \
    find /usr/local/lib/python3.11 -type d -name '__pycache__' -exec rm -r {} +

# Copy the rest of the application files
COPY . .

# Container healthcheck configuration
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import socket; socket.create_connection(('localhost', 4040), timeout=5)" || exit 1

# Main execution command
CMD ["python", "-m", "app.main"]

# Exposed ports documentation (Typical Spark UI port, for debugging)
EXPOSE 4040