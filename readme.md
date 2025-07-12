# Cross-Language Serial Communication (Java ↔ Python) via UDP

This project implements a serial communication system using Stop-and-Wait protocol over UDP. It includes two language implementations:

- Java
- Python

Both implementations are bidirectional, that means, communication between Java TX ↔ Python RX or Python TX ↔ Java RX works seamlessly.

## Features

- Supports file transfer over UDP
- Implements Stop-and-Wait protocol
- Communication is bidirectional and cross-language
- Fixed timeout of 10 seconds per data packet
- No external serial/RXTX libraries required

---

## Usage

The usage is identical for both Python and Java versions.

### Transmitter (TX)

TX <file_path> <destination_ip_address>

### Receiver (TX)

RX <file_path_to_store>