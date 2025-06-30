package com.parkingaltea.panelservice.service;

import com.lumen.ledcenter3.protocol.ExtSendUtil;
import com.lumen.ledcenter3.protocol.ExternalNetworkSendProtocol.OnTcpNetWorkListener;
import com.parkingaltea.panelservice.model.PanelMessage;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;

import java.util.concurrent.ConcurrentHashMap;

/**
 * Servicio para comunicación con paneles LED basado en el código ejemplo
 */
@Slf4j
@Service
public class PanelService {

    @Value("${panel.service.default.port:5200}")
    private int defaultPort;

    @Value("${panel.service.default.card-id:1}")
    private int cardId;

    @Value("${panel.service.default.window-no:0}")
    private int windowNo;

    // Cache de instancias de ExtSendUtil por panel
    private final ConcurrentHashMap<String, ExtSendUtil> panelSenders = new ConcurrentHashMap<>();

    /**
     * Envía un mensaje a un panel específico
     */
    public boolean sendMessage(PanelMessage panelMessage) {
        long startTime = System.currentTimeMillis();
        
        try {
            log.info("Enviando mensaje a panel {}: '{}'", panelMessage.getPanelIP(), panelMessage.getMessage());
            
            // 1️⃣ Obtener o crear instancia de ExtSendUtil
            ExtSendUtil sender = getPanelSender(panelMessage.getPanelIP());
            
            // 2️⃣ Inicializar red si no está inicializada
            if (!isPanelInitialized(panelMessage.getPanelIP())) {
                log.debug("Inicializando red para panel: {}", panelMessage.getPanelIP());
                sender.initNetwork(panelMessage.getPanelIP(), defaultPort, "255.255.255.255");
                
                // 3️⃣ Configurar listener
                setupListener(sender, panelMessage.getPanelIP());
                
                // Marcar como inicializado
                markPanelAsInitialized(panelMessage.getPanelIP());
            }
            
            // 4️⃣ Preparar arrays para sendMulti
            int itemNum = panelMessage.getItemNum();
            String[] texts = {panelMessage.getMessage()};
            int[] colors = {panelMessage.getColor()};
            int[] fontSizes = {panelMessage.getFontSize()};
            int[] showEffects = {panelMessage.getEffect()};
            
            // 5️⃣ Enviar texto con sendMulti
            log.debug("Enviando sendMulti: itemNum={}, texts={}, colors={}, fontSizes={}, showEffects={}", 
                    itemNum, java.util.Arrays.toString(texts), 
                    java.util.Arrays.toString(colors), 
                    java.util.Arrays.toString(fontSizes), 
                    java.util.Arrays.toString(showEffects));
            
            boolean result = sender.sendMulti(itemNum, texts, colors, fontSizes, showEffects);
            
            long responseTime = System.currentTimeMillis() - startTime;
            
            if (result) {
                log.info("Mensaje enviado correctamente a {} en {}ms", panelMessage.getPanelIP(), responseTime);
                return true;
            } else {
                log.error("Error al enviar mensaje a panel {} en {}ms", panelMessage.getPanelIP(), responseTime);
                return false;
            }

        } catch (Exception e) {
            long responseTime = System.currentTimeMillis() - startTime;
            log.error("Error al enviar mensaje a panel {}: {} ({}ms)", 
                    panelMessage.getPanelIP(), e.getMessage(), responseTime, e);
            return false;
        }
    }

    /**
     * Obtiene o crea una instancia de ExtSendUtil para un panel
     */
    private ExtSendUtil getPanelSender(String panelIP) {
        return panelSenders.computeIfAbsent(panelIP, ip -> {
            log.debug("Creando nueva instancia de ExtSendUtil para panel: {}", ip);
            return new ExtSendUtil();
        });
    }

    /**
     * Configura el listener para un panel
     */
    private void setupListener(ExtSendUtil sender, String panelIP) {
        sender.setListener(new OnTcpNetWorkListener() {
            @Override
            public void onSocketInit(int result) {
                log.debug("[LISTENER] Panel {} - onSocketInit: {}", panelIP, result == 1 ? "SUCCESS" : "FAIL");
            }

            @Override
            public void onStatus(int status, int socketIndex) {
                log.debug("[LISTENER] Panel {} - onStatus: Status={}, SocketIndex={}", panelIP, status, socketIndex);
            }

            public void onBackBytes(int[] backBytes, int socketIndex) {
                log.debug("[LISTENER] Panel {} - onBackBytes received on socket {}", panelIP, socketIndex);
            }

            @Override
            public void onTcpProcess(long process, long totalProcess, int socketIndex) {
                log.debug("[LISTENER] Panel {} - onTcpProcess: {}/{} (SocketIndex={})", 
                        panelIP, process, totalProcess, socketIndex);
            }

            @Override
            public void breakSocket(int socketIndex) {
                log.debug("[LISTENER] Panel {} - breakSocket called on SocketIndex={}", panelIP, socketIndex);
            }
        });
    }

    /**
     * Verifica si un panel está inicializado
     */
    private boolean isPanelInitialized(String panelIP) {
        // Por simplicidad, asumimos que si existe en el cache está inicializado
        // En una implementación más robusta, podríamos mantener un estado separado
        return panelSenders.containsKey(panelIP);
    }

    /**
     * Marca un panel como inicializado
     */
    private void markPanelAsInitialized(String panelIP) {
        log.debug("Panel {} marcado como inicializado", panelIP);
    }

    /**
     * Limpia la cache de paneles
     */
    public void clearCache() {
        panelSenders.clear();
        log.info("Cache de paneles limpiada");
    }

    /**
     * Obtiene el estado de la cache
     */
    public java.util.Map<String, Boolean> getCacheStatus() {
        java.util.Map<String, Boolean> status = new java.util.HashMap<>();
        panelSenders.keySet().forEach(ip -> status.put(ip, true));
        return status;
    }

    /**
     * Prueba la conectividad con un panel específico
     */
    public boolean testPanel(String panelIP) {
        long startTime = System.currentTimeMillis();
        
        try {
            log.info("Probando conectividad con panel: {}", panelIP);
            
            // Crear una instancia temporal para la prueba
            ExtSendUtil testSender = new ExtSendUtil();
            
            // Configurar listener básico
            testSender.setListener(new OnTcpNetWorkListener() {
                @Override
                public void onSocketInit(int result) {
                    log.debug("[TEST] Panel {} - onSocketInit: {}", panelIP, result == 1 ? "SUCCESS" : "FAIL");
                }

                @Override
                public void onStatus(int status, int socketIndex) {
                    log.debug("[TEST] Panel {} - onStatus: Status={}, SocketIndex={}", panelIP, status, socketIndex);
                }

                public void onBackBytes(int[] backBytes, int socketIndex) {
                    log.debug("[TEST] Panel {} - onBackBytes received on socket {}", panelIP, socketIndex);
                }

                @Override
                public void onTcpProcess(long process, long totalProcess, int socketIndex) {
                    log.debug("[TEST] Panel {} - onTcpProcess: {}/{} (SocketIndex={})", 
                            panelIP, process, totalProcess, socketIndex);
                }

                @Override
                public void breakSocket(int socketIndex) {
                    log.debug("[TEST] Panel {} - breakSocket called on SocketIndex={}", panelIP, socketIndex);
                }
            });
            
            // Intentar inicializar la red
            boolean initResult = testSender.initNetwork(panelIP, defaultPort, "255.255.255.255");
            
            long responseTime = System.currentTimeMillis() - startTime;
            
            if (initResult) {
                log.info("Panel {} responde correctamente en {}ms", panelIP, responseTime);
                return true;
            } else {
                log.warn("Panel {} no responde en {}ms", panelIP, responseTime);
                return false;
            }

        } catch (Exception e) {
            long responseTime = System.currentTimeMillis() - startTime;
            log.error("Error al probar panel {}: {} ({}ms)", panelIP, e.getMessage(), responseTime, e);
            return false;
        }
    }

    /**
     * Envía un mensaje a múltiples paneles
     */
    public boolean sendMultiMessage(java.util.List<String> ips, String message, Integer color, Integer fontSize, Integer windowNo) {
        long startTime = System.currentTimeMillis();
        
        try {
            log.info("Enviando mensaje a {} paneles: '{}'", ips.size(), message);
            
            // Usar valores por defecto si no se proporcionan
            int finalColor = (color != null) ? color : 7; // Blanco por defecto
            int finalFontSize = (fontSize != null) ? fontSize : 16; // Tamaño 16 por defecto
            int finalWindowNo = (windowNo != null) ? windowNo : this.windowNo;
            
            boolean allSuccess = true;
            int successCount = 0;
            
            for (String ip : ips) {
                try {
                    // Crear mensaje para este panel
                    PanelMessage panelMessage = new PanelMessage();
                    panelMessage.setPanelIP(ip);
                    panelMessage.setMessage(message);
                    panelMessage.setColor(finalColor);
                    panelMessage.setFontSize(finalFontSize);
                    panelMessage.setWindowNo(finalWindowNo);
                    panelMessage.setItemNum(0);
                    panelMessage.setEffect(0);
                    
                    // Enviar mensaje
                    boolean success = sendMessage(panelMessage);
                    if (success) {
                        successCount++;
                    } else {
                        allSuccess = false;
                    }
                    
                } catch (Exception e) {
                    log.error("Error al enviar mensaje a panel {}: {}", ip, e.getMessage(), e);
                    allSuccess = false;
                }
            }
            
            long responseTime = System.currentTimeMillis() - startTime;
            
            log.info("Envío multi-panel completado: {}/{} exitosos en {}ms", 
                    successCount, ips.size(), responseTime);
            
            return allSuccess;

        } catch (Exception e) {
            long responseTime = System.currentTimeMillis() - startTime;
            log.error("Error al enviar mensaje multi-panel: {} ({}ms)", e.getMessage(), responseTime, e);
            return false;
        }
    }
} 