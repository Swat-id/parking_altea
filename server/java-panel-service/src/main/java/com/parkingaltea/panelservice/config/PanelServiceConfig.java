package com.parkingaltea.panelservice.config;

import com.parkingaltea.panelservice.service.PanelCommunicationService;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.CommandLineRunner;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.scheduling.annotation.EnableAsync;
import org.springframework.scheduling.annotation.EnableScheduling;
import org.springframework.scheduling.concurrent.ThreadPoolTaskExecutor;

import java.util.concurrent.Executor;

/**
 * Configuración del servicio de paneles
 */
@Slf4j
@Configuration
@EnableAsync
@EnableScheduling
public class PanelServiceConfig implements CommandLineRunner {

    @Autowired
    private PanelCommunicationService panelService;

    /**
     * Configuración del executor para operaciones asíncronas
     */
    @Bean(name = "panelTaskExecutor")
    public Executor panelTaskExecutor() {
        ThreadPoolTaskExecutor executor = new ThreadPoolTaskExecutor();
        executor.setCorePoolSize(5);
        executor.setMaxPoolSize(10);
        executor.setQueueCapacity(100);
        executor.setThreadNamePrefix("PanelService-");
        executor.initialize();
        return executor;
    }

    /**
     * Inicialización del servicio al arrancar la aplicación
     */
    @Override
    public void run(String... args) throws Exception {
        log.info("Inicializando servicio de paneles Java...");
        
        try {
            // Inicializar la librería Java del fabricante
            panelService.initializeLibrary();
            
            log.info("Servicio de paneles Java inicializado correctamente");
            
        } catch (Exception e) {
            log.error("Error al inicializar el servicio de paneles: {}", e.getMessage(), e);
            throw e;
        }
    }
} 