# Moniteur réseau asynchrone CLI

Moniteur réseau en temps réel ultra-rapide en Python, capable de surveiller simultanément des dizaines d'équipements TCP et d'endpoints HTTP/HTTPS avec reporting en direct et alertes Webhook.

---

## Fonctionnalités

- **Architecture Full-Async (`asyncio`)** : sondage parallèle de l'ensemble des cibles sans aucun temps mort lié aux timeouts.
- **Sondes mixtes (TCP & HTTP/HTTPS)** : surveillance de ports standards (SSH, MySQL, Redis...) et de codes retour d'APIs web (`200 OK`, `404`, `500`).
- **Métriques avancées & historique** : calcul du pourcentage d'uptime et mini-graphique (sparkline visuelle `🟢🟢🔴🟢`) sur les 10 dernières itérations.
- **Alerting Discord Webhook** : notification immédiate lors des transitions d'état (`UP ➔ DOWN` et `DOWN ➔ UP`).
- **Arguments CLI (`argparse`)** : support du flag `--once` pour exécution en mode audit/CI (code retour 0/1), personnalisation de l'intervalle (`-i`) et du fichier de configuration (`-c`).

---

## Prérequis

- Python 3.9+
- pip

---

## Installation

1. Cloner le projet :
git clone git@github.com:gabinlsc/serv-pulse.git
cd serv-pulse

2. Configurer l'environnement :
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

3. Lancer la surveillance :
python pulse.py

---

## Options dans le CLI

- Mode continu par défaut (rafraîchissement toutes les 2s) :
  python pulse.py

- Définir un intervalle personnalisé de 5 secondes :
  python pulse.py -i 5

- Mode audit unique (exit code 0 si tout est vert, 1 si au moins un service est KO) :
  python pulse.py --once

- Utiliser un fichier de configuration alternatif :
  python pulse.py -c production.json

---

## Exemple de configuration (targets.json)

[
  {
    "webhook_url": "https://discord.com/api/webhooks/...",
    "targets": [
      {"name": "Web Principal", "type": "http", "url": "https://example.com"},
      {"name": "Serveur SSH", "type": "tcp", "host": "192.168.1.10", "port": 22},
      {"name": "Base de Données", "type": "tcp", "host": "127.0.0.1", "port": 3306}
    ]
  }
]
