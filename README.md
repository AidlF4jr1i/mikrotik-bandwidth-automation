# 📡 Auto-Balancing Network: An Adaptive Bandwidth Optimization System

This repository contains the full implementation of the final project **"Implementation of Network Automation for Bandwidth Optimization in Computer Networks"** from the Faculty of Computer Science, Sriwijaya University. This system intelligently manages network traffic across dual-ISP links to maximize bandwidth and ensure high availability.

## 🎥 Project Demo

Click the thumbnail below to watch a full demonstration of the system in action, including automated configuration, real-time monitoring, live stress testing, and automated mitigation with Telegram alerts.

[![Project Demo](https://img.youtube.com/vi/FZYJ8l-MY5c/0.jpg)](https://youtu.be/FZYJ8l-MY5c)

---

## 🧠 Project Overview

In environments with dynamic traffic, manual network configuration is inefficient and prone to errors, often leading to bottlenecks and poor performance. This project solves that problem by introducing an intelligent automation system built with Python.

The system uses the **Paramiko** library to connect to MikroTik routers via SSH, deploying adaptive **Load Balancing (PCC)** and a **Failover** mechanism. Its core feature is a real-time monitoring module that detects network stress (e.g., high CPU load) and automatically executes mitigation strategies—from adjusting traffic ratios to rerouting all traffic to a stable connection.

### ✨ Key Features

- **Automated Configuration**: Deploys complex network setups (IP, NAT, Mangle, PCC) to multiple routers with a single script.
- **Intelligent Monitoring**: Continuously tracks router CPU load to detect performance degradation in real-time.
- **Adaptive Mitigation**: Automatically adjusts traffic distribution ratios (e.g., from 60:40 to 20:80) when a link is under stress.
- **Automated Failover**: Reroutes 100% of traffic to a healthy ISP connection if mitigation is insufficient, ensuring service continuity.
- **Real-time Alerts**: Integrates with the **Telegram API** to instantly notify administrators of detected issues and actions taken.

---

## 🛠️ Technologies & Tools

- **Core Logic**: Python 3
- **Network Automation**: Paramiko (SSH)
- **Monitoring & Alerts**: Telegram API (`requests` library)
- **Stress Testing**: Custom GUI tool built with Tkinter, Psutil, & Scapy
- **Data Analysis**: Pandas & Matplotlib for parsing Wireshark captures
- **Hardware**: MikroTik RB941-2nD Routers
- **Protocols**: PCC, NAT, Recursive Gateway Failover

---

## 📊 Performance Results

The system was evaluated in four scenarios, comparing manual configuration against the automated system under normal and high-stress conditions. The automation provided a dramatic improvement in Quality of Service (QoS).

| Parameter | Manual (Single ISP, Stressed) | Automated (Dual ISP, Stressed) | Improvement |
| :--- | :---: | :---: | :---: |
| **Throughput** | 2.12 Mbps | **9.6 Mbps** | **+352%** ▲ |
| **Packet Loss**| 22.8% | **2.9%** | **-87%** ▼ |

---

## 🏗️ System Architecture & Topology

The network is designed with two ISP routers for redundancy and a central admin router that manages traffic distribution. The automation scripts are executed from an administrator's machine connected to the same management switch.

![Network Topology](Topologi/Topologi_Utama_TA.png)

---

## 📂 Repository Structure

```
.
├── 📁 Code/
│   ├── autoConfig.py      # Script for initial router configuration
│   ├── monitoring.py      # Main script for monitoring and mitigation
│   ├── Strest_tes.py      # GUI-based tool for stress testing
│   └── analysis.py        # Script for QoS analysis from .csv captures
│
├── 📁 Topologi/
│   └── Topologi_Utama_TA.png # Network architecture diagram
│
└── 📜 README.md
```

### 🗂️ Dataset

The dataset used for QoS analysis (`analysis.py`) contains packet capture data from Wireshark during the four test scenarios. It is available for download for result replication purposes.

➡️ **[Download Dataset (Google Drive)](https://drive.google.com/open?id=1P_ZR4eY4HQ-dkBK5CI_VCGTLUg7kok1m&usp=drive_fs)**

---

## 🚀 How to Run the System & Replicate Tests

Follow these steps to deploy the system and replicate the test scenarios.

1.  **Setup Hardware**: Configure the MikroTik routers on the network according to the diagram in the `Topologi/` folder. Ensure all devices are connected and reachable via SSH from the administrator's machine.

2.  **Install Dependencies**: Install the required Python libraries.
    ```bash
    pip install paramiko requests pandas matplotlib psutil
    ```

3.  **Initial Configuration (Scenario 3 & 4)**: Run the auto-configuration script to apply the base Load Balancing and Failover rules to all routers.
    ```bash
    python Code/autoConfig.py
    ```

4.  **Run Monitoring & Mitigation System (Scenario 4)**: Launch the intelligent monitoring system. This script will run continuously, watch for network stress, and listen for Telegram commands.
    ```bash
    python Code/monitoring.py
    ```

5.  **Simulate Network Stress (Scenario 2 & 4)**: To test the system's reliability, use the `Strest_tes.py` tool to apply a controlled traffic load to one of the ISP routers. This is a critical step to observe the automated mitigation and failover responses from `monitoring.py`.
    ```bash
    python Code/Strest_tes.py
    ```

---

## 📌 Conclusion

By implementing Network Automation, this project demonstrated a significant improvement in network performance and efficiency, minimizing manual intervention and enhancing scalability for future deployments.

This work serves as a practical blueprint for building resilient, self-managing networks capable of handling the demands of modern digital infrastructure.

---

## 📬 Contact

Ahmad Aidil Fajri  
📧 ahmadaidilfajri0@gmail.com  
🎓 Universitas Sriwijaya, Teknik Komputer D3
