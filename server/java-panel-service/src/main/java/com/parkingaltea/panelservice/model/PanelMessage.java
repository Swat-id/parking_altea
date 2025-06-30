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
    private Integer color = 0x00FF00; // Verde por defecto

    @Builder.Default
    @Min(value = 8, message = "El tamaño de fuente mínimo es 8")
    @Max(value = 32, message = "El tamaño de fuente máximo es 32")
    private Integer fontSize = 16;

    @Builder.Default
    @Min(value = 1, message = "La velocidad mínima es 1")
    @Max(value = 5, message = "La velocidad máxima es 5")
    private Integer speed = 3;

    @Builder.Default
    @Min(value = 0, message = "El efecto mínimo es 0")
    @Max(value = 3, message = "El efecto máximo es 3")
    private Integer effect = 0;

    @Builder.Default
    @Min(value = 1, message = "El tiempo de permanencia mínimo es 1 segundo")
    @Max(value = 60, message = "El tiempo de permanencia máximo es 60 segundos")
    private Integer stayTime = 5;

    @Builder.Default
    @Min(value = 0, message = "La alineación mínima es 0")
    @Max(value = 10, message = "La alineación máxima es 10")
    private Integer alignment = 5; // Centro por defecto
} 