FROM python:3.14-slim

WORKDIR /app

# Install system dependencies for playwright (minimal set)
RUN apt-get update && apt-get install -y --no-install-recommends \
    wget \
    ca-certificates \
    fonts-liberation \
    libnss3 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libdrm2 \
    libxkbcommon0 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxrandr2 \
    libgbm1 \
    libasound2 \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install only Chromium browser (not all browsers) with minimal deps
RUN playwright install --with-deps chromium \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean \
    && rm -rf /root/.cache

# Copy the entire hoyo application
COPY . .

# Set environment variables
ENV PYTHONUNBUFFERED=1

# Use python command directly instead of the bin wrapper
ENTRYPOINT ["python", "main.py"]
