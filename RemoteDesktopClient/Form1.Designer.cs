namespace RemoteDesktopClient
{
    partial class Form1
    {
        /// <summary>
        /// Required designer variable.
        /// </summary>
        private System.ComponentModel.IContainer components = null;

        /// <summary>
        /// Clean up any resources being used.
        /// </summary>
        /// <param name="disposing">true if managed resources should be disposed; otherwise, false.</param>
        protected override void Dispose(bool disposing)
        {
            if (disposing && (components != null))
            {
                components.Dispose();
            }
            base.Dispose(disposing);
        }

        #region Windows Form Designer generated code

        /// <summary>
        /// Required method for Designer support - do not modify
        /// the contents of this method with the code editor.
        /// </summary>
        private void InitializeComponent()
        {
            this.remoteAddressTextBox = new System.Windows.Forms.TextBox();
            this.connectButton = new System.Windows.Forms.Button();
            this.stopButton = new System.Windows.Forms.Button();
            this.displayRenderControl = new RemoteDesktopClient.CanvasControl();
            this.SuspendLayout();
            //
            // remoteAddressTextBox
            //
            this.remoteAddressTextBox.Anchor = ((System.Windows.Forms.AnchorStyles)(((System.Windows.Forms.AnchorStyles.Top | System.Windows.Forms.AnchorStyles.Left)
            | System.Windows.Forms.AnchorStyles.Right)));
            this.remoteAddressTextBox.Location = new System.Drawing.Point(12, 14);
            this.remoteAddressTextBox.Name = "remoteAddressTextBox";
            this.remoteAddressTextBox.Size = new System.Drawing.Size(614, 20);
            this.remoteAddressTextBox.TabIndex = 0;
            //
            // connectButton
            //
            this.connectButton.Anchor = ((System.Windows.Forms.AnchorStyles)((System.Windows.Forms.AnchorStyles.Top | System.Windows.Forms.AnchorStyles.Right)));
            this.connectButton.Location = new System.Drawing.Point(632, 12);
            this.connectButton.Name = "connectButton";
            this.connectButton.Size = new System.Drawing.Size(75, 23);
            this.connectButton.TabIndex = 1;
            this.connectButton.Text = "connect";
            this.connectButton.UseVisualStyleBackColor = true;
            this.connectButton.Click += new System.EventHandler(this.connectButton_Click);
            //
            // stopButton
            //
            this.stopButton.Anchor = ((System.Windows.Forms.AnchorStyles)((System.Windows.Forms.AnchorStyles.Top | System.Windows.Forms.AnchorStyles.Right)));
            this.stopButton.Location = new System.Drawing.Point(713, 12);
            this.stopButton.Name = "stopButton";
            this.stopButton.Size = new System.Drawing.Size(75, 23);
            this.stopButton.TabIndex = 3;
            this.stopButton.Text = "stop";
            this.stopButton.UseVisualStyleBackColor = true;
            this.stopButton.Click += new System.EventHandler(this.stopButton_Click);
            //
            // displayRenderControl
            //
            this.displayRenderControl.Anchor = ((System.Windows.Forms.AnchorStyles)((((System.Windows.Forms.AnchorStyles.Top | System.Windows.Forms.AnchorStyles.Bottom)
            | System.Windows.Forms.AnchorStyles.Left)
            | System.Windows.Forms.AnchorStyles.Right)));
            this.displayRenderControl.Location = new System.Drawing.Point(12, 40);
            this.displayRenderControl.Name = "displayRenderControl";
            this.displayRenderControl.Size = new System.Drawing.Size(776, 398);
            this.displayRenderControl.TabIndex = 2;
            //
            // Form1
            //
            this.AutoScaleDimensions = new System.Drawing.SizeF(6F, 13F);
            this.AutoScaleMode = System.Windows.Forms.AutoScaleMode.Font;
            this.ClientSize = new System.Drawing.Size(800, 450);
            this.Controls.Add(this.stopButton);
            this.Controls.Add(this.displayRenderControl);
            this.Controls.Add(this.connectButton);
            this.Controls.Add(this.remoteAddressTextBox);
            this.Name = "Form1";
            this.Text = "Form1";
            this.ResumeLayout(false);
            this.PerformLayout();

        }

        #endregion

        private System.Windows.Forms.TextBox remoteAddressTextBox;
        private System.Windows.Forms.Button connectButton;
        private CanvasControl displayRenderControl;
        private System.Windows.Forms.Button stopButton;
    }
}
