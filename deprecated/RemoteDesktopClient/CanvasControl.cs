using System.Windows.Forms;
using System.Drawing;
using System.Drawing.Imaging;
using System;
using System.Collections.Generic;

namespace RemoteDesktopClient
{
    public class CanvasControl : Control
    {
        public ImageWrapper NewestFrameImage;
        public ImageWrapper RenderingFrameImage;
        public CacheBitmap cacheBitmap;
        public bool autoResizing = false;
        public bool autoCentering = false;

        public int? RenderScreenWidth;
        public int? RenderScreenHeight;

        public int LastRenderWidth = 0;
        public int LastRenderHeight = 0;

        public bool IsFrameChanged()
        {
            if (RenderingFrameImage == null)
            {
                if (NewestFrameImage != null)
                {
                    RenderingFrameImage = NewestFrameImage;
                    return true;
                }
            }
            else
            {
                if (!RenderingFrameImage.Equals(NewestFrameImage))
                {
                    RenderingFrameImage = NewestFrameImage;
                    return true;
                }
            }

            return false;
        }

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


            if (RenderingFrameImage == null)
            {
                g.Clear(Color.Black);
            }
            else
            {
                // TODO auto resizing
                // TODO auto centering
                g.DrawImage(RenderingFrameImage.WindowsImage, new Point(0, 0));
            }

            g.Dispose();
        }

        protected override void OnPaint(PaintEventArgs pe)
        {
            //base.OnPaint(pe);
            bool needReRender = false;

            if (IsFrameChanged())
            {
                needReRender = true;
            }
            else if (cacheBitmap == null)
            {
                cacheBitmap = new CacheBitmap(Width, Height);
                needReRender = true;
            }
            else if (cacheBitmap.width != Width || cacheBitmap.height != Height)
            {
                cacheBitmap = new CacheBitmap(Width, Height);
                needReRender = true;
            }

            if (needReRender)
            {
                RenderCacheBitmap();
            }

            pe.Graphics.CompositingMode = System.Drawing.Drawing2D.CompositingMode.SourceCopy;
            pe.Graphics.InterpolationMode = System.Drawing.Drawing2D.InterpolationMode.NearestNeighbor;
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
