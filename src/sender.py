import socket
import time
from packet import SAUDPPacket

def send_file(file_path, receiver_host="127.0.0.1", receiver_port=9999):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.settimeout(2.0)  # Initial socket timeout for SACK responses
    dest_addr = (receiver_host, receiver_port)
    
    CHUNK_SIZE = 1024  # 1 KB per payload chunk
    seq_num = 1

    try:
        with open(file_path, "rb") as f:
            while True:
                chunk = f.read(CHUNK_SIZE)
                if not chunk:
                    break
                
                # Pack binary frame and send
                pkt_bytes = SAUDPPacket.pack_data(seq_num, chunk)
                sock.sendto(pkt_bytes, dest_addr)
                print(f"[->] Sent Packet #{seq_num}")
                
                # Listen for SACK acknowledgement
                try:
                    ack_data, _ = sock.recvfrom(1024)
                    print(f"[<-] SACK received for Packet #{seq_num}")
                except socket.timeout:
                    print(f"[!] Timeout on Packet #{seq_num} (Will be handled by Module 3 ARQ)")

                seq_num += 1
                time.sleep(0.01)

        print("[+] File transmission complete.")

    except FileNotFoundError:
        print(f"[!] Error: File '{file_path}' not found. Create a dummy file to test.")

if __name__ == "__main__":
    send_file("test_file.txt")
