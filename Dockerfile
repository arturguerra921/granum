# Use an official Python runtime as a parent image
FROM python:3.10-slim

# Set the working directory in the container
WORKDIR /app

# Copy only requirements first to leverage Docker cache
# Since we use pyproject.toml, we copy it and install deps
COPY pyproject.toml /app/
# We need src structure for setuptools find_packages if used, but for dependencies only we can try to install
# However, pip install . needs the package structure.
# Instead, let's copy everything but use --no-cache-dir for pip to save space, and install in editable mode for dev.
COPY . /app

# Install any needed packages specified in pyproject.toml in editable mode
# This allows changes in mounted volume to be reflected without reinstalling
RUN pip install --no-cache-dir -e .

# Make port 8050 available to the world outside this container
EXPOSE 8050

# Run gunicorn when the container launches
# --reload enables hot reloading for dev
CMD ["gunicorn", "-b", "0.0.0.0:8050", "wsgi:server", "--reload"]
