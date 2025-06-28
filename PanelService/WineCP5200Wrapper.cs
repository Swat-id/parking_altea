using System;
using System.Diagnostics;
using System.Threading.Tasks;

namespace ParkingAltea.PanelService
{
    public class WineCP5200Wrapper
    {
        private readonly string _winePath;
        private readonly string _dllPath;
        private readonly ILogger<WineCP5200Wrapper> _logger;

        public WineCP5200Wrapper(ILogger<WineCP5200Wrapper> logger)
        {
            _logger = logger;
            _winePath = "wine";
            _dllPath = "/opt/parking-panel-service/CP5200.dll";
        }

        public async Task<int> InitComm(uint ip, int port, uint idCode, int timeout)
        {
            try
            {
                _logger.LogDebug("Wine: Inicializando comunicación con panel IP: {IP}, Puerto: {Port}, ID: {ID}, Timeout: {Timeout}", 
                    ip, port, idCode, timeout);

                var result = await ExecuteWineFunction("InitComm", new object[] { ip, port, idCode, timeout });
                _logger.LogDebug("Wine: Resultado InitComm: {Result}", result);
                return result;
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Wine: Error en InitComm");
                return -1;
            }
        }

        public async Task<int> SplitScreen(uint ip, int screenId, int x, int y, int width, int height)
        {
            try
            {
                _logger.LogDebug("Wine: Configurando pantalla dividida para panel IP: {IP}, Screen: {Screen}, Pos: ({X},{Y}), Size: {Width}x{Height}", 
                    ip, screenId, x, y, width, height);

                var result = await ExecuteWineFunction("SplitScreen", new object[] { ip, screenId, x, y, width, height });
                _logger.LogDebug("Wine: Resultado SplitScreen: {Result}", result);
                return result;
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Wine: Error en SplitScreen");
                return -1;
            }
        }

        public async Task<int> SendText(uint ip, string text, int color, int fontSize, int speed, int effect, int stayTime, int alignment)
        {
            try
            {
                _logger.LogDebug("Wine: Enviando texto a panel IP: {IP}, Texto: '{Text}', Color: {Color}, Tamaño: {Size}, Velocidad: {Speed}, Efecto: {Effect}, Tiempo: {Time}, Alineación: {Align}", 
                    ip, text, color, fontSize, speed, effect, stayTime, alignment);

                var result = await ExecuteWineFunction("SendText", new object[] { ip, text, color, fontSize, speed, effect, stayTime, alignment });
                _logger.LogDebug("Wine: Resultado SendText: {Result}", result);
                return result;
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Wine: Error en SendText");
                return -1;
            }
        }

        private async Task<int> ExecuteWineFunction(string functionName, object[] parameters)
        {
            try
            {
                // Crear un script temporal de C# que use la DLL
                var tempScript = CreateTempScript(functionName, parameters);
                var scriptPath = $"/tmp/cp5200_{Guid.NewGuid()}.cs";
                
                await File.WriteAllTextAsync(scriptPath, tempScript);

                // Compilar el script temporal
                var exePath = scriptPath.Replace(".cs", ".exe");
                var compileResult = await CompileScript(scriptPath, exePath);
                
                if (!compileResult)
                {
                    _logger.LogError("Wine: Error compilando script temporal");
                    return -1;
                }

                // Ejecutar con Wine
                var result = await ExecuteWithWine(exePath);
                
                // Limpiar archivos temporales
                CleanupTempFiles(scriptPath, exePath);
                
                return result;
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Wine: Error ejecutando función {Function}", functionName);
                return -1;
            }
        }

        private string CreateTempScript(string functionName, object[] parameters)
        {
            var paramString = string.Join(", ", parameters.Select(p => p is string ? $"\"{p}\"" : p.ToString()));
            
            return $@"
using System;
using System.Runtime.InteropServices;

class CP5200Wrapper
{{
    [DllImport(""CP5200.dll"")]
    public static extern int CP5200_Net_Init(uint dwIP, int nIPPort, uint dwIDCode, int nTimeOut);
    
    [DllImport(""CP5200.dll"")]
    public static extern int CP5200_Net_SplitScreen(uint dwIP, int nScreenID, int nX, int nY, int nWidth, int nHeight);
    
    [DllImport(""CP5200.dll"")]
    public static extern int CP5200_Net_SendText(uint dwIP, string lpText, int nColor, int nFontSize, int nSpeed, int nEffect, int nStayTime, int nAlignment);

    static int Main()
    {{
        try
        {{
            int result = 0;
            switch(""{functionName}"")
            {{
                case ""InitComm"":
                    result = CP5200_Net_Init({paramString});
                    break;
                case ""SplitScreen"":
                    result = CP5200_Net_SplitScreen({paramString});
                    break;
                case ""SendText"":
                    result = CP5200_Net_SendText({paramString});
                    break;
            }}
            Console.WriteLine(result);
            return result;
        }}
        catch (Exception ex)
        {{
            Console.WriteLine(""-1"");
            return -1;
        }}
    }}
}}";
        }

        private async Task<bool> CompileScript(string scriptPath, string exePath)
        {
            try
            {
                var startInfo = new ProcessStartInfo
                {
                    FileName = "mcs", // Mono C# compiler
                    Arguments = $"-out:{exePath} {scriptPath}",
                    RedirectStandardOutput = true,
                    RedirectStandardError = true,
                    UseShellExecute = false,
                    CreateNoWindow = true
                };

                using var process = new Process { StartInfo = startInfo };
                process.Start();
                await process.WaitForExitAsync();

                return process.ExitCode == 0;
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Wine: Error compilando script");
                return false;
            }
        }

        private async Task<int> ExecuteWithWine(string exePath)
        {
            try
            {
                var startInfo = new ProcessStartInfo
                {
                    FileName = _winePath,
                    Arguments = exePath,
                    RedirectStandardOutput = true,
                    RedirectStandardError = true,
                    UseShellExecute = false,
                    CreateNoWindow = true,
                    WorkingDirectory = Path.GetDirectoryName(_dllPath)
                };

                using var process = new Process { StartInfo = startInfo };
                process.Start();
                
                var output = await process.StandardOutput.ReadToEndAsync();
                await process.WaitForExitAsync();

                if (int.TryParse(output.Trim(), out int result))
                {
                    return result;
                }

                return -1;
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Wine: Error ejecutando con Wine");
                return -1;
            }
        }

        private void CleanupTempFiles(string scriptPath, string exePath)
        {
            try
            {
                if (File.Exists(scriptPath))
                    File.Delete(scriptPath);
                if (File.Exists(exePath))
                    File.Delete(exePath);
            }
            catch (Exception ex)
            {
                _logger.LogWarning(ex, "Wine: Error limpiando archivos temporales");
            }
        }
    }
} 