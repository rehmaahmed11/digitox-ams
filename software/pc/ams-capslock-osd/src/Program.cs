// Caps Lock OSD - a tiny, professional Caps Lock on/off indicator for Windows.
// Shows a smooth fade-in / fade-out HUD whenever Caps Lock is toggled.
// Lives in the system tray, starts with Windows, uses ~0% CPU.

using System;
using System.Diagnostics;
using System.Drawing;
using System.Drawing.Drawing2D;
using System.Drawing.Text;
using System.Reflection;
using System.Runtime.InteropServices;
using System.Threading;
using System.Windows.Forms;
using Microsoft.Win32;

[assembly: AssemblyTitle("AMS Caps Lock OSD")]
[assembly: AssemblyDescription("AMS Caps Lock OSD - on-screen Caps Lock indicator by AMS")]
[assembly: AssemblyProduct("AMS Caps Lock OSD")]
[assembly: AssemblyCompany("AMS")]
[assembly: AssemblyCopyright("\u00A9 2026 AMS")]
[assembly: AssemblyVersion("1.1.0.0")]
[assembly: AssemblyFileVersion("1.1.0.0")]

namespace CapsLockOSD
{
    static class Program
    {
        public const string AppName = "AMS Caps Lock OSD";
        public const string Brand = "AMS";
        public const string YouTubeUrl = "https://www.youtube.com/channel/UCW5b5zJ1MW35P1x9--ExMvg";
        public const string RunValueName = "CapsLockOSD";

        [STAThread]
        static void Main()
        {
            bool createdNew;
            using (var mutex = new Mutex(true, "Local\\CapsLockOSD_SingleInstance_7F3A", out createdNew))
            {
                if (!createdNew) return; // already running

                try { Native.SetProcessDPIAware(); } catch { }
                Application.EnableVisualStyles();
                Application.SetCompatibleTextRenderingDefault(false);
                Application.Run(new TrayContext());
                GC.KeepAlive(mutex);
            }
        }
    }

    // ------------------------------------------------------------------ Tray / app logic
    sealed class TrayContext : ApplicationContext
    {
        readonly NotifyIcon tray;
        readonly OsdWindow osd;
        readonly System.Windows.Forms.Timer pollTimer;
        readonly System.Windows.Forms.Timer hookDelayTimer;
        readonly ToolStripMenuItem startupItem;
        readonly Icon iconOn, iconOff;
        readonly Native.LowLevelKeyboardProc hookProc; // keep delegate alive
        IntPtr hookHandle = IntPtr.Zero;
        bool lastState;

        public TrayContext()
        {
            osd = new OsdWindow();
            lastState = Native.IsCapsOn();

            iconOn = TrayIcons.Make(true);
            iconOff = TrayIcons.Make(false);

            var menu = new ContextMenuStrip();
            var title = new ToolStripMenuItem(Program.AppName + "  \u2022  by " + Program.Brand) { Enabled = false };
            var yt = new ToolStripMenuItem("AMS on YouTube");
            yt.Click += delegate { try { Process.Start(Program.YouTubeUrl); } catch { } };
            startupItem = new ToolStripMenuItem("Start with Windows") { CheckOnClick = true, Checked = Startup.IsEnabled() };
            startupItem.CheckedChanged += delegate { Startup.Set(startupItem.Checked); };
            var preview = new ToolStripMenuItem("Show preview");
            preview.Click += delegate { osd.ShowState(Native.IsCapsOn()); };
            var exit = new ToolStripMenuItem("Exit");
            exit.Click += delegate { ExitThread(); };
            menu.Items.AddRange(new ToolStripItem[] { title, new ToolStripSeparator(), startupItem, preview, yt, new ToolStripSeparator(), exit });
            menu.Opening += delegate { startupItem.Checked = Startup.IsEnabled(); };

            tray = new NotifyIcon { ContextMenuStrip = menu, Visible = true };
            tray.MouseClick += (s, e) => { if (e.Button == MouseButtons.Left) osd.ShowState(Native.IsCapsOn()); };
            UpdateTray();

            // Instant reaction: low-level keyboard hook for the Caps Lock key
            hookDelayTimer = new System.Windows.Forms.Timer { Interval = 25 };
            hookDelayTimer.Tick += delegate { hookDelayTimer.Stop(); Check(); };
            hookProc = HookCallback;
            try { hookHandle = Native.SetWindowsHookEx(Native.WH_KEYBOARD_LL, hookProc, Native.GetModuleHandle(null), 0); } catch { }

            // Safety net: light polling (catches toggles the hook can't see, e.g. elevated apps)
            pollTimer = new System.Windows.Forms.Timer { Interval = 150 };
            pollTimer.Tick += delegate { Check(); };
            pollTimer.Start();

            SystemEvents.DisplaySettingsChanged += delegate { osd.InvalidateCache(); };
        }

        IntPtr HookCallback(int nCode, IntPtr wParam, IntPtr lParam)
        {
            if (nCode >= 0)
            {
                int vk = Marshal.ReadInt32(lParam);
                int msg = wParam.ToInt32();
                if (vk == 0x14 && (msg == 0x0101 || msg == 0x0105 || msg == 0x0100 || msg == 0x0104))
                {
                    hookDelayTimer.Stop();
                    hookDelayTimer.Start();
                }
            }
            return Native.CallNextHookEx(hookHandle, nCode, wParam, lParam);
        }

        void Check()
        {
            bool cur = Native.IsCapsOn();
            if (cur == lastState) return;
            lastState = cur;
            UpdateTray();
            osd.ShowState(cur);
        }

        void UpdateTray()
        {
            tray.Icon = lastState ? iconOn : iconOff;
            tray.Text = "AMS Caps Lock OSD \u2014 Caps Lock: " + (lastState ? "ON" : "OFF");
        }

        protected override void ExitThreadCore()
        {
            pollTimer.Stop();
            if (hookHandle != IntPtr.Zero) Native.UnhookWindowsHookEx(hookHandle);
            tray.Visible = false;
            tray.Dispose();
            osd.Close();
            base.ExitThreadCore();
        }
    }

    // ------------------------------------------------------------------ Startup (HKCU Run key)
    static class Startup
    {
        const string RunKey = @"Software\Microsoft\Windows\CurrentVersion\Run";

        public static bool IsEnabled()
        {
            using (var k = Registry.CurrentUser.OpenSubKey(RunKey))
                return k != null && k.GetValue(Program.RunValueName) != null;
        }

        public static void Set(bool on)
        {
            try
            {
                using (var k = Registry.CurrentUser.CreateSubKey(RunKey))
                {
                    if (on) k.SetValue(Program.RunValueName, "\"" + Application.ExecutablePath + "\"");
                    else if (k.GetValue(Program.RunValueName) != null) k.DeleteValue(Program.RunValueName);
                }
            }
            catch { }
        }
    }

    // ------------------------------------------------------------------ The on-screen HUD
    sealed class OsdWindow : Form
    {
        const double FadeInMs = 170, HoldMs = 1100, FadeOutMs = 420;
        enum Phase { Hidden, FadeIn, Hold, FadeOut }

        readonly System.Windows.Forms.Timer anim = new System.Windows.Forms.Timer { Interval = 10 };
        readonly Stopwatch clock = new Stopwatch();
        Phase phase = Phase.Hidden;
        double a;            // 0..1 animation progress
        double phaseStart;   // ms
        double lastTick;
        Bitmap bmpOn, bmpOff, current;
        float scale = 1f;
        Point basePos;

        public OsdWindow()
        {
            FormBorderStyle = FormBorderStyle.None;
            ShowInTaskbar = false;
            StartPosition = FormStartPosition.Manual;
            TopMost = true;
            anim.Tick += delegate { Step(); };
            var h = Handle; // force handle creation
        }

        protected override bool ShowWithoutActivation { get { return true; } }

        protected override CreateParams CreateParams
        {
            get
            {
                var cp = base.CreateParams;
                cp.ExStyle |= 0x00080000  // WS_EX_LAYERED
                            | 0x00000020  // WS_EX_TRANSPARENT (click-through)
                            | 0x00000080  // WS_EX_TOOLWINDOW (no alt-tab)
                            | 0x08000000  // WS_EX_NOACTIVATE
                            | 0x00000008; // WS_EX_TOPMOST
                return cp;
            }
        }

        public void InvalidateCache()
        {
            if (bmpOn != null) { bmpOn.Dispose(); bmpOn = null; }
            if (bmpOff != null) { bmpOff.Dispose(); bmpOff = null; }
        }

        void EnsureBitmaps()
        {
            using (var g = CreateGraphics()) scale = g.DpiX / 96f;
            if (bmpOn == null) bmpOn = OsdRenderer.Render(true, scale);
            if (bmpOff == null) bmpOff = OsdRenderer.Render(false, scale);
        }

        public void ShowState(bool on)
        {
            EnsureBitmaps();
            current = on ? bmpOn : bmpOff;

            // Position: bottom-centre of the monitor with the mouse cursor, above the taskbar
            var wa = Screen.FromPoint(Cursor.Position).WorkingArea;
            basePos = new Point(wa.Left + (wa.Width - current.Width) / 2,
                                wa.Bottom - current.Height - (int)(70 * scale));

            if (!clock.IsRunning) clock.Start();
            double now = clock.Elapsed.TotalMilliseconds;
            lastTick = now;

            if (phase == Phase.Hidden || phase == Phase.FadeOut || phase == Phase.FadeIn)
                phase = Phase.FadeIn;           // continue from current alpha
            else
                phaseStart = now;               // already fully visible: just restart hold

            if (phase == Phase.FadeIn && a >= 1) { phase = Phase.Hold; phaseStart = now; }

            Apply();
            Native.ShowWindow(Handle, 4); // SW_SHOWNOACTIVATE
            Native.SetWindowPos(Handle, new IntPtr(-1), 0, 0, 0, 0, 0x0001 | 0x0002 | 0x0010 | 0x0040);
            anim.Start();
        }

        void Step()
        {
            double now = clock.Elapsed.TotalMilliseconds;
            double dt = now - lastTick; lastTick = now;

            switch (phase)
            {
                case Phase.FadeIn:
                    a += dt / FadeInMs;
                    if (a >= 1) { a = 1; phase = Phase.Hold; phaseStart = now; }
                    break;
                case Phase.Hold:
                    if (now - phaseStart >= HoldMs) phase = Phase.FadeOut;
                    else return; // nothing changes while holding
                    break;
                case Phase.FadeOut:
                    a -= dt / FadeOutMs;
                    if (a <= 0)
                    {
                        a = 0; phase = Phase.Hidden;
                        anim.Stop();
                        Native.ShowWindow(Handle, 0); // SW_HIDE
                        return;
                    }
                    break;
            }
            Apply();
        }

        void Apply()
        {
            if (current == null) return;
            double e = phase == Phase.FadeOut ? EaseInOut(a) : EaseOut(a);
            byte alpha = (byte)Math.Round(255 * e);
            float s = (float)(0.94 + 0.06 * e); // subtle zoom
            int slide = (int)Math.Round((1 - e) * 14 * scale);
            OsdRenderer.Present(Handle, current, new Point(basePos.X, basePos.Y + slide), alpha, s);
        }

        static double EaseOut(double t) { t = Clamp(t); return 1 - Math.Pow(1 - t, 3); }
        static double EaseInOut(double t) { t = Clamp(t); return t < .5 ? 4 * t * t * t : 1 - Math.Pow(-2 * t + 2, 3) / 2; }
        static double Clamp(double t) { return t < 0 ? 0 : (t > 1 ? 1 : t); }
    }

    // ------------------------------------------------------------------ Drawing
    static class OsdRenderer
    {
        static readonly Color Accent1 = Color.FromArgb(255, 64, 156, 255);
        static readonly Color Accent2 = Color.FromArgb(255, 0, 102, 230);

        public static Bitmap Render(bool on, float s)
        {
            int pad = (int)(22 * s);                     // room for the soft shadow
            int w = (int)(176 * s), h = (int)(198 * s);
            var bmp = new Bitmap(w + pad * 2, h + pad * 2, System.Drawing.Imaging.PixelFormat.Format32bppArgb);
            bmp.SetResolution(96, 96);

            using (var g = Graphics.FromImage(bmp))
            {
                g.SmoothingMode = SmoothingMode.AntiAlias;
                g.PixelOffsetMode = PixelOffsetMode.HighQuality;
                g.InterpolationMode = InterpolationMode.HighQualityBicubic;
                g.TextRenderingHint = TextRenderingHint.AntiAlias;
                g.Clear(Color.Transparent);

                var card = new RectangleF(pad, pad, w, h);
                float r = 26 * s;

                // Soft drop shadow
                for (int i = 0; i < 14; i++)
                {
                    float grow = i * 1.3f * s;
                    var sr = new RectangleF(card.X - grow, card.Y - grow + 5 * s, card.Width + grow * 2, card.Height + grow * 2);
                    using (var p = RoundRect(sr, r + grow))
                    using (var b = new SolidBrush(Color.FromArgb((int)(16 - i * 1.1f), 0, 0, 0)))
                        g.FillPath(b, p);
                }

                // Card body (dark glass)
                using (var p = RoundRect(card, r))
                {
                    using (var b = new LinearGradientBrush(card, Color.FromArgb(238, 40, 42, 48), Color.FromArgb(238, 24, 25, 29), 90f))
                        g.FillPath(b, p);
                    using (var pen = new Pen(Color.FromArgb(46, 255, 255, 255), 1f * s))
                        g.DrawPath(pen, p);
                }
                // Top highlight (fades out smoothly by mid-card)
                using (var p = RoundRect(new RectangleF(card.X + 1, card.Y + 1, card.Width - 2, card.Height - 2), r))
                using (var b = new LinearGradientBrush(card, Color.FromArgb(18, 255, 255, 255), Color.FromArgb(0, 255, 255, 255), 90f))
                {
                    var bl = new Blend(); bl.Positions = new[] { 0f, 0.5f, 1f }; bl.Factors = new[] { 0f, 1f, 1f };
                    b.Blend = bl;
                    g.FillPath(b, p);
                }

                // Icon badge
                float d = 78 * s;
                var badge = new RectangleF(card.X + (w - d) / 2, card.Y + 26 * s, d, d);
                if (on)
                {
                    // glow
                    for (int i = 0; i < 10; i++)
                    {
                        float gr = i * 1.6f * s;
                        using (var gb = new SolidBrush(Color.FromArgb(14 - i, Accent1)))
                            g.FillEllipse(gb, badge.X - gr, badge.Y - gr, badge.Width + gr * 2, badge.Height + gr * 2);
                    }
                    using (var b = new LinearGradientBrush(badge, Accent1, Accent2, 90f))
                        g.FillEllipse(b, badge);
                    using (var pen = new Pen(Color.FromArgb(70, 255, 255, 255), 1f * s))
                        g.DrawEllipse(pen, badge);
                }
                else
                {
                    using (var b = new SolidBrush(Color.FromArgb(28, 255, 255, 255)))
                        g.FillEllipse(b, badge);
                    using (var pen = new Pen(Color.FromArgb(60, 255, 255, 255), 1.2f * s))
                        g.DrawEllipse(pen, badge);
                }
                DrawCapsGlyph(g, badge, on, s);

                // Labels
                var labelRect = new RectangleF(card.X, badge.Bottom + 14 * s, w, 18 * s);
                var stateRect = new RectangleF(card.X, labelRect.Bottom + 1 * s, w, 30 * s);
                using (var sf = new StringFormat { Alignment = StringAlignment.Center, LineAlignment = StringAlignment.Center })
                using (var f1 = new Font("Segoe UI Semibold", 12f * s, FontStyle.Regular, GraphicsUnit.Pixel))
                using (var f2 = new Font("Segoe UI", 22f * s, FontStyle.Bold, GraphicsUnit.Pixel))
                using (var b1 = new SolidBrush(Color.FromArgb(150, 255, 255, 255)))
                using (var b2 = new SolidBrush(on ? Color.White : Color.FromArgb(185, 255, 255, 255)))
                {
                                        g.DrawString("C A P S   L O C K", f1, b1, labelRect, sf);
                    g.DrawString(on ? "ON" : "OFF", f2, b2, stateRect, sf);
                }

                // AMS branding footer
                float fy = card.Bottom - 22 * s;
                using (var pen = new Pen(Color.FromArgb(26, 255, 255, 255), 1f * s))
                    g.DrawLine(pen, card.X + 40 * s, fy - 4 * s, card.Right - 40 * s, fy - 4 * s);
                using (var sf = new StringFormat { Alignment = StringAlignment.Center, LineAlignment = StringAlignment.Center })
                using (var fb = new Font("Segoe UI", 10.5f * s, FontStyle.Bold, GraphicsUnit.Pixel))
                using (var bb = new SolidBrush(on ? Color.FromArgb(200, 120, 185, 255) : Color.FromArgb(110, 255, 255, 255)))
                    g.DrawString("A M S", fb, bb, new RectangleF(card.X, fy, w, 16 * s), sf);
            }
            return bmp;
        }

        // The ⇪ Caps Lock symbol: up arrow + bar
        static void DrawCapsGlyph(Graphics g, RectangleF box, bool on, float s)
        {
            float gw = box.Width * 0.46f, gh = box.Height * 0.50f;
            float x = box.X + (box.Width - gw) / 2, y = box.Y + (box.Height - gh) / 2;
            Func<float, float, PointF> P = (u, v) => new PointF(x + u * gw, y + v * gh);

            using (var arrow = new GraphicsPath())
            {
                arrow.AddPolygon(new[] { P(.5f, 0f), P(1f, .5f), P(.72f, .5f), P(.72f, .74f), P(.28f, .74f), P(.28f, .5f), P(0f, .5f) });
                var bar = new RectangleF(P(.28f, .86f).X, P(.28f, .86f).Y, gw * .44f, gh * .14f);

                if (on)
                {
                    using (var b = new SolidBrush(Color.White))
                    {
                        g.FillPath(b, arrow);
                        using (var bp = RoundRect(bar, 2 * s)) g.FillPath(b, bp);
                    }
                }
                else
                {
                    using (var pen = new Pen(Color.FromArgb(200, 255, 255, 255), 2.4f * s) { LineJoin = LineJoin.Round })
                    {
                        g.DrawPath(pen, arrow);
                        using (var bp = RoundRect(bar, 2 * s)) g.DrawPath(pen, bp);
                    }
                }
            }
        }

        public static GraphicsPath RoundRect(RectangleF r, float rad)
        {
            float d = Math.Min(rad * 2, Math.Min(r.Width, r.Height));
            var p = new GraphicsPath();
            if (d <= 0.5f) { p.AddRectangle(r); return p; }
            p.AddArc(r.X, r.Y, d, d, 180, 90);
            p.AddArc(r.Right - d, r.Y, d, d, 270, 90);
            p.AddArc(r.Right - d, r.Bottom - d, d, d, 0, 90);
            p.AddArc(r.X, r.Bottom - d, d, d, 90, 90);
            p.CloseFigure();
            return p;
        }

        // Push a per-pixel-alpha bitmap to a layered window with a global opacity and zoom
        public static void Present(IntPtr hwnd, Bitmap src, Point pos, byte opacity, float zoom)
        {
            Bitmap frame = src;
            bool owned = false;
            if (zoom < 0.999f)
            {
                frame = new Bitmap(src.Width, src.Height, System.Drawing.Imaging.PixelFormat.Format32bppArgb);
                owned = true;
                using (var g = Graphics.FromImage(frame))
                {
                    g.InterpolationMode = InterpolationMode.HighQualityBilinear;
                    g.PixelOffsetMode = PixelOffsetMode.HighQuality;
                    g.Clear(Color.Transparent);
                    float nw = src.Width * zoom, nh = src.Height * zoom;
                    g.DrawImage(src, (src.Width - nw) / 2, (src.Height - nh) / 2, nw, nh);
                }
            }

            IntPtr screenDc = Native.GetDC(IntPtr.Zero);
            IntPtr memDc = Native.CreateCompatibleDC(screenDc);
            IntPtr hBmp = frame.GetHbitmap(Color.FromArgb(0));
            IntPtr old = Native.SelectObject(memDc, hBmp);
            try
            {
                var size = new Native.SIZE(frame.Width, frame.Height);
                var srcPt = new Native.POINT(0, 0);
                var dst = new Native.POINT(pos.X, pos.Y);
                var blend = new Native.BLENDFUNCTION { BlendOp = 0, BlendFlags = 0, SourceConstantAlpha = opacity, AlphaFormat = 1 };
                Native.UpdateLayeredWindow(hwnd, screenDc, ref dst, ref size, memDc, ref srcPt, 0, ref blend, 2 /*ULW_ALPHA*/);
            }
            finally
            {
                Native.SelectObject(memDc, old);
                Native.DeleteObject(hBmp);
                Native.DeleteDC(memDc);
                Native.ReleaseDC(IntPtr.Zero, screenDc);
                if (owned) frame.Dispose();
            }
        }
    }

    // ------------------------------------------------------------------ Tray icons (drawn at runtime)
    static class TrayIcons
    {
        public static Icon Make(bool on)
        {
            int sz = SystemInformation.SmallIconSize.Width;
            if (sz < 16) sz = 16;
            using (var bmp = new Bitmap(sz, sz, System.Drawing.Imaging.PixelFormat.Format32bppArgb))
            {
                using (var g = Graphics.FromImage(bmp))
                {
                    g.SmoothingMode = SmoothingMode.AntiAlias;
                    g.PixelOffsetMode = PixelOffsetMode.HighQuality;
                    g.Clear(Color.Transparent);
                    float k = sz / 16f;
                    var rc = new RectangleF(0.5f * k, 0.5f * k, 15f * k, 15f * k);
                    using (var p = OsdRenderer.RoundRect(rc, 3.5f * k))
                    {
                        if (on)
                            using (var b = new SolidBrush(Color.FromArgb(255, 30, 130, 245))) g.FillPath(b, p);
                        else
                        {
                            using (var b = new SolidBrush(Color.FromArgb(255, 70, 72, 78))) g.FillPath(b, p);
                        }
                    }
                    float gw = 9f * k, gh = 10f * k, x = (sz - gw) / 2, y = 2.6f * k;
                    Func<float, float, PointF> P = (u, v) => new PointF(x + u * gw, y + v * gh);
                    using (var arrow = new GraphicsPath())
                    using (var b = new SolidBrush(on ? Color.White : Color.FromArgb(215, 255, 255, 255)))
                    {
                        arrow.AddPolygon(new[] { P(.5f, 0f), P(1f, .52f), P(.73f, .52f), P(.73f, .78f), P(.27f, .78f), P(.27f, .52f), P(0f, .52f) });
                        g.FillPath(b, arrow);
                        g.FillRectangle(b, P(.27f, .9f).X, P(.27f, .9f).Y, gw * .46f, 1.4f * k);
                    }
                }
                IntPtr h = bmp.GetHicon();
                var ico = (Icon)Icon.FromHandle(h).Clone();
                Native.DestroyIcon(h);
                return ico;
            }
        }
    }

    // ------------------------------------------------------------------ Win32
    static class Native
    {
        public const int WH_KEYBOARD_LL = 13;
        public delegate IntPtr LowLevelKeyboardProc(int nCode, IntPtr wParam, IntPtr lParam);

        public static bool IsCapsOn() { return (GetKeyState(0x14) & 0x0001) != 0; }

        [DllImport("user32.dll")] public static extern short GetKeyState(int nVirtKey);
        [DllImport("user32.dll", SetLastError = true)] public static extern IntPtr SetWindowsHookEx(int idHook, LowLevelKeyboardProc fn, IntPtr hMod, uint threadId);
        [DllImport("user32.dll")] public static extern bool UnhookWindowsHookEx(IntPtr hhk);
        [DllImport("user32.dll")] public static extern IntPtr CallNextHookEx(IntPtr hhk, int nCode, IntPtr wParam, IntPtr lParam);
        [DllImport("kernel32.dll", CharSet = CharSet.Unicode)] public static extern IntPtr GetModuleHandle(string name);
        [DllImport("user32.dll")] public static extern bool SetProcessDPIAware();
        [DllImport("user32.dll")] public static extern bool ShowWindow(IntPtr hWnd, int nCmdShow);
        [DllImport("user32.dll")] public static extern bool SetWindowPos(IntPtr hWnd, IntPtr after, int x, int y, int cx, int cy, uint flags);
        [DllImport("user32.dll")] public static extern bool DestroyIcon(IntPtr h);

        [DllImport("user32.dll")] public static extern IntPtr GetDC(IntPtr hWnd);
        [DllImport("user32.dll")] public static extern int ReleaseDC(IntPtr hWnd, IntPtr hDC);
        [DllImport("gdi32.dll")] public static extern IntPtr CreateCompatibleDC(IntPtr hDC);
        [DllImport("gdi32.dll")] public static extern bool DeleteDC(IntPtr hdc);
        [DllImport("gdi32.dll")] public static extern IntPtr SelectObject(IntPtr hDC, IntPtr hObject);
        [DllImport("gdi32.dll")] public static extern bool DeleteObject(IntPtr hObject);
        [DllImport("user32.dll", SetLastError = true)]
        public static extern bool UpdateLayeredWindow(IntPtr hwnd, IntPtr hdcDst, ref POINT pptDst, ref SIZE psize,
            IntPtr hdcSrc, ref POINT pprSrc, int crKey, ref BLENDFUNCTION pblend, int dwFlags);

        [StructLayout(LayoutKind.Sequential)] public struct POINT { public int x, y; public POINT(int x, int y) { this.x = x; this.y = y; } }
        [StructLayout(LayoutKind.Sequential)] public struct SIZE { public int cx, cy; public SIZE(int cx, int cy) { this.cx = cx; this.cy = cy; } }
        [StructLayout(LayoutKind.Sequential, Pack = 1)]
        public struct BLENDFUNCTION { public byte BlendOp, BlendFlags, SourceConstantAlpha, AlphaFormat; }
    }
}
