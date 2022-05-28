using System;
using System.Collections.Generic;
using System.ComponentModel;
using System.Data;
using System.Drawing;
using System.Drawing.Imaging;
using System.IO;
using System.Linq;
using System.Net.Sockets;
using System.Text;
using System.Threading.Tasks;
using System.Windows.Forms;

namespace RemoteDesktopClient
{
    public partial class Form1 : Form
    {
        public static readonly int DEFAULT_SERVER_PORT = 21578;
        public RemoteDesktopCommunication remoteDesktopCommunication = null;
        public Form1()
        {
            InitializeComponent();
        }

        public void changeConnectButtonState(bool state)
        {
            if (connectButton.InvokeRequired)
            {
                connectButton.Invoke(new Action(() => connectButton.Enabled = state));
            }
            else
            {
                connectButton.Enabled = state;
            }
        }

        public void OnHeightInfoReceived(int heightValue)
        {
            this.displayRenderControl.RenderScreenHeight = heightValue;
        }

        public void OnWidthInfoReceived(int widthValue)
        {
            this.displayRenderControl.RenderScreenWidth = widthValue;
        }

        public void OnImageDataReceived(byte[] imageData)
        {
            try
            {
                ImageWrapper pngImageWrapper = Utils.IMAGEWRAPPER_Get(imageData);
                displayRenderControl.NewestFrameImage = pngImageWrapper;
                displayRenderControl.Invalidate();
            }
            catch (Exception ex)
            {
                Console.WriteLine(ex);
            }
        }

        public void connectToRemoteServerThreadFunction(string ip, int port)
        {
            try
            {
                Console.WriteLine($"prepare to connect to {ip}:{port}");
                Socket socket = new Socket(AddressFamily.InterNetwork, SocketType.Stream, ProtocolType.Tcp);
                socket.Connect(ip, port);
                Console.WriteLine($"connected to {ip}:{port}");

                // TODO
                RemoteDesktopCommunication communicationObj = new RemoteDesktopCommunication(socket);
                this.remoteDesktopCommunication = communicationObj;
                communicationObj.onReceiveHeightData += OnHeightInfoReceived;
                communicationObj.onReceiveWidthData += OnWidthInfoReceived;
                communicationObj.onPngImageData += OnImageDataReceived;
                communicationObj.startCommunication();
                Console.WriteLine("communication stopped");
            }
            catch (Exception ex)
            {
                Console.WriteLine(ex);
            }

            changeConnectButtonState(true);
        }

        private void connectButton_Click(object sender, EventArgs e)
        {
            try
            {
                connectButton.Enabled = false;
                string remoteAddress = remoteAddressTextBox.Text;
                if (string.IsNullOrWhiteSpace(remoteAddress))
                {
                    MessageBox.Show("Please enter a valid remote address");
                    connectButton.Enabled = true;
                    return;
                }

                string ipAddress;
                int portNumber;

                if (remoteAddress.Contains(':'))
                {
                    var result = remoteAddress.Split(new char[] { ':' }, 2);
                    ipAddress = result[0];
                    portNumber = int.Parse(result[1]);
                }
                else
                {
                    ipAddress = remoteAddress;
                    portNumber = DEFAULT_SERVER_PORT;
                }

                Task.Run(() => connectToRemoteServerThreadFunction(ipAddress, portNumber));
            }
            catch (Exception ex)
            {
                Console.WriteLine(ex);
                MessageBox.Show(ex.Message);
                connectButton.Enabled = true;
            }
        }

        private void stopButton_Click(object sender, EventArgs e)
        {
            Console.WriteLine($"stopButton_Click - remoteDesktopCommunication: {remoteDesktopCommunication}");
            if (remoteDesktopCommunication != null)
            {
                remoteDesktopCommunication.stopFlag = true;
            }
        }
    }
}
