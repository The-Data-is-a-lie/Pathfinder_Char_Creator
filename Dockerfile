# Use the official Python image from the Docker Hub
FROM python:3.10-slim

# Set the working directory in the container
WORKDIR /app

# Set PYTHONPATH to include the Backend directory
ENV PYTHONPATH=/app/Backend

# Python buffers stdout when it is not a TTY, which a container never is. Without this, everything
# the app prints at import -- the "Redis: using <host>" / "none reachable" line that says whether
# rate limiting is actually shared across workers, and the generator's startup banner -- sits in a
# 8 KB buffer instead of reaching Render's log stream, so the deploy log shows gunicorn booting and
# nothing else. That is not cosmetic: it is the only signal that the Redis wiring took effect, and
# its absence is indistinguishable from the line never having run.
ENV PYTHONUNBUFFERED=1

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
