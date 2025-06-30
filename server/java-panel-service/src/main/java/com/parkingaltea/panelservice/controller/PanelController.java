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
import java.util.Arrays;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

/**
 * Controlador REST para el servicio de comunicación con paneles LED
 */
@Slf4j
@RestController
@RequestMapping("/panels")
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
     * Obtiene la lista de paneles disponibles
     */
    @GetMapping("/list")
    public ResponseEntity<PanelResponse> listPanels() {
        try {
            List<Map<String, String>> panels = Arrays.asList(
                Map.of("ip", "172.20.5.50", "name", "PANEL BASSETA 1", "description", "P. Basseta Centre"),
                Map.of("ip", "172.20.5.51", "name", "PANEL BASSETA 2", "description", "P. Basseta Centre"),
                Map.of("ip", "172.20.4.50", "name", "PANEL PALAU", "description", "P. Poble antic/Palau Altea"),
                Map.of("ip", "172.20.4.51", "name", "PANEL COCOLISO", "description", "P. Poble antic/Palau Altea"),
                Map.of("ip", "172.20.4.52", "name", "BELLES ARTS 2", "description", "P. Poble antic/Belles Arts 2"),
                Map.of("ip", "172.20.4.53", "name", "BELLES ARTS", "description", "P. Poble antic/Belles Arts 1"),
                Map.of("ip", "172.20.2.50", "name", "PANEL RENFE", "description", "P. Estació Altea"),
                Map.of("ip", "172.20.1.50", "name", "PANEL ALTEA VELLA", "description", "P. Altea la Vella"),
                Map.of("ip", "172.20.8.50", "name", "PANEL PITERES", "description", "P. Poble antic/Conservatori"),
                Map.of("ip", "172.20.17.50", "name", "PANEL C. ESPORTIVA", "description", "P. Ciutat Esportiva")
            );
            
            Map<String, Object> data = new HashMap<>();
            data.put("panels", panels);
            data.put("total", panels.size());
            
            PanelResponse response = PanelResponse.success("Lista de paneles obtenida correctamente", data);
            return ResponseEntity.ok(response);
            
        } catch (Exception e) {
            log.error("Error al obtener lista de paneles: {}", e.getMessage(), e);
            
            PanelResponse response = PanelResponse.error(
                "Error al obtener lista de paneles: " + e.getMessage(),
                -1,
                0.0
            );
            return ResponseEntity.internalServerError().body(response);
        }
    }

    /**
     * Obtiene el estado de los paneles
     */
    @GetMapping("/status")
    public ResponseEntity<PanelResponse> getStatus() {
        try {
            Map<String, Boolean> cacheStatus = panelService.getCacheStatus();
            
            Map<String, Object> data = new HashMap<>();
            data.put("cacheStatus", cacheStatus);
            data.put("totalPanels", cacheStatus.size());
            data.put("onlinePanels", cacheStatus.values().stream().filter(status -> status).count());
            data.put("offlinePanels", cacheStatus.values().stream().filter(status -> !status).count());
            
            PanelResponse response = PanelResponse.success(
                "Estado de paneles obtenido correctamente",
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
     * Prueba la conectividad con un panel específico
     */
    @PostMapping("/test")
    public ResponseEntity<PanelResponse> testPanel(@RequestBody Map<String, String> request) {
        long startTime = System.currentTimeMillis();
        
        try {
            String panelIP = request.get("ip");
            if (panelIP == null || panelIP.trim().isEmpty()) {
                PanelResponse response = PanelResponse.error("IP del panel es requerida", -1, 0.0);
                return ResponseEntity.badRequest().body(response);
            }
            
            log.info("Probando conectividad con panel: {}", panelIP);
            
            boolean success = panelService.testPanel(panelIP);
            
            long responseTime = System.currentTimeMillis() - startTime;
            
            Map<String, Object> data = new HashMap<>();
            data.put("ip", panelIP);
            data.put("success", success);
            data.put("responseTime", responseTime);
            
            PanelResponse response = PanelResponse.success(
                success ? "Panel " + panelIP + " responde correctamente" : "Panel " + panelIP + " no responde",
                data
            );
            response.setResponseTime((double) responseTime);
            return ResponseEntity.ok(response);
            
        } catch (Exception e) {
            long responseTime = System.currentTimeMillis() - startTime;
            log.error("Error al probar panel: {}", e.getMessage(), e);
            
            PanelResponse response = PanelResponse.error(
                "Error al probar panel: " + e.getMessage(),
                -2,
                (double) responseTime
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
     * Envía un mensaje a múltiples paneles
     */
    @PostMapping("/send-multi")
    public ResponseEntity<PanelResponse> sendMultiMessage(@RequestBody Map<String, Object> request) {
        long startTime = System.currentTimeMillis();
        
        try {
            @SuppressWarnings("unchecked")
            List<String> ips = (List<String>) request.get("ips");
            String message = (String) request.get("message");
            Integer color = (Integer) request.get("color");
            Integer fontSize = (Integer) request.get("fontSize");
            Integer windowNo = (Integer) request.get("windowNo");
            
            if (ips == null || ips.isEmpty()) {
                PanelResponse response = PanelResponse.error("Lista de IPs es requerida", -1, 0.0);
                return ResponseEntity.badRequest().body(response);
            }
            
            if (message == null || message.trim().isEmpty()) {
                PanelResponse response = PanelResponse.error("Mensaje es requerido", -1, 0.0);
                return ResponseEntity.badRequest().body(response);
            }
            
            log.info("Recibida petición para enviar mensaje a {} paneles: {}", ips.size(), ips);
            
            boolean success = panelService.sendMultiMessage(ips, message, color, fontSize, windowNo);
            
            long responseTime = System.currentTimeMillis() - startTime;
            
            if (success) {
                Map<String, Object> data = new HashMap<>();
                data.put("ips", ips);
                data.put("message", message);
                data.put("responseTime", responseTime);
                
                PanelResponse response = PanelResponse.success(
                    "Mensaje enviado correctamente a " + ips.size() + " paneles",
                    data
                );
                response.setResponseTime((double) responseTime);
                return ResponseEntity.ok(response);
            } else {
                PanelResponse response = PanelResponse.error(
                    "No se pudo enviar el mensaje a los paneles",
                    -1,
                    (double) responseTime
                );
                return ResponseEntity.badRequest().body(response);
            }
            
        } catch (Exception e) {
            long responseTime = System.currentTimeMillis() - startTime;
            log.error("Error al procesar envío multi-mensaje: {}", e.getMessage(), e);
            
            PanelResponse response = PanelResponse.error(
                "Error interno del servidor: " + e.getMessage(),
                -2,
                (double) responseTime
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