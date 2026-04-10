# 1. Use Python 3.13 as required by your audio libraries
FROM python:3.13-slim

# 2. Set environment variables to keep Python from buffering and creating .pyc files
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# 3. Set the working directory
WORKDIR /code

# 4. Install SYSTEM dependencies needed for audio and building C++ extensions
# We need ffmpeg for Whisper/librosa and build-essential for libraries like bcrypt/ujson
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    build-essential \
    gcc \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# 5. Copy requirements
COPY ./requirements.txt /code/requirements.txt

# 6. Install Python dependencies
# Note: This will take a long time because of torch and transformers
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r /code/requirements.txt

# 7. Copy your application code and env
COPY ./myapp /code/myapp
COPY .env /code/.env

# 8. Expose the port FastAPI runs on
EXPOSE 8000

# 9. Run the application
CMD ["uvicorn", "myapp.main:app", "--host", "0.0.0.0", "--port", "8000"]