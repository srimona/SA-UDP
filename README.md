# Signal-Aware UDP (SA-UDP)
**A Cross-Layer Transport Protocol for Lossy Wireless Networks**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Build: Module 1 Complete](https://img.shields.io/badge/Build-Module_1_Complete-brightgreen.svg)]()

## Executive Summary

**Signal-Aware UDP (SA-UDP)** is a custom, high-performance transport-layer protocol built over raw UDP sockets.
It addresses a fundamental flaw in traditional protocols like TCP Reno and TCP Cubic: **treating 100% of packet drops as network congestion.**
In modern wireless networks (such as 5G/6G, Starlink/LEO satellites, mobile mesh networks, and IoT arrays), data is mostly dropped due 
to **physical noise, signal fading, interference, or spatial mobility**, rather than buffer overload at intermediate routers. 
Because traditional networking architectures strictly isolate the transport layer from physical link quality, standard protocols operate
"physically blind" and slash transmission speeds by up to 50% whenever packet drops occur.
SA-UDP resolves this issue by establishing a **direct cross-layer feedback interface** between physical-layer Signal-to-Noise Ratio (SNR) telemetry and
transport-layer Automatic Repeat Request (ARQ) retransmission logic.

## Key Architectural Innovations

### 1. Congestion vs. Noise Disambiguation Engine
Whenever a packet timer expires, SA-UDP checks real-time physical channel metrics:
* **Weak Signal (SNR < SNR_thresh):** Flagged as **Physical Signal Noise**. SA-UDP retransmits the missing packet immediately **without** cutting transmission speeds.
* **Strong Signal (SNR >= SNR_thresh):** Flagged as **Router Congestion**. Transmission speeds are safely reduced to clear network load.

### 2. Predictive Timeout Scaling (RTO_pred)
Instead of relying solely on round-trip delay variance, SA-UDP dynamically scales Retransmission Timeouts using an SNR-based multiplier:

RTO_pred = (SRTT + 4 * RTTVAR) * [ 1 + alpha * ( 1 / SNR_avg ) ]

This prevents unnecessary retransmissions over weak links where packets are simply delayed by link-layer retries rather than lost.

## System Architecture & Modules

The repository is structured into four core engineering modules:
| Module | Component Name | Primary Function |
| :--- | :--- | :--- |
| **Module 1** | `Socket & Protocol Engine` | Binary packet framing, sequence tracking, CRC32 checksums, and SACK bitmasks[cite: 5]. |
| **Module 2** | `Telemetry & Link Monitor` | Tracks live wireless metrics (SNR/RSSI), moving averages (`SNR_avg`), and `Delta SNR`[cite: 5]. |
| **Module 3** | `Adaptive ARQ Controller` | Noise vs. Congestion state machine and dynamic `RTO_pred` calculations[cite: 5]. |
| **Module 4** | `Channel Emulator & Evaluator` | Benchmark engine testing throughput, retransmissions, and latency against TCP[cite: 5]. |

## live demo
access the interactive protocol simulator here: [SA-UDP live dashboard](https://sa-udp-dgwj2rqtojvcbaszgrv242.streamlit.app/)
