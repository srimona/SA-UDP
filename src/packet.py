import struct
import time
import zlib

class SAUDPPacket:
    # Frame Types
    TYPE_DATA = 1
    TYPE_SACK = 2

    # Binary Header: Type (1B), Sequence Num (4B), Timestamp (4B float), Checksum (4B)
    HEADER_FORMAT = "!B I f I"
    HEADER_SIZE = struct.calcsize(HEADER_FORMAT)

    @staticmethod
    def pack_data(seq_num: int, payload: bytes) -> bytes:
        """Packs payload data into an SA-UDP Data Frame with a custom header."""
        pkt_type = SAUDPPacket.TYPE_DATA
        timestamp = time.time()
        
        # Calculate 32-bit CRC checksum over the payload
        checksum = zlib.crc32(payload) & 0xffffffff
        
        header = struct.pack(SAUDPPacket.HEADER_FORMAT, pkt_type, seq_num, timestamp, checksum)
        return header + payload

    @staticmethod
    def unpack(raw_data: bytes):
        """Unpacks incoming raw bytes into header fields and payload."""
        if len(raw_data) < SAUDPPacket.HEADER_SIZE:
            raise ValueError("Packet smaller than header size.")
            
        header = raw_data[:SAUDPPacket.HEADER_SIZE]
        payload = raw_data[SAUDPPacket.HEADER_SIZE:]
        
        pkt_type, seq_num, timestamp, expected_checksum = struct.unpack(SAUDPPacket.HEADER_FORMAT, header)
        
        # Verify Checksum Integrity
        calculated_checksum = zlib.crc32(payload) & 0xffffffff
        is_corrupt = (calculated_checksum != expected_checksum)
        
        return {
            "type": pkt_type,
            "seq_num": seq_num,
            "timestamp": timestamp,
            "corrupt": is_corrupt,
            "payload": payload
        }

    @staticmethod
    def pack_sack(cum_ack: int, sack_bitmask: int) -> bytes:
        """Packs a Selective Acknowledgement (SACK) frame."""
        pkt_type = SAUDPPacket.TYPE_SACK
        timestamp = time.time()
        # SACK Header: Type (1B), Cum ACK (4B), Timestamp (4B), Bitmask (4B)
        return struct.pack("!B I f I", pkt_type, cum_ack, timestamp, sack_bitmask)
