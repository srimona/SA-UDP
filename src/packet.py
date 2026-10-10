import struct
import zlib
import time
from src.telemetry import TELEMETRY_SIZE

# Packet Header: SeqNum (uint32: 4B), Timestamp (double: 8B), PayloadLen (uint16: 2B), CRC32 (uint32: 4B)
HEADER_FORMAT = "!IdHI"
HEADER_SIZE = struct.calcsize(HEADER_FORMAT)

# SACK Header: AckSeqNum (uint32: 4B), Timestamp (double: 8B) + 12B Telemetry
SACK_FORMAT = "!Id"
SACK_SIZE = struct.calcsize(SACK_FORMAT)

def pack_packet(seq_num, payload):
    ts = time.time()
    payload_len = len(payload)
    header_no_crc = struct.pack("!IdH", seq_num, ts, payload_len)
    crc = zlib.crc32(header_no_crc + payload) & 0xffffffff
    header = struct.pack(HEADER_FORMAT, seq_num, ts, payload_len, crc)
    return header + payload

def unpack_packet(raw_bytes):
    if len(raw_bytes) < HEADER_SIZE:
        return None, False
    header_bytes = raw_bytes[:HEADER_SIZE]
    payload = raw_bytes[HEADER_SIZE:]
    seq_num, ts, payload_len, received_crc = struct.unpack(HEADER_FORMAT, header_bytes)
    
    header_no_crc = struct.pack("!IdH", seq_num, ts, payload_len)
    computed_crc = zlib.crc32(header_no_crc + payload) & 0xffffffff
    
    is_valid = (received_crc == computed_crc)
    return (seq_num, ts, payload), is_valid

def pack_sack(ack_seq_num, original_ts, telemetry_bytes=b""):
    sack_header = struct.pack(SACK_FORMAT, ack_seq_num, original_ts)
    return sack_header + telemetry_bytes

def unpack_sack(raw_bytes):
    sack_header_bytes = raw_bytes[:SACK_SIZE]
    telemetry_bytes = raw_bytes[SACK_SIZE:]
    ack_seq_num, original_ts = struct.unpack(SACK_FORMAT, sack_header_bytes)
    return ack_seq_num, original_ts, telemetry_bytes
