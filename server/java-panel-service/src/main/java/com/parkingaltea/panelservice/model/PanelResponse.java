package com.parkingaltea.panelservice.model;

import lombok.Data;
import lombok.NoArgsConstructor;
import lombok.AllArgsConstructor;
import lombok.Builder;

import java.time.LocalDateTime;
import java.util.List;

/**
 * Modelo para representar la respuesta de la API de paneles
 */
@Data
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class PanelResponse {
    
    private boolean success;
    private String message;
    private String panelIp;
    private String protocol;
    private List<String> texts;
    private LocalDateTime timestamp;
    private Long responseTime;
    private String errorDetails;
    
    public static PanelResponse success(String message, String panelIp, String protocol, List<String> texts) {
        return PanelResponse.builder()
                .success(true)
                .message(message)
                .panelIp(panelIp)
                .protocol(protocol)
                .texts(texts)
                .timestamp(LocalDateTime.now())
                .build();
    }
    
    public static PanelResponse error(String message, String panelIp, String protocol, String errorDetails) {
        return PanelResponse.builder()
                .success(false)
                .message(message)
                .panelIp(panelIp)
                .protocol(protocol)
                .timestamp(LocalDateTime.now())
                .errorDetails(errorDetails)
                .build();
    }
} 