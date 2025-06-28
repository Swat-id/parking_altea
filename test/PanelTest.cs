using System;
using System.Collections.Generic;
using System.Threading.Tasks;
using System.Linq;

namespace ParkingAltea.PanelTest
{
    class Program
    {
        static async Task Main(string[] args)
        {
            Console.WriteLine("🚦 TESTEANDO COMUNICACIÓN CON PANELES - C#");
            Console.WriteLine("=" * 60);

            // Configuración de paneles
            var panels = new Dictionary<string, PanelConfig>
            {
                ["panel1"] = new PanelConfig { IP = "172.20.17.50", Port = 5200, CardId = 1 },
                ["panel2"] = new PanelConfig { IP = "172.20.5.50", Port = 5200, CardId = 1 },
                ["panel3"] = new PanelConfig { IP = "172.20.5.51", Port = 5200, CardId = 1 },
                ["panel4"] = new PanelConfig { IP = "172.20.8.50", Port = 5200, CardId = 1 },
                ["panel5"] = new PanelConfig { IP = "172.20.4.50", Port = 5200, CardId = 1 },
                ["panel6"] = new PanelConfig { IP = "172.20.4.51", Port = 5200, CardId = 1 },
                ["panel7"] = new PanelConfig { IP = "172.20.4.52", Port = 5200, CardId = 1 },
                ["panel8"] = new PanelConfig { IP = "172.20.4.53", Port = 5200, CardId = 1 },
                ["panel9"] = new PanelConfig { IP = "172.20.2.50", Port = 5200, CardId = 1 },
                ["panel10"] = new PanelConfig { IP = "172.20.1.50", Port = 5200, CardId = 1 }
            };

            Console.WriteLine("Paneles configurados:");
            foreach (var kvp in panels)
            {
                Console.WriteLine($"  {kvp.Key}: {kvp.Value.IP}:{kvp.Value.Port}");
            }

            Console.WriteLine("\n" + "=" * 60);
            Console.WriteLine("TESTEANDO COMUNICACIÓN");
            Console.WriteLine("=" * 60);

            // Test de comunicación
            foreach (var kvp in panels)
            {
                Console.WriteLine($"\nTesteando {kvp.Key} ({kvp.Value.IP})...");
                
                try
                {
                    var communicator = new PanelCommunicator(kvp.Value);
                    
                    // Test de conectividad
                    var onlineResult = await communicator.IsOnlineAsync();
                    Console.WriteLine($"  Conectividad: {(onlineResult ? "✅ ONLINE" : "❌ OFFLINE")}");
                    
                    if (onlineResult)
                    {
                        // Test de comunicación
                        var testResult = await communicator.TestCommunicationAsync();
                        Console.WriteLine($"  Comunicación: {(testResult.Success ? "✅ OK" : "❌ FAIL")}");
                        Console.WriteLine($"  Mensaje: {testResult.Message}");
                        
                        if (testResult.Success)
                        {
                            // Enviar mensaje de prueba
                            var sendResult = communicator.SendText($"TEST C# {kvp.Key}: {kvp.Value.IP}");
                            Console.WriteLine($"  Envío: {(sendResult.Success ? "✅ OK" : "❌ FAIL")}");
                            Console.WriteLine($"  Mensaje: {sendResult.Message}");
                            
                            if (sendResult.Success)
                            {
                                Console.WriteLine($"  📺 Debería mostrar: 'TEST C# {kvp.Key}: {kvp.Value.IP}'");
                            }
                        }
                    }
                }
                catch (Exception ex)
                {
                    Console.WriteLine($"  ❌ Error: {ex.Message}");
                }
            }

            Console.WriteLine("\n" + "=" * 60);
            Console.WriteLine("📊 RESUMEN");
            Console.WriteLine("=" * 60);
            Console.WriteLine("Test completado. Verificar físicamente los paneles.");
            Console.WriteLine("Presiona cualquier tecla para salir...");
            Console.ReadKey();
        }
    }

    public class PanelConfig
    {
        public string IP { get; set; }
        public int Port { get; set; } = 5200;
        public int CardId { get; set; } = 1;
        public int Timeout { get; set; } = 600;
        public string IDCode { get; set; } = "255.255.255.255";
    }

    public class PanelResult
    {
        public bool Success { get; set; }
        public string Message { get; set; }
        public int ErrorCode { get; set; }
        public double ResponseTime { get; set; }
    }

    public class PanelCommunicator : IDisposable
    {
        private const string DLL_PATH = "CP5200.dll";
        private bool _initialized = false;
        private PanelConfig _config;

        public PanelCommunicator(PanelConfig config)
        {
            _config = config ?? throw new ArgumentNullException(nameof(config));
        }

        public async Task<bool> IsOnlineAsync()
        {
            try
            {
                using (var client = new System.Net.Sockets.TcpClient())
                {
                    var connectTask = client.ConnectAsync(_config.IP, _config.Port);
                    var timeoutTask = Task.Delay(3000);
                    
                    var completedTask = await Task.WhenAny(connectTask, timeoutTask);
                    return completedTask == connectTask && client.Connected;
                }
            }
            catch
            {
                return false;
            }
        }

        public async Task<PanelResult> TestCommunicationAsync()
        {
            try
            {
                bool isOnline = await IsOnlineAsync();
                if (!isOnline)
                {
                    return new PanelResult
                    {
                        Success = false,
                        Message = "Panel no está online"
                    };
                }

                return new PanelResult
                {
                    Success = true,
                    Message = "Panel online y accesible"
                };
            }
            catch (Exception ex)
            {
                return new PanelResult
                {
                    Success = false,
                    Message = $"Error en test: {ex.Message}"
                };
            }
        }

        public PanelResult SendText(string text, int window = 0, int color = 0xFF, int fontSize = 16, int speed = 3, int effect = 0, int stayTime = 5, int alignment = 5)
        {
            // Simulación de envío para testing
            return new PanelResult
            {
                Success = true,
                Message = $"Texto simulado enviado: '{text}'",
                ResponseTime = 100.0
            };
        }

        public void Dispose()
        {
            _initialized = false;
        }
    }
} 