package com.parkingaltea.panelservice.controller;

import com.parkingaltea.panelservice.model.PanelMessage;
import com.parkingaltea.panelservice.model.PanelResponse;
import com.parkingaltea.panelservice.model.SendMultiRequest;
import com.parkingaltea.panelservice.service.PanelCommunicationService;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import javax.validation.Valid;
import java.util.List;
import java.util.concurrent.CompletableFuture;

/**
 * Controlador REST para comunicación con paneles LED
 * 
 * Endpoints disponibles:
 * - POST /sendMulti - Enviar mensaje múltiple usando sendMulti
 * - POST /sendText - Enviar mensaje simple usando sendText
 * - GET /health - Estado del servicio
 * - GET /status - Estado de conexión con paneles
 */
@Slf4j
@RestController
@RequestMapping("/api/v1/panels")
@CrossOrigin(origins = "*")
public class PanelController {

    @Autowired
    private PanelCommunicationService panelService;

    /**
     * Endpoint de salud del servicio
     */
    @GetMapping("/health")
    public ResponseEntity<String> health() {
        log.info("✅ Health check solicitado");
        return ResponseEntity.ok("Panel Service OK - Protocolo Antiguo");
    }

    /**
     * Endpoint de estado del servicio
     */
    @GetMapping("/status")
    public ResponseEntity<String> status() {
        log.info("Status check solicitado");
        return ResponseEntity.ok("Panel Service Running - Protocol: OLD (Java Library)");
    }

    /**
     * Enviar mensaje múltiple a panel (protocolo antiguo)
     * 
     * @param ip IP del panel
     * @param itemNum Número de item
     * @param request DTO con arrays de textos, colores, tamaños y efectos
     * @return Respuesta del envío
     */
    @PostMapping("/sendMulti")
    public ResponseEntity<PanelResponse> sendMulti(
            @RequestParam String ip,
            @RequestParam int itemNum,
            @RequestBody SendMultiRequest request) {
        
        log.info("📤 Enviando mensaje múltiple a panel {}:{} - itemNum: {}", ip, 5000, itemNum);
        log.info("📝 Textos: {}", request.getTexts());
        log.info("🎨 Colores: {}", request.getColors());
        log.info("📏 Tamaños: {}", request.getFontSizes());
        log.info("✨ Efectos: {}", request.getShowEffects());
        
        try {
            PanelResponse response = panelService.sendMultiMessage(
                ip, 
                itemNum,
                request.getTexts(),
                request.getColors(),
                request.getFontSizes(),
                request.getShowEffects()
            );
            
            log.info("✅ Mensaje enviado exitosamente a panel {}", ip);
            return ResponseEntity.ok(response);
            
        } catch (Exception e) {
            log.error("❌ Error enviando mensaje a panel {}: {}", ip, e.getMessage(), e);
            return ResponseEntity.badRequest().body(
                PanelResponse.builder()
                    .success(false)
                    .message("Error: " + e.getMessage())
                    .build()
            );
        }
    }

    /**
     * Enviar mensaje simple usando sendText
     * 
     * Parámetros según protocolo:
     * - nWndNo: número de ventana (0-7)
     * - content: texto
     * - crColor: color (1=rojo, 2=verde, 3=amarillo, 4=azul, 5=púrpura, 6=azul, 7=blanco)
     * - nFontSize: tamaño de fuente (0=8px, 2=16px, 3=24px, 4=32px, 5=40px, 6=48px, 7=56px)
     * - nSpeed: velocidad (1-100)
     * - nEffect: efecto
     * - nStayTime: tiempo de permanencia en segundos
     * - nAlignmentHori: alineación horizontal (0=izquierda, 1=centro, 2=derecha)
     * - nAlignmentVert: alineación vertical (0=arriba, 1=centro, 2=abajo)
     */
    @PostMapping("/sendText")
    public ResponseEntity<PanelResponse> sendText(
            @RequestParam String ip,
            @RequestParam(defaultValue = "0") int nWndNo,
            @RequestParam String content,
            @RequestParam(defaultValue = "1") int crColor,
            @RequestParam(defaultValue = "2") int nFontSize,
            @RequestParam(defaultValue = "1") int nSpeed,
            @RequestParam(defaultValue = "0") int nEffect,
            @RequestParam(defaultValue = "5") int nStayTime,
            @RequestParam(defaultValue = "1") int nAlignmentHori,
            @RequestParam(defaultValue = "1") int nAlignmentVert) {
        
        log.info("Enviando mensaje simple a {}: '{}'", ip, content);
        
        try {
            // Mapear nFontSize del protocolo a píxeles
            int fontSizePixels = mapProtocolFontSizeToPixels(nFontSize);
            
            // Crear mensaje
            PanelMessage message = PanelMessage.builder()
                    .text(content)
                    .color(crColor)
                    .fontSize(fontSizePixels)
                    .windowNo(nWndNo)
                    .effect(nEffect)
                    .speed(nSpeed)
                    .stayTime(nStayTime)
                    .build();
            
            // Enviar mensaje
            CompletableFuture<PanelResponse> future = panelService.sendMessage(ip, message);
            PanelResponse response = future.get();
            
            log.info("Respuesta del envío: {}", response.getMessage());
            return ResponseEntity.ok(response);
            
        } catch (Exception e) {
            log.error("Error enviando mensaje simple: {}", e.getMessage(), e);
            return ResponseEntity.internalServerError().body(
                PanelResponse.error("Error interno", ip, "old", e.getMessage())
            );
        }
    }

    /**
     * Enviar mensaje usando el modelo PanelMessage
     */
    @PostMapping("/send")
    public ResponseEntity<PanelResponse> sendMessage(
            @RequestParam String ip,
            @Valid @RequestBody PanelMessage message) {
        
        log.info("📤 Enviando mensaje simple a panel {}: {}", ip, message.getText());
        
        try {
            PanelResponse response = panelService.sendTextMessage(message);
            log.info("✅ Mensaje enviado exitosamente");
            return ResponseEntity.ok(response);
            
        } catch (Exception e) {
            log.error("❌ Error enviando mensaje: {}", e.getMessage(), e);
            return ResponseEntity.badRequest().body(
                PanelResponse.builder()
                    .success(false)
                    .message("Error: " + e.getMessage())
                    .build()
            );
        }
    }

    /**
     * Enviar mensaje de ocupación
     */
    @PostMapping("/occupancy")
    public ResponseEntity<PanelResponse> sendOccupancy(
            @RequestParam String ip,
            @RequestParam int parkingNumber,
            @RequestParam String parkingName,
            @RequestParam int freeSpaces,
            @RequestParam int totalSpaces,
            @RequestParam String status,
            @RequestParam(defaultValue = "es") String language) {
        
        log.info("Enviando ocupación a {}: {} - {} libres de {}", ip, parkingName, freeSpaces, totalSpaces);
        
        try {
            CompletableFuture<PanelResponse> future = panelService.sendOccupancyMessage(
                ip, parkingNumber, parkingName, freeSpaces, totalSpaces, status, language
            );
            PanelResponse response = future.get();
            
            log.info("Respuesta del envío: {}", response.getMessage());
            return ResponseEntity.ok(response);
            
        } catch (Exception e) {
            log.error("Error enviando ocupación: {}", e.getMessage(), e);
            return ResponseEntity.internalServerError().body(
                PanelResponse.error("Error interno", ip, "old", e.getMessage())
            );
        }
    }

    /**
     * Mapear tamaño de fuente del protocolo a píxeles
     * Protocolo: 0=8px, 2=16px, 3=24px, 4=32px, 5=40px, 6=48px, 7=56px
     */
    private int mapProtocolFontSizeToPixels(int protocolFontSize) {
        switch (protocolFontSize) {
            case 0: return 8;   // FONTSIZE_8
            case 1: return 12;  // FONTSIZE_12
            case 2: return 16;  // FONTSIZE_16
            case 3: return 24;  // FONTSIZE_24
            case 4: return 32;  // FONTSIZE_32
            case 5: return 40;  // FONTSIZE_40
            case 6: return 48;  // FONTSIZE_48
            case 7: return 56;  // FONTSIZE_56
            default: 
                log.warn("Tamaño de fuente del protocolo {} no válido, usando 16px", protocolFontSize);
                return 16; // FONTSIZE_16 por defecto
        }
    }
} 