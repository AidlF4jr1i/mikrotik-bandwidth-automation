import paramiko
import socket
import time
import os
import logging
from datetime import datetime

# ========================
# CEK KONEKSI SSH
# ========================
logging.getLogger("paramiko").setLevel(logging.WARNING)
# Matikan error keras dari paramiko
paramiko_logger = logging.getLogger("paramiko.transport")
paramiko_logger.setLevel(logging.CRITICAL)

def wait_for_ssh_ready(host, username, password, max_retry=3, delay=10):
    for attempt in range(max_retry):
        try:
            client = paramiko.SSHClient()
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            client.connect(
                hostname=host,
                username=username,
                password=password,
                timeout=10,
                banner_timeout=10,
                auth_timeout=10
            )
            client.close()
            return True
        except (paramiko.ssh_exception.SSHException, socket.timeout) as e:
            print(f"⏳ Router {host} belum siap SSH (attempt {attempt + 1}): {type(e).__name__} - {e}")
        except Exception:
            print(f"⏳ Router {host} gagal SSH (attempt {attempt + 1}): {type(e).__name__} - {e}")
            time.sleep(delay)
    return False

    

# ========================
# SETUP LOGGING & AUTO KonfigX
# ========================
log_folder = "logs"
if not os.path.exists(log_folder):
    os.makedirs(log_folder)

today = datetime.now().strftime("%Y-%m-%d")

# Hitung Konfig ke berapa hari ini
existing_logs = [f for f in os.listdir(log_folder) if f.startswith(today)]
konfig_number = 1
while True:
    if any(f"{today}-Konfig{konfig_number}" in name for name in existing_logs):
        konfig_number += 1
    else:
        break

config_label = f"Konfig{konfig_number}"
print(f"\n📝 Menyimpan log dengan label: {config_label}\n")


# ========================
# DATA ROUTER + PERINTAH
# ========================
routers = [
    {
        "name": "ISP1",
        "host": "192.168.10.1",
        "username": "admin",
        "password": "admin1",
        "commands": [
            [
                "interface wireless set [find default-name=wlan1] band=2ghz-b/g/n disabled=no frequency=2437 ssid=@net-unsri-newBB",
                "interface wireless security-profiles set [find default=yes] supplicant-identity=MikroTik",
                "ip dhcp-client add dhcp-options=hostname,clientid disabled=no interface=wlan1",
                "queue simple add max-limit=30M/30M name=queue1 target=ether1",
                "ip address add address=10.10.10.1/30 comment=\"IP Menuju Router ADMIN\" interface=ether1 network=10.10.10.0",
                "ip firewall nat add action=masquerade chain=srcnat out-interface=wlan1",
                "ip dns set allow-remote-requests=yes servers=8.8.8.8,8.8.4.4"
            ]
        ]
    },
    {
        "name": "ISP2",
        "host": "192.168.10.2",
        "username": "admin",
        "password": "admin2",
        "commands": [
            [
                "interface wireless security-profiles set [find default=yes] supplicant-identity=MikroTik",
                "interface wireless security-profiles add authentication-types=wpa2-psk mode=dynamic-keys name=Aidil-hotspot supplicant-identity=MikroTik wpa2-pre-shared-key=PALEMBANG-2005",
                "interface wireless set [find default-name=wlan1] band=2ghz-b/g/n disabled=no frequency=2437 security-profile=Aidil ssid=\"Aidil-hotspot\"",
                "ip dhcp-client add dhcp-options=hostname,clientid disabled=no interface=wlan1",
                "queue simple add max-limit=20M/20M name=queue1 target=ether1",
                "ip address add address=20.20.20.1/30 comment=\"IP Menuju Router ADMIN\" interface=ether1 network=20.20.20.0",
                "ip firewall nat add action=masquerade chain=srcnat out-interface=wlan1",
                "ip dns set allow-remote-requests=yes servers=8.8.8.8,8.8.4.4"
            ]
        ]
    },
    {
        "name": "ADMIN-ROUTER",
        "host": "192.168.10.3",
        "username": "admin",
        "password": "admin3",
        "commands": [
            #Batch 1 - Wireless & Bridge Setup
            [
                "interface wireless security-profiles set [ find default=yes ] supplicant-identity=MikroTik",
                "interface wireless security-profiles add authentication-types=wpa2-psk mode=dynamic-keys name=profile1 supplicant-identity=\"\" wpa2-pre-shared-key=12345678",
                "interface wireless set [ find default-name=wlan1 ] disabled=no mode=ap-bridge security-profile=profile1 ssid=Mikrotik_Aidil",
                "interface bridge add name=Bridge-Client",
                "interface bridge port add bridge=Bridge-Client interface=ether3",
                "interface bridge port add bridge=Bridge-Client interface=wlan1",
                "ip address add address=172.16.1.254/24 comment=\"Laptop OR Android\" interface=Bridge-Client network=172.16.1.0",
                "ip address add address=10.10.10.2/30 comment=ISP1 interface=ether1 network=10.10.10.0",
                "ip address add address=20.20.20.2/30 comment=ISP2 interface=ether2 network=20.20.20.0"
            ],
            #Batch 2 - DHCP Server
            [
                "ip pool add name=dhcp_pool1 ranges=172.16.1.1-172.16.1.253",
                "ip dhcp-server add address-pool=dhcp_pool1 disabled=no interface=Bridge-Client name=dhcp1",
                "ip dhcp-server network add address=172.16.1.0/24 dns-server=8.8.8.8,8.8.4.4 gateway=172.16.1.254"
            ],
            #Batch 3 - DNS & Address List
            [
                "ip dns set allow-remote-requests=yes servers=8.8.8.8,8.8.4.4",
                "ip firewall address-list add address=10.0.0.0/8 list=LOCAL",
                "ip firewall address-list add address=172.16.0.0/12 list=LOCAL",
                "ip firewall address-list add address=192.168.0.0/16 list=LOCAL"
            ],
            #Batch 4 - Local Bypass Mangle
            [
                "ip firewall mangle add action=accept chain=prerouting src-address-list=LOCAL dst-address-list=LOCAL comment=\"Accept All LOCAL IP\"",
                "ip firewall mangle add action=accept chain=postrouting src-address-list=LOCAL dst-address-list=LOCAL",
                "ip firewall mangle add action=accept chain=forward src-address-list=LOCAL dst-address-list=LOCAL",
                "ip firewall mangle add action=accept chain=input src-address-list=LOCAL dst-address-list=LOCAL",
                "ip firewall mangle add action=accept chain=output src-address-list=LOCAL dst-address-list=LOCAL"
            ],
            #Batch 5 - PCC (Input & Output Marking)
            [
                "ip firewall mangle add chain=input action=mark-connection new-connection-mark=via-ether1 in-interface=ether1 passthrough=yes comment=\"Load Balance PCC-Config\"",
                "ip firewall mangle add chain=input action=mark-connection new-connection-mark=via-ether2 in-interface=ether2 passthrough=yes",
                "ip firewall mangle add chain=output action=mark-routing new-routing-mark=via-ISP1 connection-mark=via-ether1 passthrough=yes",
                "ip firewall mangle add chain=output action=mark-routing new-routing-mark=via-ISP2 connection-mark=via-ether2 passthrough=yes"
            ],
            #Batch 6 - PCC Proporsional 3:2
            [
                "ip firewall mangle add chain=prerouting action=mark-connection new-connection-mark=via-ether1 connection-state=new dst-address-type=!local dst-address-list=!LOCAL per-connection-classifier=both-addresses-and-ports:5/0 src-address-list=LOCAL comment=\"PCC-AUTO-ISP1\"",
                "ip firewall mangle add chain=prerouting action=mark-connection new-connection-mark=via-ether1 connection-state=new dst-address-type=!local dst-address-list=!LOCAL per-connection-classifier=both-addresses-and-ports:5/1 src-address-list=LOCAL comment=\"PCC-AUTO-ISP1\"",
                "ip firewall mangle add chain=prerouting action=mark-connection new-connection-mark=via-ether1 connection-state=new dst-address-type=!local dst-address-list=!LOCAL per-connection-classifier=both-addresses-and-ports:5/2 src-address-list=LOCAL comment=\"PCC-AUTO-ISP1\"",
                "ip firewall mangle add chain=prerouting action=mark-connection new-connection-mark=via-ether2 connection-state=new dst-address-type=!local dst-address-list=!LOCAL per-connection-classifier=both-addresses-and-ports:5/3 src-address-list=LOCAL comment=\"PCC-AUTO-ISP2\"",
                "ip firewall mangle add chain=prerouting action=mark-connection new-connection-mark=via-ether2 connection-state=new dst-address-type=!local dst-address-list=!LOCAL per-connection-classifier=both-addresses-and-ports:5/4 src-address-list=LOCAL comment=\"PCC-AUTO-ISP2\"",
                "ip firewall mangle add chain=prerouting action=mark-routing new-routing-mark=via-ISP1 connection-mark=via-ether1 passthrough=yes src-address-list=LOCAL dst-address-list=!LOCAL",
                "ip firewall mangle add chain=prerouting action=mark-routing new-routing-mark=via-ISP2 connection-mark=via-ether2 passthrough=yes src-address-list=LOCAL dst-address-list=!LOCAL"
            ],
            #Batch 7 - Queue + NAT: Routing-mark + Fallback 
            [
                "ip firewall mangle add action=mark-packet chain=forward comment=\"Mark ICMP Packet\" new-packet-mark=ICMP passthrough=no protocol=icmp",
                "ip firewall mangle add action=mark-packet chain=forward comment=\"Mark Download Besar (>10MB)\" connection-bytes=10000000-0 new-packet-mark=Download-Besar passthrough=no protocol=tcp",
                "queue tree add limit-at=3M max-limit=5M name=1-ICMP packet-mark=ICMP parent=Bridge-Client priority=1",
                "queue tree add limit-at=20M max-limit=30M name=2-Download-Besar packet-mark=Download-Besar parent=Bridge-Client",
                "ip firewall nat add chain=srcnat action=masquerade routing-mark=via-ISP1 out-interface=ether1 comment=\"NAT ISP1\"",
                "ip firewall nat add chain=srcnat action=masquerade routing-mark=via-ISP2 out-interface=ether2 comment=\"NAT ISP2\"",
                "ip firewall nat add chain=srcnat action=masquerade out-interface=ether1 comment=\"Fallback NAT ISP1\"",
                "ip firewall nat add chain=srcnat action=masquerade out-interface=ether2 comment=\"Fallback NAT ISP2\""
            ],
           #Batch 8 - Routing & Health Checks
            [
                "ip route add check-gateway=ping distance=1 gateway=1.1.1.1 routing-mark=via-ISP1 target-scope=30",
                "ip route add check-gateway=ping distance=1 gateway=9.9.9.9 routing-mark=via-ISP2 target-scope=30",
                "ip route add check-gateway=ping distance=1 gateway=1.1.1.1 target-scope=30 comment=\"to-ISP1\"",
                "ip route add check-gateway=ping distance=2 gateway=9.9.9.9 target-scope=30 comment=\"to-ISP2\"",
                "ip route add distance=1 dst-address=1.1.1.1/32 gateway=10.10.10.1",
                "ip route add distance=1 dst-address=9.9.9.9/32 gateway=20.20.20.1"
            ]
        ]
    }
]

# ========================
# JALANKAN KONFIGURASI
# ========================
for router in routers:
    print(f"\n🚀 Menghubungi Router {router['name']} ({router['host']})")

    # Format nama file: 2025-04-22-KonfigX-ISP1.txt
    log_filename = f"{today}-{config_label}-{router['name'].replace(' ', '_')}.txt"
    log_path = os.path.join(log_folder, log_filename)

    with open(log_path, "w", encoding="utf-8") as logfile:

        def log_write(text):
            timestamp = datetime.now().strftime("[%H:%M:%S]")
            line = f"{timestamp} {text}"
            print(line)
            logfile.write(line + "\n")

        log_write(f"⏳ Mengecek kesiapan SSH di {router['host']}...")
        if not wait_for_ssh_ready(router["host"], router["username"], router["password"]):
            log_write(f"⚠️ SSH belum siap di {router['host']}... coba lagi nanti")
            continue


        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        connected = False

        for attempt in range(3):
            try:
                log_write(f"🔄 Percobaan koneksi ke {router['host']} (attempt {attempt + 1})...")
                client.connect(
                    hostname=router["host"],
                    username=router["username"],
                    password=router["password"],
                    timeout=20,
                    banner_timeout=20
                )
                connected = True
                break
            except (paramiko.ssh_exception.SSHException, socket.timeout) as e:
                log_write(f"⚠️ Gagal konek attempt {attempt + 1}: {type(e).__name__} - {e}")
            except Exception:
                log_write(f"⚠️ Gagal konek attempt {attempt + 1}: Unknown Error")

                time.sleep(5)

        if not connected:
            log_write(f"❌ Gagal koneksi ke {router['host']} setelah 3 percobaan")
            continue

        try:
            for i, batch in enumerate(router["commands"]):
                log_write(f"🧩 Eksekusi Batch {i + 1} di {router['name']}")
                full_command = "\n".join(batch)
                stdin, stdout, stderr = client.exec_command(full_command)

                output = stdout.read().decode().strip()
                error = stderr.read().decode().strip()

                if output:
                    log_write("✅ Output:\n" + output)
                if error:
                    log_write("⚠️ Error:\n" + error)

                time.sleep(5)

            log_write(f"✅ Selesai konfigurasi {router['name']}")
            log_write(f"📝 Detail konfigurasi {router['name']}:")
            for i, batch in enumerate(router["commands"]):
                log_write(f"\n🔢 Batch {i + 1}:")
                for cmd in batch:
                    logfile.write(f"- {cmd}\n")


        except Exception as e:
            log_write(f"❌ Error saat konfigurasi di {router['name']}: {e}")
        finally:
            client.close()
