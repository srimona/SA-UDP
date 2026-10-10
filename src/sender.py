import socket
import time
from src.packet import pack_packet, unpack_sack
from src.telemetry import LinkMonitor, SignalAwareRTO

def send_file(filename="test_file.txt", host="127.0.0.1", port=9999):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.settimeout(2.0)

    rto_calculator = SignalAwareRTO(initial_rto=1.0)
    
    with open(filename, "rb") as f:
        seq_num = 1
        while chunk := f.read(1024):
            packet = pack_packet(seq_num, chunk)
            sent = False
            while not sent:
                sock.sendto(packet, (host, port))
                print(f"[->] Sent Packet #{seq_num}")

                try:
                    ack_data, _ = sock.recvfrom(1024)
                    ack_seq, orig_ts, telemetry_bytes = unpack_sack(ack_data)

                    if ack_seq == seq_num:
                        measured_rtt = time.time() - orig_ts
                        snr, rssi, loss_rate = LinkMonitor.unpack_telemetry(telemetry_bytes)
                        new_rto = rto_calculator.update_rto(measured_rtt, snr)

                        print(f"[<-] SACK #{ack_seq} | RTT: {measured_rtt*1000:.2f}ms | Telemetry SNR: {snr:.1f}dB | New Adaptive RTO: {new_rto:.3f}s")
                        sent = True
                except socket.timeout:
                    print(f"[!] Timeout for Packet #{seq_num}, retransmitting...")

            seq_num += 1

    print("\n[+] Module 2 File Transmission & Telemetry Loop Complete!")

if __name__ == "__main__":
    send_file()