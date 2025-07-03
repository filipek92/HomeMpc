FROM python:3.11-slim

# Instalace závislostí
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# Kopírování aplikace
COPY . /app
WORKDIR /app

ENV TZ="Europe/Prague"

EXPOSE 5000

# Spouštěcí skript
RUN chmod +x /app/run.sh
CMD ["/app/run.sh"]