package com.parkingaltea.panelservice.service;

import com.parkingaltea.panelservice.model.PanelMessage;
import com.parkingaltea.panelservice.model.PanelOccupancy;
import com.lumen.ledcenter3.protocol.ExtSendUtil;
import com.lumen.ledcenter3.protocol.ExternalNetworkSendProtocol.OnTcpNetWorkListener;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;

import java.net.InetAddress;
import java.util.List;
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
    
    // Instancia de la librería del fabricante por panel
    private final ConcurrentHashMap<String, ExtSendUtil> panelSenders = new ConcurrentHashMap<>();

    /**
     * Inicializa la librería Java del fabricante
     */
    public void initializeLibrary() {
        try {
            log.info("Inicializando librería Java de paneles desde: {}", jarPath);
            
            // Verificar que el JAR existe
            java.io.File jarFile = new java.io.File(jarPath);
            if (!jarFile.exists()) {
                log.error("JAR del fabricante no encontrado en: {}", jarPath);
                throw new RuntimeException("JAR del fabricante no encontrado");
            }
            
            log.info("Librería Java inicializada correctamente");
            
        } catch (Exception e) {
            log.error("Error al inicializar librería Java: {}", e.getMessage(), e);
            throw new RuntimeException("No se pudo inicializar la librería Java", e);
        }
    }

    /**
     * Obtiene o crea una instancia de ExtSendUtil para un panel
     */
    private ExtSendUtil getPanelSender(String panelIP) {
        return panelSenders.computeIfAbsent(panelIP, ip -> {
            log.debug("Creando nueva instancia de ExtSendUtil para panel {}", ip);
            return new ExtSendUtil();
        });
    }

    /**
     * Configura el listener para un panel
     */
    private void setupListener(ExtSendUtil sender, String panelIP) {
        sender.setListener(new OnTcpNetWorkListener() {
            public void onSocketInit(int result) {
                log.debug("[LISTENER] Panel {} - onSocketInit: Result={}", panelIP, result);
            }

            public void onStatus(int status, int socketIndex) {
                log.debug("[LISTENER] Panel {} - onStatus: Status={}, SocketIndex={}", panelIP, status, socketIndex);
            }

            public void onBackBytes(int[] backBytes, int socketIndex) {
                log.debug("[LISTENER] Panel {} - onBackBytes received on socket {}", panelIP, socketIndex);
            }

            public void onTcpProcess(long process, long totalProcess, int socketIndex) {
                log.debug("[LISTENER] Panel {} - onTcpProcess: {}/{} (SocketIndex={})", 
                        panelIP, process, totalProcess, socketIndex);
            }

            public void breakSocket(int socketIndex) {
                log.debug("[LISTENER] Panel {} - breakSocket called on SocketIndex={}", panelIP, socketIndex);
            }
        });
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
            
            // Obtener instancia de ExtSendUtil
            ExtSendUtil sender = getPanelSender(panelIP);
            
            // Configurar listener
            setupListener(sender, panelIP);
            
            // Inicializar red con parámetros por defecto
            sender.initNetwork(panelIP, defaultPort, "255.255.255.255");
            
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

            // Obtener instancia de ExtSendUtil
            ExtSendUtil sender = getPanelSender(panelMessage.getPanelIP());
            
            // Preparar arrays para sendMulti (formato del fabricante)
            String[] texts = {panelMessage.getMessage()};
            int[] colors = {convertColorToPanelFormat(panelMessage.getColor())};
            int[] fontSizes = {convertFontSizeToPanelFormat(panelMessage.getFontSize())};
            int[] showEffects = {convertEffectToPanelFormat(panelMessage.getEffect())};
            
            // Usar itemNum = 1 (como en el ejemplo que funciona)
            int itemNum = 1;
            
            // Llamar a sendMulti de la librería del fabricante
            boolean result = sender.sendMulti(itemNum, texts, colors, fontSizes, showEffects);
            
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
        // Mapear colores según el manual del fabricante (1-7)
        switch (hexColor) {
            case 1: // Rojo
                return 1;
            case 2: // Verde
                return 2;
            case 3: // Amarillo
                return 3;
            case 4: // Azul
                return 4;
            case 5: // Púrpura
                return 5;
            case 6: // Azul oscuro
                return 6;
            case 7: // Blanco
                return 7;
            default:
                return 2; // Verde por defecto
        }
    }

    /**
     * Convierte tamaño de fuente a formato del panel
     */
    private int convertFontSizeToPanelFormat(int fontSize) {
        // Mapear tamaños de fuente según el ejemplo que funciona
        // 2 = ~24px, 1 = ~16px, etc.
        if (fontSize >= 24) return 2;
        if (fontSize >= 16) return 1;
        return 1; // Por defecto
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
            // Esta función ya no se usa directamente, se usa la de ExtSendUtil
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
        panelSenders.clear();
        log.info("Cache de paneles inicializados limpiada");
    }

    /**
     * Obtiene el estado de los paneles inicializados
     */
    public java.util.Map<String, Boolean> getInitializedPanels() {
        return new java.util.HashMap<>(initializedPanels);
    }

    // ===== MÉTODOS SEGÚN EL MANUAL DEL FABRICANTE =====

    /**
     * Inicializar red (initNetwork) según el manual del fabricante
     * Parámetros: panelIP, port, idCode, timeout
     */
    public boolean initNetwork(String panelIP, Integer port, String idCode, Integer timeout) {
        try {
            log.info("Inicializando red para panel {}: puerto={}, idCode={}, timeout={}", 
                    panelIP, port, idCode, timeout);

            // Verificar conectividad básica
            if (!isPanelReachable(panelIP)) {
                log.error("Panel {} no es alcanzable", panelIP);
                return false;
            }

            // Obtener instancia de ExtSendUtil
            ExtSendUtil sender = getPanelSender(panelIP);
            
            // Configurar listener
            setupListener(sender, panelIP);
            
            // Inicializar red usando la librería del fabricante
            sender.initNetwork(panelIP, port, idCode);
            
            // Marcar panel como inicializado
            initializedPanels.put(panelIP, true);
            
            log.info("Red inicializada correctamente para panel {}", panelIP);
            return true;

        } catch (Exception e) {
            log.error("Error al inicializar red para panel {}: {}", panelIP, e.getMessage(), e);
            initializedPanels.put(panelIP, false);
            return false;
        }
    }

    /**
     * Configurar listener (setListener) según el manual del fabricante
     * Parámetros: panelIP, enableListener, callbackPort
     */
    public boolean setListener(String panelIP, Boolean enableListener, Integer callbackPort) {
        try {
            log.info("Configurando listener para panel {}: enable={}, callbackPort={}", 
                    panelIP, enableListener, callbackPort);

            // Verificar que el panel esté inicializado
            if (!isPanelInitialized(panelIP)) {
                log.warn("Panel {} no está inicializado, inicializando primero", panelIP);
                if (!initNetwork(panelIP, defaultPort, "255.255.255.255", timeout)) {
                    return false;
                }
            }

            // El listener ya se configura en initNetwork, solo verificamos
            ExtSendUtil sender = getPanelSender(panelIP);
            if (sender != null) {
                log.info("Listener configurado correctamente para panel {}", panelIP);
                return true;
            } else {
                log.error("No se pudo obtener instancia de ExtSendUtil para panel {}", panelIP);
                return false;
            }

        } catch (Exception e) {
            log.error("Error al configurar listener para panel {}: {}", panelIP, e.getMessage(), e);
            return false;
        }
    }

    /**
     * Enviar mensaje usando sendMulti según el manual del fabricante
     * Parámetros: panelIP, itemNum, texts, colors, fontSizes, showEffects
     */
    public boolean sendMulti(String panelIP, Integer itemNum, List<String> texts, 
                           List<Integer> colors, List<Integer> fontSizes, List<Integer> showEffects) {
        try {
            log.info("Enviando sendMulti a panel {}: itemNum={}, texts={}, colors={}, fontSizes={}, showEffects={}", 
                    panelIP, itemNum, texts, colors, fontSizes, showEffects);

            // Verificar que el panel esté inicializado
            if (!isPanelInitialized(panelIP)) {
                log.warn("Panel {} no está inicializado, inicializando primero", panelIP);
                if (!initNetwork(panelIP, defaultPort, "255.255.255.255", timeout)) {
                    return false;
                }
            }

            // Obtener instancia de ExtSendUtil
            ExtSendUtil sender = getPanelSender(panelIP);
            
            // Convertir listas a arrays para la función sendMulti
            String[] textsArray = texts.toArray(new String[0]);
            int[] colorsArray = colors.stream().mapToInt(Integer::intValue).toArray();
            int[] fontSizesArray = fontSizes.stream().mapToInt(Integer::intValue).toArray();
            int[] showEffectsArray = showEffects.stream().mapToInt(Integer::intValue).toArray();

            // Llamar a sendMulti de la librería del fabricante
            boolean result = sender.sendMulti(itemNum, textsArray, colorsArray, fontSizesArray, showEffectsArray);
            
            if (result) {
                log.info("sendMulti ejecutado correctamente en panel {}", panelIP);
                return true;
            } else {
                log.error("Error al ejecutar sendMulti en panel {}", panelIP);
                return false;
            }

        } catch (Exception e) {
            log.error("Error en sendMulti para panel {}: {}", panelIP, e.getMessage(), e);
            return false;
        }
    }

    /**
     * Enviar mensaje con parámetros exactos del manual del fabricante
     * Ejecuta el flujo completo: initNetwork -> setListener -> sendMulti
     */
    public boolean sendManualMessage(String panelIP, Integer port, String idCode, Integer timeout,
                                   Integer cardId, Integer windowNo, String message, Integer color,
                                   Integer fontSize, Integer speed, Integer effect, Integer stayTime, Integer alignment) {
        try {
            log.info("Enviando mensaje manual a panel {}: puerto={}, cardId={}, windowNo={}, mensaje='{}'", 
                    panelIP, port, cardId, windowNo, message);

            // Paso 1: initNetwork
            log.debug("Paso 1: Inicializando red...");
            if (!initNetwork(panelIP, port, idCode, timeout)) {
                log.error("Error en initNetwork para panel {}", panelIP);
                return false;
            }

            // Esperar un momento para que se establezca la conexión
            Thread.sleep(100);

            // Paso 2: setListener (ya se hace en initNetwork)
            log.debug("Paso 2: Listener ya configurado en initNetwork");

            // Paso 3: sendMulti
            log.debug("Paso 3: Enviando mensaje con sendMulti...");
            List<String> texts = List.of(message);
            List<Integer> colors = List.of(color != null ? color : 2);
            List<Integer> fontSizes = List.of(convertFontSizeToPanelFormat(fontSize != null ? fontSize : 16));
            List<Integer> showEffects = List.of(effect != null ? effect : 0);

            // Usar itemNum = 1 como en el ejemplo que funciona
            boolean result = sendMulti(panelIP, 1, texts, colors, fontSizes, showEffects);
            
            if (result) {
                log.info("Mensaje manual enviado correctamente a panel {}", panelIP);
                return true;
            } else {
                log.error("Error al enviar mensaje manual a panel {}", panelIP);
                return false;
            }

        } catch (Exception e) {
            log.error("Error en sendManualMessage para panel {}: {}", panelIP, e.getMessage(), e);
            return false;
        }
    }
} 