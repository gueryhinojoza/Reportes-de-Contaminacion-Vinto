FROM python:3.11-slim

# Sin .pyc, salida sin buffer y sin caché de pip en la imagen.
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# Usuario sin privilegios.
RUN useradd --create-home --shell /bin/bash app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Directorios de datos e imágenes y permisos para el usuario sin root.
RUN mkdir -p /app/data /app/uploads && chown -R app:app /app

USER app

EXPOSE 8080

# Se ejecuta con `sh` para no depender del bit de ejecución del archivo.
ENTRYPOINT ["/bin/sh", "entrypoint.sh"]
