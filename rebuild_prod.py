
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
    # Stream stdout
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
        
        print("\n--- 1. Pull Code ---")
        run_command(client, "cd /root/coupons && git pull origin main")

        print("\n--- 2. Build Image ---")
        run_command(client, "cd /root/coupons && docker build -t coupon-api .")

        print("\n--- 3. Stop Old Container ---")
        run_command(client, "docker stop coupon-api-container || true")
        run_command(client, "docker rm coupon-api-container || true")
        
        print("\n--- 4. Run New Container ---")
        cmd = "docker run -d --name coupon-api-container --restart unless-stopped --network host --env-file /root/coupons/.env coupon-api"
        run_command(client, cmd)
        
        print("\n--- 5. Verify Health ---")
        time.sleep(5)
        run_command(client, "curl localhost:8000/health")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        client.close()

if __name__ == "__main__":
    main()
