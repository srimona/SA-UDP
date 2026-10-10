import struct
import random
import time

# Telemetry Header Format: SNR (float: 4B), RSSI (float: 4B), Loss Rate (float: 4B)
# Total size = 12 bytes
TELEMETRY_FORMAT = "!fff"
TELEMETRY_SIZE = struct.calcsize(TELEMETRY_FORMAT)

class LinkMonitor:
    """Simulates wireless link conditions and generates telemetry reports."""
    def __init__(self, base_snr=25.0, base_rssi=-65.0):
        self.base_snr = base_snr    # Signal-to-Noise Ratio in dB
        self.base_rssi = base_rssi  # Received Signal Strength Indicator in dBm
        self.packets_received = 0
        self.packets_lost = 0

    def simulate_channel_fluctuation(self):
        """Simulates real-world signal drops and noise spikes."""
        snr_noise = random.uniform(-5.0, 3.0)
        rssi_noise = random.uniform(-4.0, 2.0)
        
        current_snr = max(5.0, self.base_snr + snr_noise)
        current_rssi = min(-30.0, self.base_rssi + rssi_noise)
        
        total_pkts = self.packets_received + self.packets_lost
        loss_rate = (self.packets_lost / total_pkts) if total_pkts > 0 else 0.0
        
        return current_snr, current_rssi, loss_rate

    def pack_telemetry(self):
        snr, rssi, loss_rate = self.simulate_channel_fluctuation()
        return struct.pack(TELEMETRY_FORMAT, snr, rssi, loss_rate), snr, rssi, loss_rate

    @staticmethod
    def unpack_telemetry(raw_bytes):
        return struct.unpack(TELEMETRY_FORMAT, raw_bytes)


class SignalAwareRTO:
    """Calculates adaptive Retransmission Timeout (RTO) using Jacobson's Algorithm + SNR scaling."""
    def __init__(self, initial_rto=1.0):
        self.srtt = None     # Smoothed RTT
        self.rttvar = None   # RTT Variance
        self.rto = initial_rto

    def update_rto(self, measured_rtt, snr):
        # 1. Standard RFC 6298 Jacobson/Karn RTT calculation
        if self.srtt is None:
            self.srtt = measured_rtt
            self.rttvar = measured_rtt / 2.0
        else:
            alpha = 0.125
            beta = 0.25
            self.rttvar = (1 - beta) * self.rttvar + beta * abs(self.srtt - measured_rtt)
            self.srtt = (1 - alpha) * self.srtt + alpha * measured_rtt

        base_rto = self.srtt + max(0.1, 4 * self.rttvar)

        # 2. Signal-Aware Scaling Factor
        # Lower SNR (< 15 dB) means degraded link -> scale up RTO to prevent back-to-back spurious retransmissions
        if snr < 12.0:
            snr_factor = 1.8
        elif snr < 20.0:
            snr_factor = 1.3
        else:
            snr_factor = 1.0

        self.rto = max(0.2, base_rto * snr_factor)
        return self.rto
