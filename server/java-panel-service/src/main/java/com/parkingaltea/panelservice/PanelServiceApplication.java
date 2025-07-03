package com.parkingaltea.panelservice;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.scheduling.annotation.EnableAsync;

/**
 * Aplicación principal del servicio de paneles Java
 * 
 * Este servicio proporciona una API REST para la comunicación con paneles LED
 * usando la librería oficial del fabricante (protocol-1.2.6.jar)
 * 
 * @author Parking Altea Team
 * @version 2.5
 */
@SpringBootApplication
@EnableAsync
public class PanelServiceApplication {

    public static void main(String[] args) {
        SpringApplication.run(PanelServiceApplication.class, args);
    }
} 