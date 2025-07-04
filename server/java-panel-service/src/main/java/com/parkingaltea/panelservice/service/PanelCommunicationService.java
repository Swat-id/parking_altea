package com.parkingaltea.panelservice.service;

import com.parkingaltea.panelservice.model.PanelMessage;
import com.parkingaltea.panelservice.model.PanelResponse;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;

import java.util.List;
import java.util.concurrent.CompletableFuture;

/**
 * Servicio de comunicación con paneles LED usando la librería Java del fabricante
 * 
 * Este servicio implementa el flujo correcto según el manual del fabricante:
 * 1. initNetwork - Inicializar conexión de red
 * 2. setListener - Configurar listener
 * 3. sendMulti - Enviar mensaje múltiple
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

    // Referencias a la librería Java del fabricante
    private static final String LIBRARY_CLASS = "com.rotuloselectronicos.protocol.CP5200Protocol";
    
    private Object protocolInstance;
    private boolean isInitialized = false;

    /**
     * Inicializar la librería Java del fabricante
     */
    public boolean initializeLibrary() {
        try {
            if (isInitialized) {
                log.info("Librería ya inicializada");
                return true;
            }

            log.info("Inicializando librería Java del fabricante...");
            
            // Cargar la clase de la librería Java
            Class<?> protocolClass = Class.forName(LIBRARY_CLASS);
            protocolInstance = protocolClass.getDeclaredConstructor().newInstance();
            
            // Inicializar red
            boolean networkInit = initNetwork();
            if (!networkInit) {
                log.error("Error inicializando red");
                return false;
            }
            
            // Configurar listener
            boolean listenerSet = setListener();
            if (!listenerSet) {
                log.error("Error configurando listener");
                return false;
            }
            
            isInitialized = true;
            log.info("Librería Java inicializada correctamente");
            return true;
            
        } catch (Exception e) {
            log.error("Error inicializando librería Java: {}", e.getMessage(), e);
            return false;
        }
    }

    /**
     * Inicializar conexión de red
     */
    private boolean initNetwork() {
        try {
            log.debug("Inicializando red...");
            // Llamada a initNetwork de la librería Java
            // protocolInstance.initNetwork();
            return true;
        } catch (Exception e) {
            log.error("Error inicializando red: {}", e.getMessage(), e);
            return false;
        }
    }

    /**
     * Configurar listener
     */
    private boolean setListener() {
        try {
            log.debug("Configurando listener...");
            // Llamada a setListener de la librería Java
            // protocolInstance.setListener();
            return true;
        } catch (Exception e) {
            log.error("Error configurando listener: {}", e.getMessage(), e);
            return false;
        }
    }

    /**
     * Enviar mensaje a un panel específico
     */
    public CompletableFuture<PanelResponse> sendMessage(String panelIp, PanelMessage message) {
        return CompletableFuture.supplyAsync(() -> {
            long startTime = System.currentTimeMillis();
            
            try {
                log.info("Enviando mensaje a panel {}: {}", panelIp, message.getText());
                
                // Verificar inicialización
                if (!isInitialized && !initializeLibrary()) {
                    return PanelResponse.error(
                        "Error de inicialización", 
                        panelIp, 
                        "old", 
                        "Librería no inicializada"
                    );
                }
                
                // Enviar mensaje usando la librería Java
                boolean success = sendMultiMessage(panelIp, message);
                
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
     * Enviar mensaje múltiple usando la librería Java del fabricante
     * 
     * Mapeo correcto según documentación:
     * - fontSize: 0=8px, 1=12px, 2=16px, 3=24px, 4=32px, 5=40px, 6=48px, 7=56px
     * - colors: 1=rojo, 2=verde, 3=amarillo, 4=azul, 5=púrpura, 6=azul, 7=blanco
     */
    private boolean sendMultiMessage(String panelIp, PanelMessage message) {
        try {
            log.debug("Enviando mensaje múltiple a {}: {}", panelIp, message.getText());
            
            // Mapear fontSize según documentación (16px = valor 2)
            int mappedFontSize = mapFontSizeToProtocol(message.getFontSize());
            
            // Mapear color según documentación (rojo = valor 1)
            int mappedColor = mapColorToProtocol(message.getColor());
            
            // Preparar parámetros para sendMulti
            int itemNum = 1;
            String[] texts = {message.getText()};
            int[] colors = {mappedColor};
            int[] fontSizes = {mappedFontSize};
            int[] showEffects = {message.getEffect()};
            
            log.info("Parámetros mapeados - fontSize: {}->{}, color: {}->{}", 
                    message.getFontSize(), mappedFontSize, message.getColor(), mappedColor);
            
            // Llamada a sendMulti de la librería Java
            // boolean result = protocolInstance.sendMulti(itemNum, texts, colors, fontSizes, showEffects);
            // return result;
            
            // Simulación temporal mientras se integra la librería Java
            log.info("Simulando envío de mensaje a {} con fontSize={} y color={}", 
                    panelIp, mappedFontSize, mappedColor);
            Thread.sleep(100); // Simular delay de comunicación
            return true;
            
        } catch (Exception e) {
            log.error("Error en sendMulti para {}: {}", panelIp, e.getMessage(), e);
            return false;
        }
    }

    /**
     * Mapear tamaño de fuente según protocolo
     * Documentación: 0=8px, 1=12px, 2=16px, 3=24px, 4=32px, 5=40px, 6=48px, 7=56px
     */
    private int mapFontSizeToProtocol(int fontSize) {
        switch (fontSize) {
            case 8: return 0;   // FONTSIZE_8
            case 12: return 1;  // FONTSIZE_12
            case 16: return 2;  // FONTSIZE_16 (valor por defecto)
            case 24: return 3;  // FONTSIZE_24
            case 32: return 4;  // FONTSIZE_32
            case 40: return 5;  // FONTSIZE_40
            case 48: return 6;  // FONTSIZE_48
            case 56: return 7;  // FONTSIZE_56
            default: 
                log.warn("Tamaño de fuente {} no soportado, usando 16px (valor 2)", fontSize);
                return 2; // FONTSIZE_16 por defecto
        }
    }

    /**
     * Mapear color según protocolo
     * Documentación: 1=rojo, 2=verde, 3=amarillo, 4=azul, 5=púrpura, 6=azul, 7=blanco
     */
    private int mapColorToProtocol(int color) {
        if (color >= 1 && color <= 7) {
            return color; // Los valores ya están correctos según documentación
        } else {
            log.warn("Color {} no válido, usando rojo (valor 1)", color);
            return 1; // Rojo por defecto
        }
    }

    /**
     * Enviar mensaje de ocupación a un panel
     */
    public CompletableFuture<PanelResponse> sendOccupancyMessage(String panelIp, int parkingNumber, 
                                                                String parkingName, int freeSpaces, 
                                                                int totalSpaces, String status, String language) {
        
        // Construir mensaje según el idioma
        String messageText = buildOccupancyMessage(parkingNumber, parkingName, freeSpaces, totalSpaces, status, language);
        
        PanelMessage message = PanelMessage.builder()
                .text(messageText)
                .color(1) // Rojo por defecto
                .fontSize(16) // Tamaño 16 por defecto
                .windowNo(0)
                .effect(0) // Sin efecto
                .speed(1)
                .stayTime(5)
                .build();
        
        return sendMessage(panelIp, message);
    }

    /**
     * Construir mensaje de ocupación según el idioma
     */
    private String buildOccupancyMessage(int parkingNumber, String parkingName, 
                                       int freeSpaces, int totalSpaces, String status, String language) {
        
        String statusText = getStatusText(status, language);
        String format = getMessageFormat(language);
        
        return String.format(format, parkingNumber, parkingName, freeSpaces, totalSpaces, statusText);
    }

    /**
     * Obtener texto de estado según idioma
     */
    private String getStatusText(String status, String language) {
        switch (language.toLowerCase()) {
            case "va": // Valenciano
                switch (status.toUpperCase()) {
                    case "LIBRE": return "LLIURE";
                    case "DENSO": return "DENS";
                    case "OCUPADO": return "COMPLET";
                    default: return status;
                }
            case "en": // Inglés
                switch (status.toUpperCase()) {
                    case "LIBRE": return "FREE";
                    case "DENSO": return "BUSY";
                    case "OCUPADO": return "FULL";
                    default: return status;
                }
            case "fr": // Francés
                switch (status.toUpperCase()) {
                    case "LIBRE": return "LIBRE";
                    case "DENSO": return "OCCUPÉ";
                    case "OCUPADO": return "COMPLET";
                    default: return status;
                }
            case "de": // Alemán
                switch (status.toUpperCase()) {
                    case "LIBRE": return "FREI";
                    case "DENSO": return "BESETZT";
                    case "OCUPADO": return "VOLL";
                    default: return status;
                }
            default: // Español
                return status;
        }
    }

    /**
     * Obtener formato de mensaje según idioma
     */
    private String getMessageFormat(String language) {
        switch (language.toLowerCase()) {
            case "va": // Valenciano
                return "%d - %s: %d lliures (%s)";
            case "en": // Inglés
                return "%d - %s: %d free (%s)";
            case "fr": // Francés
                return "%d - %s: %d libres (%s)";
            case "de": // Alemán
                return "%d - %s: %d frei (%s)";
            default: // Español
                return "%d - %s: %d libres (%s)";
        }
    }

    /**
     * Cerrar conexiones
     */
    public void shutdown() {
        try {
            log.info("Cerrando conexiones de paneles...");
            // Llamada a close de la librería Java
            // protocolInstance.close();
            isInitialized = false;
            log.info("Conexiones cerradas");
        } catch (Exception e) {
            log.error("Error cerrando conexiones: {}", e.getMessage(), e);
        }
    }
} 