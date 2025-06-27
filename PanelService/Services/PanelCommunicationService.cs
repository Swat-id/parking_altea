using System.Net.Sockets;
using ParkingAltea.PanelService.Models;
using Microsoft.Extensions.Logging;

namespace ParkingAltea.PanelService.Services
{
    public class PanelCommunicationService : IPanelCommunicationService
    {
        private readonly ILogger<PanelCommunicationService> _logger;
        private readonly Dictionary<string, bool> _initializedPanels = new();
        private readonly object _lock = new object();

        public PanelCommunicationService(ILogger<PanelCommunicationService> logger)
        {
            _logger = logger;
        }

        public async Task<PanelResponse> SendMessageAsync(string panelIP, PanelMessage message)
        {
            var startTime = DateTime.UtcNow;
            
            try
            {
                _logger.LogInformation("Enviando mensaje a panel {PanelIP}: {Text}", panelIP, message.Text);

                // Enviar mensaje usando TCP simple
                var result = await SendTextToPanelAsync(panelIP, message.Text);
                
                var responseTime = (DateTime.UtcNow - startTime).TotalMilliseconds;
                
                return new PanelResponse
                {
                    Success = result,
                    Message = result ? "Mensaje enviado exitosamente" : "Error al enviar mensaje",
                    ErrorCode = result ? 0 : -1,
                    ResponseTime = responseTime
                };
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Error enviando mensaje a panel {PanelIP}", panelIP);
                
                return new PanelResponse
                {
                    Success = false,
                    Message = $"Error: {ex.Message}",
                    ErrorCode = -1,
                    ResponseTime = (DateTime.UtcNow - startTime).TotalMilliseconds
                };
            }
        }

        public async Task<PanelResponse> SendTextAsync(string panelIP, string text)
        {
            var message = new PanelMessage { Text = text };
            return await SendMessageAsync(panelIP, message);
        }

        public async Task<PanelResponse> SendOccupancyAsync(PanelOccupancy occupancy)
        {
            var text = $"{occupancy.ParkingName}: {occupancy.Current}/{occupancy.Total} ({occupancy.Status})";
            return await SendTextAsync(occupancy.IP, text);
        }

        public async Task<PanelResponse> SendStaticTextAsync(string panelIP, string text, int x = 0, int y = 0, int width = 64, int height = 32)
        {
            var startTime = DateTime.UtcNow;
            
            try
            {
                _logger.LogInformation("Enviando texto estático a panel {PanelIP}: {Text}", panelIP, text);

                var result = await SendTextToPanelAsync(panelIP, text);
                
                var responseTime = (DateTime.UtcNow - startTime).TotalMilliseconds;
                
                return new PanelResponse
                {
                    Success = result,
                    Message = result ? "Texto estático enviado exitosamente" : "Error al enviar texto estático",
                    ErrorCode = result ? 0 : -1,
                    ResponseTime = responseTime
                };
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Error enviando texto estático a panel {PanelIP}", panelIP);
                
                return new PanelResponse
                {
                    Success = false,
                    Message = $"Error: {ex.Message}",
                    ErrorCode = -1,
                    ResponseTime = (DateTime.UtcNow - startTime).TotalMilliseconds
                };
            }
        }

        public async Task<PanelStatus> GetPanelStatusAsync(string panelIP)
        {
            var isOnline = await IsPanelOnlineAsync(panelIP);
            
            return new PanelStatus
            {
                IP = panelIP,
                Online = isOnline,
                Status = isOnline ? "ONLINE" : "OFFLINE",
                LastCommunication = DateTime.UtcNow,
                ResponseTime = 0
            };
        }

        public async Task<bool> IsPanelOnlineAsync(string panelIP)
        {
            try
            {
                using var client = new TcpClient();
                var connectTask = client.ConnectAsync(panelIP, 5200);
                var timeoutTask = Task.Delay(3000);
                
                var completedTask = await Task.WhenAny(connectTask, timeoutTask);
                return completedTask == connectTask && client.Connected;
            }
            catch
            {
                return false;
            }
        }

        public async Task<PanelResponse> TestPanelAsync(string panelIP)
        {
            var startTime = DateTime.UtcNow;
            
            try
            {
                var isOnline = await IsPanelOnlineAsync(panelIP);
                
                if (!isOnline)
                {
                    return new PanelResponse
                    {
                        Success = false,
                        Message = "Panel no está online",
                        ErrorCode = -1
                    };
                }

                // Enviar mensaje de prueba
                var testMessage = $"TEST {DateTime.Now:HH:mm:ss}";
                var result = await SendTextAsync(panelIP, testMessage);
                
                result.ResponseTime = (DateTime.UtcNow - startTime).TotalMilliseconds;
                return result;
            }
            catch (Exception ex)
            {
                return new PanelResponse
                {
                    Success = false,
                    Message = $"Error en test: {ex.Message}",
                    ErrorCode = -1,
                    ResponseTime = (DateTime.UtcNow - startTime).TotalMilliseconds
                };
            }
        }

        public async Task<BroadcastResponse> BroadcastAsync(BroadcastRequest request)
        {
            var results = new List<PanelResponse>();
            var panelIPs = request.SendToAll ? GetAllPanelIPs() : request.PanelIPs ?? new List<string>();

            foreach (var panelIP in panelIPs)
            {
                var result = await SendTextAsync(panelIP, request.Message);
                results.Add(result);
            }

            return new BroadcastResponse
            {
                TotalPanels = panelIPs.Count,
                SuccessCount = results.Count(r => r.Success),
                FailureCount = results.Count(r => !r.Success),
                Results = results
            };
        }

        public async Task<List<PanelStatus>> GetAllPanelsStatusAsync()
        {
            var panelIPs = GetAllPanelIPs();
            var statuses = new List<PanelStatus>();

            foreach (var panelIP in panelIPs)
            {
                var status = await GetPanelStatusAsync(panelIP);
                statuses.Add(status);
            }

            return statuses;
        }

        private async Task<bool> SendTextToPanelAsync(string panelIP, string text)
        {
            try
            {
                using var client = new TcpClient();
                await client.ConnectAsync(panelIP, 5200);
                
                using var stream = client.GetStream();
                var data = System.Text.Encoding.UTF8.GetBytes(text);
                await stream.WriteAsync(data, 0, data.Length);
                
                _logger.LogInformation("Mensaje enviado a panel {PanelIP}: {Text}", panelIP, text);
                return true;
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Error enviando texto a panel {PanelIP}", panelIP);
                return false;
            }
        }

        private List<string> GetAllPanelIPs()
        {
            return new List<string>
            {
                "172.20.17.50", "172.20.5.50", "172.20.5.51", "172.20.8.50", "172.20.4.50",
                "172.20.4.51", "172.20.4.52", "172.20.4.53", "172.20.2.50", "172.20.1.50"
            };
        }
    }
} 