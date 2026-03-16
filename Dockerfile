FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install Java (OpenJDK 21) and required dependencies
RUN apt-get update && apt-get install -y \
    openjdk-21-jre-headless \
    curl \
    wget \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY config.py .
COPY utils.py .
COPY server_manager.py .
COPY bot.py .

# Create servers directory
RUN mkdir -p servers

# Set environment variables
ENV PYTHONUNBUFFERED=1

# Run bot
CMD ["python", "bot.py"]
