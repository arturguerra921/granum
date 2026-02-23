# Use an official Python runtime as a parent image
FROM python:3.10-slim

# Set the working directory in the container
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy the dependency file to the working directory
COPY pyproject.toml .

# Install any needed packages specified in pyproject.toml
RUN pip install --no-cache-dir .

# Copy the current directory contents into the container at /app
COPY . .

# Make port 8050 available to the world outside this container
EXPOSE 8050

# Define environment variable
ENV NAME World

# Run app.py when the container launches
# Using gunicorn for production readiness, though python src/__main__.py works too.
# wsgi:server is defined in wsgi.py as 'server = app.server'
CMD ["gunicorn", "--bind", "0.0.0.0:8050", "wsgi:server"]
