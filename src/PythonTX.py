import socket
import struct
import hashlib
from pathlib import Path
import random
import sys


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
            self.sock.sendto(packet, (self.UDP_IP, self.UDP_PORT))
            try:
                ack_pkt, _ = self.sock.recvfrom(1024)
                ack_tx_id, ack_seq = struct.unpack('!HI', ack_pkt[:6])
                if ack_tx_id == self.TX_ID and ack_seq == expected_seq:
                    return True  # ACK received
            except socket.timeout:
                print(f"Timeout waiting for ACK for seq {expected_seq}, retrying...\r", end='')
        return False  # Timeout after retries

    def send_file(self):
        try:
            data = Path(self.FILENAME).read_bytes()
        except FileNotFoundError:
            print(f"Error: File '{self.FILENAME}' not found")
            return False

        chunk_size = 512
        chunks = [data[i:i + chunk_size] for i in range(0, len(data), chunk_size)]

        # First packet (SeqNr = 0)
        file_name_bytes = self.FILENAME.encode()
        first_pkt = struct.pack('!HIII', self.TX_ID, 0, len(chunks), len(file_name_bytes)) + file_name_bytes
        if not self.wait_for_ack(0, first_pkt):
            print("Failed to initialize transfer")
            self.sock.close()
            return False

        # Data packets (SeqNr 1..N)
        current_seq = 1
        while current_seq <= len(chunks):
            data_pkt = struct.pack('!HII', self.TX_ID, current_seq, len(chunks[current_seq - 1])) + chunks[
                current_seq - 1]
            if self.wait_for_ack(current_seq, data_pkt):
                print(
                    f"\rTransfer: {current_seq}/{len(chunks)} packets ({int((current_seq / float(len(chunks))) * 100)}%)",
                    end='')
                current_seq += 1
            else:
                print(f"\nFailed to send packet {current_seq} after retries")
                self.sock.close()
                return False

        # Last packet (SeqNr = N+1)
        md5 = hashlib.md5(data).digest()
        last_pkt = struct.pack('!HI', self.TX_ID, len(chunks) + 1) + md5
        if self.wait_for_ack(len(chunks) + 1, last_pkt):
            print("\nFile transfer completed successfully")
            self.sock.close()
            return True
        else:
            print("\nFailed to send final packet")
            self.sock.close()
            return False


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python PythonTX.py <filename> <destination_ip_address>")
        sys.exit(1)

    tx = PythonTX(sys.argv[2], sys.argv[1])
    tx.send_file()
