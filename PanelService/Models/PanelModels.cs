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
        public int Color { get; set; } = 0xFF;
        public int FontSize { get; set; } = 16;
        public int Speed { get; set; } = 3;
        public int Effect { get; set; } = 0;
        public int StayTime { get; set; } = 5;
        public int Alignment { get; set; } = 5;
    }

    public class PanelOccupancy
    {
        [Required]
        public string IP { get; set; } = string.Empty;
        
        public int Current { get; set; }
        public int Total { get; set; }
        public string Status { get; set; } = string.Empty; // LLIURE, DENS, COMPLET
        public string ParkingName { get; set; } = string.Empty;
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
    }

    public class BroadcastResponse
    {
        public int TotalPanels { get; set; }
        public int SuccessCount { get; set; }
        public int FailureCount { get; set; }
        public List<PanelResponse> Results { get; set; } = new();
        public DateTime Timestamp { get; set; } = DateTime.UtcNow;
    }
} 