using Microsoft.AspNetCore.Builder;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Hosting;
using Microsoft.Extensions.Logging;
using ParkingAltea.PanelService.Services;
using ParkingAltea.PanelService.Models;

var builder = WebApplication.CreateBuilder(args);

// Configurar servicios
builder.Services.AddControllers();
builder.Services.AddEndpointsApiExplorer();
builder.Services.AddSwaggerGen();

// Configurar CORS
builder.Services.AddCors(options =>
{
    options.AddPolicy("AllowAll", policy =>
    {
        policy.AllowAnyOrigin()
              .AllowAnyMethod()
              .AllowAnyHeader();
    });
});

// Registrar servicios
builder.Services.AddSingleton<IPanelCommunicationService, PanelCommunicationService>();
builder.Services.AddSingleton<IPanelManager, PanelManager>();

// Configurar logging
builder.Services.AddLogging(logging =>
{
    logging.AddConsole();
    logging.AddDebug();
});

var app = builder.Build();

// Configurar pipeline HTTP
if (app.Environment.IsDevelopment())
{
    app.UseSwagger();
    app.UseSwaggerUI();
}

app.UseCors("AllowAll");
app.UseRouting();
app.MapControllers();

// Configurar endpoints
app.MapGet("/", () => "Panel Communication Service - Parking Altea");
app.MapGet("/health", () => new { status = "healthy", timestamp = DateTime.UtcNow });

// Inicializar panel manager
var panelManager = app.Services.GetRequiredService<IPanelManager>();
await panelManager.InitializeAsync();

Console.WriteLine("🚦 Panel Communication Service iniciado");
Console.WriteLine($"📡 Escuchando en: {app.Urls.FirstOrDefault() ?? "http://localhost:5001"}");

app.Run(); 