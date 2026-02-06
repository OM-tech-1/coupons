
import paramiko
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
        
        # 1. Pull Code
        print("\n--- Pulling Latest Code ---")
        run_command(client, "cd /root/coupons && git fetch origin && git reset --hard origin/main")

        # 2. Rebuild & Restart
        # Ensure we rebuild to use the new code
        print("\n--- Restarting Container ---")
        run_command(client, "docker stop coupon-api-container || true")
        run_command(client, "docker rm coupon-api-container || true")
        run_command(client, "cd /root/coupons && docker build -t coupon-api .")
        
        # Note: We rely on the .env file already being fixed by previous steps
        run_command(client, "docker run -d --name coupon-api-container --restart unless-stopped --network host --env-file /root/coupons/.env coupon-api")

        # 3. Health Check
        print("\n--- Health Check ---")
        time.sleep(5)
        run_command(client, "curl localhost:8000/health")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        client.close()

if __name__ == "__main__":
    main()
