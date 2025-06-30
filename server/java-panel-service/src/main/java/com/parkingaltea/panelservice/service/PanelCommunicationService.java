package com.parkingaltea.panelservice.service;

import com.parkingaltea.panelservice.model.PanelMessage;
import com.parkingaltea.panelservice.model.PanelOccupancy;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;

import java.net.InetAddress;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.TimeUnit;

/**
 * Servicio de comunicación con paneles LED usando la librería Java del fabricante
 */
@Slf4j
@Service
public class PanelCommunicationService {

    @Value("${panel.service.library.jar-path}")
    private String jarPath;

    @Value("${panel.service.library.timeout}")
    private int timeout;

    @Value("${panel.service.library.retry-attempts}")
    private int retryAttempts;

    @Value("${panel.service.library.retry-delay}")
    private int retryDelay;

    @Value("${panel.service.default.port}")
    private int defaultPort;

    @Value("${panel.service.default.card-id}")
    private int cardId;

    @Value("${panel.service.default.window-no}")
    private int windowNo;

    // Cache de paneles inicializados
    private final ConcurrentHashMap<String, Boolean> initializedPanels = new ConcurrentHashMap<>();

    // Objeto de comunicación con la librería Java
    private Object panelProtocol;

    /**
     * Inicializa la librería Java del fabricante
     */
    public void initializeLibrary() {
        try {
            log.info("Inicializando librería Java de paneles desde: {}", jarPath);
            
            // Aquí se cargaría la librería Java del fabricante
            // Por ahora simulamos la inicialización
            
            log.info("Librería Java inicializada correctamente");
            
        } catch (Exception e) {
            log.error("Error al inicializar librería Java: {}", e.getMessage(), e);
            throw new RuntimeException("No se pudo inicializar la librería Java", e);
        }
    }

    /**
     * Envía un mensaje a un panel específico
     */
    public boolean sendMessage(PanelMessage panelMessage) {
        long startTime = System.currentTimeMillis();
        
        try {
            log.info("Enviando mensaje a panel {}: '{}'", panelMessage.getPanelIP(), panelMessage.getMessage());
            
            // Intentar envío con reintentos
            for (int attempt = 1; attempt <= retryAttempts; attempt++) {
                try {
                    log.debug("Intento {} de {} para panel {}", attempt, retryAttempts, panelMessage.getPanelIP());
                    
                    boolean success = sendMessageToPanel(panelMessage);
                    if (success) {
                        long responseTime = System.currentTimeMillis() - startTime;
                        log.info("Mensaje enviado correctamente a {} en {}ms (intento {})", 
                                panelMessage.getPanelIP(), responseTime, attempt);
                        return true;
                    }
                } catch (Exception e) {
                    log.warn("Error en intento {} para panel {}: {}", 
                            attempt, panelMessage.getPanelIP(), e.getMessage());
                    
                    if (attempt < retryAttempts) {
                        try {
                            TimeUnit.MILLISECONDS.sleep(retryDelay);
                        } catch (InterruptedException ie) {
                            Thread.currentThread().interrupt();
                            break;
                        }
                    }
                }
            }

            log.error("No se pudo enviar mensaje a panel {} después de {} intentos", 
                    panelMessage.getPanelIP(), retryAttempts);
            return false;

        } catch (Exception e) {
            long responseTime = System.currentTimeMillis() - startTime;
            log.error("Error al enviar mensaje a panel {}: {} ({}ms)", 
                    panelMessage.getPanelIP(), e.getMessage(), responseTime, e);
            return false;
        }
    }

    /**
     * Envía información de ocupación a un panel
     */
    public boolean sendOccupancy(PanelOccupancy occupancy) {
        try {
            // Construir mensaje de ocupación
            String message = buildOccupancyMessage(occupancy);
            
            // Crear PanelMessage con la información de ocupación
            PanelMessage panelMessage = PanelMessage.builder()
                    .panelIP(occupancy.getPanelIP())
                    .message(message)
                    .color(getColorForStatus(occupancy.getStatus()))
                    .fontSize(occupancy.getFontSize())
                    .speed(occupancy.getSpeed())
                    .alignment(occupancy.getAlignment())
                    .windowNo(occupancy.getWindowNo())
                    .build();

            return sendMessage(panelMessage);

        } catch (Exception e) {
            log.error("Error al enviar ocupación a panel {}: {}", occupancy.getPanelIP(), e.getMessage(), e);
            return false;
        }
    }

    /**
     * Prueba la conectividad con un panel
     */
    public boolean testPanel(String panelIP) {
        try {
            log.info("Probando conectividad con panel: {}", panelIP);
            
            // Verificar conectividad de red
            if (!isPanelReachable(panelIP)) {
                log.error("Panel {} no es alcanzable", panelIP);
                return false;
            }

            // Intentar inicializar el panel
            if (initializePanel(panelIP)) {
                log.info("Panel {} responde correctamente", panelIP);
                return true;
            } else {
                log.error("Panel {} no responde a la inicialización", panelIP);
                return false;
            }

        } catch (Exception e) {
            log.error("Error al probar panel {}: {}", panelIP, e.getMessage(), e);
            return false;
        }
    }

    /**
     * Verifica si un panel es alcanzable por red
     */
    private boolean isPanelReachable(String panelIP) {
        try {
            InetAddress address = InetAddress.getByName(panelIP);
            return address.isReachable(timeout);
        } catch (Exception e) {
            log.warn("No se pudo verificar conectividad con {}: {}", panelIP, e.getMessage());
            return false;
        }
    }

    /**
     * Verifica si un panel está inicializado
     */
    private boolean isPanelInitialized(String panelIP) {
        return initializedPanels.containsKey(panelIP) && initializedPanels.get(panelIP);
    }

    /**
     * Inicializa un panel específico
     */
    private boolean initializePanel(String panelIP) {
        try {
            log.debug("Inicializando panel: {}", panelIP);
            
            // Aquí se llamaría a la función de inicialización de la librería Java
            // Por ahora simulamos la inicialización
            
            // Simular delay de inicialización
            Thread.sleep(100);
            
            initializedPanels.put(panelIP, true);
            log.debug("Panel {} inicializado correctamente", panelIP);
            return true;

        } catch (Exception e) {
            log.error("Error al inicializar panel {}: {}", panelIP, e.getMessage(), e);
            initializedPanels.put(panelIP, false);
            return false;
        }
    }

    /**
     * Envía un mensaje a un panel usando la librería Java del fabricante
     */
    private boolean sendMessageToPanel(PanelMessage panelMessage) {
        try {
            log.debug("Enviando a panel {}: '{}' con color={}, fontSize={}, speed={}, effect={}, stayTime={}, alignment={}",
                    panelMessage.getPanelIP(), panelMessage.getMessage(), 
                    panelMessage.getColor(), panelMessage.getFontSize(), 
                    panelMessage.getSpeed(), panelMessage.getEffect(), 
                    panelMessage.getStayTime(), panelMessage.getAlignment());

            // Preparar arrays para sendMulti
            String[] texts = {panelMessage.getMessage()};
            int[] colors = {convertColorToPanelFormat(panelMessage.getColor())};
            int[] fontSizes = {panelMessage.getFontSize()};
            int[] showEffects = {convertEffectToPanelFormat(panelMessage.getEffect())};
            
            // Llamar a la función sendMulti correcta
            // boolean sendMulti(int itemNum, String[] texts, int[] colors, int[] fontSizes, int[] showEffects)
            boolean result = sendMulti(panelMessage.getWindowNo(), texts, colors, fontSizes, showEffects);
            
            if (result) {
                log.debug("Mensaje enviado exitosamente a panel {} usando sendMulti", panelMessage.getPanelIP());
                return true;
            } else {
                log.error("Error al enviar mensaje a panel {}: sendMulti retornó false", panelMessage.getPanelIP());
                return false;
            }

        } catch (Exception e) {
            log.error("Error al enviar mensaje a panel {}: {}", panelMessage.getPanelIP(), e.getMessage(), e);
            return false;
        }
    }

    /**
     * Convierte color hexadecimal a formato del panel (1-7)
     */
    private int convertColorToPanelFormat(int hexColor) {
        // Convertir color hexadecimal a formato del panel
        // 1=red, 2=green, 3=yellow, 4=blue, 5=purple, 6=blue, 7=white
        switch (hexColor) {
            case 0x0000FF: // Rojo
                return 1;
            case 0x00FF00: // Verde
                return 2;
            case 0x00FFFF: // Amarillo
                return 3;
            case 0xFF0000: // Azul
                return 4;
            case 0x800080: // Púrpura
                return 5;
            case 0x000080: // Azul oscuro (otro)
                return 6;
            case 0xFFFFFF: // Blanco
                return 7;
            default:
                return 2; // Verde por defecto
        }
    }

    /**
     * Convierte efecto a formato del panel
     */
    private int convertEffectToPanelFormat(int effect) {
        // Mapear efectos del modelo a efectos del panel
        // Los valores exactos dependen de la documentación del fabricante
        switch (effect) {
            case 0: // Sin efecto
                return 0;
            case 1: // Efecto 1
                return 1;
            case 2: // Efecto 2
                return 2;
            case 3: // Efecto 3
                return 3;
            default:
                return 0; // Sin efecto por defecto
        }
    }

    /**
     * Llama a la función sendMulti correcta de la librería Java del fabricante
     * boolean sendMulti(int itemNum, String[] texts, int[] colors, int[] fontSizes, int[] showEffects)
     */
    private boolean sendMulti(int itemNum, String[] texts, int[] colors, int[] fontSizes, int[] showEffects) {
        try {
            // Aquí se implementaría la llamada real a la librería Java del fabricante
            // Por ahora simulamos el envío exitoso
            
            log.debug("Llamando a sendMulti: itemNum={}, texts={}, colors={}, fontSizes={}, showEffects={}", 
                    itemNum, java.util.Arrays.toString(texts), 
                    java.util.Arrays.toString(colors), 
                    java.util.Arrays.toString(fontSizes), 
                    java.util.Arrays.toString(showEffects));
            
            // Simular delay de envío
            Thread.sleep(50);
            
            // Simular éxito (en producción aquí se verificaría la respuesta real)
            return true;
            
        } catch (Exception e) {
            log.error("Error en sendMulti: {}", e.getMessage(), e);
            return false;
        }
    }

    /**
     * Construye el mensaje de ocupación
     */
    private String buildOccupancyMessage(PanelOccupancy occupancy) {
        return String.format("%s\n%d/%d - %s", 
                occupancy.getParkingName(),
                occupancy.getCurrent(),
                occupancy.getTotal(),
                occupancy.getStatus());
    }

    /**
     * Obtiene el color correspondiente al estado del parking
     */
    private int getColorForStatus(String status) {
        switch (status.toUpperCase()) {
            case "LLIURE":
                return 2; // Verde (2)
            case "DENS":
                return 3;   // Amarillo (3)
            case "COMPLET":
                return 1; // Rojo (1)
            default:
                return 2;       // Verde por defecto (2)
        }
    }

    /**
     * Limpia la cache de paneles inicializados
     */
    public void clearInitializedPanels() {
        initializedPanels.clear();
        log.info("Cache de paneles inicializados limpiada");
    }

    /**
     * Obtiene el estado de los paneles inicializados
     */
    public java.util.Map<String, Boolean> getInitializedPanels() {
        return new java.util.HashMap<>(initializedPanels);
    }
} 