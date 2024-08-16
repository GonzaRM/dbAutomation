# Uso la imagen Python 3.12.5
FROM python:3.9-slim-buster

# Directorio de trabajo en el contenedor
WORKDIR /app

# Copio los archivos al contenedor
COPY . /app

COPY roles.db /app/roles.db 

# Instalo las dependencias
RUN pip install --no-cache-dir Flask Flask-SQLAlchemy Flask-JWT-Extended

# Ejecuto la aplicación
CMD ["python", "challenge.py"]