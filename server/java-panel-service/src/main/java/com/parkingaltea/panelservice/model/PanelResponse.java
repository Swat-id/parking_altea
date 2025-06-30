package com.parkingaltea.panelservice.model;

import lombok.Data;
import lombok.Builder;
import lombok.NoArgsConstructor;
import lombok.AllArgsConstructor;

import java.time.LocalDateTime;

/**
 * Modelo para las respuestas del servicio de paneles
 */
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class PanelResponse {

    @Builder.Default
    private Boolean success = true;

    private String message;

    @Builder.Default
    private Integer errorCode = 0;

    private Double responseTime;

    @Builder.Default
    private LocalDateTime timestamp = LocalDateTime.now();

    private Object data;

    /**
     * Crea una respuesta de éxito
     */
    public static PanelResponse success(String message) {
        return PanelResponse.builder()
                .success(true)
                .message(message)
                .errorCode(0)
                .timestamp(LocalDateTime.now())
                .build();
    }

    /**
     * Crea una respuesta de éxito con datos
     */
    public static PanelResponse success(String message, Object data) {
        return PanelResponse.builder()
                .success(true)
                .message(message)
                .errorCode(0)
                .timestamp(LocalDateTime.now())
                .data(data)
                .build();
    }

    /**
     * Crea una respuesta de error
     */
    public static PanelResponse error(String message, Integer errorCode) {
        return PanelResponse.builder()
                .success(false)
                .message(message)
                .errorCode(errorCode)
                .timestamp(LocalDateTime.now())
                .build();
    }

    /**
     * Crea una respuesta de error con tiempo de respuesta
     */
    public static PanelResponse error(String message, Integer errorCode, Double responseTime) {
        return PanelResponse.builder()
                .success(false)
                .message(message)
                .errorCode(errorCode)
                .responseTime(responseTime)
                .timestamp(LocalDateTime.now())
                .build();
    }
} 