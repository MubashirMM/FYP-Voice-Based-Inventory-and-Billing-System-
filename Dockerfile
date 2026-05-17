# 1. Base Image
FROM bitnami/pytorch:latest

# 2. Environment setups
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PATH="/opt/bitnami/python/bin:$PATH"

# 3. Elevate to root briefly to install dependencies
USER root

# 4. App Directory
WORKDIR /app

# 5. Handle Requirements
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir --upgrade -r /app/requirements.txt

# 6. Copy Application Code
COPY . /app

# 7. Change ownership to Bitnami's built-in non-root user (1001)
RUN chown -R 1001:1001 /app

# ==========================================================
# 8. SWITCH BACK TO NON-ROOT USER (This satisfies Semgrep)
# ==========================================================
USER 1001

# 9. Execution Engine
EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]