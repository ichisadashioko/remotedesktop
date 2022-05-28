using System.Collections.Generic;
using System.Windows.Forms;
using System.Drawing;
using System.Drawing.Imaging;
using System;
using System.IO;

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
        public delegate void OnReceivePngImageData(byte[] data);

        public static bool CompareByteArrays(byte[] array1, byte[] array2)
        {
            if (array1.Length != array2.Length)
            {
                return false;
            }

            for (int i = 0; i < array1.Length; i++)
            {
                if (array1[i] != array2[i])
                {
                    return false;
                }
            }

            return true;
        }

        public static int IMAGEWRAPPER_CACHE_INDEX = 0;
        public static ImageWrapper[] IMAGEWRAPPER_CACHE = new ImageWrapper[10];
        public static readonly int IMAGEWRAPPER_CACHE_SIZE = 10;

        public static ImageWrapper IMAGEWRAPPER_Find(byte[] pngImageData)
        {
            foreach (var item in IMAGEWRAPPER_CACHE)
            {
                if (item == null)
                {
                    continue;
                }

                if (CompareByteArrays(item.ImageData, pngImageData))
                {
                    return item;
                }
            }

            return null;
        }

        public static void IMAGEWRAPPER_Add(ImageWrapper pngImageWrapper)
        {
            IMAGEWRAPPER_CACHE_INDEX %= IMAGEWRAPPER_CACHE_SIZE;
            IMAGEWRAPPER_CACHE[IMAGEWRAPPER_CACHE_INDEX] = pngImageWrapper;
            IMAGEWRAPPER_CACHE_INDEX++;
        }

        public static ImageWrapper IMAGEWRAPPER_Get(byte[] pngImageData)
        {
            ImageWrapper pngImageWrapper = IMAGEWRAPPER_Find(pngImageData);
            if (pngImageWrapper == null)
            {
                pngImageWrapper = new ImageWrapper(pngImageData);
                IMAGEWRAPPER_Add(pngImageWrapper);
            }
            return pngImageWrapper;
        }
    }
}
