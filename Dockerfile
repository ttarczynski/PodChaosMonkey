# Use the official Python image as the base image
FROM python:3.11-slim

# Add an unpriviledged user
RUN groupadd -g 999 python && \
    useradd -r -u 999 -g python python

# Set the working directory
WORKDIR /app

# Copy requirements.txt
COPY requirements.txt app/app.py .

# Install the dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY app/app.py .

# Run application as an unpriviledged user
USER 999

# Set the entrypoint for the container
ENTRYPOINT ["/usr/local/bin/python3", "app.py"]
