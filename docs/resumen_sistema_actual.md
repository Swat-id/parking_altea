# Resumen del Sistema Actual - Parking Altea

## Funcionalidades Principales
- Gestión de ocupación en tiempo real (cámaras, paneles, API y frontend)
- Ajuste manual y automático de aforo
- Programaciones horarias y mensajes en paneles
- Gestión de usuarios y roles (superadmin, usuario)
- Asignación de recursos por usuario (parkings, paneles, cámaras)
- Logs de actividad y auditoría
- Seguridad: autenticación JWT, protección de endpoints y frontend

---

## Parkings (9)
1. **P. Ciutat Esportiva** - 500 plazas
2. **P. Poble antic/Belles Arts 1** - 45 plazas
3. **P. Poble antic/Belles Arts 2** - 45 plazas
4. **P. Poble antic/Belles Arts 3** - 45 plazas
5. **P. Poble antic/Belles Arts 4** - 45 plazas
6. **P. Poble antic/Belles Arts 5** - 45 plazas
7. **P. Port Altea** - 166 plazas
8. **P. Estació Altea** - 80 plazas
9. **P. Altea Hills** - 200 plazas

---

## Paneles (10)
- PANEL PITERES: 172.20.8.51 (Parking 6)
- PANEL PITERES 2: 172.20.8.51 (Parking 6)
- PANEL PORT: 172.20.4.52 (Parking 7)
- PANEL ESTACIO: 172.20.4.53 (Parking 8)
- PANEL HILLS: 172.20.4.54 (Parking 9)
- PANEL CIUTAT ESPORTIVA: 172.20.4.55 (Parking 1)
- PANEL BELLES ARTS 1: 172.20.4.56 (Parking 2)
- PANEL BELLES ARTS 2: 172.20.4.57 (Parking 3)
- PANEL BELLES ARTS 3: 172.20.4.58 (Parking 4)
- PANEL BELLES ARTS 4: 172.20.4.59 (Parking 5)

---

## Cámaras (13)
- Cámaras distribuidas en los 9 parkings
- Protocolo: Mensajes JSON vía HTTP POST
- Estados: ONLINE/OFFLINE según mensajes recibidos

---

## Usuarios y Credenciales Existentes
- **Superadmin**: info@swat-id.com / admin123!
- **Toni Alos**: atea.dti@altea.es / altea2025!
- **Iván Martí**: gerenciapstd@altea.es / altea2025!
- **Usuario de prueba**: test@example.com / test123

> **Nota:** Cambiar las contraseñas de los usuarios reales tras la puesta en producción.

---

## Estado de la Infraestructura
- API REST: puerto 6001
- Frontend: servido por nginx
- Worker de programaciones: activo
- Base de datos: PostgreSQL
- Seguridad: autenticación JWT, roles, protección de endpoints

---

**Última actualización:** Julio 2025 