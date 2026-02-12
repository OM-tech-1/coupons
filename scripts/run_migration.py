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
    
    # Check if column exists first to avoid error
    check_cmd = "docker exec -i coupon-api-container psql -U user -d coupon_db -c \"SELECT reference_id FROM orders LIMIT 1;\""
    stdin, stdout, stderr = client.exec_command(check_cmd)
    error = stderr.read().decode()
    
    if "column \"reference_id\" does not exist" in error:
        print("Column missing. Running migration...")
        migration_cmd = "docker exec -i coupon-api-container psql -U user -d coupon_db < /root/coupons/migrations/add_reference_id_to_orders.sql"
        stdin, stdout, stderr = client.exec_command(migration_cmd)
        print(stdout.read().decode())
        print(stderr.read().decode())
        print("Migration completed.")
    else:
        print("Column 'reference_id' already exists. Skipping migration.")

except Exception as e:
    print(f"Error: {e}")
finally:
    client.close()
