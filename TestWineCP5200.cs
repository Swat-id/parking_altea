using System;
using System.Runtime.InteropServices;

class TestCP5200
{
    [DllImport("CP5200.dll")]
    public static extern int CP5200_Net_Init(uint dwIP, int nIPPort, uint dwIDCode, int nTimeOut);
    
    [DllImport("CP5200.dll")]
    public static extern int CP5200_Net_SendText(uint dwIP, string lpText, int nColor, int nFontSize, int nSpeed, int nEffect, int nStayTime, int nAlignment);

    static int Main()
    {
        try
        {
            Console.WriteLine("Iniciando prueba de CP5200 con Wine...");
            
            // Convertir IP a formato requerido
            uint panelIP = 0x321412AC; // 172.20.17.50 en formato little-endian
            uint idCode = 0xFFFFFFFF; // 255.255.255.255
            
            Console.WriteLine($"Panel IP: {panelIP:X8}");
            Console.WriteLine($"ID Code: {idCode:X8}");
            
            // Probar inicialización
            Console.WriteLine("Probando CP5200_Net_Init...");
            int initResult = CP5200_Net_Init(panelIP, 5200, idCode, 600);
            Console.WriteLine($"Resultado Init: {initResult}");
            
            if (initResult == 1)
            {
                Console.WriteLine("Inicialización exitosa, probando SendText...");
                
                // Probar envío de texto
                int sendResult = CP5200_Net_SendText(panelIP, "TEST WINE", 3000, 16, 3, 0, 0, 0);
                Console.WriteLine($"Resultado SendText: {sendResult}");
                
                return sendResult;
            }
            else
            {
                Console.WriteLine($"Error en inicialización: {initResult}");
                return initResult;
            }
        }
        catch (Exception ex)
        {
            Console.WriteLine($"Error: {ex.Message}");
            return -1;
        }
    }
} 