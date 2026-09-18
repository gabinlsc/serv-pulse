#!/usr/bin/env python3
import asyncio
import json
import time
import argparse
import sys
import urllib.request
from collections import deque
from pathlib import Path
from rich.console import Console
from rich.table import Table
from rich.live import Live
import aiohttp

console = Console()
DEFAULT_CONFIG = Path("targets.json")

SAMPLE_TARGETS = {
    "webhook_url": "",  # Colle ton URL de Webhook Discord ici (optionnel)
    "targets": [
        {"name": "DNS Cloudflare", "type": "tcp", "host": "1.1.1.1", "port": 53},
        {"name": "DNS Google", "type": "tcp", "host": "8.8.8.8", "port": 53},
        {"name": "Google Web", "type": "http", "url": "https://www.google.com"},
        {"name": "Passerelle locale", "type": "tcp", "host": "192.168.1.1", "port": 80},
        {"name": "SSH Local", "type": "tcp", "host": "127.0.0.1", "port": 22},
    ]
}

# Suivi de l'état en mémoire
history = {}
previous_states = {}


def load_config(config_path: Path):
    if not config_path.exists():
        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(SAMPLE_TARGETS, f, indent=2)
        return SAMPLE_TARGETS
    with open(config_path, "r", encoding="utf-8") as f:
        data = json.load(f)
        # Compatibilité ascendante avec l'ancien format (liste simple)
        if isinstance(data, list):
            return {"webhook_url": "", "targets": data}
        return data


def send_discord_alert(webhook_url: str, title: str, description: str, color: int):
    if not webhook_url:
        return
    payload = {
        "embeds": [
            {
                "title": title,
                "description": description,
                "color": color,
                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            }
        ]
    }
    try:
        req = urllib.request.Request(
            webhook_url,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json", "User-Agent": "Serv-Pulse"}
        )
        urllib.request.urlopen(req, timeout=3)
    except Exception:
        pass


async def check_tcp(host: str, port: int, timeout: float = 1.5):
    start = time.perf_counter()
    try:
        _, writer = await asyncio.wait_for(
            asyncio.open_connection(host, port), timeout=timeout
        )
        latency = (time.perf_counter() - start) * 1000
        writer.close()
        await writer.wait_closed()
        return True, latency, "TCP OK"
    except Exception:
        return False, None, "TIMEOUT/REFUSED"


async def check_http(url: str, timeout: float = 2.0):
    start = time.perf_counter()
    timeout_cfg = aiohttp.ClientTimeout(total=timeout)
    try:
        async with aiohttp.ClientSession(timeout=timeout_cfg) as session:
            async with session.get(url, allow_redirects=True) as resp:
                latency = (time.perf_counter() - start) * 1000
                if resp.status < 400:
                    return True, latency, f"HTTP {resp.status}"
                return False, latency, f"HTTP {resp.status}"
    except Exception:
        return False, None, "HTTP ERROR"


async def probe_target(target: dict):
    t_type = target.get("type", "tcp").lower()
    if t_type == "http":
        up, latency, detail = await check_http(target["url"])
    else:
        up, latency, detail = await check_tcp(target["host"], target["port"])
    return target, up, latency, detail


def format_sparkline(hist):
    return "".join(["[green]🟢[/green]" if item else "[red]🔴[/red]" for item in hist])


def build_table(results, config):
    webhook_url = config.get("webhook_url", "")
    table = Table(
        title="Live async network monitor",
        header_style="bold cyan",
        border_style="blue"
    )
    table.add_column("Service", style="bold white", width=20)
    table.add_column("Type", justify="center", width=6)
    table.add_column("Cible", style="yellow", width=25)
    table.add_column("Statut", justify="center", width=12)
    table.add_column("Latence", justify="right", width=10)
    table.add_column("Historique (10)", justify="center", width=16)
    table.add_column("Uptime", justify="right", width=8)

    for target, up, latency, detail in results:
        name = target["name"]
        target_id = f"{name}-{target.get('host', target.get('url'))}"

        if target_id not in history:
            history[target_id] = deque(maxlen=10)
        history[target_id].append(up)

        # Détection changement d'état + Webhook Discord
        if target_id in previous_states and previous_states[target_id] != up:
            if up:
                send_discord_alert(
                    webhook_url,
                    f"SERVICE RÉTABLI : {name}",
                    f"Le service répond à nouveau ({detail}).",
                    0x2ECC71
                )
            else:
                send_discord_alert(
                    webhook_url,
                    f"SERVICE DOWN : {name}",
                    f"Le service ne répond plus ({detail}).",
                    0xE74C3C
                )
        previous_states[target_id] = up

        t_type = target.get("type", "tcp").upper()
        target_str = target.get("url") if t_type == "HTTP" else f"{target['host']}:{target['port']}"

        if up:
            status = f"[bold green]ONLINE[/bold green]"
            lat_str = f"[green]{latency:.1f} ms[/green]"
        else:
            status = f"[bold red]{detail}[/bold red]"
            lat_str = "[dim red]---[/dim red]"

        # Calcul Uptime
        uptime_pct = (sum(history[target_id]) / len(history[target_id])) * 100
        color_up = "green" if uptime_pct >= 90 else ("yellow" if uptime_pct >= 70 else "red")
        uptime_str = f"[{color_up}]{uptime_pct:.0f}%[/{color_up}]"

        table.add_row(
            name,
            t_type,
            target_str,
            status,
            lat_str,
            format_sparkline(history[target_id]),
            uptime_str
        )

    return table


async def run_probes(targets):
    tasks = [probe_target(t) for t in targets]
    return await asyncio.gather(*tasks)


def main():
    parser = argparse.ArgumentParser(description="Moniteur réseau asynchrone")
    parser.add_argument("-c", "--config", type=str, default="targets.json", help="Chemin du fichier JSON de configuration")
    parser.add_argument("-i", "--interval", type=int, default=2, help="Intervalle de scan en secondes (défaut: 2)")
    parser.add_argument("--once", action="store_true", help="Effectue un seul scan et sort (code 0 si tout est OK, 1 si anomalie)")

    args = parser.parse_args()
    config = load_config(Path(args.config))
    targets = config.get("targets", [])

    if not targets:
        console.print("[bold red]Aucune cible trouvée dans la configuration.[/bold red]")
        sys.exit(1)

    # Mode Audit Unique (--once) pour les pipelines CI/CD ou crons
    if args.once:
        results = asyncio.run(run_probes(targets))
        table = build_table(results, config)
        console.print(table)
        all_up = all(up for _, up, _, _ in results)
        sys.exit(0 if all_up else 1)

    # Mode Live Monitor interactif
    console.print(f"[dim]Surveillance active ({len(targets)} cibles, intervalle: {args.interval}s, Ctrl+C pour quitter)...[/dim]\n")
    first_results = asyncio.run(run_probes(targets))
    
    with Live(build_table(first_results, config), refresh_per_second=2, console=console) as live:
        try:
            while True:
                time.sleep(args.interval)
                results = asyncio.run(run_probes(targets))
                live.update(build_table(results, config))
        except KeyboardInterrupt:
            console.print("\n[bold yellow]Arrêt du monitoring.[/bold yellow] 👋")


if __name__ == "__main__":
    main()
