FROM python:3.10-slim

WORKDIR /app

# Install system dependencies if any (none for now based on pyproject.toml)
# Maybe git if setuptools needs it for versioning, but simple setup doesn't.

# Copy project files
COPY pyproject.toml README.md ./
COPY src/ src/

# Install the application and dependencies
RUN pip install --no-cache-dir .

# Expose the port the app runs on
EXPOSE 8050

# Command to run the application
CMD ["granum-run"]
