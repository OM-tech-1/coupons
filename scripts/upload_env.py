
import os
import sys
from vps import VPSClient, APP_DIR

def upload_env():
    """Upload local .env to VPS"""
    try:
        vps = VPSClient()
        vps.connect()
        
        local_env = ".env"
        remote_env = f"{APP_DIR}/.env"
        
        print(f"📤 Uploading {local_env} to {remote_env}...")
        
        sftp = vps.client.open_sftp()
        sftp.put(local_env, remote_env)
        sftp.close()
        
        print("✅ Upload complete!")
        vps.close()
        return True
    except Exception as e:
        print(f"❌ Error uploading .env: {e}")
        return False

if __name__ == "__main__":
    # Ensure we can import vps which is in the same directory
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    success = upload_env()
    sys.exit(0 if success else 1)
