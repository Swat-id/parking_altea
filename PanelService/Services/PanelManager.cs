using ParkingAltea.PanelService.Models;
using Microsoft.Extensions.Logging;

namespace ParkingAltea.PanelService.Services
{
    public class PanelManager : IPanelManager
    {
        private readonly IPanelCommunicationService _communicationService;
        private readonly ILogger<PanelManager> _logger;
        private readonly List<PanelConfig> _panels;

        public PanelManager(IPanelCommunicationService communicationService, ILogger<PanelManager> logger)
        {
            _communicationService = communicationService;
            _logger = logger;
            
            // Configurar paneles
            _panels = new List<PanelConfig>
            {
                new PanelConfig { IP = "172.20.17.50", Name = "PANEL C. ESPORTIVA", Parking = "1 - P. Ciutat Esportiva" },
                new PanelConfig { IP = "172.20.5.50", Name = "PANEL BASSETA 1", Parking = "2 - P. Basseta Centre" },
                new PanelConfig { IP = "172.20.5.51", Name = "PANEL BASSETA 2", Parking = "2 - P. Basseta Centre" },
                new PanelConfig { IP = "172.20.8.50", Name = "PANEL PITERES", Parking = "6 - P. Poble antic/Conservatori" },
                new PanelConfig { IP = "172.20.4.50", Name = "PANEL PALAU", Parking = "5 - P. Poble antic/Palau Altea" },
                new PanelConfig { IP = "172.20.4.51", Name = "PANEL COCOLISO", Parking = "5 - P. Poble antic/Palau Altea" },
                new PanelConfig { IP = "172.20.4.52", Name = "BELLES ARTS 2", Parking = "4 - P. Poble antic/Belles Arts 2" },
                new PanelConfig { IP = "172.20.4.53", Name = "BELLES ARTS", Parking = "3 - P. Poble antic/Belles Arts 1" },
                new PanelConfig { IP = "172.20.2.50", Name = "PANEL RENFE", Parking = "8 - P. Estació Altea" },
                new PanelConfig { IP = "172.20.1.50", Name = "PANEL ALTEA VELLA", Parking = "9 - P. Altea la Vella" }
            };
        }

        public async Task InitializeAsync()
        {
            _logger.LogInformation("Inicializando Panel Manager con {Count} paneles", _panels.Count);
            
            foreach (var panel in _panels)
            {
                _logger.LogInformation("Panel configurado: {Name} ({IP}) - {Parking}", panel.Name, panel.IP, panel.Parking);
            }
        }

        public async Task<PanelResponse> SendToPanelAsync(string panelIP, string message)
        {
            return await _communicationService.SendTextAsync(panelIP, message);
        }

        public async Task<PanelResponse> SendOccupancyToPanelAsync(string panelIP, int current, int total, string status)
        {
            var panel = _panels.FirstOrDefault(p => p.IP == panelIP);
            var parkingName = panel?.Parking ?? "Parking";
            
            var occupancy = new PanelOccupancy
            {
                IP = panelIP,
                Current = current,
                Total = total,
                Status = status,
                ParkingName = parkingName
            };
            
            return await _communicationService.SendOccupancyAsync(occupancy);
        }

        public async Task<BroadcastResponse> BroadcastToAllAsync(string message)
        {
            var request = new BroadcastRequest
            {
                Message = message,
                SendToAll = true
            };
            
            return await _communicationService.BroadcastAsync(request);
        }

        public async Task<List<PanelStatus>> GetAllPanelsStatusAsync()
        {
            return await _communicationService.GetAllPanelsStatusAsync();
        }

        public async Task<bool> IsPanelOnlineAsync(string panelIP)
        {
            return await _communicationService.IsPanelOnlineAsync(panelIP);
        }
    }
} 