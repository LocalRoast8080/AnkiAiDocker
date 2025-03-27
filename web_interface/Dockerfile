FROM python:3.11-slim

WORKDIR /app

# Install curl for testing and create abc user
RUN apt-get update && \
    apt-get install -y curl && \
    rm -rf /var/lib/apt/lists/* && \
    useradd -u 1000 -m abc

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Change ownership of the app directory
RUN chown -R abc:abc /app

# Switch to abc user
USER abc

EXPOSE 5000

CMD ["python", "app.py"] 