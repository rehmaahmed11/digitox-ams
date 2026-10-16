using System; using System.Drawing; using System.Drawing.Drawing2D; using System.Drawing.Imaging; using System.IO;
namespace CapsLockOSD {
static class Gen {
  static void Main(string[] a) {
    string outDir = a[0];
    OsdRenderer.Render(true, 1.5f).Save(Path.Combine(outDir,"preview_on.png"), ImageFormat.Png);
    OsdRenderer.Render(false, 1.5f).Save(Path.Combine(outDir,"preview_off.png"), ImageFormat.Png);
    foreach (int sz in new[]{16,24,32,48,64,128,256}) AppIcon(sz).Save(Path.Combine(outDir,"icon_"+sz+".png"), ImageFormat.Png);
  }
  static Bitmap AppIcon(int sz) {
    var bmp = new Bitmap(sz, sz, PixelFormat.Format32bppArgb);
    using (var g = Graphics.FromImage(bmp)) {
      g.SmoothingMode = SmoothingMode.AntiAlias; g.PixelOffsetMode = PixelOffsetMode.HighQuality; g.Clear(Color.Transparent);
      float k = sz/256f; var rc = new RectangleF(12*k,12*k,232*k,232*k);
      using (var p = OsdRenderer.RoundRect(rc, 56*k))
      using (var b = new LinearGradientBrush(rc, Color.FromArgb(255,64,156,255), Color.FromArgb(255,0,92,214), 90f)) g.FillPath(b,p);
      float gw=120*k, gh=140*k, x=(sz-gw)/2, y=56*k;
      Func<float,float,PointF> P=(u,v)=>new PointF(x+u*gw,y+v*gh);
      using (var ar = new GraphicsPath()) using (var w = new SolidBrush(Color.White)) {
        ar.AddPolygon(new[]{P(.5f,0),P(1,.5f),P(.72f,.5f),P(.72f,.74f),P(.28f,.74f),P(.28f,.5f),P(0,.5f)});
        g.FillPath(w, ar);
        using (var bp = OsdRenderer.RoundRect(new RectangleF(P(.28f,.86f).X,P(.28f,.86f).Y,gw*.44f,gh*.14f), 6*k)) g.FillPath(w,bp);
      }
    }
    return bmp;
  }
}}
