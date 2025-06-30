package com.parkingaltea.panelservice;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.scheduling.annotation.EnableAsync;
import org.springframework.scheduling.annotation.EnableScheduling;

/**
 * Aplicación principal del servicio de comunicación con paneles LED
 * 
 * Este servicio proporciona una API REST para comunicarse con los paneles
 * electrónicos del sistema de parking de Altea, utilizando la librería Java
 * del fabricante Rotuloselectronicos.net
 * 
 * @author Parking Altea Team
 * @version 1.0.0
 */
@SpringBootApplication
@EnableAsync
@EnableScheduling
public class PanelServiceApplication {

    public static void main(String[] args) {
        SpringApplication.run(PanelServiceApplication.class, args);
    }
} 