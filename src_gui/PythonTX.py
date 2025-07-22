# PythonTX.py

import socket
import struct
import hashlib
from pathlib import Path
import random


class PythonTX:
    def __init__(self, dest_ip, filename):
        self.UDP_IP = dest_ip
        self.UDP_PORT = 5005
        self.FILENAME = filename
        self.TX_ID = random.randint(0, 25535)
        self.TIMEOUT = 1  # seconds
        self.MAX_RETRIES = 10
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.settimeout(self.TIMEOUT)

    def wait_for_ack(self, expected_seq, packet):
        for _ in range(self.MAX_RETRIES):
            try:
                self.sock.sendto(packet, (self.UDP_IP, self.UDP_PORT))
                ack_pkt, _ = self.sock.recvfrom(1024)
                ack_tx_id, ack_seq = struct.unpack('!HI', ack_pkt[:6])
                if ack_tx_id == self.TX_ID and ack_seq == expected_seq:
                    return True
            except socket.timeout:
                print(f"Timeout waiting for ACK for seq {expected_seq}, retrying...\r", end='')
            except socket.gaierror:
                raise OSError("Invalid IP address or host unreachable.")
        raise TimeoutError(f"Timeout waiting for ACK for sequence {expected_seq}")

    def send_file(self):
        try:
            data = Path(self.FILENAME).read_bytes()
        except FileNotFoundError:
            raise FileNotFoundError(f"File not found: {self.FILENAME}")

        chunk_size = 512
        chunks = [data[i:i + chunk_size] for i in range(0, len(data), chunk_size)]

        file_name_bytes = self.FILENAME.encode()
        first_pkt = struct.pack('!HIII', self.TX_ID, 0, len(chunks), len(file_name_bytes)) + file_name_bytes
        if not self.wait_for_ack(0, first_pkt):
            self.sock.close()
            raise ConnectionError("Failed to initialize transfer.")

        current_seq = 1
        while current_seq <= len(chunks):
            data_pkt = struct.pack('!HII', self.TX_ID, current_seq, len(chunks[current_seq - 1])) + chunks[current_seq - 1]
            if self.wait_for_ack(current_seq, data_pkt):
                print(
                    f"\rTransfer: {current_seq}/{len(chunks)} packets "
                    f"({int((current_seq / float(len(chunks))) * 100)}%)", end='')
                current_seq += 1
            else:
                self.sock.close()
                raise ConnectionError(f"Failed to send packet {current_seq} after retries.")

        md5 = hashlib.md5(data).digest()
        last_pkt = struct.pack('!HI', self.TX_ID, len(chunks) + 1) + md5
        if self.wait_for_ack(len(chunks) + 1, last_pkt):
            print("\nFile transfer completed successfully.")
            self.sock.close()
            return True
        else:
            self.sock.close()
            raise ConnectionError("Failed to send final packet.")

