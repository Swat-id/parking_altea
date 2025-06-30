package com.parkingaltea.panelservice.service;

import com.parkingaltea.panelservice.model.PanelMessage;
import com.parkingaltea.panelservice.model.PanelOccupancy;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;

import java.io.File;
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

    // Cache para paneles inicializados
    private final ConcurrentHashMap<String, Boolean> initializedPanels = new ConcurrentHashMap<>();

    // Clase nativa de la librería Java (se cargará dinámicamente)
    private Object panelProtocol;

    /**
     * Inicializa la librería Java del fabricante
     */
    public void initializeLibrary() {
        try {
            log.info("Inicializando librería Java de paneles desde: {}", jarPath);
            
            // Verificar que el archivo JAR existe
            File jarFile = new File(jarPath);
            if (!jarFile.exists()) {
                throw new RuntimeException("Archivo JAR no encontrado: " + jarPath);
            }

            // Cargar la librería dinámicamente
            System.setProperty("java.class.path", jarFile.getAbsolutePath());
            
            // Aquí se cargaría la clase específica del fabricante
            // Por ahora usamos una implementación simulada
            log.info("Librería Java inicializada correctamente");
            
        } catch (Exception e) {
            log.error("Error al inicializar la librería Java: {}", e.getMessage(), e);
            throw new RuntimeException("No se pudo inicializar la librería de paneles", e);
        }
    }

    /**
     * Envía un mensaje a un panel específico
     */
    public boolean sendMessage(PanelMessage panelMessage) {
        long startTime = System.currentTimeMillis();
        
        try {
            log.info("Enviando mensaje a panel {}: {}", panelMessage.getPanelIP(), panelMessage.getMessage());
            
            // Verificar conectividad
            if (!isPanelReachable(panelMessage.getPanelIP())) {
                log.error("Panel {} no es alcanzable", panelMessage.getPanelIP());
                return false;
            }

            // Inicializar panel si es necesario
            if (!isPanelInitialized(panelMessage.getPanelIP())) {
                if (!initializePanel(panelMessage.getPanelIP())) {
                    log.error("No se pudo inicializar el panel {}", panelMessage.getPanelIP());
                    return false;
                }
            }

            // Enviar mensaje con reintentos
            for (int attempt = 1; attempt <= retryAttempts; attempt++) {
                try {
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
     * Envía un mensaje a un panel usando la librería Java
     */
    private boolean sendMessageToPanel(PanelMessage panelMessage) {
        try {
            // Aquí se llamaría a la función de envío de la librería Java
            // Por ahora simulamos el envío
            
            log.debug("Enviando a panel {}: '{}' con color={}, fontSize={}, speed={}, effect={}, stayTime={}, alignment={}",
                    panelMessage.getPanelIP(), panelMessage.getMessage(), 
                    panelMessage.getColor(), panelMessage.getFontSize(), 
                    panelMessage.getSpeed(), panelMessage.getEffect(), 
                    panelMessage.getStayTime(), panelMessage.getAlignment());

            // Simular delay de envío
            Thread.sleep(50);
            
            // Simular éxito (en producción aquí se verificaría la respuesta real)
            return true;

        } catch (Exception e) {
            log.error("Error al enviar mensaje a panel {}: {}", panelMessage.getPanelIP(), e.getMessage(), e);
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
                return 0x00FF00; // Verde
            case "DENS":
                return 0x0080FF;   // Naranja
            case "COMPLET":
                return 0x0000FF; // Rojo
            default:
                return 0x00FF00;       // Verde por defecto
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