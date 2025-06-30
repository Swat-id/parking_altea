package com.parkingaltea.panelservice.controller;

import com.parkingaltea.panelservice.model.PanelMessage;
import com.parkingaltea.panelservice.model.PanelOccupancy;
import com.parkingaltea.panelservice.model.PanelResponse;
import com.parkingaltea.panelservice.service.PanelCommunicationService;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.ResponseEntity;
import org.springframework.validation.annotation.Validated;
import org.springframework.web.bind.annotation.*;

import javax.validation.Valid;
import javax.validation.constraints.NotBlank;
import java.util.HashMap;
import java.util.Map;

/**
 * Controlador REST para el servicio de comunicación con paneles LED
 */
@Slf4j
@RestController
@RequestMapping("/panel")
@Validated
@CrossOrigin(origins = "*")
public class PanelController {

    @Autowired
    private PanelCommunicationService panelService;

    /**
     * Health check general del servicio (raíz)
     */
    @GetMapping("/health")
    public ResponseEntity<PanelResponse> healthRoot() {
        try {
            Map<String, Object> data = new HashMap<>();
            data.put("service", "Java Panel Service");
            data.put("version", "1.0.0");
            data.put("status", "UP");
            data.put("timestamp", System.currentTimeMillis());
            
            PanelResponse response = PanelResponse.success("Servicio funcionando correctamente", data);
            return ResponseEntity.ok(response);
            
        } catch (Exception e) {
            log.error("Error en health check: {}", e.getMessage(), e);
            
            PanelResponse response = PanelResponse.error(
                "Error en health check: " + e.getMessage(),
                -1,
                0.0
            );
            return ResponseEntity.internalServerError().body(response);
        }
    }

    /**
     * Envía un mensaje a un panel específico
     */
    @PostMapping("/send")
    public ResponseEntity<PanelResponse> sendMessage(@Valid @RequestBody PanelMessage panelMessage) {
        long startTime = System.currentTimeMillis();
        
        try {
            log.info("Recibida petición para enviar mensaje a panel: {}", panelMessage.getPanelIP());
            
            boolean success = panelService.sendMessage(panelMessage);
            
            long responseTime = System.currentTimeMillis() - startTime;
            
            if (success) {
                PanelResponse response = PanelResponse.success(
                    "Mensaje enviado correctamente al panel " + panelMessage.getPanelIP(),
                    Map.of("responseTime", responseTime)
                );
                response.setResponseTime((double) responseTime);
                return ResponseEntity.ok(response);
            } else {
                PanelResponse response = PanelResponse.error(
                    "No se pudo enviar el mensaje al panel " + panelMessage.getPanelIP(),
                    -1,
                    (double) responseTime
                );
                return ResponseEntity.badRequest().body(response);
            }
            
        } catch (Exception e) {
            long responseTime = System.currentTimeMillis() - startTime;
            log.error("Error al procesar envío de mensaje: {}", e.getMessage(), e);
            
            PanelResponse response = PanelResponse.error(
                "Error interno del servidor: " + e.getMessage(),
                -2,
                (double) responseTime
            );
            return ResponseEntity.internalServerError().body(response);
        }
    }

    /**
     * Envía información de ocupación a un panel
     */
    @PostMapping("/occupancy")
    public ResponseEntity<PanelResponse> sendOccupancy(@Valid @RequestBody PanelOccupancy occupancy) {
        long startTime = System.currentTimeMillis();
        
        try {
            log.info("Recibida petición para enviar ocupación a panel: {}", occupancy.getPanelIP());
            
            boolean success = panelService.sendOccupancy(occupancy);
            
            long responseTime = System.currentTimeMillis() - startTime;
            
            if (success) {
                PanelResponse response = PanelResponse.success(
                    "Información de ocupación enviada correctamente al panel " + occupancy.getPanelIP(),
                    Map.of("responseTime", responseTime)
                );
                response.setResponseTime((double) responseTime);
                return ResponseEntity.ok(response);
            } else {
                PanelResponse response = PanelResponse.error(
                    "No se pudo enviar la información de ocupación al panel " + occupancy.getPanelIP(),
                    -1,
                    (double) responseTime
                );
                return ResponseEntity.badRequest().body(response);
            }
            
        } catch (Exception e) {
            long responseTime = System.currentTimeMillis() - startTime;
            log.error("Error al procesar envío de ocupación: {}", e.getMessage(), e);
            
            PanelResponse response = PanelResponse.error(
                "Error interno del servidor: " + e.getMessage(),
                -2,
                (double) responseTime
            );
            return ResponseEntity.internalServerError().body(response);
        }
    }

    /**
     * Envía un mensaje a todos los paneles (broadcast)
     */
    @PostMapping("/broadcast")
    public ResponseEntity<PanelResponse> broadcastMessage(@Valid @RequestBody PanelMessage panelMessage) {
        long startTime = System.currentTimeMillis();
        
        try {
            log.info("Recibida petición de broadcast: {}", panelMessage.getMessage());
            
            // Lista de paneles conocidos (en producción vendría de la base de datos)
            String[] panelIPs = {
                "172.20.17.50", "172.20.5.50", "172.20.5.51", "172.20.8.50", "172.20.4.50",
                "172.20.4.51", "172.20.4.52", "172.20.4.53", "172.20.2.50", "172.20.1.50"
            };
            
            int successCount = 0;
            int totalCount = panelIPs.length;
            
            for (String panelIP : panelIPs) {
                PanelMessage message = PanelMessage.builder()
                        .panelIP(panelIP)
                        .message(panelMessage.getMessage())
                        .color(panelMessage.getColor())
                        .fontSize(panelMessage.getFontSize())
                        .speed(panelMessage.getSpeed())
                        .effect(panelMessage.getEffect())
                        .stayTime(panelMessage.getStayTime())
                        .alignment(panelMessage.getAlignment())
                        .build();
                
                if (panelService.sendMessage(message)) {
                    successCount++;
                }
            }
            
            long responseTime = System.currentTimeMillis() - startTime;
            
            Map<String, Object> data = new HashMap<>();
            data.put("responseTime", responseTime);
            data.put("successCount", successCount);
            data.put("totalCount", totalCount);
            data.put("successRate", (double) successCount / totalCount * 100);
            
            PanelResponse response = PanelResponse.success(
                String.format("Broadcast completado: %d/%d paneles actualizados", successCount, totalCount),
                data
            );
            response.setResponseTime((double) responseTime);
            
            return ResponseEntity.ok(response);
            
        } catch (Exception e) {
            long responseTime = System.currentTimeMillis() - startTime;
            log.error("Error al procesar broadcast: {}", e.getMessage(), e);
            
            PanelResponse response = PanelResponse.error(
                "Error interno del servidor: " + e.getMessage(),
                -2,
                (double) responseTime
            );
            return ResponseEntity.internalServerError().body(response);
        }
    }

    /**
     * Prueba la conectividad con un panel específico
     */
    @GetMapping("/test/{panelIP}")
    public ResponseEntity<PanelResponse> testPanel(@PathVariable @NotBlank String panelIP) {
        long startTime = System.currentTimeMillis();
        
        try {
            log.info("Recibida petición de prueba para panel: {}", panelIP);
            
            boolean success = panelService.testPanel(panelIP);
            
            long responseTime = System.currentTimeMillis() - startTime;
            
            if (success) {
                PanelResponse response = PanelResponse.success(
                    "Panel " + panelIP + " responde correctamente",
                    Map.of("responseTime", responseTime)
                );
                response.setResponseTime((double) responseTime);
                return ResponseEntity.ok(response);
            } else {
                PanelResponse response = PanelResponse.error(
                    "Panel " + panelIP + " no responde",
                    -1,
                    (double) responseTime
                );
                return ResponseEntity.badRequest().body(response);
            }
            
        } catch (Exception e) {
            long responseTime = System.currentTimeMillis() - startTime;
            log.error("Error al probar panel {}: {}", panelIP, e.getMessage(), e);
            
            PanelResponse response = PanelResponse.error(
                "Error interno del servidor: " + e.getMessage(),
                -2,
                (double) responseTime
            );
            return ResponseEntity.internalServerError().body(response);
        }
    }

    /**
     * Obtiene el estado de todos los paneles
     */
    @GetMapping("/status")
    public ResponseEntity<PanelResponse> getPanelStatus() {
        long startTime = System.currentTimeMillis();
        
        try {
            log.info("Recibida petición de estado de paneles");
            
            Map<String, Boolean> initializedPanels = panelService.getInitializedPanels();
            
            long responseTime = System.currentTimeMillis() - startTime;
            
            Map<String, Object> data = new HashMap<>();
            data.put("initializedPanels", initializedPanels);
            data.put("totalPanels", initializedPanels.size());
            data.put("onlinePanels", initializedPanels.values().stream().filter(Boolean::booleanValue).count());
            data.put("responseTime", responseTime);
            
            PanelResponse response = PanelResponse.success(
                "Estado de paneles obtenido correctamente",
                data
            );
            response.setResponseTime((double) responseTime);
            
            return ResponseEntity.ok(response);
            
        } catch (Exception e) {
            long responseTime = System.currentTimeMillis() - startTime;
            log.error("Error al obtener estado de paneles: {}", e.getMessage(), e);
            
            PanelResponse response = PanelResponse.error(
                "Error interno del servidor: " + e.getMessage(),
                -2,
                (double) responseTime
            );
            return ResponseEntity.internalServerError().body(response);
        }
    }

    /**
     * Obtiene los colores disponibles
     */
    @GetMapping("/colors")
    public ResponseEntity<PanelResponse> getAvailableColors() {
        long startTime = System.currentTimeMillis();
        
        try {
            Map<String, Integer> colors = Map.of(
                "red", 0x0000FF,
                "green", 0x00FF00,
                "blue", 0xFF0000,
                "yellow", 0x00FFFF,
                "orange", 0x0080FF,
                "white", 0xFFFFFF,
                "default", 3000
            );
            
            long responseTime = System.currentTimeMillis() - startTime;
            
            PanelResponse response = PanelResponse.success(
                "Colores disponibles obtenidos correctamente",
                colors
            );
            response.setResponseTime((double) responseTime);
            
            return ResponseEntity.ok(response);
            
        } catch (Exception e) {
            long responseTime = System.currentTimeMillis() - startTime;
            log.error("Error al obtener colores: {}", e.getMessage(), e);
            
            PanelResponse response = PanelResponse.error(
                "Error interno del servidor: " + e.getMessage(),
                -2,
                (double) responseTime
            );
            return ResponseEntity.internalServerError().body(response);
        }
    }

    /**
     * Limpia la cache de paneles inicializados
     */
    @PostMapping("/clear-cache")
    public ResponseEntity<PanelResponse> clearCache() {
        long startTime = System.currentTimeMillis();
        
        try {
            log.info("Recibida petición para limpiar cache de paneles");
            
            panelService.clearInitializedPanels();
            
            long responseTime = System.currentTimeMillis() - startTime;
            
            PanelResponse response = PanelResponse.success(
                "Cache de paneles limpiada correctamente"
            );
            response.setResponseTime((double) responseTime);
            
            return ResponseEntity.ok(response);
            
        } catch (Exception e) {
            long responseTime = System.currentTimeMillis() - startTime;
            log.error("Error al limpiar cache: {}", e.getMessage(), e);
            
            PanelResponse response = PanelResponse.error(
                "Error interno del servidor: " + e.getMessage(),
                -2,
                (double) responseTime
            );
            return ResponseEntity.internalServerError().body(response);
        }
    }
} 