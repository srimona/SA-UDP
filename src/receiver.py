import socket
from packet import SAUDPPacket

def start_receiver(host="127.0.0.1", port=9999):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((host, port))
    print(f"[+] SA-UDP Module 1 Receiver listening on {host}:{port}...")

    received_chunks = {}

    while True:
        data, addr = sock.recvfrom(2048)
        try:
            pkt = SAUDPPacket.unpack(data)
            
            # Check for corrupted payload
            if pkt["corrupt"]:
                print(f"[!] Packet #{pkt['seq_num']} checksum failed. Dropping.")
                continue

            if pkt["type"] == SAUDPPacket.TYPE_DATA:
                print(f"[+] Received Packet #{pkt['seq_num']} ({len(pkt['payload'])} bytes)")
                received_chunks[pkt["seq_num"]] = pkt["payload"]

                # Send SACK feedback frame acknowledging the sequence number
                sack_frame = SAUDPPacket.pack_sack(cum_ack=pkt["seq_num"], sack_bitmask=0)
                sock.sendto(sack_frame, addr)

        except Exception as e:
            print("[!] Error processing frame:", e)

if __name__ == "__main__":
    start_receiver()
