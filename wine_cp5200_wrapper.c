#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <windows.h>

// Definir las funciones de la DLL
typedef int (*CP5200_Net_Init_t)(DWORD dwIP, int nIPPort, DWORD dwIDCode, int nTimeOut);
typedef int (*CP5200_Net_SendText_t)(DWORD dwIP, LPCSTR lpText, int nColor, int nFontSize, int nSpeed, int nEffect, int nStayTime, int nAlignment);

int main(int argc, char* argv[]) {
    if (argc < 2) {
        printf("Uso: %s <comando> [parametros...]\n", argv[0]);
        printf("Comandos:\n");
        printf("  init <ip> <port> <idcode> <timeout>\n");
        printf("  sendtext <ip> <text> <color> <fontsize> <speed> <effect> <staytime> <alignment>\n");
        return 1;
    }
    
    // Cargar la DLL
    HMODULE hDll = LoadLibrary("CP5200.dll");
    if (!hDll) {
        printf("Error: No se pudo cargar CP5200.dll\n");
        return -1;
    }
    
    // Obtener las funciones
    CP5200_Net_Init_t CP5200_Net_Init = (CP5200_Net_Init_t)GetProcAddress(hDll, "CP5200_Net_Init");
    CP5200_Net_SendText_t CP5200_Net_SendText = (CP5200_Net_SendText_t)GetProcAddress(hDll, "CP5200_Net_SendText");
    
    if (!CP5200_Net_Init || !CP5200_Net_SendText) {
        printf("Error: No se pudieron encontrar las funciones en la DLL\n");
        FreeLibrary(hDll);
        return -1;
    }
    
    if (strcmp(argv[1], "init") == 0) {
        if (argc != 6) {
            printf("Error: init requiere 4 parámetros\n");
            FreeLibrary(hDll);
            return 1;
        }
        
        DWORD ip = strtoul(argv[2], NULL, 0);
        int port = atoi(argv[3]);
        DWORD idcode = strtoul(argv[4], NULL, 0);
        int timeout = atoi(argv[5]);
        
        printf("Inicializando: IP=0x%08X, Port=%d, IDCode=0x%08X, Timeout=%d\n", ip, port, idcode, timeout);
        int result = CP5200_Net_Init(ip, port, idcode, timeout);
        printf("Resultado: %d\n", result);
        
    } else if (strcmp(argv[1], "sendtext") == 0) {
        if (argc != 10) {
            printf("Error: sendtext requiere 8 parámetros\n");
            FreeLibrary(hDll);
            return 1;
        }
        
        DWORD ip = strtoul(argv[2], NULL, 0);
        char* text = argv[3];
        int color = atoi(argv[4]);
        int fontsize = atoi(argv[5]);
        int speed = atoi(argv[6]);
        int effect = atoi(argv[7]);
        int staytime = atoi(argv[8]);
        int alignment = atoi(argv[9]);
        
        printf("Enviando texto: IP=0x%08X, Text='%s', Color=%d, FontSize=%d, Speed=%d, Effect=%d, StayTime=%d, Alignment=%d\n", 
               ip, text, color, fontsize, speed, effect, staytime, alignment);
        int result = CP5200_Net_SendText(ip, text, color, fontsize, speed, effect, staytime, alignment);
        printf("Resultado: %d\n", result);
        
    } else {
        printf("Error: Comando desconocido '%s'\n", argv[1]);
        FreeLibrary(hDll);
        return 1;
    }
    
    FreeLibrary(hDll);
    return 0;
} 