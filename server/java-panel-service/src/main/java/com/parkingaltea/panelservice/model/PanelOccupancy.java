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
 * Modelo para la información de ocupación de parking
 */
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class PanelOccupancy {

    @NotBlank(message = "La IP del panel es obligatoria")
    private String panelIP;

    @NotNull(message = "El número de plazas ocupadas es obligatorio")
    @Min(value = 0, message = "El número de plazas ocupadas no puede ser negativo")
    private Integer current;

    @NotNull(message = "El número total de plazas es obligatorio")
    @Min(value = 1, message = "El número total de plazas debe ser mayor que 0")
    private Integer total;

    @NotBlank(message = "El estado del parking es obligatorio")
    private String status; // LLIURE, DENS, COMPLET

    @NotBlank(message = "El nombre del parking es obligatorio")
    private String parkingName;

    @Builder.Default
    private Integer color = 2; // Verde por defecto (2)

    @Builder.Default
    @Min(value = 8, message = "El tamaño de fuente mínimo es 8")
    @Max(value = 32, message = "El tamaño de fuente máximo es 32")
    private Integer fontSize = 16;

    @Builder.Default
    @Min(value = 1, message = "La velocidad mínima es 1")
    @Max(value = 5, message = "La velocidad máxima es 5")
    private Integer speed = 2;

    @Builder.Default
    @Min(value = 0, message = "La alineación mínima es 0")
    @Max(value = 10, message = "La alineación máxima es 10")
    private Integer alignment = 5; // Centro por defecto
} 