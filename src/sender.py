import sys
import os
import time
import socket

# Ensure root folder is in python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.packet import pack_packet, unpack_sack
from src.telemetry import SignalAwareRTO
from src.congestion import SignalAwareCongestionControl

def run_sender():
    receiver_address = ('127.0.0.1', 9999)
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.settimeout(0.5)

    rto_engine = SignalAwareRTO(initial_rto=0.200)
    congestion_control = SignalAwareCongestionControl()
    
    payload_data = [b"SA-UDP Packet Payload Data Chunk " + str(i).encode() for i in range(1, 6)]
    
    print("[+] SA-UDP Full Protocol Sender Active (Modules 1-4 Complete)...")
    print(f"[+] Transmitting {len(payload_data)} chunks to {receiver_address[0]}:{receiver_address[1]}...\n")

    seq_num = 1
    for chunk in payload_data:
        packet = pack_packet(seq_num, chunk)
        
        print(f"[->] Sent Pkt #{seq_num} | CWND: {congestion_control.cwnd:.2f} | State: {congestion_control.state}")
        
        send_time = time.time()
        sock.sendto(packet, receiver_address)

        try:
            sack_data, _ = sock.recvfrom(1024)
            rtt = time.time() - send_time
            
            unpacked = unpack_sack(sack_data)
            ack_seq = unpacked[0]
            
            # Default fallbacks
            snr = 20.0
            loss_rate = 0.0
            
            # Extract SNR and loss_rate safely regardless of unpack_sack return signature
            for item in unpacked[1:]:
                if isinstance(item, (float, int)):
                    snr = float(item)
                elif isinstance(item, dict):
                    snr = float(item.get('snr', 20.0))
                    loss_rate = float(item.get('loss_rate', 0.0))

            adaptive_rto = rto_engine.update_rto(rtt, snr)
            
            # FIX: Passing both snr and loss_rate expected by congestion control
            congestion_control.on_ack_received(snr, loss_rate)
            
            print(f"[<-] SACK #{ack_seq} | RTT: {rtt*1000:.2f}ms | SNR: {snr:.1f}dB | New CWND: {congestion_control.cwnd:.2f} | Adaptive RTO: {adaptive_rto:.3f}s\n")
            
        except (socket.timeout, ConnectionResetError):
            print(f"[!] Timeout/Loss on Pkt #{seq_num}! Triggering Signal-Aware Loss Discrimination...")
            simulated_snr = 10.0  
            congestion_control.on_timeout(simulated_snr)
            adaptive_rto = rto_engine.update_rto(0.1, simulated_snr)
            print(f"[!] Loss classified. CWND adjusted to: {congestion_control.cwnd:.2f} | Adaptive RTO: {adaptive_rto:.3f}s\n")

        seq_num += 1
        time.sleep(0.1)

    sock.close()
    print("[+] SA-UDP Full Protocol Transmission & Dynamic Rate Control Complete!")

if __name__ == "__main__":
    run_sender()