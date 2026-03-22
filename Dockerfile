# Use a lightweight Python image
FROM python:3.11-slim

# Set the working directory inside the container
WORKDIR /app

# Install system dependencies needed for sqlite-vec
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install them
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . .

# --- RENDER SPECIFIC FIXES ---

# 1. Ensure the DB directory is writeable by the container's user
# Render's default user needs permission to write the SQLite-vec file
RUN mkdir -p /app/db && chmod -R 777 /app/db

# 2. Set the default Port (Render will override this, but it's good practice)
ENV PORT=10000
EXPOSE 10000

# 3. Environment variable to help with the Torch/Transformers cache issue 
# we saw earlier on Hugging Face (prevents the 'uid not found' error)
ENV HOME=/tmp
ENV TRANSFORMERS_CACHE=/tmp/cache
RUN mkdir -p /tmp/cache && chmod -R 777 /tmp/cache

# Command to run the bot
CMD ["python", "main.py"]