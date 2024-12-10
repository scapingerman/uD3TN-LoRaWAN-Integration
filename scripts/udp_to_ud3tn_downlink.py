import base64
import subprocess
from scapy.all import sniff, UDP

# uD3TN Node C Configuration
UD3TN_HOST = "localhost"
UD3TN_PORT = 4244
UD3TN_DEST_EID = "dtn://d.dtn/bundlesink"

def send_to_ud3tn(raw_data):
    """Sends encoded downlink data to uD3TN Node C."""
    encoded_data = base64.b64encode(raw_data).decode('utf-8')
    command = [
        "python3",
        "/usr/local/lib/python3.11/dist-packages/ud3tn_utils/aap2/bin/aap2_send.py",
        "--tcp",
        UD3TN_HOST,
        str(UD3TN_PORT),
        UD3TN_DEST_EID,
        encoded_data
    ]
    try:
        subprocess.run(command, check=True, text=True)
        print(f"Downlink sent to uD3TN Node C (Base64): {encoded_data}")
    except subprocess.CalledProcessError as e:
        print(f"Error sending downlink to uD3TN Node C: {e}")

def is_downlink(packet):
    """
    Checks if the UDP packet corresponds to a downlink message.
    Adjust the logic based on specific header, port, or payload patterns.
    """
    # Example: Check if source port is 1700 (commonly for LoRaWAN downlinks)
    if packet[UDP].sport == 1700:
        return True

    # Check if payload matches known downlink patterns (adjust as needed)
    payload = bytes(packet[UDP].payload)
    if payload.startswith(b'\x02/'):  # Example pattern for downlinks
        return True

    return False

def packet_callback(packet):
    """Processes UDP packets and sends only downlink data to Node C."""
    if packet.haslayer(UDP):  # Filter all UDP packets
        if is_downlink(packet):
            raw_data = bytes(packet[UDP].payload)
            print(f"Captured UDP downlink packet: {raw_data}")
            send_to_ud3tn(raw_data)


# Listen to UDP traffic without filtering the destination port
print("Listening for UDP traffic on any port...")
sniff(filter="udp", prn=packet_callback, store=0)
