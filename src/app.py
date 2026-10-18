import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
import struct
import time
import binascii

def calculate_rto(snr: float) -> float:
    if snr < 12.0:
        return 0.270
    elif snr > 22.0:
        return 0.120
    return 0.200

if "sim_cwnd" not in st.session_state:
    st.session_state.sim_cwnd = 4.0

st.set_page_config(
    page_title="Signal-Aware UDP Protocol Engine",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("Signal-Aware UDP Protocol Engine")
st.markdown(
    "A cross-layer transport protocol engine that separates non-congestive wireless fading "
    "from intermediate buffer queue overflow using real-time SNR telemetry feedback."
)

tab1, tab2, tab3 = st.tabs(["Interactive Simulator", "Protocol Analytics", "Binary Packet Inspector"])

with tab1:
    st.subheader("Interactive Protocol Execution")
    col1, col2 = st.columns([1, 2])

    with col1:
        st.markdown("### Channel & Test Conditions")
        snr_val = st.slider("Channel SNR (dB)", min_value=5.0, max_value=30.0, value=25.0, step=0.5)
        loss_toggle = st.checkbox("Inject Channel Degradation / Packet Loss", value=False)
        queue_drop = st.button("Inject Router Queue Congestion")

        current_rto = calculate_rto(snr_val)

        st.metric("Adaptive Retransmission Timeout (RTO)", f"{current_rto:.3f} s")
        if snr_val < 12.0:
            st.warning("State: Robust Telemetry Mode (RTO Scaled 1.8x, CWND Preserved)")
        elif snr_val > 22.0:
            st.success("State: Turbo Mode (RTO Scaled 0.6x, Fast AIMD Growth)")
        else:
            st.info("State: Standard Adaptive Mode (Reno Baseline)")

    with col2:
        st.markdown("### Telemetry Feedback & Congestion Control")
        
        if queue_drop:
            st.session_state.sim_cwnd = max(1.0, st.session_state.sim_cwnd / 2.0)
            st.error(f"Router queue congestion registered. Multiplicative decrease applied: CWND cut to {st.session_state.sim_cwnd:.2f} pkts.")
        elif loss_toggle and snr_val < 12.0:
            st.info(f"Wireless fade drop detected at {snr_val} dB. CWND preserved at {st.session_state.sim_cwnd:.2f} pkts.")
        else:
            if snr_val > 22.0:
                st.session_state.sim_cwnd += 0.50
            elif snr_val >= 12.0:
                st.session_state.sim_cwnd += 0.25
            st.write(f"Telemetry acknowledgement processed. CWND: {st.session_state.sim_cwnd:.2f} pkts.")

        st.metric("Current Congestion Window (CWND)", f"{st.session_state.sim_cwnd:.2f} pkts")
        st.progress(min(float(st.session_state.sim_cwnd) / 20.0, 1.0))

with tab2:
    st.subheader("Performance Characteristics & State Machine Curve")
    snr_range = np.linspace(5.0, 30.0, 100)
    rto_values = [calculate_rto(s) for s in snr_range]
    standard_rto = [0.200 for _ in snr_range]

    fig, ax = plt.subplots(figsize=(8, 4))
    ax.plot(snr_range, standard_rto, label="Standard Static RTO (0.200s)", color="#e74c3c", linestyle="--")
    ax.plot(snr_range, rto_values, label="Signal-Aware Adaptive RTO", color="#2ecc71", linewidth=2.5)
    ax.axvline(12.0, color="#f39c12", linestyle=":", label="Robust Threshold (12 dB)")
    ax.axvline(22.0, color="#3498db", linestyle=":", label="Turbo Threshold (22 dB)")

    ax.set_xlabel("Reported SNR (dB)")
    ax.set_ylabel("Retransmission Timeout (seconds)")
    ax.set_title("Retransmission Timeout Adaptation vs. Signal-to-Noise Ratio")
    ax.grid(True, alpha=0.3)
    ax.legend()
    st.pyplot(fig)

with tab3:
    st.subheader("Binary Framing & Packet Inspector")
    col_hdr, col_sack = st.columns(2)

    with col_hdr:
        st.markdown("#### 18-Byte Data Header (`!IdHI`)")
        sample_payload = b"Sensor payload data testing SA-UDP cross-layer packet formatting."
        crc_val = binascii.crc32(sample_payload) & 0xffffffff
        header_bytes = struct.pack("!IdHI", 101, time.time(), len(sample_payload), crc_val)
        seq, ts, length, crc = struct.unpack("!IdHI", header_bytes)

        st.code(
            f"Header Size   : 18 Bytes\n"
            f"Raw Hex       : {header_bytes.hex()}\n"
            f"Sequence Num  : {seq}\n"
            f"Timestamp     : {ts:.4f}\n"
            f"Payload Len   : {length} bytes\n"
            f"CRC32 Check   : 0x{crc:08X}",
            language="text"
        )

    with col_sack:
        st.markdown("#### 24-Byte SACK Telemetry Frame (`!fff`)")
        sample_sack = struct.pack("!Id", 101, time.time()) + struct.pack("!fff", 26.5, -62.0, 0.0)
        ack_seq, ack_ts = struct.unpack("!Id", sample_sack[:12])
        snr_rep, rssi_rep, loss_rep = struct.unpack("!fff", sample_sack[12:])

        st.code(
            f"Frame Size    : {len(sample_sack)} Bytes\n"
            f"Raw Hex       : {sample_sack.hex()}\n"
            f"ACK Seq Num   : {ack_seq}\n"
            f"Echoed TS     : {ack_ts:.4f}\n"
            f"Reported SNR  : {snr_rep:.2f} dB\n"
            f"Reported RSSI : {rssi_rep:.2f} dBm\n"
            f"Channel Loss  : {loss_rep:.1f}%",
            language="text"
        )