#container basato su oython 3.13
FROM python:3.14

#locazione di lavoro
WORKDIR /app

#copia dei file del progetto nel container
COPY . /app

#librerie del progetto
# RUN pip install --no-cache-dir flask cryptography sqlalchemy pymysql requests
RUN pip install --no-cache-dir flask flask-sqlalchemy psycopg2-binary cryptography sqlalchemy pymysql requests

# Comando per avviare l'applicazione
CMD ["python", "flaskr/app.py"]

