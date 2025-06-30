package com.parkingaltea.panelservice.service;

import com.parkingaltea.panelservice.model.PanelMessage;
import com.parkingaltea.panelservice.model.PanelOccupancy;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import org.springframework.test.util.ReflectionTestUtils;

import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.*;

@ExtendWith(MockitoExtension.class)
class PanelCommunicationServiceTest {

    @InjectMocks
    private PanelCommunicationService panelService;

    @BeforeEach
    void setUp() {
        // Configurar valores por defecto para las pruebas
        ReflectionTestUtils.setField(panelService, "timeout", 1000);
        ReflectionTestUtils.setField(panelService, "retryAttempts", 2);
        ReflectionTestUtils.setField(panelService, "retryDelay", 100);
        ReflectionTestUtils.setField(panelService, "defaultPort", 5200);
        ReflectionTestUtils.setField(panelService, "cardId", 1);
        ReflectionTestUtils.setField(panelService, "windowNo", 0);
    }

    @Test
    void testSendMessage_Success() {
        // Given
        PanelMessage message = PanelMessage.builder()
                .panelIP("192.168.1.100")
                .message("Test Message")
                .color(0x00FF00)
                .fontSize(16)
                .speed(3)
                .effect(0)
                .stayTime(5)
                .alignment(5)
                .build();

        // When
        boolean result = panelService.sendMessage(message);

        // Then
        assertTrue(result, "El mensaje debería enviarse correctamente");
    }

    @Test
    void testSendOccupancy_Success() {
        // Given
        PanelOccupancy occupancy = PanelOccupancy.builder()
                .panelIP("192.168.1.100")
                .current(45)
                .total(500)
                .status("LLIURE")
                .parkingName("P. Ciutat Esportiva")
                .color(0x00FF00)
                .fontSize(16)
                .speed(2)
                .alignment(5)
                .build();

        // When
        boolean result = panelService.sendOccupancy(occupancy);

        // Then
        assertTrue(result, "La ocupación debería enviarse correctamente");
    }

    @Test
    void testTestPanel_Success() {
        // Given
        String panelIP = "192.168.1.100";

        // When
        boolean result = panelService.testPanel(panelIP);

        // Then
        assertTrue(result, "El panel debería responder correctamente");
    }

    @Test
    void testGetInitializedPanels() {
        // Given
        PanelMessage message = PanelMessage.builder()
                .panelIP("192.168.1.100")
                .message("Test")
                .build();

        // When
        panelService.sendMessage(message);
        var initializedPanels = panelService.getInitializedPanels();

        // Then
        assertNotNull(initializedPanels, "La lista de paneles inicializados no debería ser null");
        assertTrue(initializedPanels.containsKey("192.168.1.100"), 
                "El panel debería estar en la lista de inicializados");
    }

    @Test
    void testClearInitializedPanels() {
        // Given
        PanelMessage message = PanelMessage.builder()
                .panelIP("192.168.1.100")
                .message("Test")
                .build();

        panelService.sendMessage(message);
        assertTrue(panelService.getInitializedPanels().containsKey("192.168.1.100"));

        // When
        panelService.clearInitializedPanels();

        // Then
        assertTrue(panelService.getInitializedPanels().isEmpty(), 
                "La cache debería estar vacía después de limpiarla");
    }

    @Test
    void testSendMessage_InvalidIP() {
        // Given
        PanelMessage message = PanelMessage.builder()
                .panelIP("invalid.ip.address")
                .message("Test Message")
                .build();

        // When
        boolean result = panelService.sendMessage(message);

        // Then
        assertFalse(result, "El mensaje no debería enviarse con una IP inválida");
    }

    @Test
    void testSendMessage_EmptyMessage() {
        // Given
        PanelMessage message = PanelMessage.builder()
                .panelIP("192.168.1.100")
                .message("")
                .build();

        // When
        boolean result = panelService.sendMessage(message);

        // Then
        assertFalse(result, "El mensaje no debería enviarse con texto vacío");
    }
} 