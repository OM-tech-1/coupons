
import paramiko

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
    output = stdout.read().decode().strip()
    if output:
        print(output)
    err = stderr.read().decode().strip()
    if err:
        print(f"STDERR: {err}")

def main():
    try:
        client = connect()
        
        print("\n--- Check Recent Logs (Last 100 lines) ---")
        run_command(client, "docker logs coupon-api-container --tail 100")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        client.close()

if __name__ == "__main__":
    main()
