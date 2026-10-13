import sys
import os
import time
import matplotlib.pyplot as plt

# Ensure root folder is in python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.telemetry import SignalAwareRTO

def run_performance_simulation():
    print("[+] Running SA-UDP Module 4 Performance Benchmark...")

    # Simulated SNR range (from clear channel 25 dB down to heavy interference 5 dB)
    snr_levels = [25.0, 20.0, 15.0, 10.0, 5.0]
    sample_rtt = 0.05  # 50 ms baseline RTT

    blind_rto_times = []
    sa_udp_rto_times = []

    rto_engine = SignalAwareRTO(initial_rto=0.2)

    for snr in snr_levels:
        # Standard blind RTO (Pure RTT delay-based, ignores SNR)
        blind_rto = sample_rtt + 0.1
        blind_rto_times.append(blind_rto)

        # SA-UDP Signal-Aware RTO (Scales dynamically based on SNR)
        sa_rto = rto_engine.update_rto(sample_rtt, snr)
        sa_udp_rto_times.append(sa_rto)

        print(f"[*] SNR: {snr:4.1f} dB | Blind RTO: {blind_rto:.3f}s | SA-UDP Adaptive RTO: {sa_rto:.3f}s")

    # Generate Performance Visualization Chart
    plt.figure(figsize=(9, 5))
    plt.plot(snr_levels, blind_rto_times, 'r--o', linewidth=2, label="Standard RTO (Blind to Signal)")
    plt.plot(snr_levels, sa_udp_rto_times, 'g-s', linewidth=2, label="SA-UDP Adaptive RTO (Signal-Aware)")

    plt.gca().invert_xaxis()  # Invert so channel degradation moves left-to-right
    plt.title("SA-UDP Retransmission Timeout Adaptation vs. Wireless Interference", fontsize=12)
    plt.xlabel("Signal-to-Noise Ratio (SNR in dB) [Degrading Channel ->]", fontsize=10)
    plt.ylabel("Retransmission Timeout (RTO in Seconds)", fontsize=10)
    plt.grid(True, linestyle=":", alpha=0.6)
    plt.legend(fontsize=10)

    # Save output plot inside src directory
    output_path = os.path.join("src", "performance_chart.png")
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"\n[+] Benchmark complete! Performance chart saved as '{output_path}'")
    
    # Display plot window
    plt.show()

if __name__ == "__main__":
    run_performance_simulation()