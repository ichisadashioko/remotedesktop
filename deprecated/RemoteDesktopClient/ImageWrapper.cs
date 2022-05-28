using System.Drawing;
using System.IO;
using System.Security.Cryptography;

namespace RemoteDesktopClient
{
    public class ImageWrapper
    {
        public byte[] ImageData;
        public Image WindowsImage;
        public byte[] _MD5HASH;

        public byte[] MD5HASH
        {
            get
            {
                if (_MD5HASH == null)
                {
                    MD5 md5 = MD5.Create();
                    _MD5HASH = md5.ComputeHash(ImageData);
                }

                return _MD5HASH;
            }
        }

        public ImageWrapper(byte[] pngImageData)
        {
            ImageData = pngImageData;
            WindowsImage = Image.FromStream(new MemoryStream(ImageData));
        }

        public bool Equals(ImageWrapper that)
        {
            if (that == null)
            {
                return false;
            }

            return Utils.CompareByteArrays(this.MD5HASH, that.MD5HASH);
        }
    }
}
