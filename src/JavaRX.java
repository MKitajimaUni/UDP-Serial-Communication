import java.io.*;
import java.net.*;
import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.nio.file.Files;
import java.nio.file.Paths;
import java.security.MessageDigest;
import java.util.*;

public class JavaRX {
    static final int PORT = 5005;
    static final int BUFFER_SIZE = 1024;
    static final int INT_SIZE_BYTE = 4;
    static final int SHORT_SIZE_BYTE = 2;

    public static void main(String[] args) throws Exception {
        if (args.length != 1) {
            System.err.println("Usage: java JavaRX <path_to_write_the_file>");
            System.exit(1);
        }

        receiveData(args[0]);
    }

    private static void receiveData(String fileName2Store) throws Exception {
        DatagramSocket socket = new DatagramSocket(PORT);
        MessageDigest md = MessageDigest.getInstance("MD5");
        Map<Integer, byte[]> buffer = new TreeMap<>();
        short txId = -1;
        int maxSeq = -1;
        String fileName;
        int expectedSeq = 1; // Track expected sequence number

        while (true) {
            byte[] buf = new byte[BUFFER_SIZE];
            DatagramPacket packet = new DatagramPacket(buf, buf.length);
            socket.receive(packet);

            ByteBuffer bb = ByteBuffer.wrap(packet.getData());
            short txIdTemp = bb.getShort(); // tid
            int seq = bb.getInt(); // sequence number

            // first packet
            if (seq == 0) {
                // Send ACK for first packet
                sendAck(socket, packet.getAddress(), packet.getPort(), txId, 0);

                txId = txIdTemp;
                maxSeq = bb.getInt();
                int nameLen = bb.getInt();
                byte[] nameBytes = new byte[nameLen];
                bb.get(nameBytes);
                fileName = new String(nameBytes);
                System.out.println("Transmission started with TID " + txId);
                System.out.println("Receiving file: " + fileName + " with " + (maxSeq + 1) + " packets");
            }
            // last packet
            else if (seq == maxSeq + 1 && txId == txIdTemp) {
                // Send final ACK
                sendAck(socket, packet.getAddress(), packet.getPort(), txId, maxSeq + 1);

                byte[] md5 = new byte[16];
                bb.get(md5);

                ByteArrayOutputStream baos = new ByteArrayOutputStream();
                int lostPkt = 0;
                MessageDigest fileMd = MessageDigest.getInstance("MD5");

                for (int i = 1; i <= maxSeq; i++) {
                    if (buffer.containsKey(i)) {
                        byte[] chunk = buffer.get(i);
                        baos.write(chunk);
                        fileMd.update(chunk);
                    } else {
                        lostPkt++;
                    }
                }

                System.out.println("\nPacket transfer completed with " + lostPkt + " missing packets.");

                byte[] fileData = baos.toByteArray();
                byte[] localHash = fileMd.digest(); // Get MD5 of accumulated data

                if (Arrays.equals(md5, localHash)) {
                    Files.write(Paths.get(fileName2Store), fileData);
                    System.out.println("File written. MD5 OK.");
                } else {
                    System.out.println("MD5 mismatch!");
                    System.out.println("Expected MD5: " + bytesToHex(md5));
                    System.out.println("Calculated MD5: " + bytesToHex(localHash));
                }

                break;
            }
            // data packet
            else if (txId == txIdTemp) {
                if (seq == expectedSeq) {
                    // Expected packet received
                    // Send ACK for this packet
                    sendAck(socket, packet.getAddress(), packet.getPort(), txId, seq);
                    expectedSeq++;

                    int len = bb.getInt();
                    byte[] chunk = new byte[len];
                    bb.get(chunk);
                    md.update(chunk);

                    if (!buffer.containsKey(seq)) {
                        buffer.put(seq, chunk);
                    }

                    System.out.print("\rReceive: " +
                            (seq) + "/" + (maxSeq) + " packets (" +
                            ((int) ((seq / (double) maxSeq) * 100)) + "%)");
                }
            }
        }

        socket.close();
    }

    private static void sendAck(DatagramSocket socket, InetAddress address, int port, short txId, int seq) throws IOException {
        ByteBuffer ackBuffer = ByteBuffer.allocate(INT_SIZE_BYTE + SHORT_SIZE_BYTE).order(ByteOrder.BIG_ENDIAN);
        ackBuffer.putShort(txId).putInt(seq);
        DatagramPacket ackPacket = new DatagramPacket(ackBuffer.array(), ackBuffer.position(), address, port);
        socket.send(ackPacket);
    }

    // Helper method to print hex
    private static String bytesToHex(byte[] bytes) {
        StringBuilder sb = new StringBuilder();
        for (byte b : bytes) {
            sb.append(String.format("%02x", b));
        }
        return sb.toString();
    }
}
