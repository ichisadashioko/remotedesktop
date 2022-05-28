using System;
using System.Collections.Generic;
using System.Drawing;
using System.Drawing.Imaging;
using System.IO;
namespace RemoteDesktopServer
{
    public static class Program
    {
        /// <summary>
        /// The main entry point for the application.
        /// </summary>
        [STAThread]
        static void Main()
        {
            //string sampleFilepath = @"D:\downloads\GA-Z77X-UP4_TH-003.png";
            //byte[] samplePngData = File.ReadAllBytes(sampleFilepath);
            //Image image = Image.FromStream(new MemoryStream(samplePngData));
            //Console.WriteLine($"Image size: {image.Width}x{image.Height}");

            //int[] arr1 = new int[] { 1, 2, 3, 4, 5, 6, 7, 8, 9, 10 };
            //int[] arr2 = new int[] { 1, 2, 3, 4, 5, 6, 7, 8, 9, 10 };
            //bool compareResult = (arr1 == arr2);
            //Console.WriteLine($"Compare result: {compareResult}");

            List<int> aList = new List<int>(10);
            Console.WriteLine($"List size: {aList.Count}");

            Console.ReadLine();
        }
    }
}
