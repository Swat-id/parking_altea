using System.Runtime.InteropServices;
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

                // Inicializar panel si es necesario
                if (!await InitializePanelAsync(panelIP))
                {
                    return new PanelResponse
                    {
                        Success = false,
                        Message = "No se pudo inicializar el panel",
                        ErrorCode = -1
                    };
                }

                // Enviar mensaje usando CP5200
                var result = SendTextToPanel(panelIP, message);
                
                var responseTime = (DateTime.UtcNow - startTime).TotalMilliseconds;
                
                return new PanelResponse
                {
                    Success = result >= 0,
                    Message = result >= 0 ? "Mensaje enviado exitosamente" : $"Error al enviar mensaje (código: {result})",
                    ErrorCode = result,
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

                if (!await InitializePanelAsync(panelIP))
                {
                    return new PanelResponse
                    {
                        Success = false,
                        Message = "No se pudo inicializar el panel",
                        ErrorCode = -1
                    };
                }

                var result = SendStaticTextToPanel(panelIP, text, x, y, width, height);
                
                var responseTime = (DateTime.UtcNow - startTime).TotalMilliseconds;
                
                return new PanelResponse
                {
                    Success = result >= 0,
                    Message = result >= 0 ? "Texto estático enviado exitosamente" : $"Error al enviar texto estático (código: {result})",
                    ErrorCode = result,
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
                using var client = new System.Net.Sockets.TcpClient();
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

        private async Task<bool> InitializePanelAsync(string panelIP)
        {
            lock (_lock)
            {
                if (_initializedPanels.ContainsKey(panelIP))
                {
                    return _initializedPanels[panelIP];
                }
            }

            try
            {
                var config = GetPanelConfig(panelIP);
                var result = CP5200_Net_Init(config.IP, config.Port, config.IDCode, config.Timeout);
                
                var success = result >= 0;
                
                lock (_lock)
                {
                    _initializedPanels[panelIP] = success;
                }

                _logger.LogInformation("Inicialización panel {PanelIP}: {Result}", panelIP, success ? "OK" : "FAIL");
                return success;
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Error inicializando panel {PanelIP}", panelIP);
                
                lock (_lock)
                {
                    _initializedPanels[panelIP] = false;
                }
                
                return false;
            }
        }

        private int SendTextToPanel(string panelIP, PanelMessage message)
        {
            try
            {
                var config = GetPanelConfig(panelIP);
                var textPtr = Marshal.StringToHGlobalAnsi(message.Text);
                
                var result = CP5200_Net_SendText(
                    config.CardId,
                    message.Window,
                    textPtr,
                    message.Color,
                    message.FontSize,
                    message.Speed,
                    message.Effect,
                    message.StayTime,
                    message.Alignment
                );
                
                Marshal.FreeHGlobal(textPtr);
                return result;
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Error enviando texto a panel {PanelIP}", panelIP);
                return -1;
            }
        }

        private int SendStaticTextToPanel(string panelIP, string text, int x, int y, int width, int height)
        {
            try
            {
                var config = GetPanelConfig(panelIP);
                var textPtr = Marshal.StringToHGlobalAnsi(text);
                
                var result = CP5200_Net_SendStatic(
                    config.CardId,
                    0, // window
                    textPtr,
                    0xFF, // color
                    16, // fontSize
                    0, // alignment
                    x, y, width, height
                );
                
                Marshal.FreeHGlobal(textPtr);
                return result;
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Error enviando texto estático a panel {PanelIP}", panelIP);
                return -1;
            }
        }

        private PanelConfig GetPanelConfig(string panelIP)
        {
            return new PanelConfig
            {
                IP = panelIP,
                Port = 5200,
                CardId = 1,
                Timeout = 600,
                IDCode = "255.255.255.255"
            };
        }

        private List<string> GetAllPanelIPs()
        {
            return new List<string>
            {
                "172.20.17.50", "172.20.5.50", "172.20.5.51", "172.20.8.50", "172.20.4.50",
                "172.20.4.51", "172.20.4.52", "172.20.4.53", "172.20.2.50", "172.20.1.50"
            };
        }

        // CP5200 DLL Imports
        [DllImport("CP5200.dll")]
        private static extern int CP5200_Net_Init(uint dwIP, int nIPPort, uint dwIDCode, int nTimeOut);

        [DllImport("CP5200.dll")]
        private static extern int CP5200_Net_SendText(int nCardID, int nWndNo, IntPtr pText, int crColor, int nFontSize, int nSpeed, int nEffect, int nStayTime, int nAlignment);

        [DllImport("CP5200.dll")]
        private static extern int CP5200_Net_SendStatic(int nCardID, int nWndNo, IntPtr pText, int crColor, int nFontSize, int nAlignment, int x, int y, int cx, int cy);
    }
} 