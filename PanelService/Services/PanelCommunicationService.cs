using ParkingAltea.PanelService.Models;
using System.Runtime.InteropServices;

namespace ParkingAltea.PanelService.Services
{
    public class PanelCommunicationService : IPanelCommunicationService
    {
        private readonly ILogger<PanelCommunicationService> _logger;
        private readonly Dictionary<string, PanelConfig> _panelConfigs;
        private readonly Dictionary<string, bool> _initializedPanels;
        private readonly Dictionary<string, bool> _splitScreenDone; // Cache para SplitScreen

        public PanelCommunicationService(ILogger<PanelCommunicationService> logger)
        {
            _logger = logger;
            _initializedPanels = new Dictionary<string, bool>();
            _splitScreenDone = new Dictionary<string, bool>(); // Cache para SplitScreen
            
            _panelConfigs = new Dictionary<string, PanelConfig>
            {
                { "172.20.17.50", new PanelConfig { IP = "172.20.17.50", Name = "PANEL C. ESPORTIVA", Parking = "P. Ciutat Esportiva" } },
                { "172.20.5.50", new PanelConfig { IP = "172.20.5.50", Name = "PANEL BASSETA 1", Parking = "P. Poble antic 1" } },
                { "172.20.5.51", new PanelConfig { IP = "172.20.5.51", Name = "PANEL BASSETA 2", Parking = "P. Poble antic 2" } },
                { "172.20.8.50", new PanelConfig { IP = "172.20.8.50", Name = "PANEL PITERES", Parking = "P. Poble antic 3" } },
                { "172.20.4.50", new PanelConfig { IP = "172.20.4.50", Name = "PANEL PALAU", Parking = "P. Poble antic 4" } },
                { "172.20.4.51", new PanelConfig { IP = "172.20.4.51", Name = "PANEL COCOLISO", Parking = "P. Poble antic 5" } },
                { "172.20.4.52", new PanelConfig { IP = "172.20.4.52", Name = "BELLES ARTS 2", Parking = "P. Port Altea" } },
                { "172.20.4.53", new PanelConfig { IP = "172.20.4.53", Name = "BELLES ARTS", Parking = "P. Estació Altea" } },
                { "172.20.2.50", new PanelConfig { IP = "172.20.2.50", Name = "PANEL RENFE", Parking = "P. Altea Hills" } },
                { "172.20.1.50", new PanelConfig { IP = "172.20.1.50", Name = "PANEL ALTEA VELLA", Parking = "P. Ciutat Esportiva" } }
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

                // 1. Inicializar panel si no está inicializado
                if (!await InitializePanelAsync(panelIP))
                {
                    return -1;
                }

                // 2. Configurar SplitScreen UNA VEZ por panel (según ejemplo del fabricante)
                if (!_splitScreenDone.ContainsKey(panelIP) || !_splitScreenDone[panelIP])
                {
                    int[] windowRect = new int[4] { 0, 0, CP5200Wrapper.DefaultConfig.ScreenWidth, CP5200Wrapper.DefaultConfig.ScreenHeight };
                    var splitResult = CP5200Wrapper.CP5200_Net_SplitScreen(
                        CP5200Wrapper.DefaultConfig.CardID,
                        CP5200Wrapper.DefaultConfig.ScreenWidth,
                        CP5200Wrapper.DefaultConfig.ScreenHeight,
                        1, // Una ventana
                        windowRect
                    );

                    if (splitResult >= 0)
                    {
                        _splitScreenDone[panelIP] = true;
                        _logger.LogDebug("SplitScreen configurado para panel {PanelIP}", panelIP);
                    }
                    else
                    {
                        _logger.LogWarning("Error configurando SplitScreen para panel {PanelIP}: {Result}", panelIP, splitResult);
                        // Continuar de todas formas, puede que funcione sin SplitScreen
                    }
                }

                // 3. Convertir texto a puntero
                var textPtr = Marshal.StringToHGlobalAnsi(message.Text);

                try
                {
                    // 4. Enviar usando CP5200_Net_SendText (función correcta para texto básico)
                    var result = CP5200Wrapper.CP5200_Net_SendText(
                        CP5200Wrapper.DefaultConfig.CardID,  // CardID = 1
                        CP5200Wrapper.DefaultConfig.WindowNo, // Window = 0
                        textPtr,                              // Texto
                        message.Color,                        // Color
                        message.FontSize,                     // FontSize = 16
                        message.Speed,                        // Speed = 3
                        message.Effect,                       // Effect = 0
                        message.StayTime,                     // StayTime = 0 (permanente)
                        message.Alignment                     // Alignment = 0
                    );

                    _logger.LogDebug("Envío SendText a panel {PanelIP}: resultado {Result}", panelIP, result);
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

                // Primero configurar la pantalla dividida (SplitScreen) como en el ejemplo del SDK
                int[] windowRect = new int[4] { 0, 0, CP5200Wrapper.DefaultConfig.ScreenWidth, CP5200Wrapper.DefaultConfig.ScreenHeight };
                var splitResult = CP5200Wrapper.CP5200_Net_SplitScreen(
                    CP5200Wrapper.DefaultConfig.CardID,
                    CP5200Wrapper.DefaultConfig.ScreenWidth,
                    CP5200Wrapper.DefaultConfig.ScreenHeight,
                    1, // Una ventana
                    windowRect
                );

                if (splitResult < 0)
                {
                    _logger.LogWarning("Error configurando SplitScreen para texto estático en panel {PanelIP}: {Result}", panelIP, splitResult);
                    // Continuar de todas formas, puede que funcione sin SplitScreen
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
                "LLIURE" => PanelColors.Green,    // Verde: 0x00FF00 (65280)
                "DENS" => PanelColors.Orange,     // Naranja: 0x0080FF (33023) 
                "COMPLET" => PanelColors.Red,     // Rojo: 0x0000FF (255)
                _ => PanelColors.White            // Blanco: 0xFFFFFF (16777215)
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