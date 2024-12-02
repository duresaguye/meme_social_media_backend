# Use the official Python image from Docker Hub
FROM python:3.10-slim

# Set the working directory in the container
WORKDIR /app

# Copy only the requirements.txt first and install dependencies
COPY requirements.txt /app/

RUN apt-get update && apt-get install -y libpq-dev \
    && pip install --no-cache-dir -r requirements.txt

# Copy the rest of the app into the container
COPY . /app/

# Expose the port Django will run on
EXPOSE 8000

# Run Django development server (for local dev)
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
