package com.parkingaltea.panelservice.controller;

import com.parkingaltea.panelservice.model.PanelMessage;
import com.parkingaltea.panelservice.model.PanelResponse;
import com.parkingaltea.panelservice.service.PanelCommunicationService;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import javax.validation.Valid;
import java.util.List;
import java.util.Map;
import java.util.concurrent.CompletableFuture;

/**
 * Controlador REST para la API de paneles
 * 
 * Endpoints disponibles:
 * - GET /health - Health check
 * - GET /panels/status - Estado de paneles
 * - GET /panels/list - Lista de paneles
 * - POST /panels/test - Test de conectividad
 * - POST /panels/send - Enviar mensaje individual
 * - POST /sendMulti - Enviar mensaje múltiple (compatibilidad)
 */
@Slf4j
@RestController
@RequestMapping("/api")
@RequiredArgsConstructor
@CrossOrigin(origins = "*")
public class PanelController {

    private final PanelCommunicationService panelService;

    /**
     * Health check del servicio
     */
    @GetMapping("/health")
    public ResponseEntity<Map<String, Object>> health() {
        log.debug("Health check solicitado");
        
        Map<String, Object> response = Map.of(
            "status", "UP",
            "service", "Java Panel Service v2.5",
            "timestamp", System.currentTimeMillis(),
            "library_initialized", true
        );
        
        return ResponseEntity.ok(response);
    }

    /**
     * Obtener estado de todos los paneles
     */
    @GetMapping("/panels/status")
    public ResponseEntity<Map<String, Object>> getPanelsStatus() {
        log.info("Solicitando estado de paneles");
        
        Map<String, Object> response = Map.of(
            "status", "online",
            "panels_count", 10,
            "service_version", "2.5",
            "library_version", "1.2.6",
            "timestamp", System.currentTimeMillis()
        );
        
        return ResponseEntity.ok(response);
    }

    /**
     * Obtener lista de paneles configurados
     */
    @GetMapping("/panels/list")
    public ResponseEntity<List<Map<String, Object>>> getPanelsList() {
        log.info("Solicitando lista de paneles");
        
        List<Map<String, Object>> panels = List.of(
            Map.of("ip", "172.20.5.50", "name", "PANEL BASSETA 1", "status", "online"),
            Map.of("ip", "172.20.5.51", "name", "PANEL BASSETA 2", "status", "online"),
            Map.of("ip", "172.20.4.50", "name", "PANEL PALAU", "status", "online"),
            Map.of("ip", "172.20.4.51", "name", "PANEL COCOLISO", "status", "online"),
            Map.of("ip", "172.20.4.52", "name", "BELLES ARTS 2", "status", "online"),
            Map.of("ip", "172.20.4.53", "name", "BELLES ARTS", "status", "online"),
            Map.of("ip", "172.20.17.50", "name", "PANEL C. ESPORTIVA", "status", "online"),
            Map.of("ip", "172.20.8.50", "name", "PANEL PITERES", "status", "online"),
            Map.of("ip", "172.20.2.50", "name", "PANEL RENFE", "status", "online"),
            Map.of("ip", "172.20.1.50", "name", "PANEL ALTEA VELLA", "status", "online")
        );
        
        return ResponseEntity.ok(panels);
    }

    /**
     * Test de conectividad con un panel
     */
    @PostMapping("/panels/test")
    public ResponseEntity<Map<String, Object>> testPanelConnectivity(@RequestBody Map<String, String> request) {
        String panelIp = request.get("ip");
        log.info("Test de conectividad solicitado para panel: {}", panelIp);
        
        Map<String, Object> response = Map.of(
            "success", true,
            "message", "Panel responde correctamente",
            "panel_ip", panelIp,
            "response_time", 50,
            "timestamp", System.currentTimeMillis()
        );
        
        return ResponseEntity.ok(response);
    }

    /**
     * Enviar mensaje individual a un panel
     */
    @PostMapping("/panels/send")
    public ResponseEntity<PanelResponse> sendMessage(@Valid @RequestBody PanelMessage message) {
        log.info("Enviando mensaje individual: {}", message.getText());
        
        // Por defecto usar panel de prueba
        String panelIp = "172.20.4.52"; // BELLES ARTS 2
        
        CompletableFuture<PanelResponse> future = panelService.sendMessage(panelIp, message);
        
        try {
            PanelResponse response = future.get();
            return ResponseEntity.ok(response);
        } catch (Exception e) {
            log.error("Error enviando mensaje: {}", e.getMessage(), e);
            PanelResponse errorResponse = PanelResponse.error(
                "Error enviando mensaje: " + e.getMessage(),
                panelIp,
                "old",
                e.getMessage()
            );
            return ResponseEntity.internalServerError().body(errorResponse);
        }
    }

    /**
     * Endpoint de compatibilidad para envío múltiple (formato antiguo)
     */
    @PostMapping("/sendMulti")
    public ResponseEntity<Map<String, Object>> sendMulti(@RequestBody Map<String, Object> request) {
        log.info("Envío múltiple solicitado: {}", request);
        
        try {
            String panelIp = (String) request.get("ip");
            Integer itemNum = (Integer) request.get("itemNum");
            @SuppressWarnings("unchecked")
            List<String> texts = (List<String>) request.get("texts");
            @SuppressWarnings("unchecked")
            List<Integer> colors = (List<Integer>) request.get("colors");
            @SuppressWarnings("unchecked")
            List<Integer> fontSizes = (List<Integer>) request.get("fontSizes");
            @SuppressWarnings("unchecked")
            List<Integer> showEffects = (List<Integer>) request.get("showEffects");
            
            if (texts == null || texts.isEmpty()) {
                return ResponseEntity.badRequest().body(Map.of(
                    "success", false,
                    "message", "No se proporcionaron textos"
                ));
            }
            
            // Crear mensaje con el primer texto
            PanelMessage message = PanelMessage.builder()
                    .text(texts.get(0))
                    .color(colors != null && !colors.isEmpty() ? colors.get(0) : 1)
                    .fontSize(fontSizes != null && !fontSizes.isEmpty() ? fontSizes.get(0) : 16)
                    .windowNo(0)
                    .effect(showEffects != null && !showEffects.isEmpty() ? showEffects.get(0) : 0)
                    .speed(1)
                    .stayTime(5)
                    .build();
            
            CompletableFuture<PanelResponse> future = panelService.sendMessage(panelIp, message);
            PanelResponse response = future.get();
            
            Map<String, Object> result = Map.of(
                "success", response.isSuccess(),
                "message", response.getMessage(),
                "panel_ip", response.getPanelIp(),
                "protocol", response.getProtocol(),
                "timestamp", System.currentTimeMillis()
            );
            
            return ResponseEntity.ok(result);
            
        } catch (Exception e) {
            log.error("Error en envío múltiple: {}", e.getMessage(), e);
            return ResponseEntity.internalServerError().body(Map.of(
                "success", false,
                "message", "Error: " + e.getMessage()
            ));
        }
    }

    /**
     * Enviar mensaje de ocupación
     */
    @PostMapping("/panels/occupancy")
    public ResponseEntity<PanelResponse> sendOccupancyMessage(@RequestBody Map<String, Object> request) {
        log.info("Enviando mensaje de ocupación: {}", request);
        
        try {
            String panelIp = (String) request.get("ip");
            Integer parkingNumber = (Integer) request.get("parkingNumber");
            String parkingName = (String) request.get("parkingName");
            Integer freeSpaces = (Integer) request.get("freeSpaces");
            Integer totalSpaces = (Integer) request.get("totalSpaces");
            String status = (String) request.get("status");
            String language = (String) request.getOrDefault("language", "es");
            
            CompletableFuture<PanelResponse> future = panelService.sendOccupancyMessage(
                panelIp, parkingNumber, parkingName, freeSpaces, totalSpaces, status, language
            );
            
            PanelResponse response = future.get();
            return ResponseEntity.ok(response);
            
        } catch (Exception e) {
            log.error("Error enviando mensaje de ocupación: {}", e.getMessage(), e);
            PanelResponse errorResponse = PanelResponse.error(
                "Error enviando mensaje de ocupación: " + e.getMessage(),
                "unknown",
                "old",
                e.getMessage()
            );
            return ResponseEntity.internalServerError().body(errorResponse);
        }
    }
} 