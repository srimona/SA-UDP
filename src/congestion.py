import sys
import os

# Ensure parent directory is in Python path for absolute imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


class SignalAwareCongestionControl:
    """Discriminates wireless bit-corruption loss from network congestion loss

    and dynamically scales the congestion window (cwnd).
    """

    def __init__(self, initial_cwnd=2.0, max_cwnd=64.0):
        self.cwnd = float(initial_cwnd)  # Congestion window size (in packets)
        self.ssthresh = 32.0  # Slow start threshold
        self.max_cwnd = float(max_cwnd)
        self.state = "SLOW_START"  # SLOW_START or CONGESTION_AVOIDANCE

    def on_ack_received(self, snr, loss_rate):
        """Updates cwnd on successful SACK arrival based on RFC 5681 logic."""
        if self.state == "SLOW_START":
            self.cwnd += 1.0
            if self.cwnd >= self.ssthresh:
                self.state = "CONGESTION_AVOIDANCE"
        elif self.state == "CONGESTION_AVOIDANCE":
            # Additive Increase: ~1 full packet per RTT
            self.cwnd += 1.0 / self.cwnd

        self.cwnd = min(self.cwnd, self.max_cwnd)
        return self.cwnd

    def on_packet_loss(self, snr, loss_rate):
        """Loss Discrimination Logic:

        - SNR < 12.0 dB: Loss is caused by wireless interference -> Maintain
        cwnd.
        - SNR >= 12.0 dB: Loss is caused by router buffer overflow -> Halve
        cwnd.
        """
        if snr < 12.0:
            # Wireless loss: Do NOT reduce congestion window aggressively
            print(
                f"[!] Loss detected | SNR: {snr:.1f} dB (<12dB) -> Classified as WIRELESS NOISE. CWND preserved at {self.cwnd:.2f}"
            )
        else:
            # True Congestion Loss: Apply TCP Multiplicative Decrease
            self.ssthresh = max(2.0, self.cwnd / 2.0)
            self.cwnd = max(1.0, self.ssthresh)
            self.state = "CONGESTION_AVOIDANCE"
            print(
                f"[!] Loss detected | SNR: {snr:.1f} dB (>=12dB) -> Classified as CONGESTION. CWND reduced to {self.cwnd:.2f}"
            )

        return self.cwnd