# 🐳 Docker Mirror Benchmark

**Production-grade benchmarking tool for Docker Registry Mirrors with real `docker pull` testing & automatic optimal configuration generation**

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Docker](https://img.shields.io/badge/docker-required-2496ED?logo=docker)](https://www.docker.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Platform](https://img.shields.io/badge/platform-linux-lightgrey.svg)]()

---

## 📋 Overview

**Docker Mirror Benchmark** is a senior-level Python script that performs **real end-to-end testing** of Docker Registry mirrors. Unlike HTTP-only ping tools, this script actually configures each mirror in `/etc/docker/daemon.json`, restarts the Docker daemon, and performs a real `docker pull` — giving you accurate, production-representative metrics.

**✨ New in v2.0:** Automatically generates and applies an optimal `daemon.json` configuration based on test results!

### Why This Script?

| Feature | HTTP-only Testers | v1.0 | **v2.0 (Current)** |
|---------|-------------------|------|---------------------|
| Real `docker pull` | ❌ | ✅ | ✅ |
| Daemon restart testing | ❌ | ✅ | ✅ |
| Automatic `daemon.json` backup/restore | ❌ | ✅ | ✅ |
| Insecure registry handling | ❌ | ✅ | ✅ |
| Timeout protection | ⚠️ | ✅ | ✅ |
| Graceful cleanup on Ctrl+C | ❌ | ✅ | ✅ |
| JSON + table reports | ⚠️ | ✅ | ✅ |
| **Auto-generate optimal daemon.json** | ❌ | ❌ | ✅ |
| **Auto-apply best mirrors to system** | ❌ | ❌ | ✅ |
| **Preserves existing Docker settings** | ❌ | ❌ | ✅ |

---

## ✨ Key Features

- 🎯 **Real Pull Testing** — Uses actual `docker pull` command, not just HTTP API calls
- 💾 **Automatic Backup** — Backs up `/etc/docker/daemon.json` before any modification
- 🔄 **Safe Restore** — Always restores original config, even on `Ctrl+C` or crash
- ⏱️ **Timeout Protection** — Every operation has a timeout to prevent hangs
- 🔒 **Insecure Registry Support** — Properly handles self-signed certificates
- 📊 **Rich Metrics** — DNS, TCP, TLS, pull time, speed (Mbps & MiB/s)
- 📝 **Dual Output** — Beautiful terminal table + JSON report
- 🎨 **TTY-Aware Colors** — Colors only when outputting to a real terminal
- 🛡️ **Graceful Interruption** — Clean shutdown with proper cleanup
- 🔧 **Flexible Configuration** — Add mirrors via code, CLI, or env vars
- 🤖 **Smart Auto-Config** — Generates optimal `daemon.json` from top performers
- 🚀 **One-Click Apply** — Apply best mirrors to your system with `--apply-config`

---

## 🚀 Quick Start

### Prerequisites

| Requirement | Minimum Version | Notes |
|-------------|-----------------|-------|
| **Linux OS** | Any modern distro | Ubuntu, Debian, CentOS, RHEL tested |
| **Python** | 3.8+ | Uses only standard library |
| **Docker Engine** | 19.03+ | Required for daemon management |
| **Root/Sudo** | Required | For `/etc/docker/daemon.json` modification |

### Installation

```bash
# Clone or download the script
git clone https://github.com/Skryldev/MirrorPilot.git
cd MirrorPilot

# No pip dependencies required! Uses only Python standard library
```

### Basic Usage

```bash
# Run with default settings (tests built-in mirror list)
sudo python3 docker_mirror_benchmark.py

# Test with a specific image
sudo python3 docker_mirror_benchmark.py --image ubuntu:22.04

# Generate JSON report
sudo python3 docker_mirror_benchmark.py --json report.json

# Add extra mirrors via CLI
sudo python3 docker_mirror_benchmark.py \
  --mirror https://my-mirror.example.com \
  --insecure-mirror https://internal.corp.local:5000
```

---

## 📖 Usage Guide

### Command Line Arguments

#### 🎯 Core Arguments

| Argument | Short | Type | Default | Required | Description |
|----------|-------|------|---------|----------|-------------|
| `--image` | | `str` | `ubuntu:latest` | ❌ | Docker image to pull for benchmarking |
| `--timeout` | | `float` | `300.0` | ❌ | Maximum seconds to wait for each `docker pull` |
| `--json` | | `str` | `None` | ❌ | Path to write JSON report file |
| `--verbose` | `-v` | `flag` | `False` | ❌ | Show detailed pull output on failure |

#### 🔧 Mirror Management Arguments

| Argument | Short | Type | Default | Repeatable | Description |
|----------|-------|------|---------|------------|-------------|
| `--mirror` | `-m` | `str` | `[]` | ✅ | Add secure HTTPS mirror URL to test |
| `--insecure-mirror` | `-i` | `str` | `[]` | ✅ | Add mirror with self-signed cert (skip TLS verify) |

#### 🛡️ Safety & Control Arguments

| Argument | Short | Type | Default | Description |
|----------|-------|------|---------|-------------|
| `--keep-config` | `-k` | `flag` | `False` | **Dangerous:** Do NOT restore original `daemon.json` |
| `--help` | `-h` | `flag` | `False` | Show help message and exit |

#### 🤖 Auto-Configuration Arguments (NEW!)

| Argument | Type | Default | Description |
|----------|------|---------|-------------|
| `--export-config PATH` | `str` | `None` | Export optimal `daemon.json` to specified file path |
| `--apply-config` | `flag` | `False` | Apply optimal mirrors to `/etc/docker/daemon.json` and restart Docker |
| `--max-mirrors N` | `int` | `3` | Number of top-performing mirrors to include in generated config |

---

### 📝 Usage Examples

#### Example 1: Quick Sanity Check

**Scenario:** Test all configured mirrors with a small image

| Parameter | Value | Reason |
|-----------|-------|--------|
| Image | `alpine:latest` | Small image (~5MB), fast test |
| Timeout | `120` | Short timeout for quick check |

```bash
sudo python3 docker_mirror_benchmark.py \
  --image alpine:latest \
  --timeout 120
```

**Expected Duration:** ~2-5 minutes total

---

#### Example 2: Production Workload Test

**Scenario:** Test with realistic Python application image

| Parameter | Value | Reason |
|-----------|-------|--------|
| Image | `python:3.11-slim` | Realistic size (~150MB) |
| Timeout | `600` | Allow 10 minutes per mirror |
| Output | JSON report | For documentation |

```bash
sudo python3 docker_mirror_benchmark.py \
  --image python:3.11-slim \
  --timeout 600 \
  --json mirrors_$(date +%Y%m%d).json
```

**Expected Duration:** ~10-30 minutes depending on mirrors

---

#### Example 3: Internal Corporate Mirror

**Scenario:** Test internal registry with self-signed certificate

| Parameter | Value | Reason |
|-----------|-------|--------|
| Mirror | `https://registry.corp.local` | Internal HTTPS mirror |
| Insecure | ✅ | Self-signed cert requires `--insecure-mirror` |

```bash
sudo python3 docker_mirror_benchmark.py \
  --insecure-mirror https://registry.corp.local \
  --image nginx:alpine
```

---

#### Example 4: Export Optimal Configuration (Safe Mode)

**Scenario:** Test all mirrors, then export the optimal `daemon.json` for manual review

| Parameter | Value | Reason |
|-----------|-------|--------|
| Export path | `./daemon.json.generated` | Safe output location |
| Max mirrors | `3` | Include top 3 performers for fallback |

```bash
sudo python3 docker_mirror_benchmark.py \
  --export-config ./daemon.json.generated \
  --max-mirrors 3
```

**What happens:**
1. ✅ Tests all mirrors
2. ✅ Restores original `daemon.json` (system unchanged)
3. ✅ Writes optimal config to `./daemon.json.generated`
4. 📋 You review and manually deploy when ready

---

#### Example 5: Auto-Apply Best Configuration (Production Mode)

**Scenario:** Automatically configure Docker with the best performing mirrors

| Parameter | Value | Reason |
|-----------|-------|--------|
| Apply config | ✅ | Auto-apply to system |
| Max mirrors | `2` | Top 2 for redundancy |

```bash
sudo python3 docker_mirror_benchmark.py \
  --apply-config \
  --max-mirrors 2
```

**What happens:**
1. ✅ Tests all mirrors
2. ✅ Generates optimal config with top 2 performers
3. ✅ Applies config to `/etc/docker/daemon.json`
4. ✅ Restarts Docker with new configuration
5. ✅ **Skips restore** (system stays configured)

---

#### Example 6: Full Production Workflow

**Scenario:** Complete benchmark → review → deploy workflow

```bash
# Step 1: Run full benchmark with JSON report
sudo python3 docker_mirror_benchmark.py \
  --image ubuntu:22.04 \
  --timeout 300 \
  --json full_benchmark.json \
  --export-config ./daemon.json.generated

# Step 2: Review the generated config
cat ./daemon.json.generated | jq .

# Step 3: Review the JSON report
cat full_benchmark.json | jq '.results[] | {name, success, speed_mbps}'

# Step 4: If satisfied, apply to production
sudo cp ./daemon.json.generated /etc/docker/daemon.json
sudo systemctl restart docker
```

---

#### Example 7: Multi-Mirror Comparison with Auto-Apply

**Scenario:** Test multiple mirrors from command line and auto-apply best ones

| Mirror | Type | Notes |
|--------|------|-------|
| `https://mirror1.example.com` | Secure | Public mirror |
| `https://mirror2.example.com` | Secure | Public mirror |
| `https://internal.corp:5000` | Insecure | Internal with custom port |

```bash
sudo python3 docker_mirror_benchmark.py \
  --mirror https://mirror1.example.com \
  --mirror https://mirror2.example.com \
  --insecure-mirror https://internal.corp:5000 \
  --apply-config \
  --max-mirrors 2 \
  --json comparison_report.json
```

---

### 🔄 Configuration File

Edit the `MIRRORS` list at the top of the script to define mirrors:

```python
MIRRORS: List[Dict[str, Any]] = [
    {
        "name": "FastMirror",      # Display name in reports
        "url": "https://mirror.example.com",  # Full URL with scheme
        "insecure": False          # Set True for self-signed certs
    },
    {
        "name": "InternalCorp",
        "url": "https://registry.corp.local",
        "insecure": True           # Skip TLS verification
    },
    {
        "name": "DevRegistry",
        "url": "https://dev.host:5000",  # Custom port
        "insecure": True
    },
]
```

#### Mirror Configuration Schema

| Field | Type | Required | Description | Example |
|-------|------|----------|-------------|---------|
| `name` | `str` | ✅ | Human-readable name for reports | `"FastMirror"` |
| `url` | `str` | ✅ | Complete mirror URL (scheme + host + port) | `"https://mirror.example.com:5000"` |
| `insecure` | `bool` | ❌ | Set `True` to skip TLS certificate verification | `True` |

---

## 🤖 Smart Auto-Configuration Logic

### How It Works

The auto-configuration feature uses intelligent logic to generate production-ready configurations:

```
┌─────────────────────────────────────────┐
│  1. Test All Mirrors                    │
│     • Real docker pull for each         │
│     • Measure speed, latency, success   │
└──────────────┬──────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────┐
│  2. Filter Successful Mirrors           │
│     • Only mirrors with success=true    │
│     • Discard failed/timeout mirrors    │
└──────────────┬──────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────┐
│  3. Sort by Performance                 │
│     • Primary: speed_mbps (descending)  │
│     • Secondary: pull_seconds           │
└──────────────┬──────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────┐
│  4. Select Top N (--max-mirrors)        │
│     • Default: 3 mirrors                │
│     • Provides redundancy/fallback      │
└──────────────┬──────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────┐
│  5. Build Optimal Config                │
│     • Preserve existing settings        │
│     • Update registry-mirrors           │
│     • Clean insecure-registries         │
└──────────────┬──────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────┐
│  6. Export or Apply                     │
│     • --export-config: Write to file    │
│     • --apply-config: Apply to system   │
└─────────────────────────────────────────┘
```

### Safety Features

| Feature | Description | Benefit |
|---------|-------------|---------|
| **Preserves Settings** | Keeps `log-driver`, `storage-driver`, `mtu`, etc. | No configuration loss |
| **Deep Copy** | Uses `copy.deepcopy()` to avoid mutation bugs | Original config untouched |
| **Insecure Cleanup** | Removes stale `insecure-registries` entries | Clean configuration |
| **Failure Protection** | Won't apply if all mirrors failed | Prevents broken config |
| **Selective Restore** | Skips restore only when `--apply-config` succeeds | Safe by default |

### Generated Configuration Example

**Before (original `daemon.json`):**
```json
{
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "10m",
    "max-file": "3"
  },
  "storage-driver": "overlay2",
  "registry-mirrors": ["https://old-broken-mirror.com"],
  "insecure-registries": ["https://old-broken-mirror.com", "https://internal.corp:5000"]
}
```

**After (generated optimal config):**
```json
{
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "10m",
    "max-file": "3"
  },
  "storage-driver": "overlay2",
  "registry-mirrors": [
    "https://docker.mobinhost.com",
    "https://docker-mirror.liara.ir",
    "https://docker.arvancloud.ir"
  ],
  "insecure-registries": [
    "https://internal.corp:5000",
    "docker.mobinhost.com",
    "docker.arvancloud.ir"
  ]
}
```

**Notice:**
- ✅ `log-driver`, `log-opts`, `storage-driver` preserved
- ✅ Old broken mirror removed
- ✅ Top 3 performing mirrors added
- ✅ Insecure flags correctly set for mirrors that need them
- ✅ Internal corp registry preserved in insecure list

---

## 🔄 How It Works

```
┌─────────────────────────────────────┐
│  1. Pre-flight Checks               │
│     • Verify root privileges        │
│     • Verify Docker installed       │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│  2. Read & Backup daemon.json       │
│     • Store original config         │
│     • Copy to /tmp (safe location)  │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│  3. For Each Mirror:                │
│     a) Write to daemon.json         │
│     b) Restart Docker daemon        │
│     c) Wait for Docker ready        │
│     d) Run real `docker pull`       │
│     e) Measure size & speed         │
│     f) Clean up pulled image        │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│  4. Generate Optimal Config         │
│     • Filter successful mirrors     │
│     • Sort by speed                 │
│     • Select top N                  │
│     • Build production config       │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│  5. Export or Apply                 │
│     • --export-config: Write file   │
│     • --apply-config: Apply & skip  │
│       restore                       │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│  6. Restore (if not --apply-config) │
│     • Original config restored      │
│     • Docker restarted (again)      │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│  7. Generate Reports                │
│     • Terminal table                │
│     • JSON file (optional)          │
└─────────────────────────────────────┘
```

---

## 📊 Sample Output

### Terminal Output

```
Mirror       OK   Docker Ready  Pull Time  Size (MB)  MiB/s  Mbps   Error
-----------  ---  ------------  ---------  ---------  -----  -----  ---------------------
MobinHost    YES  0.09s         18.91s     39.66      2.10   16.77
ArvanCloud   YES  0.06s         27.20s     39.66      1.46   11.66
Docker.ir    NO   2.45s         -          -          -      -      i/o timeout
ManageIT     NO   0.05s         -          -          -      -      no such host
Kernel.ir    NO   0.06s         -          -          -      -      EOF

★ Best mirror: MobinHost
  Pull time : 18.91s
  Speed     : 16.77 Mbps  (2.10 MiB/s)
```

### JSON Report Structure

```json
{
  "generated_at": "2026-08-25T12:34:56.789012+00:00",
  "image": "ubuntu:latest",
  "pull_timeout": 300.0,
  "results": [
    {
      "name": "MobinHost",
      "mirror_url": "https://docker.mobinhost.com",
      "success": true,
      "error": null,
      "docker_ready_seconds": 0.09,
      "pull_seconds": 18.91,
      "image_size_mb": 39.66,
      "speed_mib_s": 2.10,
      "speed_mbps": 16.77,
      "total_seconds": 21.45,
      "pull_output_tail": "Pull complete\nDigest: sha256:...",
      "extra": {}
    }
  ]
}
```

---

## 📈 Metrics Reference

### Performance Metrics

| Metric | Unit | Description | How Calculated |
|--------|------|-------------|----------------|
| **Docker Ready** | seconds | Time for Docker daemon to respond after restart | `docker info` polling |
| **Pull Time** | seconds | Total time to download image from mirror | `time.monotonic()` measurement |
| **Size (MB)** | MiB | Actual image size on disk | `docker image inspect` |
| **MiB/s** | MiB/sec | Download speed in Mebibytes per second | `size_mb / pull_seconds` |
| **Mbps** | Mbit/sec | Download speed in Megabits per second | `mib_s * 8` |
| **Total** | seconds | Full cycle time including overhead | All steps combined |

### Success Indicators

| Indicator | Meaning | Action Required |
|-----------|---------|-----------------|
| `YES` (green) | Mirror tested successfully | Can be used in production |
| `NO` (red) | Mirror failed | Check error message, investigate |
| `i/o timeout` | Network unreachable | Firewall, DNS, or mirror down |
| `no such host` | DNS resolution failed | Domain doesn't exist or DNS issue |
| `EOF` | Connection closed unexpectedly | Mirror rejected request or is unstable |
| `certificate signed by unknown authority` | TLS verification failed | Use `--insecure-mirror` flag |

---

## 🔢 Exit Codes

| Code | Meaning | Scenario |
|------|---------|----------|
| `0` | Success | At least one mirror tested successfully |
| `1` | Failure | All mirrors failed to test |
| `2` | Configuration Error | No mirrors defined or invalid arguments |
| `130` | Interrupted | User pressed `Ctrl+C` (graceful shutdown) |

**Example Usage:**

```bash
# Use exit code in CI/CD pipeline
sudo python3 docker_mirror_benchmark.py --apply-config
if [ $? -eq 0 ]; then
  echo "✓ Mirrors configured successfully"
else
  echo "✗ No working mirrors found"
  exit 1
fi
```

---

## ⚠️ Important Notes

### Safety First

| ✅ Safe Practices | ⚠️ Warnings |
|-------------------|-------------|
| Automatic backup of `daemon.json` | Never run without `sudo` |
| Always restores original config (unless `--apply-config`) | Don't use `--keep-config` unless intentional |
| Validates JSON before writing | Don't interrupt during daemon restart |
| Uses `finally` block for cleanup | Test in non-production environment first |
| No persistent credential storage | Review generated config before applying |
| Deep copy preserves all settings | Backup important configs before testing |

### Security Considerations

| Concern | Mitigation |
|---------|------------|
| Requires root privileges | Script validates permissions before execution |
| `insecure` flag disables TLS | Only use for trusted internal mirrors |
| Modifies system Docker config | Automatic backup and restore mechanism |
| No credential storage | Script doesn't store any secrets |
| Network traffic to mirrors | Use trusted mirrors only |

### Performance Tips

| Tip | Benefit | When to Use |
|-----|---------|-------------|
| Use `alpine:latest` | Fast testing (~5MB) | Quick sanity checks |
| Use `python:3.11-slim` | Realistic workload | Production planning |
| Increase `--timeout` | Prevent false failures | Slow networks or large images |
| Run multiple times | Average results | Accurate benchmarking |
| Test during off-peak | Accurate network metrics | Capacity planning |
| Use `--max-mirrors 2` | Faster config application | When you only need primary + fallback |

---

## 🛠️ Troubleshooting

### Common Errors & Solutions

| Error Message | Meaning | Solution |
|---------------|---------|----------|
| `This script MUST run as root` | Missing sudo privileges | Run with `sudo python3 ...` |
| `Docker did not become ready within 60s` | Daemon failed to start | Check `journalctl -u docker`, restore backup |
| `dial tcp ... i/o timeout` | Mirror unreachable | Check firewall, verify URL, skip mirror |
| `no such host` | DNS resolution failed | Verify DNS, add to `/etc/hosts` if internal |
| `EOF` or connection reset | Mirror closed connection | Try `--insecure-mirror`, check authentication |
| `certificate signed by unknown authority` | TLS verification failed | Use `--insecure-mirror` flag |
| `Command not found: docker` | Docker not installed | Install Docker Engine first |
| `Invalid JSON in daemon.json` | Corrupted config file | Restore from backup manually |
| `No successful mirrors found` | All mirrors failed | Check network, verify mirror URLs |

### Manual Recovery

If something goes wrong, manually restore your Docker configuration:

```bash
# Check backup exists
ls -la /tmp/daemon.json.benchmark_backup

# Restore backup
sudo cp /tmp/daemon.json.benchmark_backup /etc/docker/daemon.json

# Restart Docker
sudo systemctl restart docker

# Verify Docker is working
docker info
```

### Debugging Tips

| Symptom | Debug Command | Expected Result |
|---------|---------------|-----------------|
| Mirror timeout | `curl -v https://mirror.example.com/v2/` | HTTP 200 or 401 |
| DNS issues | `nslookup mirror.example.com` | Valid IP address |
| Docker won't start | `sudo journalctl -u docker -n 50` | No errors |
| Invalid daemon.json | `sudo cat /etc/docker/daemon.json \| jq .` | Valid JSON |
| Permission denied | `sudo systemctl status docker` | Active (running) |
| Config not applied | `docker info \| grep -i mirror` | Shows registry-mirrors |

### Auto-Config Issues

| Problem | Cause | Solution |
|---------|-------|----------|
| Generated config is empty | All mirrors failed | Check network connectivity, verify mirror URLs |
| Old settings lost | Corrupted original config | Restore from `/tmp/daemon.json.benchmark_backup` |
| Insecure flags missing | Mirror not marked insecure | Use `--insecure-mirror` or set `"insecure": true` in MIRRORS |
| Wrong mirrors selected | Speed measurement inaccurate | Increase `--timeout`, run multiple tests |

---

## 🤝 Contributing

Contributions are welcome! Please:

1. **Fork** the repository
2. **Create** a feature branch (`git checkout -b feature/amazing-feature`)
3. **Commit** your changes (`git commit -m 'Add amazing feature'`)
4. **Push** to the branch (`git push origin feature/amazing-feature`)
5. **Open** a Pull Request

### Code Style

| Aspect | Standard |
|--------|----------|
| Python version | 3.8+ |
| Type hints | Required for all functions |
| Docstrings | Google style |
| Line length | 100 characters |
| Imports | Standard library only |

---

## 📝 License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- Inspired by the need for reliable Docker mirror testing in restricted networks
- Built with Python's excellent standard library (no external dependencies!)
- Thanks to the Docker community for maintaining the Registry HTTP API v2 spec
- Special thanks to contributors who helped add auto-configuration features

---

## 📚 Related Resources

| Resource | Description |
|----------|-------------|
| [Docker Registry API v2](https://docs.docker.com/registry/spec/api/) | Official API specification |
| [Docker daemon.json reference](https://docs.docker.com/engine/reference/commandline/dockerd/) | Configuration options |
| [Registry mirrors](https://docs.docker.com/registry/recipes/mirror/) | Official Docker documentation |
| [Docker security best practices](https://docs.docker.com/engine/security/) | Security guidelines |

---

<div align="center">

**If this tool helped you, please ⭐ star the repository!**

Made with ❤️ by developers, for developers

</div>