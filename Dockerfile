FROM python:3.11-slim

# Set working directory
WORKDIR /code

# Update apt-get and install git, cleanup afterwards
RUN apt-get update && \
    apt-get install -y git && \
    apt-get clean

# Install Python requirements
COPY requirements.txt requirements.txt
RUN python -m pip install -r requirements.txt

# Show Python prints within container in terminal
ENV PYTHONUNBUFFERED 1

# Copy necessary files
COPY main.py .

# Start app with uvicorn
CMD uvicorn --host 0.0.0.0 --port 8000 main:app