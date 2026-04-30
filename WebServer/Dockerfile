# Usa una versione stabile e leggera
FROM python:3.12-slim

#locazione di lavoro
WORKDIR /app

#copia dei file del progetto nel container
COPY . /app

#librerie del progetto
RUN pip install --no-cache-dir flask cryptography sqlalchemy pymysql requests
# RUN pip install --no-cache-dir flask flask-sqlalchemy psycopg2-binary cryptography sqlalchemy pymysql requests

# Comando per avviare l'applicazione
CMD ["python", "flaskr/app.py"]

