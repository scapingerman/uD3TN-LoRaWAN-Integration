# Setup Instructions for uD3TN LoRaWAN Integration

This guide will help you configure and test the **uD3TN LoRaWAN Integration**, which involves embedding uD3TN nodes between a LoRa Gateway and The Things Network (TTN). The setup uses a Raspberry Pi with a RAK2287 concentrator and Docker for the UDP packet forwarder.

---

## Prerequisites

### Hardware Requirements:
1. **LoRa Gateway:**
   - Raspberry Pi 3
   - RAK2287 with RAK5146 Pi HAT
2. **LoRa End Device:**
   - Heltec LoRa 32 V3 (ESP32-S3-based board)

### Software Requirements:
1. **Docker** for the UDP packet forwarder.
2. **uD3TN**:
   - A lightweight DTN stack for managing data bundles.
   - Build from source following the official repository:  
     [uD3TN GitLab](https://gitlab.com/d3tn/ud3tn).  
3. **Python**:
   - Required for running utility scripts (e.g., `aap2_send.py` and `udp_to_ud3tn.py`).
4. **The Things Network (TTN) account**:
   - Ensure your gateway and end device are registered and active.

---

## Step-by-Step Setup

### Step 1: Configure the LoRa Gateway

1. **Install the UDP Packet Forwarder**:
   - Clone the RAKWireless UDP packet forwarder repository:
     ```bash
     git clone https://github.com/RAKWireless/udp-packet-forwarder.git
     cd udp-packet-forwarder
     ```

   - Create a `docker-compose.yml` file with the following configuration:
     ```yaml
     version: '2'

     services:
       udp-packet-forwarder:
         image: rakwireless/udp-packet-forwarder:latest
         container_name: udp-packet-forwarder
         restart: unless-stopped
         privileged: true
         network_mode: host
         environment:
           MODEL: "RAK2287"
           INTERFACE: "SPI"
           DEVICE: "/dev/spidev0.0"
           SERVER_HOST: "localhost"
           SERVER_PORT: 1700
           BAND: "eu_863_870"
     ```

   - Start the packet forwarder:
     ```bash
     sudo docker-compose up -d
     ```

2. **Verify the Gateway**:
   - Ensure the gateway connects to TTN and displays uplink messages in the TTN console.

---

### Step 2: Set Up uD3TN Nodes

1. **Build and Install uD3TN**:
   - Clone the uD3TN repository:
     ```bash
     git clone https://gitlab.com/d3tn/ud3tn.git
     cd ud3tn
     git submodule update --init --recursive
     make posix
     ```

2. **Start the uD3TN Nodes**:
   - Start **Node A** for uplinks:
     ```bash
     build/posix/ud3tn --eid dtn://a.dtn/ --bp-version 7 --aap2-port 4242 --cla "mtcp:*,4224" -L 4
     ```
   - Start **Node B** for uplinks:
     ```bash
     build/posix/ud3tn --eid dtn://b.dtn/ --bp-version 7 --aap2-port 4243 --cla "mtcp:*,4225" -L 4
     ```
   - Start **Node C** for downlinks:
     ```bash
     build/posix/ud3tn --eid dtn://c.dtn/ --bp-version 7 --aap2-port 4244 --cla "mtcp:*,4226" -L 4
     ```
   - Start **Node D** for downlinks:
     ```bash
     build/posix/ud3tn --eid dtn://d.dtn/ --bp-version 7 --aap2-port 4245 --cla "mtcp:*,4227" -L 4
     ```

3. **Establish Inter-Node Connections**:
   - Link **Node A** to **Node B**:
     ```bash
     python tools/aap2/aap2_config.py --tcp localhost 4242 --schedule 1 3600 100000 dtn://b.dtn/ mtcp:localhost:4225
     ```
   - Link **Node C** to **Node D**:
     ```bash
     python tools/aap2/aap2_config.py --tcp localhost 4244 --schedule 1 3600 100000 dtn://d.dtn/ mtcp:localhost:4227
     ```

---

### Step 3: Set Up Uplink and Downlink Scripts

1. **Uplink Scripts**:
   - Run the uplink UDP capture script (`udp_to_ud3tn_uplink.py`) to forward gateway traffic to **Node A**:
     ```bash
     python udp_to_ud3tn_uplink.py
     ```
   - Run the TTN forwarding script (`aap2_to_ttn.py`) to send data from **Node B** to TTN:
     ```bash
     python tools/aap2/aap2_to_ttn.py --tcp localhost 4243 --agentid bundlesink
     ```

2. **Downlink Scripts**:
   - Run the downlink UDP capture script (`udp_to_ud3tn_downlink.py`) to forward TTN traffic to **Node D**:
     ```bash
     python udp_to_ud3tn_downlink.py
     ```
   - Run the gateway forwarding script (`aap2_to_gateway.py`) to send data from **Node C** to the gateway:
     ```bash
     python tools/aap2/aap2_to_gateway.py --tcp localhost 4245 --agentid bundlesink
     ```

---

### Step 4: Test the Workflow

1. **Verify Uplink Traffic**:
   - Send a test uplink message from your LoRa end device.
   - Confirm:
     - The uplink is captured by `udp_to_ud3tn_uplink.py`.
     - It is sent to TTN via **Node B**.

2. **Verify Downlink Traffic**:
   - Schedule a downlink message in TTN.
   - Confirm:
     - The downlink is captured by `udp_to_ud3tn_downlink.py`.
     - It is forwarded to the gateway via **Node C**.

---

### Troubleshooting

- **No messages captured**: Ensure the UDP packet forwarder is running and configured to forward packets to `localhost:1700`.
- **uD3TN not sending data**: Verify node connections with the `aap2_config.py` script.
- **TTN not receiving uplinks**: Confirm the gateway is registered and active in TTN.

---

This guide provides a comprehensive setup for testing the **uD3TN LoRaWAN Integration**. The configuration allows for flexible experimentation, paving the way for future optimizations such as adding LoRa links directly to uD3TN nodes.
