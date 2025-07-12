import java.io.*;
import java.net.*;
import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.nio.file.Files;
import java.security.MessageDigest;
import java.util.Random;

public class JavaTX {
    public static final int PORT = 5005;
    private static final int TIMEOUT_MS = 1000;
    private static final int MAX_RETRIES = 10;

    public static void main(String[] args) throws Exception {
        if (args.length != 2) {
            System.err.println("Usage: java JavaTX <file_path> <dest_ip_address>");
            System.exit(1);
        }

        sendData(args[0], args[1]);
    }

    private static void sendData(String filePath, String destIPAddress) throws Exception {
        DatagramSocket socket = new DatagramSocket();
        socket.setSoTimeout(TIMEOUT_MS);
        InetAddress address = InetAddress.getByName(destIPAddress);
        File file = new File(filePath);
        byte[] fileBytes = Files.readAllBytes(file.toPath());

        int chunkSize = 512;
        int numPackets = (int) Math.ceil(fileBytes.length / (double) chunkSize);
        short txId = (short) new Random().nextInt(0, 25536);

        // First packet
        ByteBuffer first = ByteBuffer.allocate(14 + file.getName().length()).order(ByteOrder.BIG_ENDIAN);
        first.putShort(txId).putInt(0).putInt(numPackets).putInt(file.getName().length());
        first.put(file.getName().getBytes());

        // Send initialization packet with retry logic
        if (!waitForAck(socket, address, txId, first.array(), 0)) {
            System.out.println("Failed to initialize transfer after retries");
            socket.close();
            return;
        }

        // Data packets
        int currentSeq = 1;
        while (currentSeq <= numPackets) {
            int start = (currentSeq - 1) * chunkSize;
            int len = Math.min(chunkSize, fileBytes.length - start);
            ByteBuffer dataPkt = ByteBuffer.allocate(10 + len).order(ByteOrder.BIG_ENDIAN);
            dataPkt.putShort(txId).putInt(currentSeq).putInt(len).put(fileBytes, start, len);

            boolean received = waitForAck(socket, address, txId, dataPkt.array(), currentSeq);
            if (received) {
                // ACK received, move to next packet
                System.out.print("\rTransfer: " +
                        (currentSeq) + "/" + (numPackets) + " packets (" +
                        ((int) ((currentSeq / (double) numPackets) * 100)) + "%)");
                currentSeq++;

            } else {
                // Timeout after retries
                System.out.println("\nFailed to send packet " + currentSeq + " after retries");
                socket.close();
                return;
            }
        }

        // Last packet
        MessageDigest md = MessageDigest.getInstance("MD5");
        byte[] hash = md.digest(fileBytes);
        ByteBuffer last = ByteBuffer.allocate(22).order(ByteOrder.BIG_ENDIAN);
        last.putShort(txId).putInt(numPackets + 1).put(hash);

        if (waitForAck(socket, address, txId, last.array(), numPackets + 1)) {
            System.out.println("\nFile transfer completed successfully");
        } else {
            System.out.println("\nFailed to send final packet after retries");
        }

        socket.close();
    }

    /**
     * Tries to receive an ACK packet.
     * If given time exceeds, return false, otherwise, return true.
     */
    private static boolean waitForAck(DatagramSocket socket, InetAddress address,
                                      short txId, byte[] data, int seq) throws IOException {
        byte[] ackBuf = new byte[10]; // Enough for both ACK and PCK-LOSS
        DatagramPacket ackPacket = new DatagramPacket(ackBuf, ackBuf.length);

        for (int retry = 0; retry < MAX_RETRIES; retry++) {
            // Send the packet
            DatagramPacket packet = new DatagramPacket(data, data.length, address, JavaTX.PORT);
            socket.send(packet);

            try {
                // Wait for response
                socket.receive(ackPacket);
                ByteBuffer bb = ByteBuffer.wrap(ackPacket.getData());
                short ackTxId = bb.getShort();
                int ackSeq = bb.getInt();

                if (ackTxId == txId && ackSeq == seq)
                    return true; // ACK receive

            } catch (SocketTimeoutException e) {
                System.out.println("Timeout waiting for ACK for packet " + seq + ".\nNumber of retry:" + (retry + 1) + "\r");
            }
        }
        return false;
    }
}