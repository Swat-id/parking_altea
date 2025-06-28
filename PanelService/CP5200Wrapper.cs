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

        // Conversión de IP a uint
        public static uint IPToUInt(string ipAddress)
        {
            var parts = ipAddress.Split('.');
            if (parts.Length != 4)
                return 0;

            uint result = 0;
            for (int i = 0; i < 4; i++)
            {
                if (!uint.TryParse(parts[i], out uint part))
                    return 0;
                result = (result << 8) | part;
            }
            return result;
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