import tkinter as tk
from tkinter import ttk
import subprocess
import threading
import time
import psutil
import socket

root = tk.Tk()
root.title("🧪 Stress Test Suite v5.4")
root.geometry("1000x700")
root.configure(bg="#1e1e1e")

style = ttk.Style()
style.theme_use('default')
style.configure("TLabel", background="#1e1e1e", foreground="#00ff99")
style.configure("TFrame", background="#1e1e1e")

# ========== FRAME SETUP ==========
left_panel = ttk.Frame(root, width=300, relief=tk.RIDGE)
center_panel = ttk.Frame(root, width=700)
bottom_panel = ttk.Frame(root, height=180)

left_panel.grid(row=0, column=0, sticky="nswe")
center_panel.grid(row=0, column=1, sticky="nswe")
bottom_panel.grid(row=1, column=0, columnspan=2, sticky="we")

root.grid_rowconfigure(0, weight=3)
root.grid_rowconfigure(1, weight=1)
root.grid_columnconfigure(0, weight=1)
root.grid_columnconfigure(1, weight=2)

# ========== MONITORING ==========
ttk.Label(center_panel, text="📊 System Resource Monitor").pack(anchor="w", padx=10, pady=5)
canvas_cpu = tk.Canvas(center_panel, width=660, height=100, bg="#222222", highlightthickness=0)
canvas_mem = tk.Canvas(center_panel, width=660, height=100, bg="#222222", highlightthickness=0)
canvas_net = tk.Canvas(center_panel, width=660, height=100, bg="#222222", highlightthickness=0)
canvas_cpu.pack(pady=5)
canvas_mem.pack(pady=5)
canvas_net.pack(pady=5)

cpu_history, mem_history, net_history = [0]*60, [0]*60, [0]*60

log_box = tk.Text(bottom_panel, bg="#1e1e1e", fg="#cccccc", height=10, wrap="word")
log_box.pack(fill="both", expand=True, padx=5, pady=5)
log_box.insert(tk.END, "[🧪 LOG] Stress Test Suite initialized...\n")

def log(msg):
    log_box.insert(tk.END, f"[+] {msg}\n")
    log_box.see(tk.END)

def draw_graph(canvas, data, label):
    canvas.delete("all")
    w, h = int(canvas['width']), int(canvas['height'])
    max_val = max(data) if max(data) > 0 else 1
    scale_y = h / max_val
    scale_x = w / len(data)

    for i in range(1, len(data)):
        x1 = (i - 1) * scale_x
        y1 = h - data[i - 1] * scale_y
        x2 = i * scale_x
        y2 = h - data[i] * scale_y
        canvas.create_line(x1, y1, x2, y2, fill="#00ff99", width=2)

    canvas.create_text(5, 5, anchor="nw", text=label, fill="#ffffff", font=("Arial", 8))

def update_stats():
    cpu = psutil.cpu_percent()
    mem = psutil.virtual_memory().percent
    net = psutil.net_io_counters().bytes_sent + psutil.net_io_counters().bytes_recv

    cpu_history.append(cpu)
    mem_history.append(mem)
    net_history.append(net / 1024)

    for h in [cpu_history, mem_history, net_history]:
        if len(h) > 60: h.pop(0)

    draw_graph(canvas_cpu, cpu_history, "CPU Usage %")
    draw_graph(canvas_mem, mem_history, "Memory Usage %")
    draw_graph(canvas_net, net_history, "Network Throughput (KB/s)")

    root.after(1000, update_stats)

update_stats()

# ========== TARGET CONTROL PANEL ==========
targets = {
    "192.168.1.13": {"alias": "ISP1"},
    "192.168.1.14": {"alias": "ISP2"}
}

def create_target_controls(parent, ip, alias):
    frame = ttk.LabelFrame(parent, text=f"{alias}", padding=5)
    frame.pack(fill="x", padx=5, pady=5)

    def toggle_status(label, state):
        label.config(text=label.cget("text").split()[0] + (" ✅" if state else " ❌"),
                     fg="#00ff00" if state else "#ff3333")

    status_scan = tk.Label(frame, text="Scanner ❌", fg="#ff3333", bg="#1e1e1e")
    status_tcp = tk.Label(frame, text="TCP Test ❌", fg="#ff3333", bg="#1e1e1e")
    status_udp = tk.Label(frame, text="UDP Test ❌", fg="#ff3333", bg="#1e1e1e")

    def scan_loop():
        while targets[ip].get("scan_running", False):
            subprocess.call(f"nmap -T4 -Pn -F {ip} >nul", shell=True)
            time.sleep(2)

    def start_scan():
        if not targets[ip].get("scan_running", False):
            targets[ip]["scan_running"] = True
            t = threading.Thread(target=scan_loop, daemon=True)
            targets[ip]["scan_thread"] = t
            t.start()
            toggle_status(status_scan, True)
            log(f"[{alias}] Benchmark scan started")

    def stop_scan():
        targets[ip]["scan_running"] = False
        toggle_status(status_scan, False)
        log(f"[{alias}] Benchmark scan stopped")

    def tcp_test(ip, ports):
        while targets[ip].get("tcp_test", False):
            for port in ports:
                try:
                    with socket.create_connection((ip, port), timeout=2) as s:
                        s.send(b"HEAD / HTTP/1.1\r\nHost: test\r\n\r\n")
                except:
                    continue

    def start_tcp():
        if not targets[ip].get("tcp_test", False):
            targets[ip]["tcp_test"] = True
            t = threading.Thread(target=tcp_test, args=(ip, [80, 443]), daemon=True)
            targets[ip]["tcp_thread"] = t
            t.start()
            toggle_status(status_tcp, True)
            log(f"[{alias}] TCP stress test started")

    def stop_tcp():
        targets[ip]["tcp_test"] = False
        toggle_status(status_tcp, False)
        log(f"[{alias}] TCP test stopped")

    def udp_test(ip):
        while targets[ip].get("udp_test", False):
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                s.sendto(b"A" * 1024, (ip, 53))
                s.close()
            except:
                continue

    def start_udp():
        if not targets[ip].get("udp_test", False):
            targets[ip]["udp_test"] = True
            t = threading.Thread(target=udp_test, args=(ip,), daemon=True)
            targets[ip]["udp_thread"] = t
            t.start()
            toggle_status(status_udp, True)
            log(f"[{alias}] UDP test started")

    def stop_udp():
        targets[ip]["udp_test"] = False
        toggle_status(status_udp, False)
        log(f"[{alias}] UDP test stopped")

    def button_row(label, start_cmd, stop_cmd):
        row = ttk.Frame(frame)
        tk.Button(row, text=label, width=10, command=start_cmd).pack(side="left", padx=2)
        tk.Button(row, text="⛔", width=3, command=stop_cmd).pack(side="left")
        return row

    for row_fn in [
        (button_row("🔎 Scan", start_scan, stop_scan), status_scan),
        (button_row("📶 TCP", start_tcp, stop_tcp), status_tcp),
        (button_row("📡 UDP", start_udp, stop_udp), status_udp),
    ]:
        row_fn[0].pack(fill="x")
        row_fn[1].pack(side="left", padx=10)

ttk.Label(left_panel, text="🎯 Target Nodes").pack(anchor="w", pady=5, padx=5)
target_container = ttk.Frame(left_panel)
target_container.pack(fill="both", expand=True)

for ip, data in targets.items():
    create_target_controls(target_container, ip, data.get("alias", ip))

root.mainloop()
