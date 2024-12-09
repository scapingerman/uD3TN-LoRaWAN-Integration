#!/usr/bin/env python3
# SPDX-License-Identifier: BSD-3-Clause OR Apache-2.0
# encoding: utf-8

import argparse
import logging
import sys
import base64
import socket

import cbor2  # type: ignore

from pyd3tn.bundle7 import Bundle
from ud3tn_utils.aap2 import (
    AAP2UnixClient,
    AAP2TCPClient,
    AAP2ServerDisconnected,
    BundleADUFlags,
    ResponseStatus,
)
from ud3tn_utils.aap2.bin.helpers import (
    add_common_parser_arguments,
    add_keepalive_parser_argument,
    get_secret_from_args,
    initialize_logger,
)

logger = logging.getLogger(__name__)

# Gateway Configuration
GATEWAY_IP = "localhost"  # Change according to your gateway IP
GATEWAY_PORT = 1700  # Standard Gateway LoRa port

def send_to_gateway(binary_data):
    """
    Send binary data directly to the Gateway.
    """
    print(f"Attempting to send to Gateway: {binary_data}")
    try:
        # Create a UDP socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # Send data directly to the Gateway
        sock.sendto(binary_data, (GATEWAY_IP, GATEWAY_PORT))
        print(f"Data successfully sent to Gateway: {binary_data}")
        logger.info(f"Data successfully sent to Gateway: {binary_data}")
    except Exception as e:
        print(f"Error sending data to Gateway: {e}")
        logger.error(f"Error sending data to Gateway: {e}")
    finally:
        sock.close()

def decode_and_forward(data):
    """
    Decode received data, print it, and send it to the Gateway.
    """
    print(f"Received data to decode: {data}")
    try:
        # Decode Base64 content
        decoded_data = base64.b64decode(data)
        print(f"Decoded data (binary): {decoded_data}")
        logger.info(f"Decoded data (binary): {decoded_data}")

        # Send directly to the Gateway
        send_to_gateway(decoded_data)

    except base64.binascii.Error as e:
        print(f"Base64 decoding error: {e}")
        logger.error(f"Base64 decoding error: {e}")
    except Exception as e:
        print(f"Unknown decoding error: {e}")
        logger.error(f"Unknown decoding error: {e}")

def run_aap_recv(aap2_client, max_count, output, verify_pl, newline):
    logger.info("Waiting for bundles...")
    print("Waiting for bundles...")
    counter = 0

    while True:
        try:
            msg = aap2_client.receive_msg()
        except AAP2ServerDisconnected:
            logger.warning("uD3TN has closed the connection.")
            print("uD3TN has closed the connection.")
            sys.exit(1)
        except KeyboardInterrupt:
            logger.info("Terminated by keyboard interruption.")
            print("Terminated by keyboard interruption.")
            sys.exit(130)  # exit status for SIGINT

        msg_type = msg.WhichOneof("msg")
        if msg_type == "keepalive":
            logger.debug("Keepalive message received, responding.")
            aap2_client.send_response_status(
                ResponseStatus.RESPONSE_STATUS_ACK
            )
            continue
        elif msg_type != "adu":
            logger.info("Message with field '%s' received, discarding.", msg_type)
            continue

        adu_msg, bundle_data = aap2_client.receive_adu(msg.adu)
        aap2_client.send_response_status(
            ResponseStatus.RESPONSE_STATUS_SUCCESS
        )

        enc = False
        err = False

        if BundleADUFlags.BUNDLE_ADU_BPDU in adu_msg.adu_flags:
            payload = cbor2.loads(bundle_data)
            bundle = Bundle.parse(payload[2])
            payload = bundle.payload_block.data
            enc = True
        else:
            payload = bundle_data

        if not err:
            enc = " encapsulated" if enc else ""
            logger.info(
                "Bundle received%s from '%s', payload size = %d",
                enc,
                msg.adu.src_eid,
                len(payload),
            )
            print(
                f"Bundle received{enc} from '{msg.adu.src_eid}', payload size = {len(payload)}"
            )

            # Decode, print, and send to the Gateway
            decode_and_forward(payload)

            if newline:
                output.write(b"\n")
            output.flush()
            if verify_pl is not None and verify_pl.encode("utf-8") != payload:
                logger.fatal("Unexpected payload != '%s'", verify_pl)
                sys.exit(1)
        else:
            logger.warning(
                "Unknown administrative record type received from '%s'!",
                msg.adu.src_eid
            )

        counter += 1
        if max_count and counter >= max_count:
            logger.info("Expected number of bundles received, terminating.")
            return

def main():
    parser = argparse.ArgumentParser(
        description="Register an agent with uD3TN and wait for bundles.",
    )

    add_common_parser_arguments(parser)
    add_keepalive_parser_argument(parser)

    parser.add_argument(
        "-c", "--count",
        type=int,
        default=None,
        help="Number of bundles to receive before termination.",
    )
    parser.add_argument(
        "-o", "--output",
        type=argparse.FileType("wb"),
        default=sys.stdout.buffer,
        help="File to write received bundle contents.",
    )
    parser.add_argument(
        "--verify-pl",
        default=None,
        help="Verify that the payload matches the provided string.",
    )
    parser.add_argument(
        "--newline",
        action="store_true",
        help="Print a newline after each received payload.",
    )

    args = parser.parse_args()
    global logger
    logger = initialize_logger(args.verbosity)

    try:
        if args.tcp:
            aap2_client = AAP2TCPClient(address=args.tcp)
        else:
            aap2_client = AAP2UnixClient(address=args.socket)

        with aap2_client:
            secret = aap2_client.configure(
                args.agentid,
                subscribe=True,
                secret=get_secret_from_args(args),
                keepalive_seconds=args.keepalive_seconds,
            )
            logger.info("Agent secret assigned: '%s'", secret)
            run_aap_recv(
                aap2_client,
                args.count,
                args.output,
                args.verify_pl,
                args.newline,
            )
    finally:
        args.output.close()

if __name__ == "__main__":
    main()
