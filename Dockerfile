# Base image
FROM python:3.9-slim

# Install system dependencies for psycopg2 and other Python packages
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    curl

# Install Rust (for building extensions that require it)
RUN curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y
ENV PATH="/root/.cargo/bin:${PATH}"

# Set working directory
WORKDIR /app

# Copy the requirements file
COPY requirements.txt /app/

# Install dependencies
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . /app/

# Set the command to run the app
CMD ["python", "app.py"]
