# 1. Using the cached Bitnami image
FROM bitnami/pytorch:latest

# 2. Environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# 3. Set working directory
WORKDIR /code

# 4. Install ONLY the basic build tools (these exist in core repo)
USER root
RUN tdnf update -y && tdnf install -y \
    build-essential \
    gcc \
    && tdnf clean all

# 5. Copy requirements
COPY ./requirements.txt /code/requirements.txt

# 6. Install Python dependencies 
# We add imageio-ffmpeg here so Whisper/Librosa can find a working ffmpeg binary
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir imageio-ffmpeg && \
    pip install --no-cache-dir -r /code/requirements.txt

# 7. Copy your application code and env
COPY ./myapp /code/myapp
COPY .env /code/.env

# 8. Expose port
EXPOSE 8000

# 9. Run the application
CMD ["uvicorn", "myapp.main:app", "--host", "0.0.0.0", "--port", "8000"]