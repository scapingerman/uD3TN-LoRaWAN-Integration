# LoRa-uD3TN Gateway Interposition Repository

## Overview
This repository contains all scripts, configurations, and documentation required to implement the uD3TN LoRaWAN Integration, where uD3TN nodes act as intermediaries between a LoRaWAN gateway and The Things Network (TTN). This approach supports delay-tolerant communication, enabling resilient IoT deployments in challenging environments.

---


## Repository Structure

```plaintext

├── README.md                       # Project overview
├── docs/
│   └── setup_instructions.md       # Step-by-step setup guide
├── scripts/
│   ├── udp_to_ud3tn_uplink.py      # Captures uplinks to uD3TN Node A
│   ├── aap2_to_ttn.py              # Sends data from Node B to TTN
│   ├── udp_to_ud3tn_downlink.py    # Captures downlinks from TTN to Node D
│   ├── aap2_to_gateway.py          # Sends data from Node C to the gateway
└── docker/
    └── docker-compose.yml          # UDP Packet Forwarder setup

```

# System Architecture
Uplink Path:
```bash
LoRa End Device → Gateway → uD3TN Node A → (disrupted link) → uD3TN Node B → TTN
```
Downlink Path:
```bash
TTN → uD3TN Node C → (disrupted link) → uD3TN Node D → Gateway → LoRa End Device
```

# Requirements
## Hardware
- Gateway: Raspberry Pi 3 with RAK2287 and RAK5146 Pi HAT
- End Device: Heltec LoRa 32 V3 (ESP32-S3-based board)

## Software
- Docker: To run the UDP packet forwarder.
- uD3TN: A lightweight DTN implementation, compiled from source ([uD3TN GitLab](https://gitlab.com/d3tn/ud3tn)).
- Python: To execute utility scripts.
- The Things Network (TTN): Ensure your gateway and end device are registered.

## Installation & Setup
Follow the step-by-step guide in setup_instructions.md.
