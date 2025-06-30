package com.parkingaltea.panelservice.controller;

import com.parkingaltea.panelservice.model.PanelMessage;
import com.parkingaltea.panelservice.model.PanelResponse;
import com.parkingaltea.panelservice.service.PanelService;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.ResponseEntity;
import org.springframework.validation.annotation.Validated;
import org.springframework.web.bind.annotation.*;

import javax.validation.Valid;
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
    private PanelService panelService;

    /**
     * Health check del servicio
     */
    @GetMapping("/health")
    public ResponseEntity<PanelResponse> health() {
        try {
            Map<String, Object> data = new HashMap<>();
            data.put("service", "Java Panel Service v2.5");
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
     * Obtiene el estado de la cache de paneles
     */
    @GetMapping("/status")
    public ResponseEntity<PanelResponse> getStatus() {
        try {
            Map<String, Boolean> cacheStatus = panelService.getCacheStatus();
            
            Map<String, Object> data = new HashMap<>();
            data.put("cacheStatus", cacheStatus);
            data.put("totalPanels", cacheStatus.size());
            
            PanelResponse response = PanelResponse.success(
                "Estado de la cache obtenido correctamente",
                data
            );
            return ResponseEntity.ok(response);
            
        } catch (Exception e) {
            log.error("Error al obtener estado: {}", e.getMessage(), e);
            
            PanelResponse response = PanelResponse.error(
                "Error al obtener estado: " + e.getMessage(),
                -1,
                0.0
            );
            return ResponseEntity.internalServerError().body(response);
        }
    }

    /**
     * Limpia la cache de paneles
     */
    @PostMapping("/clear-cache")
    public ResponseEntity<PanelResponse> clearCache() {
        try {
            panelService.clearCache();
            
            PanelResponse response = PanelResponse.success("Cache de paneles limpiada correctamente");
            return ResponseEntity.ok(response);
            
        } catch (Exception e) {
            log.error("Error al limpiar cache: {}", e.getMessage(), e);
            
            PanelResponse response = PanelResponse.error(
                "Error al limpiar cache: " + e.getMessage(),
                -1,
                0.0
            );
            return ResponseEntity.internalServerError().body(response);
        }
    }

    /**
     * Obtiene información sobre los colores disponibles
     */
    @GetMapping("/colors")
    public ResponseEntity<PanelResponse> getColors() {
        try {
            Map<String, Object> colors = new HashMap<>();
            colors.put("1", "Rojo");
            colors.put("2", "Verde");
            colors.put("3", "Amarillo");
            colors.put("4", "Azul");
            colors.put("5", "Púrpura");
            colors.put("6", "Azul oscuro");
            colors.put("7", "Blanco");
            
            PanelResponse response = PanelResponse.success("Colores disponibles obtenidos correctamente", colors);
            return ResponseEntity.ok(response);
            
        } catch (Exception e) {
            log.error("Error al obtener colores: {}", e.getMessage(), e);
            
            PanelResponse response = PanelResponse.error(
                "Error al obtener colores: " + e.getMessage(),
                -1,
                0.0
            );
            return ResponseEntity.internalServerError().body(response);
        }
    }
} 