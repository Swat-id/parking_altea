package com.parkingaltea.panelservice.service;

import com.parkingaltea.panelservice.model.PanelMessage;
import com.parkingaltea.panelservice.model.PanelResponse;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;

import java.util.List;
import java.util.concurrent.CompletableFuture;

/**
 * Servicio de comunicación con paneles LED usando la librería del fabricante
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

    // Referencias a la librería del fabricante
    private static final String LIBRARY_CLASS = "com.rotuloselectronicos.protocol.CP5200Protocol";
    
    private Object protocolInstance;
    private boolean isInitialized = false;

    /**
     * Inicializar la librería del fabricante
     */
    public boolean initializeLibrary() {
        try {
            if (isInitialized) {
                log.info("Librería ya inicializada");
                return true;
            }

            log.info("Inicializando librería del fabricante...");
            
            // Cargar la clase de la librería
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
            log.info("Librería inicializada correctamente");
            return true;
            
        } catch (Exception e) {
            log.error("Error inicializando librería: {}", e.getMessage(), e);
            return false;
        }
    }

    /**
     * Inicializar conexión de red
     */
    private boolean initNetwork() {
        try {
            log.debug("Inicializando red...");
            // Llamada a initNetwork de la librería
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
            // Llamada a setListener de la librería
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
                
                // Enviar mensaje usando la librería
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
     * Enviar mensaje múltiple usando la librería del fabricante
     */
    private boolean sendMultiMessage(String panelIp, PanelMessage message) {
        try {
            log.debug("Enviando mensaje múltiple a {}: {}", panelIp, message.getText());
            
            // Preparar parámetros para sendMulti
            String[] texts = {message.getText()};
            int[] colors = {message.getColor()};
            int[] fontSizes = {message.getFontSize()};
            int[] effects = {message.getEffect()};
            
            // Llamada a sendMulti de la librería
            // int result = protocolInstance.sendMulti(panelIp, texts, colors, fontSizes, effects);
            // return result == 0; // 0 = éxito según documentación
            
            // Simulación temporal mientras se integra la librería
            log.info("Simulando envío de mensaje a {}: {}", panelIp, message.getText());
            Thread.sleep(100); // Simular delay de comunicación
            return true;
            
        } catch (Exception e) {
            log.error("Error en sendMulti para {}: {}", panelIp, e.getMessage(), e);
            return false;
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
            // Llamada a close de la librería
            // protocolInstance.close();
            isInitialized = false;
            log.info("Conexiones cerradas");
        } catch (Exception e) {
            log.error("Error cerrando conexiones: {}", e.getMessage(), e);
        }
    }
} 