using ParkingAltea.PanelService.Models;

namespace ParkingAltea.PanelService.Services
{
    public interface IPanelManager
    {
        Task InitializeAsync();
        Task<PanelResponse> SendToPanelAsync(string panelIP, string message);
        Task<PanelResponse> SendOccupancyToPanelAsync(string panelIP, int current, int total, string status);
        Task<BroadcastResponse> BroadcastToAllAsync(string message);
        Task<List<PanelStatus>> GetAllPanelsStatusAsync();
        Task<bool> IsPanelOnlineAsync(string panelIP);
    }
} 