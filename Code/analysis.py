import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# --- Load dataset ---
df = pd.read_csv("C:\\Users\\Lenovo\\Documents\\A.Project_Python\\DASHBOARD\\Analisis_QOS_Trafik\\dataset\\CASE2.csv")

# --- Filter ICMP Echo Request dan Reply ---
icmp_request = df[df["Info"].str.contains("Echo \\(ping\\) request", na=False)].copy()
icmp_reply = df[df["Info"].str.contains("Echo \\(ping\\) reply", na=False)].copy()

icmp_request.reset_index(drop=True, inplace=True)
icmp_reply.reset_index(drop=True, inplace=True)
icmp_reply["used"] = False

# --- Pairing berdasarkan waktu terdekat ---
paired_rows = []
for i, req in icmp_request.iterrows():
    replies = icmp_reply[(icmp_reply["Time"] > req["Time"]) & (~icmp_reply["used"])]
    if not replies.empty:
        closest_idx = (replies["Time"] - req["Time"]).abs().idxmin()
        rep = icmp_reply.loc[closest_idx]
        Delay = rep["Time"] - req["Time"]
        paired_rows.append({
            "RequestTime": req["Time"],
            "ReplyTime": rep["Time"],
            "Delay": Delay * 1000  # ms
        })
        icmp_reply.at[closest_idx, "used"] = True

paired_df = pd.DataFrame(paired_rows)
paired_df["Jitter"] = paired_df["Delay"].diff().abs()

# --- Packet loss ---
total_req = len(icmp_request)
total_rep = len(paired_df)
Packet_loss_percent = ((total_req - total_rep) / total_req * 100) if total_req > 0 else 0

# --- Delay & Jitter Global ---
average_Delay = paired_df["Delay"].mean()
average_Jitter = paired_df["Jitter"].mean()

# --- Time Binning ---
interval = 10  # detik
start_time = df['Time'].min()
paired_df["TimeBin"] = ((paired_df["RequestTime"] - start_time) // interval).astype(int) * interval

grouped_Delay = paired_df.groupby("TimeBin")["Delay"].mean().sort_index()
grouped_Jitter = paired_df.groupby("TimeBin")["Jitter"].mean().sort_index()

# --- Packet loss per Interval ---
icmp_request["TimeBin"] = ((icmp_request["Time"] - start_time) // interval).astype(int) * interval
icmp_reply["TimeBin"] = ((icmp_reply["Time"] - start_time) // interval).astype(int) * interval
req_count = icmp_request.groupby("TimeBin").size()
rep_count = paired_df.groupby("TimeBin").size()
Packet_loss_by_bin = ((req_count - rep_count) / req_count * 100).fillna(100).sort_index()

# --- Throughput ---
IP_df = df[df['Protocol'].isin(['TCP', 'UDP', 'ICMP'])].copy()
IP_df = IP_df.sort_values(by='Time')
IP_df["TimeBin"] = ((IP_df["Time"] - start_time) // interval).astype(int) * interval
bytes_per_bin = IP_df.groupby("TimeBin")["Length"].sum()
throughput_per_bin = (bytes_per_bin * 8) / (interval * 1_000_000)  # Mbps
throughput_per_bin = throughput_per_bin.sort_index()

duration = IP_df["Time"].iloc[-1] - IP_df["Time"].iloc[0]
total_bytes = IP_df["Length"].sum()
throughput_mbps = (total_bytes * 8) / (duration * 1_000_000) if duration > 0 else 0

# --- GRAFIK 1: Delay, Jitter (y1) dan Packet loss (y2) ---
sns.set(style="whitegrid")
fig, ax1 = plt.subplots(figsize=(15, 7))

# Y-axis pertama
ax1.plot(grouped_Delay.index, grouped_Delay.values, label="Average Delay (ms)", marker='o')
ax1.plot(grouped_Jitter.index, grouped_Jitter.values, label="Jitter (ms)", marker='s')
ax1.set_xlabel("Waktu (detik sejak awal Capture)")
ax1.set_ylabel("Delay / Jitter (ms)")
ax1.tick_params(axis='y')
ax1.legend(loc='upper left')

# Y-axis kedua
ax2 = ax1.twinx()
ax2.plot(Packet_loss_by_bin.index, Packet_loss_by_bin.values, label="Packet loss (%)", color='green', marker='x')
ax2.set_ylabel("Packet loss (%)", color='green')
ax2.tick_params(axis='y', labelcolor='green')

# Gabungkan legend dari kedua axis
lines1, labels1 = ax1.get_legend_handles_labels()
lines2, labels2 = ax2.get_legend_handles_labels()
ax1.legend(lines1 + lines2, labels1 + labels2, loc='upper left')

plt.title("Grafik QoS: Delay, Jitter, dan Packet loss per Interval")
fig.tight_layout()
plt.savefig("Grafik Delay_Jitter_PacketL_CASE2_v2.png")
plt.show()

# --- GRAFIK 2: Throughput ---
plt.figure(figsize=(15, 5))
plt.bar(throughput_per_bin.index, throughput_per_bin.values, width=8, color='skyblue', label="Throughput (Mbps)")
plt.xlabel("Waktu (detik sejak awal Capture)")
plt.ylabel("Throughput (Mbps)")
plt.title("Grafik Throughput per Interval")
plt.legend()
plt.tight_layout()
plt.savefig("Grafik Throughput_CASE2.png")
plt.show()

# --- Summary (dibulatkan) ---
print(f"Total Echo Request: {total_req}")
print(f"Total Echo Reply (paired): {total_rep}")
print(f"Packet loss (Total): {round(Packet_loss_percent, 1)}%")
print(f"Average Delay: {round(average_Delay, 1)} ms")
print(f"Jitter (Average): {round(average_Jitter, 1)} ms")
print(f"Throughput (Average): {round(throughput_mbps, 2)} Mbps")
print(f"Durasi Capture: {round(duration, 2)} detik")
