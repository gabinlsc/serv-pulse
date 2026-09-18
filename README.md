# Moniteur réseau CLI en direct

Outil CLI léger et autonome en Python permettant de surveiller en temps réel la disponibilité et la latence TCP d'un parc de serveurs, services ou équipements réseau locaux.

---

## Fonctionnalités

- **Checks TCP réels** : mesure instantanée de la connectivité via sockets réseau natives (`socket.socket`).
- **Calcul de latence** : mesure précise du temps d'établissement de poignée de main en millisecondes.
- **Rendu dynamique** : tableau stylisé dans le terminal actualisé en direct grâce à la bibliothèque `rich`.
- **Fichier de configuration JSON** : génération automatique d'un `targets.json` personnalisable sans toucher au code source.

---

## Prérequis

- Python 3.9+
- pip

---

## Installation et lancement

1. Clone le projet :
``git clone git@github.com:gabinlsc/serv-pulse.git
cd serv-pulse``

2. Crée et active un environnement virtuel :
``python3 -m venv venv
source venv/bin/activate``

3. Installe les dépendances :
``pip install -r requirements.txt``

4. Lance le moniteur :
``python pulse.py``

---

## Configuration (targets.json)

Au premier démarrage, le fichier `targets.json` est initialisé avec des cibles types. Tu peux l'adapter selon tes besoins :

[
  {
    "name": "Mon VPS SSH",
    "host": "vps.example.com",
    "port": 22
  },
  {
    "name": "Serveur Web",
    "host": "192.168.1.50",
    "port": 80
  }
]
EOF
