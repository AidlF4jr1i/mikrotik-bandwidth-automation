
# 📡 Network Automation for Bandwidth Optimization

This repository contains the full implementation and documentation of the final project titled **"Implementasi Network Automation untuk Optimasi Bandwidth pada Jaringan Komputer"** conducted at the Faculty of Computer Science, Sriwijaya University.

## 🧠 Project Overview

The project addresses the critical need for dynamic bandwidth optimization in computer networks using **Network Automation**. Traditional static/manual configurations often fail to adapt to high or fluctuating traffic conditions. To solve this, a Python-based automation system utilizing **Paramiko** (SSH automation) was developed.

### ✅ Objectives

- Automate bandwidth allocation using Load Balancing (PCC method).
- Replace manual configurations with adaptive scripts.
- Improve QoS parameters such as **Throughput**, **Packet Loss**, **Delay**, and **Jitter**.
- Implement real-time monitoring and alert via **Telegram bot**.

## 🛠 Technologies & Tools

- **Python 3**
- **Paramiko** (SSH automation library)
- **MikroTik RouterOS**
- **Visual Studio Code**
- **Wireshark** (Traffic Capture)
- **Telegram API** (Notifications)
- **RB941-2nD MikroTik Routers**
- **Stress Testing Scripts**

## 📊 Experimental Scenarios

The project tested four configurations:

1. **Skenario 1** – Manual bandwidth management with single ISP.
2. **Skenario 2** – Single ISP under stress test (no automation).
3. **Skenario 3** – Two ISPs with PCC Load Balancing (automated).
4. **Skenario 4** – Two ISPs with PCC + stress test + monitoring + alerting.

| Scenario | Throughput ↑ | Packet Loss ↓ |
|----------|--------------|----------------|
| Manual (S1) | 2.92 Mbps | 22.8% |
| Automated (S4) | 11.98 Mbps | 2.1% |

## 🔁 Topology

The final system used:

- 3 Routers (ISP1, ISP2, Admin Router)
- 1 Client Device
- 1 Admin Laptop (runs Python scripts & monitoring)
- 1 Switch

Implemented automation includes:

- Auto IP assignment
- NAT & PCC rules
- Failover recursive gateway
- Monitoring CPU usage
- Real-time Telegram alerts

## 📂 Repository Structure




## 🚀 How to Run

1. Ensure MikroTik routers are accessible via SSH.
2. Configure IP addresses as per `docs/Topology_Design.png`.
3. Run `config_automation.py` to apply router configurations.
4. Use `stress_test.py` to simulate traffic.
5. Monitor system health using `monitoring_bot.py`.

## 📌 Conclusion

By implementing Network Automation, this project demonstrated a significant improvement in network performance and efficiency, minimizing manual intervention and enhancing scalability for future deployments.

## 📬 Contact

Ahmad Aidil Fajri  
📧 aidil.fajri@student.unsri.ac.id  
🏫 Universitas Sriwijaya, Teknik Komputer D3

