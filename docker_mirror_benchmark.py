#!/usr/bin/env python3

from __future__ import annotations

import argparse
import copy
import json
import os
import shutil
import subprocess
import sys
import time
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urlparse

# =============================================================================
# Configuration
# =============================================================================

DAEMON_JSON_PATH = Path("/etc/docker/daemon.json")
DAEMON_JSON_BACKUP = Path("/tmp/daemon.json.benchmark_backup")
DOCKER_READY_TIMEOUT = 60.0
DOCKER_RESTART_TIMEOUT = 90.0

# =============================================================================
# YOUR MIRROR LIST
# =============================================================================
MIRRORS: List[Dict[str, Any]] = [
    {"name": "Docker.ir",      "url": "https://registry.docker.ir",    "insecure": False},
    {"name": "ManageIT",       "url": "https://docker.manageit.ir",    "insecure": False},
    {"name": "ArvanCloud",     "url": "https://docker.arvancloud.ir",  "insecure": True},
    {"name": "MobinHost",      "url": "https://docker.mobinhost.com",  "insecure": True},
    {"name": "Docker.host",     "url": "https://docker.host:5000",      "insecure": False},
    {"name": "Kernel.ir",      "url": "https://docker.kernel.ir",      "insecure": False},
    {"name": "Liara.ir",       "url": "https://docker-mirror.liara.ir", "insecure": False},
    
    {"name": "Iranserver.com", "url": "https://docker.iranserver.com", "insecure": False},
    {"name": "Focker.ir",      "url": "https://focker.ir", "insecure": False},
    {"name": "Runflare.com",   "url": "https://mirror-docker.runflare.com", "insecure": False},
    {"name": "Mirror.cdn.ir",  "url": "https://mirror.cdn.ir", "insecure": False},
    {"name": "Jamko.ir",       "url": "https://docker.jamko.ir", "insecure": False},
    {"name": "Haiocloud.com",  "url": "https://docker.haiocloud.com", "insecure": False},
    {"name": "Nrp.co",         "url": "https://docker.nrp.co", "insecure": False},

    {"name": "Kubarcloud.com",  "url": "https://docker-mirror.kubarcloud.com", "insecure": False},
    {"name": "Megan.ir",        "url": "https://hub.megan.ir", "insecure": False},
    {"name": "Hyperclouds.ir",  "url": "https://docker.hyperclouds.ir", "insecure": False},
    {"name": "Atlantiscloud.ir","url": "https://hub.atlantiscloud.ir", "insecure": True},
    {"name": "Pardisco.co",     "url": "https://mirrors.pardisco.co", "insecure": False},
    {"name": "Kargadan.ir",     "url": "https://docker-mirror.kargadan.ir", "insecure": False},
    {"name": "Devneeds.ir/",    "url": "http://docker.devneeds.ir/", "insecure": False},

]
# =============================================================================


@dataclass
class MirrorResult:
    name: str
    mirror_url: str
    success: bool = False
    error: Optional[str] = None
    docker_ready_seconds: Optional[float] = None
    pull_seconds: Optional[float] = None
    image_size_mb: Optional[float] = None
    speed_mib_s: Optional[float] = None
    speed_mbps: Optional[float] = None
    total_seconds: Optional[float] = None
    pull_output_tail: Optional[str] = None
    extra: Dict[str, Any] = field(default_factory=dict)

class Logger:
    
    # ANSI color codes
    GREEN  = "\033[92m"
    RED    = "\033[91m"
    YELLOW = "\033[93m"
    CYAN   = "\033[96m"
    BOLD   = "\033[1m"
    RESET  = "\033[0m"
    
    def __init__(self, stream=None):
        self.stream = stream or sys.stderr
        # Only use colors if stream is an actual terminal (not pipe/redirect)
        self.use_colors = self._is_tty()
    
    def _is_tty(self) -> bool:
        """Check if the output stream is a real terminal."""
        try:
            return hasattr(self.stream, 'isatty') and self.stream.isatty()
        except Exception:
            return False
    
    def _color(self, code: str) -> str:
        """Return color code only if colors are enabled."""
        return code if self.use_colors else ""
    
    def _write(self, text: str) -> None:
        """
        Write text with forced flush.
        Using flush=True solves the indentation/cursor-shift issue.
        """
        # Normalize line endings and ensure they start on a new line
        if text and not text.startswith('\n'):
            text = text
        
        print(text, file=self.stream, flush=True)
    
    def info(self, msg: str) -> None:
        c = self._color(self.CYAN)
        r = self._color(self.RESET)
        self._write(f"{c}[INFO]{r} {msg}")
    
    def ok(self, msg: str) -> None:
        c = self._color(self.GREEN)
        r = self._color(self.RESET)
        self._write(f"{c}[ OK ]{r} {msg}")
    
    def warn(self, msg: str) -> None:
        c = self._color(self.YELLOW)
        r = self._color(self.RESET)
        self._write(f"{c}[WARN]{r} {msg}")
    
    def err(self, msg: str) -> None:
        c = self._color(self.RED)
        r = self._color(self.RESET)
        self._write(f"{c}[FAIL]{r} {msg}")
    
    def step(self, msg: str) -> None:
        b = self._color(self.BOLD)
        r = self._color(self.RESET)
        line = "=" * 60
        # Print separator lines and message with explicit newlines
        self._write("")
        self._write(f"{b}{line}{r}")
        self._write(f"{b}  {msg}{r}")
        self._write(f"{b}{line}{r}")
    
    def raw(self, msg: str) -> None:
        """Print raw text without any prefix."""
        self._write(msg)


# Global logger instance
log = Logger()


# =============================================================================
# Helper functions
# =============================================================================

def run_cmd(cmd: List[str], timeout: float = 30.0) -> subprocess.CompletedProcess:
    try:
        return subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    except subprocess.TimeoutExpired:
        raise TimeoutError(f"Command timed out after {timeout}s: {' '.join(cmd)}")
    except FileNotFoundError:
        raise RuntimeError(f"Command not found: {cmd[0]}")


def extract_host_port(url: str) -> str:
    parsed = urlparse(url)
    return parsed.netloc or url


def check_root() -> None:
    if os.geteuid() != 0:
        log.err("This script MUST run as root. Use: sudo python3 docker_mirror_benchmark.py")
        sys.exit(1)


def check_docker_installed() -> None:
    try:
        result = run_cmd(["docker", "--version"], timeout=10)
        if result.returncode != 0:
            log.err(f"Docker not working: {result.stderr.strip()}")
            sys.exit(1)
        log.ok(f"Docker found: {result.stdout.strip()}")
    except (TimeoutError, RuntimeError) as exc:
        log.err(f"Docker check failed: {exc}")
        sys.exit(1)


def backup_daemon_json() -> None:
    if DAEMON_JSON_PATH.exists():
        shutil.copy2(DAEMON_JSON_PATH, DAEMON_JSON_BACKUP)
        log.ok(f"Backed up {DAEMON_JSON_PATH} → {DAEMON_JSON_BACKUP}")
    else:
        DAEMON_JSON_BACKUP.write_text("{}\n")
        log.warn("No existing daemon.json. Created empty backup.")


def restore_daemon_json() -> None:
    if DAEMON_JSON_BACKUP.exists():
        shutil.copy2(DAEMON_JSON_BACKUP, DAEMON_JSON_PATH)
        log.ok("Restored daemon.json from backup.")
    else:
        DAEMON_JSON_PATH.write_text("{}\n")
        log.warn("No backup found. Wrote empty daemon.json.")


def read_daemon_json() -> Dict[str, Any]:
    if DAEMON_JSON_PATH.exists():
        try:
            with open(DAEMON_JSON_PATH, "r") as f:
                return json.load(f)
        except json.JSONDecodeError:
            log.warn(f"{DAEMON_JSON_PATH} is invalid JSON. Starting fresh.")
    return {}


def write_daemon_json(config: Dict[str, Any]) -> None:
    DAEMON_JSON_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(DAEMON_JSON_PATH, "w") as f:
        json.dump(config, f, indent=2)
        f.write("\n")


def configure_mirror(mirror_url: str, insecure: bool = False) -> None:
    config = read_daemon_json()
    config["registry-mirrors"] = [mirror_url]

    if insecure:
        host_port = extract_host_port(mirror_url)
        insecure_list = config.get("insecure-registries", [])
        insecure_list = [x for x in insecure_list if extract_host_port(x) != host_port]
        insecure_list.append(host_port)
        config["insecure-registries"] = insecure_list
    else:
        host_port = extract_host_port(mirror_url)
        if "insecure-registries" in config:
            config["insecure-registries"] = [
                x for x in config["insecure-registries"] if extract_host_port(x) != host_port
            ]

    write_daemon_json(config)
    log.info(f"daemon.json configured with mirror: {mirror_url}")


def restart_docker() -> float:
    restart_commands = [
        ["systemctl", "restart", "docker"],
        ["service", "docker", "restart"],
        ["systemctl", "restart", "docker.service"],
    ]

    restarted = False
    for cmd in restart_commands:
        try:
            log.info(f"Trying: {' '.join(cmd)}")
            result = run_cmd(cmd, timeout=DOCKER_RESTART_TIMEOUT)
            if result.returncode == 0:
                restarted = True
                log.ok("Docker restart command succeeded.")
                break
            else:
                log.warn(f"  rc={result.returncode} stderr={result.stderr.strip()[:120]}")
        except (TimeoutError, RuntimeError) as exc:
            log.warn(f"  Failed: {exc}")
            continue

    if not restarted:
        raise RuntimeError("All Docker restart methods failed")

    return wait_for_docker_ready()


def wait_for_docker_ready(timeout: float = DOCKER_READY_TIMEOUT) -> float:
    start = time.monotonic()
    while time.monotonic() - start < timeout:
        try:
            result = run_cmd(["docker", "info"], timeout=5)
            if result.returncode == 0:
                return time.monotonic() - start
        except (TimeoutError, RuntimeError):
            pass
        time.sleep(1)
    raise TimeoutError(f"Docker did not become ready within {timeout}s")


def remove_image(image: str) -> None:
    try:
        run_cmd(["docker", "rmi", "-f", image], timeout=60)
    except Exception:
        pass


def pull_image(image: str, timeout: float) -> Tuple[float, str]:
    remove_image(image)
    start = time.monotonic()
    try:
        result = run_cmd(["docker", "pull", image], timeout=timeout)
        elapsed = time.monotonic() - start
        if result.returncode != 0:
            error_detail = result.stderr.strip() or result.stdout.strip()
            raise RuntimeError(f"docker pull failed (rc={result.returncode}): {error_detail[:300]}")
        return elapsed, result.stdout
    except subprocess.TimeoutExpired:
        elapsed = time.monotonic() - start
        raise TimeoutError(f"docker pull timed out after {timeout}s (elapsed {elapsed:.1f}s)")


def get_image_size_mb(image: str) -> Optional[float]:
    try:
        result = run_cmd(
            ["docker", "image", "inspect", image, "--format", "{{.Size}}"], timeout=15
        )
        if result.returncode == 0 and result.stdout.strip().isdigit():
            return int(result.stdout.strip()) / (1024 * 1024)
    except Exception:
        pass
    return None


def test_mirror(mirror: Dict[str, Any], image: str, pull_timeout: float) -> MirrorResult:
    name = mirror.get("name", mirror["url"])
    url = mirror["url"]
    insecure = mirror.get("insecure", False)
    result = MirrorResult(name=name, mirror_url=url)
    total_start = time.monotonic()

    try:
        configure_mirror(url, insecure)
        log.info("Restarting Docker daemon...")
        ready_time = restart_docker()
        result.docker_ready_seconds = round(ready_time, 3)
        log.ok(f"Docker ready in {ready_time:.2f}s")

        log.info(f"Pulling '{image}' (timeout={pull_timeout}s)...")
        pull_time, output = pull_image(image, pull_timeout)
        result.pull_seconds = round(pull_time, 3)
        result.pull_output_tail = "\n".join(output.strip().splitlines()[-5:])
        log.ok(f"Pull completed in {pull_time:.2f}s")

        size_mb = get_image_size_mb(image)
        result.image_size_mb = round(size_mb, 3) if size_mb else None
        if size_mb and pull_time > 0:
            mib_s = size_mb / pull_time
            result.speed_mib_s = round(mib_s, 3)
            result.speed_mbps = round(mib_s * 8, 3)

        remove_image(image)
        result.success = True

    except TimeoutError as exc:
        result.error = f"Timeout: {exc}"
        remove_image(image)
    except RuntimeError as exc:
        result.error = str(exc)
        remove_image(image)
    except Exception as exc:
        result.error = f"{type(exc).__name__}: {exc}"
        remove_image(image)
    finally:
        result.total_seconds = round(time.monotonic() - total_start, 3)

    return result


# =============================================================================
# Optimal Config Generator
# =============================================================================

def build_optimal_config(
    original_config: Dict[str, Any], 
    results: List[MirrorResult], 
    mirrors_meta: List[Dict[str, Any]], 
    max_mirrors: int
) -> Optional[Dict[str, Any]]:
    successful = [r for r in results if r.success]
    if not successful:
        return None
        
    successful.sort(key=lambda r: r.speed_mbps or 0.0, reverse=True)
    top_results = successful[:max_mirrors]
    
    new_config = copy.deepcopy(original_config)
    url_to_meta = {m["url"]: m for m in mirrors_meta}
    
    registry_mirrors = [r.mirror_url for r in top_results]
    new_config["registry-mirrors"] = registry_mirrors
    
    all_tested_hosts = {extract_host_port(m["url"]) for m in mirrors_meta}
    existing_insecure = new_config.get("insecure-registries", [])
    
    cleaned_insecure = [ir for ir in existing_insecure if ir not in all_tested_hosts]
    
    for r in top_results:
        meta = url_to_meta.get(r.mirror_url, {})
        if meta.get("insecure", False):
            host_port = extract_host_port(r.mirror_url)
            if host_port not in cleaned_insecure:
                cleaned_insecure.append(host_port)
                
    if cleaned_insecure:
        new_config["insecure-registries"] = cleaned_insecure
    elif "insecure-registries" in new_config:
        del new_config["insecure-registries"]
        
    return new_config


# =============================================================================
# Reporting
# =============================================================================

def fmt(val: Any, suffix: str = "") -> str:
    if val is None: return "-"
    if isinstance(val, float): return f"{val:.2f}{suffix}"
    return f"{val}{suffix}"


def print_report(results: List[MirrorResult]) -> None:
    if not results: return

    sorted_results = sorted(
        results,
        key=lambda r: (not r.success, -(r.speed_mbps or 0), r.pull_seconds or float("inf")),
    )

    headers = ["Mirror", "OK", "Docker Ready", "Pull Time", "Size (MB)", "MiB/s", "Mbps", "Error"]
    rows = []
    for r in sorted_results:
        ok_str = "YES" if r.success else "NO"  # Changed from unicode to ASCII for terminal safety
        rows.append([
            r.name[:35], ok_str, fmt(r.docker_ready_seconds, "s"),
            fmt(r.pull_seconds, "s"), fmt(r.image_size_mb), fmt(r.speed_mib_s),
            fmt(r.speed_mbps), (r.error or "")[:70],
        ])

    widths = [max(len(headers[i]), *(len(row[i]) for row in rows)) for i in range(len(headers))]
    def render(cells: List[str]) -> str:
        return "  ".join(c.ljust(w) for c, w in zip(cells, widths))

    log.raw("")
    log.raw(render(headers))
    log.raw("  ".join("-" * w for w in widths))  # Changed from unicode to ASCII
    for row in rows: log.raw(render(row))

    log.raw("")
    ok = [r for r in sorted_results if r.success]
    
    b = log._color(log.BOLD)
    g = log._color(log.GREEN)
    r = log._color(log.RED)
    rst = log._color(log.RESET)
    
    if ok:
        best = ok[0]
        log.raw(f"{g}{b}★ Best mirror: {best.name}{rst}")
        log.raw(f"  Pull time : {fmt(best.pull_seconds, 's')}")
        log.raw(f"  Speed     : {fmt(best.speed_mbps)} Mbps  ({fmt(best.speed_mib_s)} MiB/s)")
    else:
        log.raw(f"{r}✗ No mirror succeeded.{rst}")


def write_json_report(results: List[MirrorResult], args: argparse.Namespace, path: str) -> None:
    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "image": args.image,
        "pull_timeout": args.timeout,
        "results": [asdict(r) for r in results],
    }
    with open(path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    log.ok(f"JSON report → {path}")


# =============================================================================
# Main
# =============================================================================

def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="Production-level Docker mirror benchmark with auto-config generation.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    p.add_argument("--image", default="ubuntu:latest", help="Image to pull")
    p.add_argument("--timeout", type=float, default=300.0, help="Timeout for docker pull")
    p.add_argument("--json", dest="json_file", help="Write JSON report")
    p.add_argument("--mirror", action="append", default=[], help="Extra secure mirror")
    p.add_argument("--insecure-mirror", action="append", default=[], help="Extra insecure mirror")
    p.add_argument("--keep-config", action="store_true", help="Do NOT restore original daemon.json")
    p.add_argument("--verbose", action="store_true", help="Show pull output tail on failure")
    p.add_argument("--export-config", type=str, metavar="PATH",
                    help="Export optimal daemon.json to this file")
    p.add_argument("--apply-config", action="store_true",
                    help="Apply optimal mirrors to /etc/docker/daemon.json and restart Docker")
    p.add_argument("--max-mirrors", type=int, default=3,
                    help="Max number of top-performing mirrors to include in config")
    return p


def main() -> int:
    args = build_parser().parse_args()

    check_root()
    check_docker_installed()

    mirrors = list(MIRRORS)
    for url in args.mirror:
        mirrors.append({"name": url, "url": url, "insecure": False})
    insecure_override = set(args.insecure_mirror)
    for m in mirrors:
        if m["url"] in insecure_override:
            m["insecure"] = True

    if not mirrors:
        log.err("No mirrors to test.")
        return 2

    log.info(f"Testing {len(mirrors)} mirrors with image '{args.image}'")

    original_config = read_daemon_json()
    backup_daemon_json()

    results: List[MirrorResult] = []
    interrupted = False
    generated_config = None

    try:
        for idx, mirror in enumerate(mirrors, 1):
            log.step(f"[{idx}/{len(mirrors)}] Testing: {mirror['name']}")
            r = test_mirror(mirror, args.image, args.timeout)
            results.append(r)

            if r.success:
                log.ok(f"{r.name} → {fmt(r.speed_mbps)} Mbps in {fmt(r.pull_seconds, 's')}")
            else:
                log.err(f"{r.name} → {r.error}")
                if args.verbose and r.pull_output_tail:
                    log.raw(f"  Pull output:\n{r.pull_output_tail}")

        if args.export_config or args.apply_config:
            generated_config = build_optimal_config(
                original_config, results, mirrors, args.max_mirrors
            )
            
            if generated_config:
                log.ok(f"Optimal config generated with {len(generated_config.get('registry-mirrors', []))} mirrors.")
                log.raw("")
                b = log._color(log.BOLD)
                rst = log._color(log.RESET)
                log.raw(f"{b}Optimal daemon.json configuration:{rst}")
                log.raw(json.dumps(generated_config, indent=2))
                
                if args.export_config:
                    try:
                        with open(args.export_config, "w", encoding="utf-8") as f:
                            json.dump(generated_config, f, indent=2)
                            f.write("\n")
                        log.ok(f"Exported optimal config to: {args.export_config}")
                    except IOError as e:
                        log.err(f"Failed to write export file: {e}")
                        
                if args.apply_config:
                    log.info("Applying optimal config to /etc/docker/daemon.json...")
                    write_daemon_json(generated_config)
                    log.info("Restarting Docker with optimal config...")
                    restart_docker()
                    log.ok("Docker is now running with the optimal mirrors!")
            else:
                log.warn("No successful mirrors found. Cannot generate or apply optimal config.")

    except KeyboardInterrupt:
        interrupted = True
        log.raw("")
        log.warn("Interrupted by user (Ctrl+C). Cleaning up...")

    finally:
        if args.apply_config and generated_config is not None:
            log.info("Skipping restore: --apply-config was used successfully.")
        elif not args.keep_config:
            log.info("Restoring original daemon.json...")
            restore_daemon_json()
            log.info("Restarting Docker with original config...")
            try:
                restart_docker()
                log.ok("Docker restored successfully.")
            except Exception as exc:
                log.err(f"Failed to restore Docker: {exc}")
                log.warn("You may need to manually fix /etc/docker/daemon.json and restart Docker.")
        else:
            log.warn("--keep-config set. daemon.json was NOT restored.")

    print_report(results)

    if args.json_file:
        write_json_report(results, args, args.json_file)

    if interrupted:
        return 130

    return 0 if any(r.success for r in results) else 1


if __name__ == "__main__":
    sys.exit(main())