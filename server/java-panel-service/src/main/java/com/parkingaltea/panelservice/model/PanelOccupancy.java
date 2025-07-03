package com.parkingaltea.panelservice.model;

import lombok.Data;
import lombok.NoArgsConstructor;
import lombok.AllArgsConstructor;
import lombok.Builder;

import javax.validation.constraints.NotBlank;
import javax.validation.constraints.NotNull;
import javax.validation.constraints.Min;

/**
 * Modelo para representar la ocupación de un parking
 */
@Data
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class PanelOccupancy {
    
    @NotBlank(message = "La IP del panel es obligatoria")
    private String ip;
    
    @NotNull(message = "El número de parking es obligatorio")
    @Min(value = 1, message = "El número de parking debe ser mayor que 0")
    private Integer parkingNumber;
    
    @NotBlank(message = "El nombre del parking es obligatorio")
    private String parkingName;
    
    @NotNull(message = "Las plazas libres son obligatorias")
    @Min(value = 0, message = "Las plazas libres no pueden ser negativas")
    private Integer freeSpaces;
    
    @NotNull(message = "El total de plazas es obligatorio")
    @Min(value = 1, message = "El total de plazas debe ser mayor que 0")
    private Integer totalSpaces;
    
    @NotBlank(message = "El estado del parking es obligatorio")
    private String status; // LIBRE, DENSO, OCUPADO
    
    private String language = "es"; // es, va, en, fr, de
} 