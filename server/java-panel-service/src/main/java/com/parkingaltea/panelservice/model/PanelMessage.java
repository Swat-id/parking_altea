package com.parkingaltea.panelservice.model;

import lombok.Data;
import lombok.Builder;
import lombok.NoArgsConstructor;
import lombok.AllArgsConstructor;

import javax.validation.constraints.NotBlank;
import javax.validation.constraints.NotNull;
import javax.validation.constraints.Min;
import javax.validation.constraints.Max;

/**
 * Modelo para los mensajes enviados a los paneles LED
 */
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class PanelMessage {

    @NotBlank(message = "La IP del panel es obligatoria")
    private String panelIP;

    @NotBlank(message = "El mensaje es obligatorio")
    private String message;

    @Builder.Default
    @Min(value = 1, message = "El color mínimo es 1")
    @Max(value = 7, message = "El color máximo es 7")
    private Integer color = 1; // Rojo por defecto

    @Builder.Default
    @Min(value = 1, message = "El tamaño de fuente mínimo es 1")
    @Max(value = 7, message = "El tamaño de fuente máximo es 7")
    private Integer fontSize = 2; // Tamaño 2 por defecto (~24px)

    @Builder.Default
    @Min(value = 0, message = "El efecto mínimo es 0")
    @Max(value = 3, message = "El efecto máximo es 3")
    private Integer effect = 0; // Sin efecto por defecto

    @Builder.Default
    @Min(value = 1, message = "El itemNum mínimo es 1")
    @Max(value = 10, message = "El itemNum máximo es 10")
    private Integer itemNum = 1; // Item 1 por defecto

    @Builder.Default
    @Min(value = 0, message = "El windowNo mínimo es 0")
    @Max(value = 3, message = "El windowNo máximo es 3")
    private Integer windowNo = 0; // Ventana 0 por defecto
} 