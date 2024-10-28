# Dockerfile per monitor_proxmox.py

# Usa una immagine base Python
FROM python:3.10-slim

# Imposta la directory di lavoro
WORKDIR /app

# Copia i file requirements.txt per le dipendenze
COPY requirements.txt requirements.txt

# Installa le dipendenze Python
RUN pip install --no-cache-dir -r requirements.txt

# Copia il file dello script nel container
COPY monitor_proxmox.py monitor_proxmox.py

# Comando per avviare lo script
CMD ["python", "monitor_proxmox.py"]

