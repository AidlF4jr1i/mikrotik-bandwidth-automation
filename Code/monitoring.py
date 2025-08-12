import paramiko
import time
import requests
import csv
import os
import threading
import re
from datetime import datetime

# ========== KONFIG ==========
ISP1 = {"host": "192.168.10.1", "username": "admin", "password": "admin1"}
ISP2 = {"host": "192.168.10.2", "username": "admin", "password": "admin2"}
ADMIN_ROUTER = {"host": "192.168.10.3", "username": "admin", "password": "admin3"}

CPU_HIGH = 60
CPU_LOW = 40
RECOVERY_TIMER = 10
MITIGATION_DURATION = 10
STUCK_TIMEOUT = 12
DEFAULT_DELAY = 10

ISP_GATEWAYS = {
    "isp1": "1.1.1.1",
    "isp2": "9.9.9.9"
}

TELEGRAM_BOT_TOKEN = "7781361596:AAFwmHkJFMEpKfFW91EEkTiGqUaCQj_FvbE"
CHAT_ID = "1386580081"

# Buat folder log jika belum ada
LOG_DIR = "Log_monitoring"
if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)

TIMESTAMP = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
LOG_FILE = os.path.join(LOG_DIR, f"log-{TIMESTAMP}.txt")
CSV_FILE = os.path.join(LOG_DIR, f"log-{TIMESTAMP}.csv")


status = {
    "isp1": {"state": "normal", "cpu": -1, "recovery_start": None, "mitigation_start": None, "failover_pending": False,"failover_triggered_at": None},
    "isp2": {"state": "normal", "cpu": -1, "recovery_start": None, "mitigation_start": None, "failover_pending": False,"failover_triggered_at": None},
}
current_mode = "load_balance"
pcc_ratio_state = "60:40"
active_mitigation = {"isp1": False, "isp2": False}
global last_active_gateway_count
last_active_gateway_count = 2

# ========== TELEGRAM ==========
def send_telegram_alert(msg):
    try:
        requests.post(
            f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
            data={"chat_id": CHAT_ID, "text": msg, "parse_mode": "Markdown"}
        )
    except Exception as e:
        print(f"❌ Telegram error ({type(e).__name__}): {e}")


def log_event(message):
    send_telegram_alert(message)
    cpu1 = status["isp1"]["cpu"] if status["isp1"]["cpu"] is not None else -1
    cpu2 = status["isp2"]["cpu"] if status["isp2"]["cpu"] is not None else -1
    write_log(cpu1, cpu2, current_mode, message)

def send_csv_to_telegram():
    if not os.path.exists(CSV_FILE):
            log_event("⚠️ CSV tidak ditemukan untuk dikirim.")
            return
    try:
        with open(CSV_FILE, 'rb') as f:
            files = {"document": f}
            data = {"chat_id": CHAT_ID, "caption": "📊 Export Log CPU ISP Monitoring"}
            requests.post(f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendDocument", files=files, data=data)
    except Exception as e:
        print(f"❌ Kirim CSV gagal: {e}")

def telegram_command_listener():
    offset = None
    print("📡 Telegram listener aktif...")
    while True:
        try:
            url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getUpdates"
            params = {"offset": offset, "timeout": 30}
            resp = requests.get(url, params=params, timeout=35)

            if resp.status_code != 200:
                print(f"❌ Telegram HTTP error: {resp.status_code}")
                time.sleep(10)
                continue

            data = resp.json()
            for msg in data.get("result", []):
                offset = msg["update_id"] + 1

                message = msg.get("message")
                if not message:
                    continue

                chat_id = str(message.get("chat", {}).get("id", ""))
                if chat_id != CHAT_ID:
                    continue

                text = message.get("text", "").strip().lower()
                print(f"📩 Diterima perintah Telegram: {text}")
                write_log(status["isp1"]["cpu"], status["isp2"]["cpu"], current_mode, f"Command Telegram: {text}")
                if not text:
                    continue

                if text == "/status":
                    send_telegram_alert(f"""
📊 Status Monitoring
ISP1: {status['isp1']['cpu']}% | ISP2: {status['isp2']['cpu']}%
Mode: {current_mode} | PCC: {pcc_ratio_state}
Mitigasi: {", ".join([k.upper() for k,v in active_mitigation.items() if v]) or "-"}""")

                elif text == "/export":
                    export_log_to_csv()
                    send_csv_to_telegram()

                elif text == "/routing":
                    gws = get_active_gateway()
                    aktif = ", ".join([k.upper() for k, v in gws.items() if v["active"]]) if gws else "-"
                    send_telegram_alert(f"📍 Routing aktif saat ini: {aktif}")

                elif text == "/help":
                    send_telegram_alert("""📖 *Command Tersedia:*
/status - Cek status CPU & mode
/export - Export log ke CSV
/routing - Lihat default gateway aktif
/help - Tampilkan daftar perintah""")

        except requests.exceptions.ReadTimeout:
            print("⚠ Timeout dari Telegram, mencoba ulang...")
        except Exception as e:
            print(f"⚠ Telegram listener error ({type(e).__name__}): {e}")
        time.sleep(3)


# ========== FUNGSI UTAMA ==========
def get_cpu_load(router, label):
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(router["host"], username=router["username"], password=router["password"], timeout=20)
        stdin, stdout, stderr = ssh.exec_command("/system resource print without-paging")
        output = stdout.read().decode()
        ssh.close()
        match = re.search(r"cpu-load:\s+(\d+)", output)
        if match:
            return int(match.group(1))
    except Exception as e:
        print(f"❌ Gagal ambil CPU {label}: {e}")
    return None

def write_log(cpu1, cpu2, mode, event_msg=""):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"[{now}] ISP1: {cpu1}% | ISP2: {cpu2}% | Mode: {mode} | Event: {event_msg}\n")

def export_log_to_csv():
    if not os.path.exists(LOG_FILE):
        return
    with open(LOG_FILE, "r", encoding="utf-8") as txt, open(CSV_FILE, "w", newline="", encoding="utf-8") as csv_out:
        writer = csv.writer(csv_out)
        writer.writerow(["timestamp", "cpu_isp1", "cpu_isp2", "mode", "event"])
        for line in txt:
            try:
                parts = line.strip().split("] ")
                timestamp = parts[0].replace("[", "")
                data = parts[1]
                cpu1 = data.split("ISP1:")[1].split("%")[0].strip()
                cpu2 = data.split("ISP2:")[1].split("%")[0].strip()
                mode = data.split("Mode:")[1].split("|")[0].strip() if "| Event:" in data else data.split("Mode:")[1].strip()
                event = data.split("| Event:")[1].strip() if "| Event:" in data else ""
                writer.writerow([timestamp, cpu1, cpu2, mode, event])
            except Exception as e:
                print(f"⚠️ Gagal parsing log: {e}")


def exec_admin_router(command):
    try:
        print(f"📤 Menjalankan command: {command}")  # Tambah debug
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(ADMIN_ROUTER["host"], username=ADMIN_ROUTER["username"], password=ADMIN_ROUTER["password"], timeout=10)
        stdin, stdout, stderr = ssh.exec_command(command)

        out = stdout.read().decode()
        err = stderr.read().decode()
        print(f"📥 Output: {out.strip()}")
        if err.strip():
            print(f"❗ Error: {err.strip()}")

        ssh.close()
    except Exception as e:
        print(f"❌ Router command error ({type(e).__name__}): {e}")


def run_command(commands):
    if isinstance(commands, str):
        commands = [commands]
    for cmd in commands:
        print(f"🧾 [RUN_COMMAND] {cmd}")  # Tambah log
        exec_admin_router(cmd)


def switch_to_isp_only(isp, source="routing"):
    global current_mode
    target = "ISP1" if isp == "isp1" else "ISP2"
    old_connection_mark = "via-ether2" if isp == "isp1" else "via-ether1"

    if source == "cpu":
        log_event(f"🔁 *FAILOVER CPU*: Trafik dialihkan ke {target}")
    else:
        log_event(f"🔁 *FAILOVER ROUTING*: Trafik dialihkan ke {target}")
    
    if current_mode != f"only-{isp}":
        log_event(f"🔁 Trafik dialihkan ke {target} (failover)")
        
        # 💡 Hapus semua koneksi
        clear_stuck_connections(old_connection_mark)

        # Ubah mark PCC
        set_pcc_ratio_dynamic("ISP1-100" if isp == "isp1" else "ISP2-100")
        
        run_command([
            f"ip route enable [find comment=\"to-{target}\"]",
            f"ip route enable [find where routing-mark=\"via-{target}\"]",
            f"ip route disable [find comment=\"to-{'ISP2' if isp == 'isp1' else 'ISP1'}\"]",
            f"ip route disable [find where routing-mark=\"via-{'ISP2' if isp == 'isp1' else 'ISP1'}\"]"
        ])
        current_mode = f"only-{isp}"



def set_load_balancing():
    global current_mode
    if current_mode != "load_balance":
        log_event("⚖ Load balancing aktif kembali")

        run_command([
            "ip route enable [find comment=\"to-ISP1\"]",
            "ip route enable [find comment=\"to-ISP2\"]",
            "ip route enable [find where routing-mark=\"via-ISP1\"]",
            "ip route enable [find where routing-mark=\"via-ISP2\"]"
        ])
        current_mode = "load_balance"


def set_pcc_ratio_dynamic(mode):
    global pcc_ratio_state
    print(f"🔁 [PCC-RATIO] Mode: {mode}")  # Tambah log
    if mode == "60:40":
        commands = [
            'ip firewall mangle set [find comment~"PCC-AUTO" and per-connection-classifier~"5/0"] new-connection-mark=via-ether1',
            'ip firewall mangle set [find comment~"PCC-AUTO" and per-connection-classifier~"5/1"] new-connection-mark=via-ether1',
            'ip firewall mangle set [find comment~"PCC-AUTO" and per-connection-classifier~"5/2"] new-connection-mark=via-ether1',
            'ip firewall mangle set [find comment~"PCC-AUTO" and per-connection-classifier~"5/3"] new-connection-mark=via-ether2',
            'ip firewall mangle set [find comment~"PCC-AUTO" and per-connection-classifier~"5/4"] new-connection-mark=via-ether2',
        ]
        pcc_ratio_state = "60:40"

    elif mode == "ISP1-100":
        commands = [
            'ip firewall mangle set [find comment~"PCC-AUTO"] new-connection-mark=via-ether1'
        ]
        pcc_ratio_state = "100% (ISP1)"

    elif mode == "ISP2-100":
        commands = [
            'ip firewall mangle set [find comment~"PCC-AUTO"] new-connection-mark=via-ether2'
        ]
        pcc_ratio_state = "100% (ISP2)"

    elif mode == "ISP1-20":
        commands = []
        for i in [1]:
            commands.append(f'ip firewall mangle set [find comment~"PCC-AUTO" and per-connection-classifier=both-addresses-and-ports:5/{i}] new-connection-mark=via-ether1')
        for i in [0, 2, 3, 4]:
            commands.append(f'ip firewall mangle set [find comment~"PCC-AUTO" and per-connection-classifier=both-addresses-and-ports:5/{i}] new-connection-mark=via-ether2')
        pcc_ratio_state = "20:80 (ISP2)"

    elif mode == "ISP2-20":
        commands = []
        for i in [1]:
            commands.append(f'ip firewall mangle set [find comment~"PCC-AUTO" and per-connection-classifier=both-addresses-and-ports:5/{i}] new-connection-mark=via-ether2')
        for i in [0, 2, 3, 4]:
            commands.append(f'ip firewall mangle set [find comment~"PCC-AUTO" and per-connection-classifier=both-addresses-and-ports:5/{i}] new-connection-mark=via-ether1')
        pcc_ratio_state = "20:80 (ISP1)"
        
    log_event(f"🔧 PCC rasio diubah: {pcc_ratio_state}")
    run_command(commands)


def get_active_gateway():
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(ADMIN_ROUTER["host"], username=ADMIN_ROUTER["username"], password=ADMIN_ROUTER["password"], timeout=10)
        stdin, stdout, stderr = ssh.exec_command('ip route print detail where dst-address=0.0.0.0/0')
        output = stdout.read().decode()
        ssh.close()

        result = {
            "isp1": {"active": False, "xs": False},
            "isp2": {"active": False, "xs": False}
        }

        current_route = ""
        is_active = False
        is_disabled = False
        is_isp1 = False
        is_isp2 = False

        for line in output.splitlines():
            line = line.strip()
            if re.match(r'^\d', line):
                # Save data for previous entry
                if current_route:
                    if is_isp1:
                        if "X" in current_route:
                            result["isp1"]["xs"] = True
                        if "A" in current_route:
                            result["isp1"]["active"] = True
                    elif is_isp2:
                        if "X" in current_route:
                            result["isp2"]["xs"] = True
                        if "A" in current_route:
                            result["isp2"]["active"] = True

                # Reset
                current_route = line
                is_active = "A" in line
                is_disabled = "X" in line
                is_isp1 = False
                is_isp2 = False
            else:
                if "to-ISP1" in line or "routing-mark=via-ISP1" in line:
                    is_isp1 = True
                elif "to-ISP2" in line or "routing-mark=via-ISP2" in line:
                    is_isp2 = True

        # Last entry
        if current_route:
            if is_isp1:
                if "X" in current_route:
                    result["isp1"]["xs"] = True
                if "A" in current_route:
                    result["isp1"]["active"] = True
            elif is_isp2:
                if "X" in current_route:
                    result["isp2"]["xs"] = True
                if "A" in current_route:
                    result["isp2"]["active"] = True

        return result

    except Exception as e:
        print(f"❌ Gagal baca route di ADMIN: {e}")
        return {}

def clear_stuck_connections(connection_mark):
    print(f"🧹 Menghapus koneksi dengan connection-mark={connection_mark}")
    try:
        cmd = f"/ip firewall connection remove [find connection-mark={connection_mark}]"
        exec_admin_router(cmd)
        log_event(f"🧹 Koneksi dengan mark {connection_mark} dihapus (fail-over cleanup).")
    except Exception as e:
        print(f"❌ Gagal hapus koneksi ({connection_mark}): {e}")

# ========== MONITORING ==========
threading.Thread(target=telegram_command_listener, daemon=True).start()

try:
    
    print("🟢 Monitoring dimulai...")
    log_event("🟢 Monitoring dimulai")
    while True:
        now = datetime.now()
        cpu1 = get_cpu_load(ISP1, "ISP1")
        cpu2 = get_cpu_load(ISP2, "ISP2")
        status["isp1"]["cpu"] = cpu1 if cpu1 is not None else -1
        status["isp2"]["cpu"] = cpu2 if cpu2 is not None else -1

        print(f"📈 ISP1: {cpu1}% | {status['isp1']['state']}")
        print(f"📈 ISP2: {cpu2}% | {status['isp2']['state']}")

        # 🔁 Deteksi failover otomatis

        try:
            route_status = get_active_gateway()
            print(f"✅ Status Route: {route_status}")
            print(f"🌐 Mode sekarang: {current_mode}")

            isp1_down = not route_status["isp1"]["active"] and not route_status["isp1"]["xs"]
            isp2_down = not route_status["isp2"]["active"] and not route_status["isp2"]["xs"]

            # Deteksi gateway ISP tidak reachable (hanya status S, belum disabled)
            if isp1_down:
                log_event("⚠ Internet ISP1 kemungkinan *DOWN* (gateway tidak reachable).")
            if isp2_down:
                log_event("⚠ Internet ISP2 kemungkinan *DOWN* (gateway tidak reachable).")

            # Recovery dari failover CPU (jika sebelumnya disable dan sekarang aktif lagi)
            if route_status["isp1"]["active"] and route_status["isp2"]["active"] and current_mode != "load_balance":
                # 🧹 Bersihkan semua koneksi yang terlanjur ngunci ke salah satu ISP
                clear_stuck_connections("via-ether1")
                clear_stuck_connections("via-ether2")
                log_event("✅ Kedua ISP aktif kembali. Load balancing tersedia.")
                set_load_balancing()
                set_pcc_ratio_dynamic("60:40")

        except Exception as e:
            print(f"❌ Gagal cek routing aktif: {e}")



        # 🚦 CPU Check + Mitigasi
        for isp_key, cpu, label in [("isp1", cpu1, "ISP1"), ("isp2", cpu2, "ISP2")]:
            if current_mode != "load_balance" and status[isp_key]["state"] != "overload":
                print(f"⏭ Skip Pemindahan Rasio {label}, mode sekarang: {current_mode}")
                continue
            other = "isp2" if isp_key == "isp1" else "isp1"
            if cpu is None:
                continue
            if cpu >= CPU_HIGH:
                if status[isp_key]["state"] != "overload":
                    status[isp_key]["state"] = "overload"
                    status[isp_key]["mitigation_start"] = now
                    
                    if status[other]["state"] != "overload":
                        status[other]["mitigation_start"] = None
                    
                    active_mitigation[isp_key] = True
                    active_mitigation[other] = False
                    log_event(f"🚨 CPU {label} tinggi: {cpu}%")
                    log_event(f"⚠ Rasio dialihkan ke {other.upper()}")
                    set_pcc_ratio_dynamic("ISP1-20" if isp_key == "isp1" else "ISP2-20")
                
                elif status[isp_key]["mitigation_start"] and (now - status[isp_key]["mitigation_start"]).total_seconds() >= MITIGATION_DURATION:
                    if not status[isp_key]["failover_pending"]:
                        status[isp_key]["failover_pending"] = True
                        status[isp_key]["failover_triggered_at"] = now
                        print(f"⏳ Delay failover {label}, menunggu 15 detik konfirmasi CPU tetap tinggi...")
                    elif (now - status[isp_key]["failover_triggered_at"]).total_seconds() >= 15:
                        switch_to_isp_only(other)
                        status[isp_key]["failover_pending"] = False
                        status[isp_key]["failover_triggered_at"] = None

                elif status[isp_key]["mitigation_start"] and (now - status[isp_key]["mitigation_start"]).total_seconds() > STUCK_TIMEOUT:
                    log_event(f"🛑 Mitigasi {label} tidak efektif. CPU tetap tinggi.")
                    set_pcc_ratio_dynamic("60:40")
                    status[isp_key]["state"] = "normal"
                    status[isp_key]["mitigation_start"] = None
                    active_mitigation[isp_key] = False
                    log_event(f"🔄 Reset mitigasi {label}, status disetel ulang.")
            elif status[isp_key]["state"] == "overload" and cpu < CPU_LOW:
                if not status[isp_key]["recovery_start"]:
                    status[isp_key]["recovery_start"] = now
                elif (now - status[isp_key]["recovery_start"]).total_seconds() >= RECOVERY_TIMER:
                    
                    status[isp_key]["state"] = "normal"
                    active_mitigation[isp_key] = False
                    status[isp_key]["recovery_start"] = None
                    log_event(f"✅ CPU {label} kembali normal: {cpu}%")
                    
                    # Reset failover_pending dan triggered_at untuk menghindari stuck
                    if status[isp_key]["failover_pending"]:
                        status[isp_key]["failover_pending"] = False
                        status[isp_key]["failover_triggered_at"] = None
                        print(f"🛑 Failover {label} dibatalkan karena CPU pulih sebelum trigger")

                    set_pcc_ratio_dynamic("60:40")
                    set_load_balancing()


        write_log(cpu1 or -1, cpu2 or -1, current_mode)
        time.sleep(DEFAULT_DELAY)

except KeyboardInterrupt:
    print("🛑 Monitoring dihentikan oleh user.")
    export_log_to_csv()
    send_csv_to_telegram()