using System.ComponentModel.DataAnnotations;

namespace ParkingAltea.PanelService.Models
{
    public class PanelConfig
    {
        [Required]
        public string IP { get; set; } = string.Empty;
        
        public int Port { get; set; } = 5200;
        public int CardId { get; set; } = 1;
        public int Timeout { get; set; } = 600;
        public string IDCode { get; set; } = "255.255.255.255";
        public string Name { get; set; } = string.Empty;
        public string Parking { get; set; } = string.Empty;
    }

    public class PanelMessage
    {
        [Required]
        public string Text { get; set; } = string.Empty;
        
        public int Window { get; set; } = 0;
        public int Color { get; set; } = 0xFF0000; // Rojo por defecto
        public int FontSize { get; set; } = 16;
        public int Speed { get; set; } = 3; // Velocidad de movimiento
        public int Effect { get; set; } = 0; // 0 = sin efecto, 1 = efecto especial
        public int StayTime { get; set; } = 5; // Tiempo en segundos
        public int Alignment { get; set; } = 5; // 0 = izquierda, 5 = centro, 10 = derecha
    }

    public class PanelOccupancy
    {
        [Required]
        public string IP { get; set; } = string.Empty;
        
        public int Current { get; set; }
        public int Total { get; set; }
        public string Status { get; set; } = string.Empty; // LLIURE, DENS, COMPLET
        public string ParkingName { get; set; } = string.Empty;
        public int Color { get; set; } = 0x00FF00; // Verde por defecto
        public int FontSize { get; set; } = 16;
        public int Speed { get; set; } = 2; // Movimiento más lento para ocupación
        public int Alignment { get; set; } = 5; // Centrado
    }

    public class PanelResponse
    {
        public bool Success { get; set; }
        public string Message { get; set; } = string.Empty;
        public int ErrorCode { get; set; }
        public double ResponseTime { get; set; }
        public DateTime Timestamp { get; set; } = DateTime.UtcNow;
    }

    public class PanelStatus
    {
        public string IP { get; set; } = string.Empty;
        public string Name { get; set; } = string.Empty;
        public bool Online { get; set; }
        public string Status { get; set; } = string.Empty;
        public DateTime LastCommunication { get; set; }
        public double ResponseTime { get; set; }
    }

    public class BroadcastRequest
    {
        [Required]
        public string Message { get; set; } = string.Empty;
        
        public List<string>? PanelIPs { get; set; }
        public bool SendToAll { get; set; } = true;
        public int Color { get; set; } = 0xFFFF00; // Amarillo por defecto
        public int FontSize { get; set; } = 16;
        public int Speed { get; set; } = 3;
        public int Alignment { get; set; } = 5;
    }

    public class BroadcastResponse
    {
        public int TotalPanels { get; set; }
        public int SuccessCount { get; set; }
        public int FailureCount { get; set; }
        public List<PanelResponse> Results { get; set; } = new();
        public DateTime Timestamp { get; set; } = DateTime.UtcNow;
    }

    // Constantes para colores predefinidos
    public static class PanelColors
    {
        public const int Red = 0xFF0000;
        public const int Green = 0x00FF00;
        public const int Blue = 0x0000FF;
        public const int Yellow = 0xFFFF00;
        public const int Cyan = 0x00FFFF;
        public const int Magenta = 0xFF00FF;
        public const int White = 0xFFFFFF;
        public const int Orange = 0xFF8000;
        public const int Purple = 0x8000FF;
    }

    // Constantes para alineación
    public static class PanelAlignment
    {
        public const int Left = 0;
        public const int Center = 5;
        public const int Right = 10;
    }

    // Constantes para efectos
    public static class PanelEffects
    {
        public const int None = 0;
        public const int Blink = 1;
        public const int Scroll = 2;
        public const int Fade = 3;
    }

    // Constantes para velocidad
    public static class PanelSpeed
    {
        public const int VerySlow = 1;
        public const int Slow = 2;
        public const int Normal = 3;
        public const int Fast = 4;
        public const int VeryFast = 5;
    }
} 