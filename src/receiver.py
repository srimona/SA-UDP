import socket
from src.packet import unpack_packet, pack_sack
from src.telemetry import LinkMonitor

def start_receiver(host="127.0.0.1", port=9999):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((host, port))
    print(f"[+] SA-UDP Module 2 Receiver listening on {host}:{port}...")

    monitor = LinkMonitor(base_snr=25.0, base_rssi=-65.0)

    while True:
        data, addr = sock.recvfrom(2048)
        (seq_num, original_ts, payload), is_valid = unpack_packet(data)

        if is_valid:
            monitor.packets_received += 1
            telemetry_bytes, snr, rssi, loss_rate = monitor.pack_telemetry()
            print(f"[+] Recv Pkt #{seq_num} | SNR: {snr:.1f} dB | RSSI: {rssi:.1f} dBm | Loss: {loss_rate:.2f}")

            sack_packet = pack_sack(seq_num, original_ts, telemetry_bytes)
            sock.sendto(sack_packet, addr)
        else:
            monitor.packets_lost += 1
            print(f"[!] CRC Error / Corrupted Packet received from {addr}")

if __name__ == "__main__":
    start_receiver()