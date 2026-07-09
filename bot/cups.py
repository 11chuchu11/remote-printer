import subprocess


def print_file(printer: str, path: str, config: dict | None = None) -> None:
    cfg = config or {}
    opts = []
    if cfg.get("copies", 1) != 1:
        opts += ["-n", str(cfg["copies"])]
    if cfg.get("media"):
        opts += ["-o", f"media={cfg['media']}"]
    if cfg.get("sides"):
        opts += ["-o", f"sides={cfg['sides']}"]
    if cfg.get("color") == "gray":
        opts += ["-o", "ColorModel=Gray"]
    pages = cfg.get("pages", "all")
    if pages == "odd":
        opts += ["-o", "page-set=odd"]
    elif pages == "even":
        opts += ["-o", "page-set=even"]
    elif pages not in ("all", "", None):
        opts += ["-o", f"page-ranges={pages}"]
    subprocess.run(["lp", "-d", printer, *opts, path], check=True, timeout=30)


def get_status(printer: str) -> str:
    r = subprocess.run(["lpstat", "-l", "-p", printer], capture_output=True, text=True, timeout=10)
    return r.stdout.strip() or r.stderr.strip() or "Sin respuesta de CUPS."


def get_ink(printer: str) -> str:
    r = subprocess.run(["lpstat", "-l", "-p", printer], capture_output=True, text=True, timeout=10)
    lines = [l for l in r.stdout.splitlines() if "Marker" in l or "marker" in l or "ink" in l.lower() or "toner" in l.lower()]
    return "\n".join(lines) if lines else ""


def get_queue(printer: str) -> list[str]:
    r = subprocess.run(["lpstat", "-o", printer], capture_output=True, text=True, timeout=10)
    return [l for l in r.stdout.strip().splitlines() if l]


def cancel_job(job_id: str) -> None:
    subprocess.run(["cancel", job_id], check=True, timeout=10)


def cancel_all(printer: str) -> int:
    count = 0
    for line in get_queue(printer):
        try:
            cancel_job(line.split()[0])
            count += 1
        except subprocess.CalledProcessError:
            pass
    return count
