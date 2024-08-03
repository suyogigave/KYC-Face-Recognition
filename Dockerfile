# Use an official Python runtime as a parent image
FROM python:3.9-slim

# Set the working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libsm6 \
    libxrender1 \
    libxext6 \
    poppler-utils \
    cmake \
    && apt-get clean

# Copy the current directory contents into the container at /app
COPY . /app

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Make port 5000 available to the world outside this container
EXPOSE 5000

# Define environment variables
ENV FLASK_APP=app.py
ENV FLASK_ENV=production  # Set Flask to run in production mode

# Run app.py when the container launches
CMD ["flask", "run", "--host=0.0.0.0"]
