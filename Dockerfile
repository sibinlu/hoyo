FROM python:3.11-slim

WORKDIR /app

# Install minimal system dependencies for playwright runtime
# (browsers will be mounted from host, so we don't need playwright install)
RUN apt-get update && apt-get install -y --no-install-recommends \
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

# Copy the entire hoyo application
COPY . .

# Set environment variables
ENV PYTHONUNBUFFERED=1
# Tell Playwright to use mounted browser cache from host
ENV PLAYWRIGHT_BROWSERS_PATH=/ms-playwright

# Use python command directly instead of the bin wrapper
ENTRYPOINT ["python", "main.py"]
