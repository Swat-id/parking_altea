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
import java.time.LocalDateTime;
import java.util.HashMap;
import java.util.List;
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
                "red", 1,
                "green", 2,
                "yellow", 3,
                "blue", 4,
                "purple", 5,
                "blue2", 6,
                "white", 7,
                "default", 2
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

    // ===== NUEVOS ENDPOINTS SEGÚN EL MANUAL DEL FABRICANTE =====

    /**
     * Inicializar red (initNetwork) según el manual del fabricante
     */
    @PostMapping("/init-network")
    public ResponseEntity<PanelResponse> initNetwork(@RequestBody Map<String, Object> initData) {
        long startTime = System.currentTimeMillis();
        
        try {
            String panelIP = (String) initData.get("panelIP");
            Integer port = (Integer) initData.get("port");
            String idCode = (String) initData.get("idCode");
            Integer timeout = (Integer) initData.get("timeout");

            log.info("Inicializando red para panel {}: puerto={}, idCode={}, timeout={}", 
                    panelIP, port, idCode, timeout);

            // Aquí se llamaría a la función initNetwork de la librería Java
            boolean success = panelService.initNetwork(panelIP, port, idCode, timeout);
            long responseTime = System.currentTimeMillis() - startTime;

            PanelResponse response = PanelResponse.builder()
                    .success(success)
                    .message(success ? 
                            "Red inicializada correctamente para panel " + panelIP : 
                            "Error al inicializar red para panel " + panelIP)
                    .responseTime((double) responseTime)
                    .timestamp(LocalDateTime.now())
                    .build();
            return ResponseEntity.ok(response);

        } catch (Exception e) {
            long responseTime = System.currentTimeMillis() - startTime;
            log.error("Error en initNetwork: {}", e.getMessage(), e);
            
            PanelResponse response = PanelResponse.builder()
                    .success(false)
                    .message("Error interno: " + e.getMessage())
                    .responseTime((double) responseTime)
                    .timestamp(LocalDateTime.now())
                    .build();
            return ResponseEntity.ok(response);
        }
    }

    /**
     * Configurar listener (setListener) según el manual del fabricante
     */
    @PostMapping("/set-listener")
    public ResponseEntity<PanelResponse> setListener(@RequestBody Map<String, Object> listenerData) {
        long startTime = System.currentTimeMillis();
        
        try {
            String panelIP = (String) listenerData.get("panelIP");
            Boolean enableListener = (Boolean) listenerData.get("enableListener");
            Integer callbackPort = (Integer) listenerData.get("callbackPort");

            log.info("Configurando listener para panel {}: enable={}, callbackPort={}", 
                    panelIP, enableListener, callbackPort);

            // Aquí se llamaría a la función setListener de la librería Java
            boolean success = panelService.setListener(panelIP, enableListener, callbackPort);
            long responseTime = System.currentTimeMillis() - startTime;

            PanelResponse response = PanelResponse.builder()
                    .success(success)
                    .message(success ? 
                            "Listener configurado correctamente para panel " + panelIP : 
                            "Error al configurar listener para panel " + panelIP)
                    .responseTime((double) responseTime)
                    .timestamp(LocalDateTime.now())
                    .build();
            return ResponseEntity.ok(response);

        } catch (Exception e) {
            long responseTime = System.currentTimeMillis() - startTime;
            log.error("Error en setListener: {}", e.getMessage(), e);
            
            PanelResponse response = PanelResponse.builder()
                    .success(false)
                    .message("Error interno: " + e.getMessage())
                    .responseTime((double) responseTime)
                    .timestamp(LocalDateTime.now())
                    .build();
            return ResponseEntity.ok(response);
        }
    }

    /**
     * Enviar mensaje usando sendMulti según el manual del fabricante
     */
    @PostMapping("/send-multi")
    public ResponseEntity<PanelResponse> sendMulti(@RequestBody Map<String, Object> sendMultiData) {
        long startTime = System.currentTimeMillis();
        
        try {
            String panelIP = (String) sendMultiData.get("panelIP");
            Integer itemNum = (Integer) sendMultiData.get("itemNum");
            @SuppressWarnings("unchecked")
            List<String> texts = (List<String>) sendMultiData.get("texts");
            @SuppressWarnings("unchecked")
            List<Integer> colors = (List<Integer>) sendMultiData.get("colors");
            @SuppressWarnings("unchecked")
            List<Integer> fontSizes = (List<Integer>) sendMultiData.get("fontSizes");
            @SuppressWarnings("unchecked")
            List<Integer> showEffects = (List<Integer>) sendMultiData.get("showEffects");

            log.info("Enviando sendMulti a panel {}: itemNum={}, texts={}, colors={}, fontSizes={}, showEffects={}", 
                    panelIP, itemNum, texts, colors, fontSizes, showEffects);

            // Aquí se llamaría a la función sendMulti de la librería Java
            boolean success = panelService.sendMulti(panelIP, itemNum, texts, colors, fontSizes, showEffects);
            long responseTime = System.currentTimeMillis() - startTime;

            PanelResponse response = PanelResponse.builder()
                    .success(success)
                    .message(success ? 
                            "sendMulti ejecutado correctamente en panel " + panelIP : 
                            "Error al ejecutar sendMulti en panel " + panelIP)
                    .responseTime((double) responseTime)
                    .timestamp(LocalDateTime.now())
                    .build();
            return ResponseEntity.ok(response);

        } catch (Exception e) {
            long responseTime = System.currentTimeMillis() - startTime;
            log.error("Error en sendMulti: {}", e.getMessage(), e);
            
            PanelResponse response = PanelResponse.builder()
                    .success(false)
                    .message("Error interno: " + e.getMessage())
                    .responseTime((double) responseTime)
                    .timestamp(LocalDateTime.now())
                    .build();
            return ResponseEntity.ok(response);
        }
    }

    /**
     * Enviar mensaje con parámetros exactos del manual
     */
    @PostMapping("/send-manual")
    public ResponseEntity<PanelResponse> sendManual(@RequestBody Map<String, Object> manualData) {
        long startTime = System.currentTimeMillis();
        
        try {
            String panelIP = (String) manualData.get("panelIP");
            Integer port = (Integer) manualData.get("port");
            String idCode = (String) manualData.get("idCode");
            Integer timeout = (Integer) manualData.get("timeout");
            Integer cardId = (Integer) manualData.get("cardId");
            Integer windowNo = (Integer) manualData.get("windowNo");
            String message = (String) manualData.get("message");
            Integer color = (Integer) manualData.get("color");
            Integer fontSize = (Integer) manualData.get("fontSize");
            Integer speed = (Integer) manualData.get("speed");
            Integer effect = (Integer) manualData.get("effect");
            Integer stayTime = (Integer) manualData.get("stayTime");
            Integer alignment = (Integer) manualData.get("alignment");

            log.info("Enviando mensaje manual a panel {}: puerto={}, cardId={}, windowNo={}, mensaje='{}'", 
                    panelIP, port, cardId, windowNo, message);

            // Ejecutar flujo completo según el manual
            boolean success = panelService.sendManualMessage(panelIP, port, idCode, timeout, 
                    cardId, windowNo, message, color, fontSize, speed, effect, stayTime, alignment);
            long responseTime = System.currentTimeMillis() - startTime;

            PanelResponse response = PanelResponse.builder()
                    .success(success)
                    .message(success ? 
                            "Mensaje manual enviado correctamente a panel " + panelIP : 
                            "Error al enviar mensaje manual a panel " + panelIP)
                    .responseTime((double) responseTime)
                    .timestamp(LocalDateTime.now())
                    .build();
            return ResponseEntity.ok(response);

        } catch (Exception e) {
            long responseTime = System.currentTimeMillis() - startTime;
            log.error("Error en sendManual: {}", e.getMessage(), e);
            
            PanelResponse response = PanelResponse.builder()
                    .success(false)
                    .message("Error interno: " + e.getMessage())
                    .responseTime((double) responseTime)
                    .timestamp(LocalDateTime.now())
                    .build();
            return ResponseEntity.ok(response);
        }
    }
} 