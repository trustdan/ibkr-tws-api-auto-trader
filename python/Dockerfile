FROM python:3.10-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY . .

# Set default environment variables
ENV IBKR_HOST=localhost
ENV IBKR_PORT=7497
ENV IBKR_CLIENT_ID=1
ENV LOG_LEVEL=INFO

# Expose port for health checks
EXPOSE 8000

# Create a non-root user and switch to it
RUN useradd -m traderapp
USER traderapp

HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1

# Run the application with health checks
CMD ["python", "-m", "src.main"] 