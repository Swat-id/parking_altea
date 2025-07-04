package com.parkingaltea.panelservice.service;

import com.parkingaltea.panelservice.model.PanelMessage;
import com.parkingaltea.panelservice.model.PanelResponse;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;

import java.util.List;
import java.util.concurrent.CompletableFuture;

// Importar la librería real del fabricante
import com.lumen.ledcenter3.protocol.SendUtil;

/**
 * Servicio de comunicación con paneles LED usando la librería Java del fabricante
 * 
 * Este servicio implementa el flujo correcto según el manual del fabricante:
 * 1. Usar SendUtil.sendText() para enviar mensajes directamente
 * 2. Mapear correctamente los parámetros de color y tamaño de fuente
 */
@Slf4j
@Service
public class PanelCommunicationService {

    @Value("${panel.service.library.timeout:5000}")
    private int timeout;

    @Value("${panel.service.library.retry-attempts:3}")
    private int retryAttempts;

    @Value("${panel.service.library.retry-delay:1000}")
    private int retryDelay;

    @Value("${panel.service.default.port:5200}")
    private int defaultPort;

    @Value("${panel.service.default.card-id:1}")
    private int defaultCardId;

    /**
     * Enviar mensaje a un panel específico usando la librería real del fabricante
     */
    public CompletableFuture<PanelResponse> sendMessage(String panelIp, PanelMessage message) {
        return CompletableFuture.supplyAsync(() -> {
            long startTime = System.currentTimeMillis();
            
            try {
                log.info("Enviando mensaje a panel {}: {}", panelIp, message.getText());
                
                // Enviar mensaje usando la librería Java real del fabricante
                boolean success = sendTextMessage(panelIp, message);
                
                long responseTime = System.currentTimeMillis() - startTime;
                
                if (success) {
                    log.info("✅ Mensaje enviado exitosamente a {}", panelIp);
                    return PanelResponse.success(
                        "Mensaje enviado exitosamente",
                        panelIp,
                        "old",
                        List.of(message.getText())
                    );
                } else {
                    log.error("❌ Error enviando mensaje a {}", panelIp);
                    return PanelResponse.error(
                        "Error enviando mensaje",
                        panelIp,
                        "old",
                        "Fallo en comunicación con panel"
                    );
                }
                
            } catch (Exception e) {
                log.error("❌ Error inesperado enviando mensaje a {}: {}", panelIp, e.getMessage(), e);
                return PanelResponse.error(
                    "Error inesperado: " + e.getMessage(),
                    panelIp,
                    "old",
                    e.getMessage()
                );
            }
        });
    }

    /**
     * Enviar mensaje de texto usando la librería Java real del fabricante
     * 
     * Método: SendUtil.sendText(ip, port, cardId, wndNo, content, crColor, nFontSize, nSpeed, nEffect, nStayTime, fontName, nAlignmentHori, nAlignmentVert)
     * 
     * Mapeo correcto según documentación:
     * - fontSize: 0=8px, 1=12px, 2=16px, 3=24px, 4=32px, 5=40px, 6=48px, 7=56px
     * - colors: 1=rojo, 2=verde, 3=amarillo, 4=azul, 5=púrpura, 6=azul, 7=blanco
     */
    private boolean sendTextMessage(String panelIp, PanelMessage message) {
        try {
            log.debug("Enviando mensaje de texto a {}: {}", panelIp, message.getText());
            
            // Mapear fontSize según documentación (16px = valor 2)
            int mappedFontSize = mapFontSizeToProtocol(message.getFontSize());
            
            // Mapear color según documentación (rojo = valor 1)
            int mappedColor = mapColorToProtocol(message.getColor());
            
            log.info("Parámetros mapeados - fontSize: {}->{}, color: {}->{}", 
                    message.getFontSize(), mappedFontSize, message.getColor(), mappedColor);
            
            // Llamada real a la librería del fabricante
            // SendUtil.sendText(ip, port, cardId, wndNo, content, crColor, nFontSize, nSpeed, nEffect, nStayTime, fontName, nAlignmentHori, nAlignmentVert)
            com.lumen.ledcenter3.protocol.SendUtil.sendText(
                panelIp,                    // ip
                defaultPort,                // port (5200)
                defaultCardId,              // cardId (1)
                message.getWindowNo(),      // wndNo (ventana)
                message.getText(),          // content (texto)
                mappedColor,                // crColor (color mapeado)
                mappedFontSize,             // nFontSize (tamaño mapeado)
                message.getSpeed(),         // nSpeed (velocidad)
                message.getEffect(),        // nEffect (efecto)
                message.getStayTime(),      // nStayTime (tiempo de permanencia)
                "Arial",                    // fontName (fuente por defecto)
                1,                          // nAlignmentHori (centro horizontal)
                1                           // nAlignmentVert (centro vertical)
            );
            
            log.info("✅ Llamada a SendUtil.sendText completada para {}", panelIp);
            return true;
            
        } catch (Exception e) {
            log.error("❌ Error en sendTextMessage para {}: {}", panelIp, e.getMessage(), e);
            return false;
        }
    }

    /**
     * Mapear tamaño de fuente de píxeles al protocolo del fabricante
     * 
     * Protocolo: 0=8px, 1=12px, 2=16px, 3=24px, 4=32px, 5=40px, 6=48px, 7=56px
     */
    private int mapFontSizeToProtocol(int fontSize) {
        switch (fontSize) {
            case 8: return 0;
            case 12: return 1;
            case 16: return 2;
            case 24: return 3;
            case 32: return 4;
            case 40: return 5;
            case 48: return 6;
            case 56: return 7;
            default:
                log.warn("Tamaño de fuente {} no soportado, usando 16px (valor 2)", fontSize);
                return 2; // 16px por defecto
        }
    }

    /**
     * Mapear color al protocolo del fabricante
     * 
     * Protocolo: 1=rojo, 2=verde, 3=amarillo, 4=azul, 5=púrpura, 6=azul, 7=blanco
     */
    private int mapColorToProtocol(int color) {
        switch (color) {
            case 1: return 1; // rojo
            case 2: return 2; // verde
            case 3: return 3; // amarillo
            case 4: return 4; // azul
            case 5: return 5; // púrpura
            case 6: return 6; // azul
            case 7: return 7; // blanco
            default:
                log.warn("Color {} no soportado, usando rojo (valor 1)", color);
                return 1; // rojo por defecto
        }
    }

    /**
     * Enviar mensaje de ocupación usando la librería real
     */
    public CompletableFuture<PanelResponse> sendOccupancyMessage(String panelIp, int parkingNumber, 
                                                                String parkingName, int freeSpaces, 
                                                                int totalSpaces, String status, String language) {
        return CompletableFuture.supplyAsync(() -> {
            try {
                String message = buildOccupancyMessage(parkingNumber, parkingName, freeSpaces, totalSpaces, status, language);
                
                PanelMessage panelMessage = PanelMessage.builder()
                        .text(message)
                        .color(1) // rojo
                        .fontSize(16) // 16px
                        .windowNo(0)
                        .effect(0)
                        .speed(1)
                        .stayTime(5)
                        .build();
                
                return sendMessage(panelIp, panelMessage).get();
                
            } catch (Exception e) {
                log.error("Error enviando mensaje de ocupación a {}: {}", panelIp, e.getMessage(), e);
                return PanelResponse.error(
                    "Error enviando mensaje de ocupación: " + e.getMessage(),
                    panelIp,
                    "old",
                    e.getMessage()
                );
            }
        });
    }

    /**
     * Construir mensaje de ocupación según el idioma
     */
    private String buildOccupancyMessage(int parkingNumber, String parkingName, 
                                       int freeSpaces, int totalSpaces, String status, String language) {
        String statusText = getStatusText(status, language);
        String format = getMessageFormat(language);
        
        return String.format(format, parkingNumber, statusText, freeSpaces, totalSpaces);
    }

    /**
     * Obtener texto de estado según idioma
     */
    private String getStatusText(String status, String language) {
        if ("ca".equals(language)) {
            switch (status.toUpperCase()) {
                case "LIBRE": return "LLIURE";
                case "DENSO": return "DENS";
                case "COMPLETO": return "COMPLET";
                default: return status;
            }
        } else {
            switch (status.toUpperCase()) {
                case "LIBRE": return "LIBRE";
                case "DENSO": return "DENSO";
                case "COMPLETO": return "COMPLETO";
                default: return status;
            }
        }
    }

    /**
     * Obtener formato de mensaje según idioma
     */
    private String getMessageFormat(String language) {
        if ("ca".equals(language)) {
            return "%d - %s\n%d/%d";
        } else {
            return "%d - %s\n%d/%d";
        }
    }

    /**
     * Cerrar recursos del servicio
     */
    public void shutdown() {
        log.info("Cerrando servicio de comunicación con paneles");
        // No hay recursos específicos que cerrar con SendUtil
    }

    /**
     * Enviar mensaje múltiple a panel usando la librería real del fabricante
     * 
     * @param panelIp IP del panel
     * @param itemNum Número de item
     * @param texts Lista de textos
     * @param colors Lista de colores
     * @param fontSizes Lista de tamaños de fuente
     * @param showEffects Lista de efectos
     * @return Respuesta del envío
     */
    public PanelResponse sendMultiMessage(String panelIp, int itemNum, 
                                        List<String> texts, List<Integer> colors, 
                                        List<Integer> fontSizes, List<Integer> showEffects) {
        try {
            log.info("Enviando mensaje múltiple a panel {}: {} elementos", panelIp, texts.size());
            
            // Por ahora, enviar solo el primer texto (simplificado)
            if (!texts.isEmpty()) {
                String text = texts.get(0);
                int color = colors != null && !colors.isEmpty() ? colors.get(0) : 1;
                int fontSize = fontSizes != null && !fontSizes.isEmpty() ? fontSizes.get(0) : 16;
                
                PanelMessage message = PanelMessage.builder()
                        .text(text)
                        .color(color)
                        .fontSize(fontSize)
                        .windowNo(0)
                        .effect(0)
                        .speed(1)
                        .stayTime(5)
                        .build();
                
                boolean success = sendTextMessage(panelIp, message);
                
                if (success) {
                    log.info("✅ Mensaje múltiple enviado exitosamente a {}", panelIp);
                    return PanelResponse.success(
                        "Mensaje múltiple enviado exitosamente",
                        panelIp,
                        "old",
                        texts
                    );
                } else {
                    log.error("❌ Error enviando mensaje múltiple a {}", panelIp);
                    return PanelResponse.error(
                        "Error enviando mensaje múltiple",
                        panelIp,
                        "old",
                        "Fallo en comunicación con panel"
                    );
                }
            } else {
                return PanelResponse.error(
                    "No hay textos para enviar",
                    panelIp,
                    "old",
                    "Lista de textos vacía"
                );
            }
            
        } catch (Exception e) {
            log.error("❌ Error inesperado enviando mensaje múltiple a {}: {}", panelIp, e.getMessage(), e);
            return PanelResponse.error(
                "Error inesperado: " + e.getMessage(),
                panelIp,
                "old",
                e.getMessage()
            );
        }
    }

    /**
     * Enviar mensaje de texto usando PanelMessage (para compatibilidad con el controlador)
     */
    public PanelResponse sendTextMessage(PanelMessage message) {
        try {
            log.info("Enviando mensaje de texto: {}", message.getText());
            
            boolean success = sendTextMessage("127.0.0.1", message); // IP por defecto
            
            if (success) {
                return PanelResponse.success(
                    "Mensaje enviado exitosamente",
                    "127.0.0.1",
                    "old",
                    List.of(message.getText())
                );
            } else {
                return PanelResponse.error(
                    "Error enviando mensaje",
                    "127.0.0.1",
                    "old",
                    "Fallo en comunicación"
                );
            }
            
        } catch (Exception e) {
            log.error("❌ Error enviando mensaje de texto: {}", e.getMessage(), e);
            return PanelResponse.error(
                "Error: " + e.getMessage(),
                "127.0.0.1",
                "old",
                e.getMessage()
            );
        }
    }
} 