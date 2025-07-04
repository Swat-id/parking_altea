package com.parkingaltea.panelservice.model;

import lombok.Data;
import java.util.List;

/**
 * DTO para peticiones de envío múltiple a paneles
 */
@Data
public class SendMultiRequest {
    private List<String> texts;
    private List<Integer> colors;
    private List<Integer> fontSizes;
    private List<Integer> showEffects;
} 