
import paramiko
import sys
import time

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
    while True:
        line = stdout.readline()
        if not line:
            break
        print(line.strip())
    err = stderr.read().decode().strip()
    if err:
        print(f"STDERR: {err}")

def main():
    try:
        client = connect()
        
        print("\n--- Force Git Update ---")
        run_command(client, "cd /root/coupons && git fetch origin && git reset --hard origin/main")
        run_command(client, "cd /root/coupons && git log -n 1")

        print("\n--- Rebuild ---")
        run_command(client, "cd /root/coupons && docker build --no-cache -t coupon-api .")

        print("\n--- Restart ---")
        run_command(client, "docker stop coupon-api-container || true")
        run_command(client, "docker rm coupon-api-container || true")
        run_command(client, "docker run -d --name coupon-api-container --restart unless-stopped --network host --env-file /root/coupons/.env coupon-api")
        
        print("\n--- Health Check ---")
        time.sleep(5)
        run_command(client, "curl localhost:8000/health")
        
        print("\n--- Check Logs for Debug ---")
        run_command(client, "docker logs coupon-api-container --tail 50")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        client.close()

if __name__ == "__main__":
    main()
