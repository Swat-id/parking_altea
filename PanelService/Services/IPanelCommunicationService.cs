using ParkingAltea.PanelService.Models;

namespace ParkingAltea.PanelService.Services
{
    public interface IPanelCommunicationService
    {
        Task<PanelResponse> SendMessageAsync(string panelIP, PanelMessage message);
        Task<PanelResponse> SendTextAsync(string panelIP, string text);
        Task<PanelResponse> SendOccupancyAsync(PanelOccupancy occupancy);
        Task<PanelResponse> SendStaticTextAsync(string panelIP, string text, int x = 0, int y = 0, int width = 64, int height = 32);
        Task<PanelStatus> GetPanelStatusAsync(string panelIP);
        Task<bool> IsPanelOnlineAsync(string panelIP);
        Task<PanelResponse> TestPanelAsync(string panelIP);
        Task<BroadcastResponse> BroadcastAsync(BroadcastRequest request);
        Task<List<PanelStatus>> GetAllPanelsStatusAsync();
    }
} 