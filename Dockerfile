FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY main.py .
COPY templates/ templates/

# Create data directory for schedules
RUN mkdir -p /data

# Expose port
EXPOSE 5011

# Run the application
CMD ["python", "main.py"]
