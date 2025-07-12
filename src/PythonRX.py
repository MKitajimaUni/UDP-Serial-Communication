import socket
import struct
import hashlib
from sortedcontainers import SortedDict


class PythonRX:
    def __init__(self, output_filename):
        self.UDP_IP = "0.0.0.0"  # Listen on all interfaces
        self.UDP_PORT = 5005
        self.OUTPUT_FILENAME = output_filename
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind((self.UDP_IP, self.UDP_PORT))

        self.buffer = SortedDict()
        self.max_seq = None
        self.file_name = None
        self.tx_id = None
        self.expected_seq = 1
        self.number_of_retry = 0

    def send_ack(self, addr, tx_id, seq):
        ack_pkt = struct.pack('!HI', tx_id, seq)
        self.sock.sendto(ack_pkt, addr)

    def receive_file(self):
        print(f"Receiver listening on port {self.UDP_PORT}...")

        while True:
            try:
                pkt, addr = self.sock.recvfrom(4096)
                tx_id_temp, seq_nr = struct.unpack('!HI', pkt[:6])

                # Initial packet (seq_nr = 0)
                if seq_nr == 0:
                    self.tx_id = tx_id_temp
                    self.max_seq, name_len = struct.unpack('!II', pkt[6:14])
                    self.file_name = pkt[14:14 + name_len].decode()
                    print(f"Transmission started with TID {tx_id_temp}")
                    print(f"Receiving file: {self.file_name} with {self.max_seq} packets")
                    self.send_ack(addr, self.tx_id, 0)

                # Final packet (seq_nr = max_seq + 1)
                elif seq_nr == self.max_seq + 1 and self.tx_id == tx_id_temp:
                    print(f"\nTransmission completed with {self.number_of_retry} retries")
                    self.send_ack(addr, self.tx_id, self.max_seq + 1)

                    md5_recv = pkt[6:22]
                    file_data = b''.join(self.buffer[i] for i in range(1, self.max_seq + 1))
                    md5_local = hashlib.md5(file_data).digest()

                    if md5_local == md5_recv:
                        print("MD5 matched. Writing file.")
                        with open(self.OUTPUT_FILENAME, "wb") as f:
                            f.write(file_data)
                        return True
                    else:
                        print("MD5 mismatch!")
                        return False

                # Data packet
                elif self.tx_id == tx_id_temp:
                    if seq_nr == self.expected_seq:
                        data_len = struct.unpack('!I', pkt[6:10])[0]
                        data = pkt[10:10 + data_len]
                        self.buffer[seq_nr] = data
                        print(
                            f"\rReceive: {seq_nr}/{self.max_seq} packets ({int((seq_nr / float(self.max_seq)) * 100)}%)",
                            end='')
                        self.send_ack(addr, self.tx_id, seq_nr)
                        self.expected_seq += 1
                    else:
                        self.number_of_retry += 1
                        self.send_ack(addr, self.tx_id, self.expected_seq - 1)  # Re-send last ACK

            except KeyboardInterrupt:
                print("\nReceiver shutting down...")
                self.sock.close()
                return False


if __name__ == "__main__":
    import sys

    if len(sys.argv) != 2:
        print("Usage: python PythonRX.py <output_filename>")
        sys.exit(1)

    receiver = PythonRX(sys.argv[1])
    receiver.receive_file()