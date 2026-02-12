
import os
import argparse
from vps import VPSClient

def upload_files():
    parser = argparse.ArgumentParser(description="Upload updated order files")
    parser.add_argument("--host", default=os.getenv("VPS_HOST"), help="VPS Host IP")
    parser.add_argument("--user", default=os.getenv("VPS_USER", "root"), help="VPS User")
    parser.add_argument("--password", default=os.getenv("VPS_PASSWORD"), help="VPS Password")
    
    args = parser.parse_args()
    
    if not args.host or not args.password:
        print("❌ Error: VPS credentials not found in env or args")
        return

    vps = VPSClient()
    print(f"🔌 Connecting to {args.user}@{args.host}...")
    
    files_to_upload = [
        ("app/schemas/order.py", "/root/coupons/app/schemas/order.py"),
        ("app/services/order_service.py", "/root/coupons/app/services/order_service.py")
    ]
    
    try:
        vps.connect()
        sftp = vps.client.open_sftp()
        
        for local, remote in files_to_upload:
            local_path = os.path.abspath(local)
            if not os.path.exists(local_path):
                print(f"⚠️ Local file not found: {local_path}")
                continue
                
            print(f"📤 Uploading {local} -> {remote}")
            sftp.put(local_path, remote)
            
        sftp.close()
        print("✅ Files uploaded successfully")
        
        # Rebuild and restart service to pick up changes
        print("🔨 Rebuilding Docker image...")
        vps.run("cd /root/coupons && docker build -t coupon-api .")
        
        print("🔄 Restarting container...")
        vps.run("docker stop coupon-api-container || true")
        vps.run("docker rm coupon-api-container || true")
        vps.run("docker run -d --name coupon-api-container --restart unless-stopped --network host --env-file /root/coupons/.env coupon-api")
        
        print("⏳ Waiting for health check...")
        import time
        time.sleep(5)
        vps.run("curl -s localhost:8000/health")
        print("\n✅ Deployment updated successfully")
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
    finally:
        vps.close()

if __name__ == "__main__":
    upload_files()
