using System.Runtime.InteropServices;

namespace ParkingAltea.PanelService
{
    public class CP5200Wrapper
    {
        private const string DLL_PATH = "CP5200.dll";

        // Inicialización de red
        [DllImport(DLL_PATH, CharSet = CharSet.Auto)]
        public static extern int CP5200_Net_Init(uint dwIP, int nIPPort, uint dwIDCode, int nTimeOut);

        // Envío de texto con etiquetas
        [DllImport(DLL_PATH, CharSet = CharSet.Auto)]
        public static extern int CP5200_Net_SendTagText(int nCardID, int nWndNo, IntPtr pText, int crColor, int nFontSize, int nSpeed, int nEffect, int nStayTime, int nAlignment);

        // Envío de texto estático
        [DllImport(DLL_PATH, CharSet = CharSet.Auto)]
        public static extern int CP5200_Net_SendStatic(int nCardID, int nWndNo, IntPtr pText, int crColor, int nFontSize, int nAlignment, int x, int y, int cx, int cy);

        // Configuración de pantalla
        [DllImport(DLL_PATH, CharSet = CharSet.Auto)]
        public static extern int CP5200_Net_SplitScreen(int nCardID, int nScrWidth, int nScrHeight, int nWndCnt, int[] pWndRects);

        // Configuración de tiempo
        [DllImport(DLL_PATH, CharSet = CharSet.Auto)]
        public static extern int CP5200_Net_SetTime(byte nCardID, byte[] pInfo);

        // Reproducción de programas
        [DllImport(DLL_PATH, CharSet = CharSet.Auto)]
        public static extern int CP5200_Net_PlaySelectedPrg(int nCardID, int[] pSelected, int nSelCnt, int nOption);

        // Conversión de IP a uint con byte swapping correcto (según ejemplo del fabricante)
        public static uint IPToUInt(string ipAddress)
        {
            try
            {
                System.Net.IPAddress ipaddress = System.Net.IPAddress.Parse(ipAddress);
                uint lIp = (uint)ipaddress.Address;
                lIp = ((lIp & 0xFF000000) >> 24) + ((lIp & 0x00FF0000) >> 8) + 
                      ((lIp & 0x0000FF00) << 8) + ((lIp & 0x000000FF) << 24);
                return lIp;
            }
            catch
            {
                return 0;
            }
        }

        // Configuración por defecto
        public static class DefaultConfig
        {
            public const int CardID = 1;
            public const int WindowNo = 0;
            public const int Port = 5200;
            public const int Timeout = 3000;
            public const uint IDCode = 0xFFFFFFFF; // 255.255.255.255
            public const int ScreenWidth = 64;
            public const int ScreenHeight = 32;
        }
    }
} 