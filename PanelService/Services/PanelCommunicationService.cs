using ParkingAltea.PanelService.Models;
using System.Runtime.InteropServices;

namespace ParkingAltea.PanelService.Services
{
    public class PanelCommunicationService : IPanelCommunicationService
    {
        private readonly ILogger<PanelCommunicationService> _logger;
        private readonly Dictionary<string, PanelConfig> _panelConfigs;
        private readonly Dictionary<string, bool> _initializedPanels;

        public PanelCommunicationService(ILogger<PanelCommunicationService> logger)
        {
            _logger = logger;
            _initializedPanels = new Dictionary<string, bool>();
            
            _panelConfigs = new Dictionary<string, PanelConfig>
            {
                { "192.168.1.101", new PanelConfig { IP = "192.168.1.101", Name = "Panel 1", Parking = "P. Ciutat Esportiva" } },
                { "192.168.1.102", new PanelConfig { IP = "192.168.1.102", Name = "Panel 2", Parking = "P. Poble antic 1" } },
                { "192.168.1.103", new PanelConfig { IP = "192.168.1.103", Name = "Panel 3", Parking = "P. Poble antic 2" } },
                { "192.168.1.104", new PanelConfig { IP = "192.168.1.104", Name = "Panel 4", Parking = "P. Poble antic 3" } },
                { "192.168.1.105", new PanelConfig { IP = "192.168.1.105", Name = "Panel 5", Parking = "P. Poble antic 4" } },
                { "192.168.1.106", new PanelConfig { IP = "192.168.1.106", Name = "Panel 6", Parking = "P. Poble antic 5" } },
                { "192.168.1.107", new PanelConfig { IP = "192.168.1.107", Name = "Panel 7", Parking = "P. Port Altea" } },
                { "192.168.1.108", new PanelConfig { IP = "192.168.1.108", Name = "Panel 8", Parking = "P. Estació Altea" } },
                { "192.168.1.109", new PanelConfig { IP = "192.168.1.109", Name = "Panel 9", Parking = "P. Altea Hills" } },
                { "192.168.1.110", new PanelConfig { IP = "192.168.1.110", Name = "Panel 10", Parking = "P. Ciutat Esportiva" } }
            };
        }

        public async Task<PanelResponse> SendMessageAsync(string panelIP, PanelMessage message)
        {
            var stopwatch = System.Diagnostics.Stopwatch.StartNew();
            
            try
            {
                _logger.LogInformation("Enviando mensaje a panel {PanelIP}: {Message}", panelIP, message.Text);

                // Inicializar panel si no está inicializado
                if (!await InitializePanelAsync(panelIP))
                {
                    throw new Exception($"No se pudo inicializar el panel {panelIP}");
                }

                // Enviar mensaje usando la DLL CP5200
                var result = await SendTextViaDLLAsync(panelIP, message);
                
                stopwatch.Stop();
                
                return new PanelResponse
                {
                    Success = result >= 0,
                    Message = result >= 0 ? "Mensaje enviado correctamente" : $"Error enviando mensaje (código: {result})",
                    ErrorCode = result,
                    ResponseTime = stopwatch.ElapsedMilliseconds,
                    Timestamp = DateTime.UtcNow
                };
            }
            catch (Exception ex)
            {
                stopwatch.Stop();
                _logger.LogError(ex, "Error enviando mensaje a panel {PanelIP}", panelIP);
                
                return new PanelResponse
                {
                    Success = false,
                    Message = $"Error: {ex.Message}",
                    ErrorCode = -1,
                    ResponseTime = stopwatch.ElapsedMilliseconds,
                    Timestamp = DateTime.UtcNow
                };
            }
        }

        public async Task<PanelResponse> SendOccupancyAsync(PanelOccupancy occupancy)
        {
            try
            {
                _logger.LogInformation("Enviando ocupación a panel {PanelIP}: {Current}/{Total} - {Status}", 
                    occupancy.IP, occupancy.Current, occupancy.Total, occupancy.Status);

                // Determinar color basado en el estado
                var color = DetermineOccupancyColor(occupancy.Status);
                
                // Construir mensaje de ocupación
                var message = new PanelMessage
                {
                    Text = $"{occupancy.ParkingName}\n{occupancy.Current}/{occupancy.Total} - {occupancy.Status}",
                    Color = color,
                    FontSize = occupancy.FontSize,
                    Speed = occupancy.Speed,
                    Effect = PanelEffects.None,
                    StayTime = 10,
                    Alignment = occupancy.Alignment
                };

                return await SendMessageAsync(occupancy.IP, message);
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Error enviando ocupación a panel {PanelIP}", occupancy.IP);
                
                return new PanelResponse
                {
                    Success = false,
                    Message = $"Error: {ex.Message}",
                    ErrorCode = -1,
                    ResponseTime = 0,
                    Timestamp = DateTime.UtcNow
                };
            }
        }

        public async Task<BroadcastResponse> BroadcastAsync(BroadcastRequest request)
        {
            var results = new List<PanelResponse>();
            var panelIPs = request.SendToAll ? _panelConfigs.Keys.ToList() : request.PanelIPs ?? new List<string>();

            foreach (var panelIP in panelIPs)
            {
                var message = new PanelMessage
                {
                    Text = request.Message,
                    Color = request.Color,
                    FontSize = request.FontSize,
                    Speed = request.Speed,
                    Effect = PanelEffects.None,
                    StayTime = 5,
                    Alignment = request.Alignment
                };

                var response = await SendMessageAsync(panelIP, message);
                results.Add(response);
            }

            return new BroadcastResponse
            {
                TotalPanels = panelIPs.Count,
                SuccessCount = results.Count(r => r.Success),
                FailureCount = results.Count(r => !r.Success),
                Results = results,
                Timestamp = DateTime.UtcNow
            };
        }

        public async Task<PanelResponse> TestPanelAsync(string panelIP)
        {
            try
            {
                _logger.LogInformation("Testeando conectividad del panel {PanelIP}", panelIP);

                // Enviar mensaje de prueba
                var testMessage = new PanelMessage
                {
                    Text = "TEST CONNECTION",
                    Color = PanelColors.Yellow,
                    FontSize = 16,
                    Speed = PanelSpeed.Normal,
                    Effect = PanelEffects.Blink,
                    StayTime = 2,
                    Alignment = PanelAlignment.Center
                };

                return await SendMessageAsync(panelIP, testMessage);
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Error testeando panel {PanelIP}", panelIP);
                
                return new PanelResponse
                {
                    Success = false,
                    Message = $"Error: {ex.Message}",
                    ErrorCode = -1,
                    ResponseTime = 0,
                    Timestamp = DateTime.UtcNow
                };
            }
        }

        public async Task<PanelStatus> GetPanelStatusAsync(string panelIP)
        {
            try
            {
                var isOnline = await TestConnectivityAsync(panelIP);
                
                return new PanelStatus
                {
                    IP = panelIP,
                    Name = _panelConfigs.ContainsKey(panelIP) ? _panelConfigs[panelIP].Name : "Panel Desconocido",
                    Online = isOnline,
                    Status = isOnline ? "ONLINE" : "OFFLINE",
                    LastCommunication = DateTime.UtcNow,
                    ResponseTime = isOnline ? 50 : 0
                };
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Error obteniendo estado del panel {PanelIP}", panelIP);
                
                return new PanelStatus
                {
                    IP = panelIP,
                    Name = "Error",
                    Online = false,
                    Status = "ERROR",
                    LastCommunication = DateTime.UtcNow,
                    ResponseTime = 0
                };
            }
        }

        public async Task<PanelResponse> SendStaticTextAsync(string panelIP, string text, int x, int y, int width, int height)
        {
            try
            {
                _logger.LogInformation("Enviando texto estático a panel {PanelIP}: {Text}", panelIP, text);

                // Inicializar panel si no está inicializado
                if (!await InitializePanelAsync(panelIP))
                {
                    throw new Exception($"No se pudo inicializar el panel {panelIP}");
                }

                // Enviar texto estático usando la DLL CP5200
                var result = await SendStaticTextViaDLLAsync(panelIP, text, x, y, width, height);
                
                return new PanelResponse
                {
                    Success = result >= 0,
                    Message = result >= 0 ? "Texto estático enviado correctamente" : $"Error enviando texto estático (código: {result})",
                    ErrorCode = result,
                    ResponseTime = 0,
                    Timestamp = DateTime.UtcNow
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
                    ResponseTime = 0,
                    Timestamp = DateTime.UtcNow
                };
            }
        }

        private async Task<bool> InitializePanelAsync(string panelIP)
        {
            if (_initializedPanels.ContainsKey(panelIP) && _initializedPanels[panelIP])
            {
                return true;
            }

            try
            {
                var panelIPUInt = CP5200Wrapper.IPToUInt(panelIP);
                if (panelIPUInt == 0)
                {
                    _logger.LogError("IP inválida: {PanelIP}", panelIP);
                    return false;
                }

                // Inicializar usando la DLL CP5200
                var result = CP5200Wrapper.CP5200_Net_Init(
                    panelIPUInt,
                    CP5200Wrapper.DefaultConfig.Port,
                    CP5200Wrapper.DefaultConfig.IDCode,
                    CP5200Wrapper.DefaultConfig.Timeout
                );

                if (result >= 0)
                {
                    _initializedPanels[panelIP] = true;
                    _logger.LogInformation("Panel {PanelIP} inicializado correctamente", panelIP);
                    return true;
                }
                else
                {
                    _logger.LogError("Error inicializando panel {PanelIP}: código {Result}", panelIP, result);
                    return false;
                }
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Excepción inicializando panel {PanelIP}", panelIP);
                return false;
            }
        }

        private async Task<int> SendTextViaDLLAsync(string panelIP, PanelMessage message)
        {
            try
            {
                var panelIPUInt = CP5200Wrapper.IPToUInt(panelIP);
                if (panelIPUInt == 0)
                {
                    return -1;
                }

                // Convertir texto a puntero
                var textPtr = Marshal.StringToHGlobalAnsi(message.Text);

                try
                {
                    // Enviar usando la DLL CP5200
                    var result = CP5200Wrapper.CP5200_Net_SendTagText(
                        CP5200Wrapper.DefaultConfig.CardID,
                        CP5200Wrapper.DefaultConfig.WindowNo,
                        textPtr,
                        message.Color,
                        message.FontSize,
                        message.Speed,
                        message.Effect,
                        message.StayTime,
                        message.Alignment
                    );

                    _logger.LogDebug("Envío a panel {PanelIP}: resultado {Result}", panelIP, result);
                    return result;
                }
                finally
                {
                    // Liberar memoria del puntero
                    Marshal.FreeHGlobal(textPtr);
                }
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Error enviando texto via DLL a panel {PanelIP}", panelIP);
                return -1;
            }
        }

        private async Task<int> SendStaticTextViaDLLAsync(string panelIP, string text, int x, int y, int width, int height)
        {
            try
            {
                var panelIPUInt = CP5200Wrapper.IPToUInt(panelIP);
                if (panelIPUInt == 0)
                {
                    return -1;
                }

                // Convertir texto a puntero
                var textPtr = Marshal.StringToHGlobalAnsi(text);

                try
                {
                    // Enviar texto estático usando la DLL CP5200
                    var result = CP5200Wrapper.CP5200_Net_SendStatic(
                        CP5200Wrapper.DefaultConfig.CardID,
                        CP5200Wrapper.DefaultConfig.WindowNo,
                        textPtr,
                        PanelColors.White, // Color por defecto
                        16, // Tamaño de fuente por defecto
                        5, // Alineación centro
                        x, y, width, height
                    );

                    _logger.LogDebug("Envío estático a panel {PanelIP}: resultado {Result}", panelIP, result);
                    return result;
                }
                finally
                {
                    // Liberar memoria del puntero
                    Marshal.FreeHGlobal(textPtr);
                }
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Error enviando texto estático via DLL a panel {PanelIP}", panelIP);
                return -1;
            }
        }

        private int DetermineOccupancyColor(string status)
        {
            return status.ToUpper() switch
            {
                "LLIURE" => PanelColors.Green,
                "DENS" => PanelColors.Yellow,
                "COMPLET" => PanelColors.Red,
                _ => PanelColors.White
            };
        }

        private async Task<bool> TestConnectivityAsync(string panelIP)
        {
            try
            {
                // Probar conectividad intentando inicializar el panel
                return await InitializePanelAsync(panelIP);
            }
            catch
            {
                return false;
            }
        }
    }
} 