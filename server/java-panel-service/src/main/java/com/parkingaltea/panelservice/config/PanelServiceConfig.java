package com.parkingaltea.panelservice.config;

import com.parkingaltea.panelservice.service.PanelCommunicationService;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.CommandLineRunner;
import org.springframework.stereotype.Component;

import java.util.HashMap;
import java.util.Map;

/**
 * Configuración del servicio de paneles
 */
@Slf4j
@Component
public class PanelServiceConfig implements CommandLineRunner {

    @Autowired
    private PanelCommunicationService panelService;

    // Configuración de paneles con IPs reales
    private static final Map<String, String> PANELS = new HashMap<>();
    
    static {
        PANELS.put("172.20.17.50", "PANEL C. ESPORTIVA - P. Ciutat Esportiva");
        PANELS.put("172.20.5.50", "PANEL BASSETA 1 - P. Basseta Centre");
        PANELS.put("172.20.5.51", "PANEL BASSETA 2 - P. Basseta Centre");
        PANELS.put("172.20.8.50", "PANEL PITERES - P. Poble antic/Conservatori");
        PANELS.put("172.20.4.50", "PANEL PALAU - P. Poble antic/Palau Altea");
        PANELS.put("172.20.4.51", "PANEL COCOLISO - P. Poble antic/Palau Altea");
        PANELS.put("172.20.4.52", "BELLES ARTS 2 - P. Poble antic/Belles Arts 2");
        PANELS.put("172.20.4.53", "BELLES ARTS - P. Poble antic/Belles Arts 1");
        PANELS.put("172.20.2.50", "PANEL RENFE - P. Estació Altea");
        PANELS.put("172.20.1.50", "PANEL ALTEA VELLA - P. Altea la Vella");
    }

    @Override
    public void run(String... args) throws Exception {
        log.info("Inicializando servicio de paneles Java...");
        
        try {
            // Inicializar la librería Java
            panelService.initializeLibrary();
            
            // Mostrar información de paneles configurados
            log.info("Paneles configurados ({}):", PANELS.size());
            for (Map.Entry<String, String> entry : PANELS.entrySet()) {
                log.info("  - {}: {}", entry.getKey(), entry.getValue());
            }
            
            log.info("Servicio de paneles Java inicializado correctamente");
            
        } catch (Exception e) {
            log.error("Error al inicializar el servicio de paneles: {}", e.getMessage(), e);
            // No lanzar excepción para permitir que la aplicación continúe
        }
    }

    /**
     * Obtiene la lista de paneles configurados
     */
    public static Map<String, String> getPanels() {
        return new HashMap<>(PANELS);
    }

    /**
     * Verifica si una IP pertenece a un panel configurado
     */
    public static boolean isPanelConfigured(String ip) {
        return PANELS.containsKey(ip);
    }

    /**
     * Obtiene el nombre del panel por IP
     */
    public static String getPanelName(String ip) {
        return PANELS.getOrDefault(ip, "Panel Desconocido");
    }
} 