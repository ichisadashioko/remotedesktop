using System.Windows.Forms;
using System.Drawing;
using System.Drawing.Imaging;
using System;

namespace RemoteDesktopClient
{
    public class CanvasControl : Control
    {
        public Bitmap RenderingScreenImage;
        public CacheBitmap cacheBitmap;
        public bool autoResizing = false;
        public bool autoCentering = false;

        public void RenderCacheBitmap()
        {
            if (cacheBitmap == null)
            {
                Console.WriteLine("cacheBitmap is null");
                return;
            }

            if (cacheBitmap.bitmap == null)
            {
                Console.WriteLine("cacheBitmap.bitmap is null");
                return;
            }
            Graphics g = Graphics.FromImage(cacheBitmap.bitmap);

            if (RenderingScreenImage == null)
            {
                g.Clear(Color.Black);
            }
            else
            {
                // TODO auto resizing
                // TODO auto centering
                g.DrawImage(RenderingScreenImage, new Point(0, 0));
            }

            g.Dispose();
        }

        protected override void OnPaint(PaintEventArgs pe)
        {
            base.OnPaint(pe);

            if (cacheBitmap == null)
            {
                cacheBitmap = new CacheBitmap(Width, Height);
                RenderCacheBitmap();
                // TODO re-render bitmap
            }
            else if (cacheBitmap.width != Width || cacheBitmap.height != Height)
            {
                cacheBitmap = new CacheBitmap(Width, Height);
                RenderCacheBitmap();
                // TODO re-render bitmap
            }

            //pe.Graphics.DrawRectangle(Pens.Black, 0, 0, this.Width - 1, this.Height - 1);
            pe.Graphics.DrawImage(cacheBitmap.bitmap, 0, 0);
        }
    }

    public class CacheBitmap
    {
        public Bitmap bitmap;
        public int width;
        public int height;

        public CacheBitmap(int width, int height)
        {
            this.width = width;
            this.height = height;
            bitmap = new Bitmap(width, height, PixelFormat.Format32bppArgb);
        }
    }
}
