using System.Net.Sockets;
using System;
using System.Collections.Generic;
using System.Threading;

namespace RemoteDesktopClient
{
    public static class Utils
    {
        public static byte[] DecompressGzipData(byte[] data)
        {
            using (var compressedStream = new System.IO.MemoryStream(data))
            using (var zipStream = new System.IO.Compression.GZipStream(compressedStream, System.IO.Compression.CompressionMode.Decompress))
            using (var resultStream = new System.IO.MemoryStream())
            {
                zipStream.CopyTo(resultStream);
                return resultStream.ToArray();
            }
        }

        public delegate void OnReceiveWidthData(int width);
        public delegate void OnReceiveHeightData(int height);
        public delegate void OnFrameData(byte[] data);
    }
    public enum CommunicationState
    {
        GET_WIDTH,
        GET_HEIGHT,
        GET_IMAGE,
    }
    public class RemoteDesktopCommunication
    {
        public Socket socket;
        public bool stopFlag = false;
        public CommunicationState state = CommunicationState.GET_WIDTH;
        uint? width = null;
        uint? height = null;
        List<byte> pendingData = new List<byte>();

        public Thread handlePendingDataThread = null;
        public Utils.OnFrameData onFrameData = null;
        public Utils.OnReceiveWidthData onReceiveWidthData = null;
        public Utils.OnReceiveHeightData onReceiveHeightData = null;

        public RemoteDesktopCommunication(Socket socket)
        {
            this.socket = socket;
        }

        public void handlePendingDataThreadFunction()
        {
            List<byte> _pendingData = new List<byte>();
            bool canContinue = true;
            byte[] compressedDataSizeBytes = new byte[4];
            uint compressedDataSize;
            int estimatePendingDataSize;

            while (!stopFlag)
            {
                if ((this.pendingData.Count < 1) && !canContinue)
                {
                    try
                    {
                        Thread.Sleep(Timeout.Infinite);
                    }
                    catch (ThreadInterruptedException ex)
                    {
                        //Console.WriteLine(ex);
                        Console.WriteLine("Thread awoken");
                        Console.WriteLine($"this.pendingData.Count: {this.pendingData.Count}");
                        Console.WriteLine($"_pendingData.Count: {_pendingData.Count}");
                        canContinue = true;
                        continue;
                    }
                }

                Console.WriteLine($"handlePendingDataThreadFunction: locking this.pendingData");
                lock (this.pendingData)
                {
                    Console.WriteLine($"handlePendingDataThreadFunction: locked this.pendingData");
                    Console.WriteLine($"before copy: this.pendingData.Count: {this.pendingData.Count} | _pendingData.Count: {_pendingData.Count}");
                    _pendingData.AddRange(this.pendingData);
                    this.pendingData.Clear();
                    Console.WriteLine($"after copy: this.pendingData.Count: {this.pendingData.Count} | _pendingData.Count: {_pendingData.Count}");
                }

                if (_pendingData.Count < 4)
                {
                    canContinue = false;
                    continue;
                }

                if (this.state == CommunicationState.GET_WIDTH)
                {
                    byte[] widthBytes = new byte[4];

                    Console.Write("widthBytes ");
                    for (int i = 0; i < 4; i++)
                    {
                        byte value = _pendingData[i];
                        widthBytes[i] = value;
                        Console.Write(value);
                    }
                    Console.WriteLine();

                    width = BitConverter.ToUInt32(widthBytes, 0);
                    Console.WriteLine($"width: {width}");
                    if (width > 8192)
                    {
                        Console.Error.WriteLine($"width: {width}. there is probably a problem the the byte order");
                        this.stopFlag = true;
                        return;
                    }

                    if (onReceiveWidthData != null)
                    {
                        // invoke the callback in thread
                        (new Thread(() => onReceiveWidthData((int)width.Value))).Start();
                        //onReceiveWidthData((int)width);
                    }

                    _pendingData.RemoveRange(0, 4);
                    this.state = CommunicationState.GET_HEIGHT;
                    canContinue = true;
                    continue;
                }
                else if (this.state == CommunicationState.GET_HEIGHT)
                {
                    byte[] heightBytes = new byte[4];

                    Console.Write("heightBytes ");
                    for (int i = 0; i < 4; i++)
                    {
                        byte value = _pendingData[i];
                        heightBytes[i] = value;
                        Console.Write(value);
                    }
                    Console.WriteLine();

                    height = BitConverter.ToUInt32(heightBytes, 0);
                    Console.WriteLine($"height: {height}");
                    if (height > 8192)
                    {
                        Console.Error.WriteLine($"height: {height}. there is probably a problem the the byte order");
                        this.stopFlag = true;
                        return;
                    }

                    if (onReceiveHeightData != null)
                    {
                        // invoke the callback in thread
                        (new Thread(() => onReceiveHeightData((int)height.Value))).Start();
                        //onReceiveHeightData((int)height);
                    }

                    _pendingData.RemoveRange(0, 4);
                    this.state = CommunicationState.GET_IMAGE;
                    canContinue = true;
                    continue;
                }
                else if (this.state == CommunicationState.GET_IMAGE)
                {
                    for (int i = 0; i < 4; i++)
                    {
                        compressedDataSizeBytes[i] = _pendingData[i];
                    }

                    compressedDataSize = BitConverter.ToUInt32(compressedDataSizeBytes, 0);
                    if (compressedDataSize > 1073741824) // 1GB
                    {
                        Console.Error.WriteLine($"compressedDataSize: {compressedDataSize}. there is probably a problem the the byte order");
                        this.stopFlag = true;
                        return;
                    }

                    estimatePendingDataSize = ((int)compressedDataSize) + 4;

                    if (_pendingData.Count < estimatePendingDataSize)
                    {
                        canContinue = false;
                        continue;
                    }

                    byte[] compressedData = new byte[compressedDataSize];
                    for (int i = 0; i < compressedDataSize; i++)
                    {
                        compressedData[i] = _pendingData[i + 4];
                    }

                    // uncompress gzip data
                    byte[] uncompressedData = Utils.DecompressGzipData(compressedData);
                    int uncompressedDataSize = uncompressedData.Length;
                    int expectedFrameSize = (int)(width * height * 3);
                    if ((uncompressedDataSize % expectedFrameSize) != 0)
                    {
                        Console.Error.WriteLine($"uncompressedDataSize: {uncompressedDataSize} - expectedFrameSize: {expectedFrameSize} - corrupted data stream");
                        this.stopFlag = true;
                        return;
                    }

                    Console.WriteLine($"uncompressedDataSize: {uncompressedDataSize}");

                    // TODO run callback async function
                    if (onFrameData != null)
                    {
                        // invoke the callback in thread
                        (new Thread(() => onFrameData(uncompressedData))).Start();
                        //onFrameData(uncompressedData);
                    }

                    _pendingData.RemoveRange(0, estimatePendingDataSize);
                }
            }
        }

        public void startCommunication()
        {
            this.handlePendingDataThread = new Thread(this.handlePendingDataThreadFunction);
            this.handlePendingDataThread.Start();

            byte[] buffer = new byte[65536];
            int bytesRead;
            while (!stopFlag)
            {
                bytesRead = this.socket.Receive(buffer);
                if (bytesRead > 0)
                {
                    lock (this.pendingData)
                    {
                        for (int i = 0; i < bytesRead; i++)
                        {
                            this.pendingData.Add(buffer[i]);
                        }
                    }

                    if (this.handlePendingDataThread.ThreadState == ThreadState.Stopped)
                    {
                        this.stopFlag = true;
                        Console.WriteLine("handlePendingDataThread stopped");

                        this.socket.Close();
                        return;
                    }
                    else if (this.handlePendingDataThread.ThreadState == ThreadState.WaitSleepJoin)
                    {
                        this.handlePendingDataThread.Interrupt();
                    }
                }
                else
                {
                    if (!this.socket.Connected)
                    {
                        this.stopFlag = true;
                        Console.WriteLine("socket disconnected");
                        return;
                    }
                    else if (this.handlePendingDataThread.ThreadState == ThreadState.Stopped)
                    {
                        Console.WriteLine("handlePendingDataThread stopped");
                        this.stopFlag = true;
                        this.socket.Close();
                        return;
                    }
                }
            }


            if (this.socket.Connected)
            {
                this.stopFlag = true;
                Console.WriteLine("disconnecting the socket");
                this.socket.Close();
            }
        }
    }
}
