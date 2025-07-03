package com.parkingaltea.panelservice.model;

import lombok.Data;
import lombok.NoArgsConstructor;
import lombok.AllArgsConstructor;
import lombok.Builder;

import javax.validation.constraints.NotBlank;
import javax.validation.constraints.NotNull;
import javax.validation.constraints.Min;
import javax.validation.constraints.Max;

/**
 * Modelo para representar un mensaje de panel
 */
@Data
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class PanelMessage {
    
    @NotBlank(message = "El texto del mensaje es obligatorio")
    private String text;
    
    @NotNull(message = "El color es obligatorio")
    @Min(value = 1, message = "El color debe estar entre 1 y 7")
    @Max(value = 7, message = "El color debe estar entre 1 y 7")
    private Integer color;
    
    @NotNull(message = "El tamaño de fuente es obligatorio")
    @Min(value = 8, message = "El tamaño de fuente debe estar entre 8 y 64")
    @Max(value = 64, message = "El tamaño de fuente debe estar entre 8 y 64")
    private Integer fontSize;
    
    @NotNull(message = "El número de ventana es obligatorio")
    @Min(value = 0, message = "El número de ventana debe estar entre 0 y 7")
    @Max(value = 7, message = "El número de ventana debe estar entre 0 y 7")
    private Integer windowNo;
    
    @Min(value = 0, message = "El efecto debe estar entre 0 y 15")
    @Max(value = 15, message = "El efecto debe estar entre 0 y 15")
    private Integer effect = 0;
    
    @Min(value = 1, message = "La velocidad debe estar entre 1 y 10")
    @Max(value = 10, message = "La velocidad debe estar entre 1 y 10")
    private Integer speed = 1;
    
    @Min(value = 1, message = "El tiempo de permanencia debe estar entre 1 y 60")
    @Max(value = 60, message = "El tiempo de permanencia debe estar entre 1 y 60")
    private Integer stayTime = 5;
} 