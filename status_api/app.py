import os
import time
from pathlib import Path

from flask import Flask, jsonify


HOST_PROC = Path(os.environ.get("HOST_PROC", "/host/proc"))
HOST_SYS = Path(os.environ.get("HOST_SYS", "/host/sys"))
HOST_ROOT = Path(os.environ.get("HOST_ROOT", "/hostfs"))

app = Flask(__name__)

_last_net = {}


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def human_bytes(num: float) -> str:
    units = ["B", "KB", "MB", "GB", "TB"]
    value = float(num)
    for unit in units:
        if value < 1024 or unit == units[-1]:
            if unit == "B":
                return f"{int(value)} {unit}"
            return f"{value:.1f} {unit}"
        value /= 1024
    return f"{value:.1f} TB"


def read_cpu_stat() -> dict[str, tuple[int, int]]:
    stats = {}
    for line in read_text(HOST_PROC / "stat").splitlines():
        if not line.startswith("cpu"):
            break
        parts = line.split()
        label = parts[0]
        if label != "cpu" and not label[3:].isdigit():
            continue
        values = [int(part) for part in parts[1:]]
        idle = values[3] + values[4]
        total = sum(values)
        stats[label] = (idle, total)
    return stats


def _cpu_percent(idle_1: int, total_1: int, idle_2: int, total_2: int) -> float:
    total_delta = total_2 - total_1
    idle_delta = idle_2 - idle_1
    if total_delta <= 0:
        return 0.0
    return max(0.0, min(100.0, 100.0 * (1 - idle_delta / total_delta)))


def read_cpu_percent(sample_seconds: float = 0.2) -> tuple[float, list[dict]]:
    stats_1 = read_cpu_stat()
    time.sleep(sample_seconds)
    stats_2 = read_cpu_stat()

    overall = _cpu_percent(*stats_1.get("cpu", (0, 0)), *stats_2.get("cpu", (0, 0)))

    cores = []
    core_labels = sorted(
        (label for label in stats_1 if label != "cpu" and label in stats_2),
        key=lambda label: int(label[3:]),
    )
    for label in core_labels:
        percent = _cpu_percent(*stats_1[label], *stats_2[label])
        cores.append({"core": int(label[3:]), "percent": round(percent, 1)})

    return round(overall, 1), cores


def read_memory() -> dict:
    wanted = {}
    for line in read_text(HOST_PROC / "meminfo").splitlines():
        key, value = line.split(":", 1)
        wanted[key] = int(value.strip().split()[0]) * 1024
    total = wanted.get("MemTotal", 0)
    available = wanted.get("MemAvailable", 0)
    used = max(0, total - available)
    percent = (used / total * 100.0) if total else 0.0

    cached = wanted.get("Cached", 0) + wanted.get("Buffers", 0)
    swap_total = wanted.get("SwapTotal", 0)
    swap_free = wanted.get("SwapFree", 0)
    swap_used = max(0, swap_total - swap_free)
    swap_percent = (swap_used / swap_total * 100.0) if swap_total else 0.0

    return {
        "used_bytes": used,
        "total_bytes": total,
        "used_text": f"{human_bytes(used)} / {human_bytes(total)}",
        "percent": round(percent, 1),
        "cached_bytes": cached,
        "cached_text": human_bytes(cached),
        "swap_total_bytes": swap_total,
        "swap_used_bytes": swap_used,
        "swap_percent": round(swap_percent, 1),
    }


def disk_label(display_path: str) -> str:
    """Best-effort label derived from the mount path. Root ('/') is left
    blank on purpose - the frontend supplies a translated 'System' label
    for it since this string is shown directly to the user and the API
    itself stays locale-agnostic."""
    if display_path == "/":
        return ""
    name = display_path.rsplit("/", 1)[-1]
    return name.replace("_", " ").replace("-", " ").capitalize() or ""


def read_disks() -> list[dict]:
    host_root_prefix = str(HOST_ROOT)
    disks = []
    seen_mountpoints = set()
    try:
        lines = read_text(HOST_PROC / "mounts").splitlines()
    except OSError:
        lines = []

    for line in lines:
        parts = line.split()
        if len(parts) < 3:
            continue
        device, mountpoint, fstype = parts[0], parts[1], parts[2]
        # Only real block devices, mounted somewhere under the host root bind mount.
        if not device.startswith("/dev/") or not mountpoint.startswith(host_root_prefix):
            continue
        if mountpoint in seen_mountpoints:
            continue
        seen_mountpoints.add(mountpoint)

        try:
            stats = os.statvfs(mountpoint)
        except OSError:
            continue
        total = stats.f_blocks * stats.f_frsize
        if total <= 0:
            continue
        free = stats.f_bavail * stats.f_frsize
        used = total - free
        display_path = mountpoint[len(host_root_prefix):] or "/"
        disks.append(
            {
                "device": device,
                "path": display_path,
                "is_root": display_path == "/",
                "label": disk_label(display_path),
                "fstype": fstype,
                "used_bytes": used,
                "total_bytes": total,
                "used_text": f"{human_bytes(used)} / {human_bytes(total)}",
                "percent": round(used / total * 100.0, 1),
            }
        )

    disks.sort(key=lambda item: item["path"] != "/")
    return disks


def read_temperature() -> dict:
    for zone in sorted((HOST_SYS / "class/thermal").glob("thermal_zone*/temp")):
        try:
            raw = int(read_text(zone).strip())
        except (OSError, ValueError):
            continue
        if 1000 <= raw <= 200000:
            celsius = raw / 1000.0
            return {"celsius": round(celsius, 1)}
    return {"celsius": None}


def read_uptime() -> dict:
    """Only the raw seconds go over the wire - all duration formatting
    ('7d 21h' / '7 dias, 21h, 30min') is locale-dependent text and is done
    client-side by the frontend's i18n layer instead."""
    try:
        raw = read_text(HOST_PROC / "uptime").split()[0]
        return {"seconds": int(float(raw))}
    except (OSError, ValueError, IndexError):
        return {"seconds": None}


def candidate_ifaces() -> list[Path]:
    base = HOST_SYS / "class/net"
    if not base.exists():
        return []
    ignored_prefixes = ("br-", "docker", "veth", "lo", "tun", "tap")
    return [
        path
        for path in sorted(base.iterdir())
        if not any(path.name.startswith(prefix) for prefix in ignored_prefixes)
    ]


def read_networks() -> list[dict]:
    results = []
    now = time.time()

    for iface_path in candidate_ifaces():
        iface = iface_path.name
        try:
            operstate = read_text(iface_path / "operstate").strip()
        except OSError:
            operstate = "unknown"

        try:
            rx_bytes = int(read_text(iface_path / "statistics/rx_bytes").strip())
            tx_bytes = int(read_text(iface_path / "statistics/tx_bytes").strip())
        except (OSError, ValueError):
            rx_bytes = None
            tx_bytes = None

        rx_text = "N/A"
        tx_text = "N/A"
        rx_total = "N/A"
        tx_total = "N/A"
        if rx_bytes is not None and tx_bytes is not None:
            rx_total = human_bytes(rx_bytes)
            tx_total = human_bytes(tx_bytes)
            prev = _last_net.get(iface)
            if prev:
                elapsed = now - prev["time"]
                if elapsed > 0:
                    rx_rate = max(0.0, (rx_bytes - prev["rx"]) / elapsed)
                    tx_rate = max(0.0, (tx_bytes - prev["tx"]) / elapsed)
                    rx_text = f"{human_bytes(rx_rate)}/s"
                    tx_text = f"{human_bytes(tx_rate)}/s"
            _last_net[iface] = {"time": now, "rx": rx_bytes, "tx": tx_bytes}

        results.append(
            {
                "iface": iface,
                # Tunnel-type interfaces (tailscale, wireguard) report
                # operstate "unknown" at the kernel level even when fully
                # up and actively passing traffic - treat that as up too.
                "up": operstate in ("up", "unknown"),
                "rx_total": rx_total,
                "tx_total": tx_total,
                "rx_text": rx_text,
                "tx_text": tx_text,
            }
        )

    results.sort(key=lambda item: (not item["up"], item["iface"]))
    return results


@app.get("/status")
def status():
    cpu_percent, cpu_cores = read_cpu_percent()
    return jsonify(
        {
            "cpu": {"percent": cpu_percent, "cores": cpu_cores},
            "memory": read_memory(),
            "disks": read_disks(),
            "networks": read_networks(),
            "temperature": read_temperature(),
            "uptime": read_uptime(),
            "updated_at": int(time.time()),
        }
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=9105, debug=False)
