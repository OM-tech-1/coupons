
import paramiko
import sys

HOSTNAME = "156.67.216.229"
USERNAME = "root"
PASSWORD = "Uf7PJFeoC9j05es@"

def connect():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    print(f"Connecting to {HOSTNAME}...")
    client.connect(HOSTNAME, username=USERNAME, password=PASSWORD)
    return client

def run_command(client, command):
    print(f"Running: {command}")
    stdin, stdout, stderr = client.exec_command(command)
    out = stdout.read().decode().strip()
    if out: print(f"STDOUT:\n{out}")
    err = stderr.read().decode().strip()
    if err: print(f"STDERR:\n{err}")

def main():
    try:
        client = connect()
        print("\n--- Check Git Status ---")
        run_command(client, "cd /root/coupons && git status")
        run_command(client, "cd /root/coupons && git log -n 1")
        
        print("\n--- Check File Content ---")
        run_command(client, "grep 'DEBUG ENV VARS' /root/coupons/app/main.py")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        client.close()

if __name__ == "__main__":
    main()
