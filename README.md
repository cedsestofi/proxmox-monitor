### proxmox-monitor
## software di monitoraggio datacenter proxmox

# requisiti: 
docker e docker compose
Datacenter proxmox in cui è stato creato un apposito utente e un telativo token. Sia utente che token devono avere assegnati almeno i permessi di PVEAuditor

Avere registrato un oggetto per le notifiche su https://ntfy.sh 
# Uso:

dopo avere scaricato il software in una cartella rinominare o creare una copia del file env in .env e editarne il contenuto inserendo i valori relativi ai propri utenti, token e oggetti per le notifiche (seguire le istruzioni presenti nel file stesso)

per la compilazione e l'esecuzione lanciare i seguenti comandi:

```bash
docker compose build
docker compose up -d
```

per controllare l'esecuzione del programma si può lanciare il comando:
```bash
docker compose logs -f
```

