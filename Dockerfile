# Use the official Python image from the Docker Hub
FROM python:3.10-slim

# Set the working directory in the container
WORKDIR /app

# Set PYTHONPATH to include the Backend directory
ENV PYTHONPATH=/app/Backend

# install uv (runs much faster than pip)
RUN pip install uv

# Copy the requirements file into the container
COPY requirements-docker.txt .

# Install the dependencies
RUN uv pip install --no-cache-dir --system -r requirements-docker.txt

# Copy the rest of the application code into the container
COPY . .

# Expose the port the app runs on
EXPOSE 5000

# Command to run the application
# Simple dev
# CMD ["python", "Backend/app.py"]
# Prod code
CMD ["sh", "-c", "PYTHONPATH=/app/Backend gunicorn -w 4 --preload -b 0.0.0.0:5000 Backend.app:app"]
