import base64
import socket
import subprocess
from scapy.all import sniff, IP, UDP

# uD3TN Configuration for Uplink
NODE_A_HOST = "localhost"
NODE_A_PORT = 4242
NODE_B_EID = "dtn://b.dtn/bundlesink"  # Node B Identifier

# Function to send packets to the corresponding uD3TN node
def send_to_ud3tn(host, port, eid, raw_data):
    """Sends encoded data to uD3TN at the specified node."""
    encoded_data = base64.b64encode(raw_data).decode('utf-8')
    command = [
        "python3",
        "/usr/local/lib/python3.11/dist-packages/ud3tn_utils/aap2/bin/aap2_send.py",
        "--tcp",
        host,
        str(port),
        eid,
        encoded_data
    ]
    try:
        subprocess.run(command, check=True, text=True)
        print(f"Packet sent to {eid} (Base64): {encoded_data}")
    except subprocess.CalledProcessError as e:
        print(f"Error sending packet to {eid}: {e}")

# Callback to process UDP packets
def packet_callback(packet):
    """Processes only uplink UDP packets."""
    if packet.haslayer(UDP) and packet[UDP].sport == 1700:  # Filter uplinks
        raw_data = bytes(packet[UDP].payload)
        print(f"Uplink captured: {raw_data}")
        send_to_ud3tn(NODE_A_HOST, NODE_A_PORT, NODE_B_EID, raw_data)

# Start the UDP server on localhost:1700
def start_udp_server():
    """Starts the UDP server on port 1700 and captures uplink packets."""
    udp_ip = "localhost"
    udp_port = 1700

    # Create the UDP socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((udp_ip, udp_port))

    print(f"UDP server started on {udp_ip}:{udp_port}, waiting for uplinks...")

    while True:
        data, addr = sock.recvfrom(1024)  # 1024-byte buffer
        print(f"Received {data} from {addr}")

        # Create a Scapy IP and UDP packet for the payload
        ip_packet = IP(dst=addr[0]) / UDP(dport=addr[1], sport=1700) / data

        # Call the callback to process the packet
        packet_callback(ip_packet)

if __name__ == "__main__":
    start_udp_server()
