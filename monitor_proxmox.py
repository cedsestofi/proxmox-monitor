import time
import requests
import os
from proxmoxer import ProxmoxAPI
import urllib3

# Disabilita i warning SSL
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Configura il tuo Proxmox API Token
PROXMOX_HOSTS = os.getenv("PROXMOX_HOSTS", "").split(",")
PROXMOX_USER = os.getenv("PROXMOX_USER")
PROXMOX_TOKEN_NAME = os.getenv("PROXMOX_TOKEN_NAME")
PROXMOX_TOKEN_VALUE = os.getenv("PROXMOX_TOKEN_VALUE")
CHECK_INTERVAL = int(os.getenv("CHECK_INTERVAL")) # Tempo tra i controlli (in secondi)

# Soglia di utilizzo storage in percentuale oltre la quale inviare un avviso
STORAGE_USAGE_THRESHOLD = int(os.getenv("CHECK_THRESHOLD"))

# Configura il topic per ntfy.sh
#NTFY_TOPIC = "Sesto_251024_proxmox"
NTFY_TOPIC = os.getenv("NTFY_TOPIC")

# Notifica via Telegram
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

headers = {
    "Authorization": f"PVEAPIToken={PROXMOX_USER}!{PROXMOX_TOKEN_NAME}={PROXMOX_TOKEN_VALUE}"
}

verify_ssl = False  # Cambia a True se il certificato SSL è valido

def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message}
    requests.post(url, json=payloadi)

def send_ntfy_message(message):
    url = f"https://ntfy.sh/{NTFY_TOPIC}"
    requests.post(url, data=message.encode(encoding='utf-8'))

def get_nodes(proxmox_host):
    url = f"https://{proxmox_host}:8006/api2/json/nodes"
    response = requests.get(url, headers=headers, verify=verify_ssl)
    response.raise_for_status()
    return response.json().get('data', [])

def get_storage_for_node(proxmox_host, node):
    url = f"https://{proxmox_host}:8006/api2/json/nodes/{node}/storage"
    response = requests.get(url, headers=headers, verify=verify_ssl)
    response.raise_for_status()
    return response.json().get('data', [])

def get_storage_status(proxmox_host, node, storage):
    url = f"https://{proxmox_host}:8006/api2/json/nodes/{node}/storage/{storage}/status"
    response = requests.get(url, headers=headers, verify=verify_ssl)
    response.raise_for_status()
    return response.json().get('data', {})

def monitor_proxmox():
    proxmox = None
    
    for host in PROXMOX_HOSTS:
        try:
            proxmox = ProxmoxAPI(
                host,
                user=PROXMOX_USER,
                token_name=PROXMOX_TOKEN_NAME,
                token_value=PROXMOX_TOKEN_VALUE,
                verify_ssl=False
            )
            # Test se il nodo risponde
            proxmox.nodes.get()
            break
        except Exception as e:
            proxmox = None

    if proxmox is None:
        send_ntfy_message("Errore: Nessun host disponibile risponde.")
        send_ntfy_message("Monitoraggio terminato.")
        return

    try:
        # Controlla lo stato dei nodi
        nodes = proxmox.nodes.get()
        
        for node in nodes:
            if node.get('status') != 'online':
                send_ntfy_message(f"Nodo {node['node']} non è online: stato {node['status']}")

        # Controlla lo stato delle VM e dei container
        for node in nodes:
            vms = proxmox.nodes(node['node']).qemu.get()
            
            for vm in vms:
                if 'tags' in vm and 'produzione' in vm['tags']:
                    if vm.get('status') != 'running':
                        send_ntfy_message(f"VM {vm['name']} ({vm['vmid']}) su nodo {node['node']} non è in esecuzione.")

            containers = proxmox.nodes(node['node']).lxc.get()
            
            for container in containers:
                if 'tags' in container and 'produzione' in container['tags']:
                    if container.get('status') != 'running':
                        send_ntfy_message(f"Container {container['name']} ({container['vmid']}) su nodo {node['node']} non è in esecuzione.")
        
        # Controlla lo stato degli storage
        for proxmox_host in PROXMOX_HOSTS:
            nodes = get_nodes(proxmox_host)
            for node in nodes:
                node_name = node['node']
                storages = get_storage_for_node(proxmox_host, node_name)
                for storage in storages:
                    storage_id = storage['storage']
                    status = get_storage_status(proxmox_host, node_name, storage_id)

                    # Verifica se lo storage è abilitato ma non attivo
                    if status.get('enabled') == 1 and status.get('active') != 1:
                        send_ntfy_message(f"Storage {storage_id} sul nodo {node_name} non è attivo nonostante sia abilitato.")
                    
                    # Verifica la percentuale di utilizzo dello storage
                    total = status.get('total')
                    used = status.get('used')
                    if total and used:
                        usage_percentage = (used / total) * 100
                        if usage_percentage > STORAGE_USAGE_THRESHOLD:
                            send_ntfy_message(f"Attenzione: lo storage {storage_id} sul nodo {node_name} ha superato la soglia di utilizzo ({usage_percentage:.2f}% utilizzato).")

    except Exception as e:
        send_ntfy_message(f"Errore durante il monitoraggio: {str(e)}")
        send_ntfy_message("Monitoraggio terminato a causa di un errore.")

if __name__ == "__main__":
    while True:
        monitor_proxmox()
        time.sleep(CHECK_INTERVAL)
