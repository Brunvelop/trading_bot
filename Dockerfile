# Usar una imagen base de Python
FROM python:3.8

# Establecer un directorio de trabajo
WORKDIR /app

# Copiar el archivo de requerimientos al contenedor
COPY requirements.txt .

# Instalar las dependencias
RUN pip install -r requirements.txt

# Copiar el resto del código al contenedor
COPY . .

# Ejecutar el script de Python cuando el contenedor se inicie
CMD ["python", "./kraken_bot.py"]