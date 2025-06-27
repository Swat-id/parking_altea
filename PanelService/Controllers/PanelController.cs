using Microsoft.AspNetCore.Mvc;
using ParkingAltea.PanelService.Models;
using ParkingAltea.PanelService.Services;

namespace ParkingAltea.PanelService.Controllers
{
    [ApiController]
    [Route("api/[controller]")]
    public class PanelController : ControllerBase
    {
        private readonly IPanelManager _panelManager;
        private readonly IPanelCommunicationService _communicationService;
        private readonly ILogger<PanelController> _logger;

        public PanelController(
            IPanelManager panelManager,
            IPanelCommunicationService communicationService,
            ILogger<PanelController> logger)
        {
            _panelManager = panelManager;
            _communicationService = communicationService;
            _logger = logger;
        }

        [HttpGet("status")]
        public async Task<ActionResult<List<PanelStatus>>> GetStatus()
        {
            try
            {
                var status = await _panelManager.GetAllPanelsStatusAsync();
                return Ok(status);
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Error obteniendo estado de paneles");
                return StatusCode(500, new { error = "Error interno del servidor" });
            }
        }

        [HttpGet("status/{panelIP}")]
        public async Task<ActionResult<PanelStatus>> GetPanelStatus(string panelIP)
        {
            try
            {
                var status = await _communicationService.GetPanelStatusAsync(panelIP);
                return Ok(status);
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Error obteniendo estado del panel {PanelIP}", panelIP);
                return StatusCode(500, new { error = "Error interno del servidor" });
            }
        }

        [HttpPost("send")]
        public async Task<ActionResult<PanelResponse>> SendMessage([FromBody] SendMessageRequest request)
        {
            try
            {
                if (string.IsNullOrEmpty(request.PanelIP) || string.IsNullOrEmpty(request.Message))
                {
                    return BadRequest(new { error = "PanelIP y Message son requeridos" });
                }

                var message = new PanelMessage
                {
                    Text = request.Message,
                    Color = request.Color,
                    FontSize = request.FontSize,
                    Speed = request.Speed,
                    Effect = request.Effect,
                    StayTime = request.StayTime,
                    Alignment = request.Alignment
                };

                var response = await _panelManager.SendToPanelAsync(request.PanelIP, message);
                return Ok(response);
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Error enviando mensaje al panel {PanelIP}", request.PanelIP);
                return StatusCode(500, new { error = "Error interno del servidor" });
            }
        }

        [HttpPost("occupancy")]
        public async Task<ActionResult<PanelResponse>> SendOccupancy([FromBody] SendOccupancyRequest request)
        {
            try
            {
                if (string.IsNullOrEmpty(request.PanelIP))
                {
                    return BadRequest(new { error = "PanelIP es requerido" });
                }

                var occupancy = new PanelOccupancy
                {
                    IP = request.PanelIP,
                    Current = request.Current,
                    Total = request.Total,
                    Status = request.Status,
                    ParkingName = request.ParkingName,
                    Color = request.Color,
                    FontSize = request.FontSize,
                    Speed = request.Speed,
                    Alignment = request.Alignment
                };

                var response = await _communicationService.SendOccupancyAsync(occupancy);
                
                return Ok(response);
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Error enviando ocupación al panel {PanelIP}", request.PanelIP);
                return StatusCode(500, new { error = "Error interno del servidor" });
            }
        }

        [HttpPost("broadcast")]
        public async Task<ActionResult<BroadcastResponse>> Broadcast([FromBody] BroadcastRequest request)
        {
            try
            {
                if (string.IsNullOrEmpty(request.Message))
                {
                    return BadRequest(new { error = "Message es requerido" });
                }

                var response = await _communicationService.BroadcastAsync(request);
                return Ok(response);
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Error en broadcast");
                return StatusCode(500, new { error = "Error interno del servidor" });
            }
        }

        [HttpPost("test/{panelIP}")]
        public async Task<ActionResult<PanelResponse>> TestPanel(string panelIP)
        {
            try
            {
                var response = await _communicationService.TestPanelAsync(panelIP);
                return Ok(response);
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Error testeando panel {PanelIP}", panelIP);
                return StatusCode(500, new { error = "Error interno del servidor" });
            }
        }

        [HttpPost("static")]
        public async Task<ActionResult<PanelResponse>> SendStaticText([FromBody] SendStaticTextRequest request)
        {
            try
            {
                if (string.IsNullOrEmpty(request.PanelIP) || string.IsNullOrEmpty(request.Text))
                {
                    return BadRequest(new { error = "PanelIP y Text son requeridos" });
                }

                var response = await _communicationService.SendStaticTextAsync(
                    request.PanelIP, 
                    request.Text, 
                    request.X, 
                    request.Y, 
                    request.Width, 
                    request.Height
                );
                
                return Ok(response);
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Error enviando texto estático al panel {PanelIP}", request.PanelIP);
                return StatusCode(500, new { error = "Error interno del servidor" });
            }
        }

        [HttpGet("colors")]
        public ActionResult<object> GetAvailableColors()
        {
            return Ok(new
            {
                colors = new
                {
                    Red = PanelColors.Red,
                    Green = PanelColors.Green,
                    Blue = PanelColors.Blue,
                    Yellow = PanelColors.Yellow,
                    Cyan = PanelColors.Cyan,
                    Magenta = PanelColors.Magenta,
                    White = PanelColors.White,
                    Orange = PanelColors.Orange,
                    Purple = PanelColors.Purple
                },
                alignments = new
                {
                    Left = PanelAlignment.Left,
                    Center = PanelAlignment.Center,
                    Right = PanelAlignment.Right
                },
                effects = new
                {
                    None = PanelEffects.None,
                    Blink = PanelEffects.Blink,
                    Scroll = PanelEffects.Scroll,
                    Fade = PanelEffects.Fade
                },
                speeds = new
                {
                    VerySlow = PanelSpeed.VerySlow,
                    Slow = PanelSpeed.Slow,
                    Normal = PanelSpeed.Normal,
                    Fast = PanelSpeed.Fast,
                    VeryFast = PanelSpeed.VeryFast
                }
            });
        }
    }

    // Request models
    public class SendMessageRequest
    {
        public string PanelIP { get; set; } = string.Empty;
        public string Message { get; set; } = string.Empty;
        public int Color { get; set; } = PanelColors.Red;
        public int FontSize { get; set; } = 16;
        public int Speed { get; set; } = PanelSpeed.Normal;
        public int Effect { get; set; } = PanelEffects.None;
        public int StayTime { get; set; } = 5;
        public int Alignment { get; set; } = PanelAlignment.Center;
    }

    public class SendOccupancyRequest
    {
        public string PanelIP { get; set; } = string.Empty;
        public int Current { get; set; }
        public int Total { get; set; }
        public string Status { get; set; } = string.Empty;
        public string ParkingName { get; set; } = string.Empty;
        public int Color { get; set; } = PanelColors.Green;
        public int FontSize { get; set; } = 16;
        public int Speed { get; set; } = PanelSpeed.Slow;
        public int Alignment { get; set; } = PanelAlignment.Center;
    }

    public class SendStaticTextRequest
    {
        public string PanelIP { get; set; } = string.Empty;
        public string Text { get; set; } = string.Empty;
        public int X { get; set; } = 0;
        public int Y { get; set; } = 0;
        public int Width { get; set; } = 64;
        public int Height { get; set; } = 32;
    }
} 