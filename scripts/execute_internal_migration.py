import os
import paramiko
from dotenv import load_dotenv

load_dotenv()

hostname = os.getenv("VPS_HOST", "156.67.216.229")
username = os.getenv("VPS_USER", "root")
password = os.getenv("VPS_PASSWORD")

if not password:
    print("Error: VPS_PASSWORD not set in .env")
    exit(1)

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

try:
    print(f"Connecting to {hostname}...")
    client.connect(hostname, username=username, password=password)
    
    # 1. Upload the internal migration script
    sftp = client.open_sftp()
    local_path = "scripts/apply_migration_internal.py"
    remote_path = "/root/coupons/scripts/apply_migration_internal.py"
    print(f"Uploading {local_path} to {remote_path}...")
    sftp.put(local_path, remote_path)
    sftp.close()
    
    # 2. Copy to container and execute
    print("Executing migration inside container...")
    # First ensure the directory exists or just copy to /app/
    cmd = "docker cp /root/coupons/scripts/apply_migration_internal.py coupon-api-container:/app/apply_migration_internal.py"
    client.exec_command(cmd)
    
    # Execute
    cmd_exec = "docker exec coupon-api-container python3 /app/apply_migration_internal.py"
    stdin, stdout, stderr = client.exec_command(cmd_exec)
    
    print("\n--- Output ---")
    print(stdout.read().decode())
    print("\n--- Errors ---")
    print(stderr.read().decode())

except Exception as e:
    print(f"Error: {e}")
finally:
    client.close()
