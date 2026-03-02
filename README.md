# mailban-monitor

Monitora il set nftables `banned_v4` su Proxmox e notifica un'API centrale quando la lista degli IP bannati cambia.

## Come funziona

Deve essere eseguito su ogni nodo nella quale la regola è installata. Ogni 10 secondi esegue:

```
nft -j list set inet pve_smtp_guard banned_v4
```

Confronta la lista `elem` del JSON restituito con quella del ciclo precedente.
Se rileva aggiunte o rimozioni, invia una richiesta POST all'API con il dettaglio delle modifiche e successiva manipolazione e notifica.

## Struttura del progetto

```
mailbanmanager/
├── monitor.py   # script principale
├── .env         # configurazione (non committare)
└── README.md
```

## Configurazione

Copia e modifica il file `.env`:

```env
NODE_NAME=nome-del-nodo
API_KEY=la-tua-api-key
API_URL=http://5.231.80.239/change
```

| Variabile   | Descrizione                                    |
|-------------|------------------------------------------------|
| `NODE_NAME` | Nome del nodo Proxmox, incluso nel payload API |
| `API_KEY`   | Chiave di autenticazione per l'API             |
| `API_URL`   | Endpoint API a cui inviare le notifiche        |

## Installazione

Richiede Python 3.10+ e `nft` disponibile nel PATH (deve girare sull'host Proxmox).

```bash
pip install requests python-dotenv
```

## Avvio

```bash
python monitor.py
```

Output di esempio:

```
[INFO] Starting monitor (interval=10s, node=pve-node1)
[INFO] Initial snapshot: 14 IPs
[OK] No change (14 IPs)
[CHANGE] +2 added, -1 removed
  Added:   ['1.2.3.4', '5.6.7.8']
  Removed: ['9.10.11.12']
[INFO] Notified API → 200
```

## Payload API

Quando viene rilevata una variazione, viene inviata una POST all'URL definito in `API_URL`:

```json
{
  "node": "nome-del-nodo",
  "apikey": "la-tua-api-key",
  "added": ["1.2.3.4", "5.6.7.8"],
  "removed": ["9.10.11.12"]
}
```

## Avvio come servizio systemd

Crea `/etc/systemd/system/mailban-monitor.service`:

```ini
[Unit]
Description=Mailban IP Monitor
After=network.target

[Service]
ExecStart=/usr/bin/python3 /opt/mailbanmanager/monitor.py
WorkingDirectory=/opt/mailbanmanager
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

Poi:

```bash
systemctl daemon-reload
systemctl enable --now mailban-monitor
journalctl -fu mailban-monitor
```
