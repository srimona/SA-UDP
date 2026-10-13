import os
import socket
import sys
import time

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.congestion import SignalAwareCongestionControl
from src.packet import pack_packet, unpack_sack
from src.telemetry import LinkMonitor, SignalAwareRTO


def send_file(filename="test_file.txt", host="127.0.0.1", port=9999):
  sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

  rto_calc = SignalAwareRTO(initial_rto=1.0)
  cc_engine = SignalAwareCongestionControl(initial_cwnd=2.0)

  # Verify test file existence or create a default dummy file
  if not os.path.exists(filename):
    with open(filename, "w") as f:
      f.write("SA-UDP Module 3 Test Payload\n" * 200)

  with open(filename, "rb") as f:
    file_bytes = f.read()

  # Slicing file into 1024-byte chunks
  chunk_size = 1024
  chunks = [
      file_bytes[i : i + chunk_size]
      for i in range(0, len(file_bytes), chunk_size)
  ]
  total_packets = len(chunks)

  base_seq = 1
  next_seq = 1
  last_known_snr = 25.0  # Default clean link baseline

  print(
      f"[+] SA-UDP Module 3 Sender active. Transmitting {total_packets} chunks"
      f" to {host}:{port}..."
  )

  while base_seq <= total_packets:
    # Transmit packets up to current congestion window limit
    while (
        next_seq < base_seq + int(cc_engine.cwnd) and next_seq <= total_packets
    ):
      packet = pack_packet(next_seq, chunks[next_seq - 1])
      sock.sendto(packet, (host, port))
      print(
          f"[->] Sent Pkt #{next_seq} | CWND: {cc_engine.cwnd:.2f} | State:"
          f" {cc_engine.state}"
      )
      next_seq += 1

    # Set socket timeout dynamically to current signal-aware RTO
    sock.settimeout(rto_calc.rto)

    try:
      ack_data, _ = sock.recvfrom(2048)
      ack_seq, orig_ts, telemetry_bytes = unpack_sack(ack_data)
      snr, rssi, loss_rate = LinkMonitor.unpack_telemetry(telemetry_bytes)
      last_known_snr = snr

      if ack_seq >= base_seq:
        measured_rtt = time.time() - orig_ts
        new_rto = rto_calc.update_rto(measured_rtt, snr)
        new_cwnd = cc_engine.on_ack_received(snr, loss_rate)

        print(
            f"[<-] SACK #{ack_seq} | RTT: {measured_rtt*1000:.2f}ms | SNR:"
            f" {snr:.1f}dB | New CWND: {new_cwnd:.2f} | Adaptive RTO:"
            f" {new_rto:.3f}s"
        )
        base_seq = ack_seq + 1

    except socket.timeout:
      print(f"[!] RTO Timeout triggered for Packet #{base_seq}!")
      # Trigger cross-layer loss discrimination on current SNR value
      cc_engine.on_packet_loss(snr=last_known_snr, loss_rate=0.1)
      next_seq = base_seq  # Go-Back-N retransmission trigger

  print("\n[+] Module 3 File Transmission & Dynamic Rate Control Complete!")


if __name__ == "__main__":
  send_file()