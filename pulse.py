#!/usr/bin/env python3
import socket
import time
import json
from pathlib import Path
from rich.console import Console
from rich.table import Table
from rich.live import Live

console = Console()
CONFIG_FILE = Path("targets.json")

DEFAULT_TARGETS = [
    {"name": "DNS Cloudflare", "host": "1.1.1.1", "port": 53},
    {"name": "DNS Google", "host": "8.8.8.8", "port": 53},
    {"name": "Passerelle locale", "host": "192.168.1.1", "port": 80},
    {"name": "Web Local", "host": "127.0.0.1", "port": 80},
    {"name": "SSH Local", "host": "127.0.0.1", "port": 22},
]


def load_targets():
    if not CONFIG_FILE.exists():
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(DEFAULT_TARGETS, f, indent=2)
        return DEFAULT_TARGETS
    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def check_service(host: str, port: int, timeout: float = 1.0):
    start = time.perf_counter()
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(timeout)
    try:
        sock.connect((host, port))
        latency = (time.perf_counter() - start) * 1000
        sock.close()
        return True, latency
    except (socket.timeout, socket.error):
        return False, None


def build_table(targets):
    table = Table(title="Moniteur de services réseau", header_style="bold cyan")
    table.add_column("Service", style="bold white", width=22)
    table.add_column("Hôte", style="yellow")
    table.add_column("Port", justify="right", style="cyan")
    table.add_column("Statut", justify="center")
    table.add_column("Latence", justify="right")

    for t in targets:
        up, lat = check_service(t["host"], t["port"])
        if up:
            status = "[bold green]ONLINE[/bold green]"
            lat_str = f"[green]{lat:.1f} ms[/green]"
        else:
            status = "[bold red]OFFLINE[/bold red]"
            lat_str = "[dim red]---[/dim red]"

        table.add_row(t["name"], t["host"], str(t["port"]), status, lat_str)

    return table


def main():
    targets = load_targets()
    console.print(f"[dim]Cibles chargées depuis {CONFIG_FILE.name} (Ctrl+C pour quitter)[/dim]\n")
    
    with Live(build_table(targets), refresh_per_second=1, console=console) as live:
        try:
            while True:
                time.sleep(2)
                live.update(build_table(targets))
        except KeyboardInterrupt:
            console.print("\n[bold yellow]Arrêt du monitoring.[/bold yellow]")


if __name__ == "__main__":
    main()
