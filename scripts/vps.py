#!/usr/bin/env python3
"""
Consolidated VPS Operations CLI

Usage:
  python scripts/vps.py deploy          # Deploy to VPS
  python scripts/vps.py logs            # Get container logs
  python scripts/vps.py status          # Check container status
  python scripts/vps.py rebuild         # Rebuild with cache
  python scripts/vps.py rebuild --no-cache  # Rebuild without cache
  python scripts/vps.py exec <cmd>      # Execute command on VPS
"""

import argparse
import os
import sys
import time
from typing import Optional

try:
    import paramiko
except ImportError:
    print("Error: paramiko not installed. Run: pip install paramiko")
    sys.exit(1)

from dotenv import load_dotenv

load_dotenv()

# VPS Connection Config
HOSTNAME = os.getenv("VPS_HOST")
USERNAME = os.getenv("VPS_USER")
PASSWORD = os.getenv("VPS_PASSWORD")
CONTAINER_NAME = "coupon-api-container"
IMAGE_NAME = "coupon-api"
APP_DIR = "/root/coupons"


class VPSClient:
    """SSH client wrapper for VPS operations"""
    
    def __init__(self):
        self.client: Optional[paramiko.SSHClient] = None
    
    def connect(self) -> None:
        """Establish SSH connection"""
        if not all([HOSTNAME, USERNAME, PASSWORD]):
            print("Error: Missing VPS credentials in .env")
            print("Required: VPS_HOST, VPS_USER, VPS_PASSWORD")
            sys.exit(1)
        
        self.client = paramiko.SSHClient()
        self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        print(f"🔌 Connecting to {HOSTNAME}...")
        self.client.connect(HOSTNAME, username=USERNAME, password=PASSWORD)
        print("✅ Connected")
    
    def run(self, command: str, stream: bool = False) -> str:
        """Execute command on VPS"""
        if not self.client:
            raise RuntimeError("Not connected")
        
        print(f"▶ {command}")
        stdin, stdout, stderr = self.client.exec_command(command)
        
        if stream:
            while True:
                line = stdout.readline()
                if not line:
                    break
                print(line.rstrip())
        
        out = stdout.read().decode().strip()
        err = stderr.read().decode().strip()
        
        if not stream and out:
            print(out)
        if err:
            print(f"⚠ {err}")
        
        return out
    
    def close(self) -> None:
        """Close SSH connection"""
        if self.client:
            self.client.close()
            print("🔌 Disconnected")


def cmd_deploy(vps: VPSClient, args: argparse.Namespace) -> None:
    """Deploy application to VPS"""
    print("\n📦 Deploying to VPS...")
    vps.run(f"cd {APP_DIR} && git pull", stream=True)
    vps.run(f"docker build -t {IMAGE_NAME} .", stream=True)
    vps.run(f"docker stop {CONTAINER_NAME} || true")
    vps.run(f"docker rm {CONTAINER_NAME} || true")
    vps.run(f"docker run -d --name {CONTAINER_NAME} --restart unless-stopped "
            f"--network host --env-file {APP_DIR}/.env {IMAGE_NAME}")
    
    print("\n⏳ Waiting for startup...")
    time.sleep(5)
    vps.run("curl -s localhost:8000/health")
    print("\n✅ Deployment complete!")


def cmd_rebuild(vps: VPSClient, args: argparse.Namespace) -> None:
    """Rebuild Docker image"""
    cache_flag = "--no-cache" if args.no_cache else ""
    print(f"\n🔨 Rebuilding image {cache_flag}...")
    vps.run(f"cd {APP_DIR} && docker build {cache_flag} -t {IMAGE_NAME} .", stream=True)
    
    # Restart container
    vps.run(f"docker stop {CONTAINER_NAME} || true")
    vps.run(f"docker rm {CONTAINER_NAME} || true")
    vps.run(f"docker run -d --name {CONTAINER_NAME} --restart unless-stopped "
            f"--network host --env-file {APP_DIR}/.env {IMAGE_NAME}")
    
    print("\n⏳ Waiting for startup...")
    time.sleep(5)
    vps.run("curl -s localhost:8000/health")
    print("\n✅ Rebuild complete!")


def cmd_logs(vps: VPSClient, args: argparse.Namespace) -> None:
    """Get container logs"""
    lines = args.lines or 100
    print(f"\n📋 Last {lines} log lines:")
    vps.run(f"docker logs --tail {lines} {CONTAINER_NAME}")


def cmd_status(vps: VPSClient, args: argparse.Namespace) -> None:
    """Check container status"""
    print("\n📊 Container Status:")
    vps.run(f"docker ps -a --filter name={CONTAINER_NAME}")
    print("\n🏥 Health Check:")
    vps.run("curl -s localhost:8000/health")


def cmd_exec(vps: VPSClient, args: argparse.Namespace) -> None:
    """Execute arbitrary command"""
    if not args.command:
        print("Error: Please provide a command")
        return
    cmd = " ".join(args.command)
    vps.run(cmd, stream=True)


def main():
    parser = argparse.ArgumentParser(
        description="VPS Operations CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    subparsers = parser.add_subparsers(dest="action", help="Available commands")
    
    # Deploy
    subparsers.add_parser("deploy", help="Deploy to VPS")
    
    # Rebuild
    rebuild_parser = subparsers.add_parser("rebuild", help="Rebuild Docker image")
    rebuild_parser.add_argument("--no-cache", action="store_true", help="Build without cache")
    
    # Logs
    logs_parser = subparsers.add_parser("logs", help="Get container logs")
    logs_parser.add_argument("-n", "--lines", type=int, default=100, help="Number of lines")
    
    # Status
    subparsers.add_parser("status", help="Check container status")
    
    # Exec
    exec_parser = subparsers.add_parser("exec", help="Execute command on VPS")
    exec_parser.add_argument("command", nargs="*", help="Command to execute")
    
    args = parser.parse_args()
    
    if not args.action:
        parser.print_help()
        sys.exit(1)
    
    commands = {
        "deploy": cmd_deploy,
        "rebuild": cmd_rebuild,
        "logs": cmd_logs,
        "status": cmd_status,
        "exec": cmd_exec,
    }
    
    vps = VPSClient()
    try:
        vps.connect()
        commands[args.action](vps, args)
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)
    finally:
        vps.close()


if __name__ == "__main__":
    main()
