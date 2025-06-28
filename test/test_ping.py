#!/usr/bin/env python3
import subprocess

def test_ping(ip):
    try:
        print(f"Probando ping a {ip}...")
        result = subprocess.run(
            ["ping", "-c", "1", "-W", "1", ip], 
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE,
            timeout=3
        )
        print(f"Return code: {result.returncode}")
        print(f"Stdout: {result.stdout.decode()}")
        print(f"Stderr: {result.stderr.decode()}")
        return result.returncode == 0
    except subprocess.TimeoutExpired:
        print(f"Timeout pinging {ip}")
        return False
    except Exception as e:
        print(f"Error pinging {ip}: {e}")
        return False

# Probar con algunas IPs conocidas
test_ips = [
    "172.20.5.51",  # Panel que sabemos que responde
    "172.20.4.148", # Cámara del parking 4
    "172.20.2.181", # Cámara del parking 8
    "8.8.8.8"       # Google DNS para comparar
]

for ip in test_ips:
    print(f"\n{'='*50}")
    online = test_ping(ip)
    print(f"Resultado: {'ONLINE' if online else 'OFFLINE'}")
    print(f"{'='*50}") 