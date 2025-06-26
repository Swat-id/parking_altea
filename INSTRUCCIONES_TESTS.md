# Instrucciones para Ejecutar Tests de Validación

## Script de Validación Completa

He creado un script completo de validación que prueba todos los aspectos del sistema:

### Archivo: `test_complete_validation.py`

Este script incluye los siguientes tests:

1. **Conectividad de la API** - Verifica que la API esté respondiendo en puerto 6001
2. **Conectividad del Frontend** - Verifica que el frontend esté respondiendo en puerto 5789
3. **Login Toni Alos** - Prueba autenticación con credenciales correctas
4. **Login Iván Martí** - Prueba autenticación con credenciales correctas
5. **Endpoints protegidos** - Verifica acceso a recursos con token válido
6. **Endpoints de estadísticas** - Prueba funcionalidad de estadísticas
7. **Endpoints de paneles** - Prueba funcionalidad de paneles

## Cómo ejecutar en el servidor

### Opción 1: Desde el directorio del proyecto
```bash
cd /root/parking_altea
git pull origin v2.2
python3 test_complete_validation.py
```

### Opción 2: Ejecutar directamente
```bash
cd /root/parking_altea
python3 test_complete_validation.py
```

## Resultados esperados

Si todo funciona correctamente, deberías ver:

```
============================================================
TEST COMPLETO DE VALIDACIÓN - PARKING ALTEA
============================================================
Fecha: 2024-01-XX XX:XX:XX

1. Test de conectividad de la API...
✅ PASÓ Conectividad API
   Detalles: Status: 200

2. Test de conectividad del Frontend...
✅ PASÓ Conectividad Frontend
   Detalles: Status: 200

3. Test de login - Toni Alos...
✅ PASÓ Login Toni Alos
   Detalles: Login exitoso para Toni Alos

4. Test de login - Iván Martí...
✅ PASÓ Login Iván Martí
   Detalles: Login exitoso para Iván Martí

5. Test de endpoints protegidos...
✅ PASÓ Endpoints protegidos
   Detalles: Parkings obtenidos: X

6. Test de endpoints de estadísticas...
✅ PASÓ Endpoints de estadísticas
   Detalles: Estadísticas por hora obtenidas: X registros

7. Test de endpoints de paneles...
✅ PASÓ Endpoints de paneles
   Detalles: Paneles obtenidos: X

============================================================
RESUMEN DE TESTS
============================================================
Tests pasados: 7/7
Porcentaje de éxito: 100.0%

🎉 TODOS LOS TESTS PASARON EXITOSAMENTE!
El sistema está funcionando correctamente.

============================================================
Resultados guardados en: test_validation_results.json
```

## Archivos de salida

El script genera:
- **test_validation_results.json** - Resultados detallados en formato JSON

## Troubleshooting

Si algún test falla:

1. **Conectividad API**: Verificar que el servicio backend esté corriendo en puerto 6001
2. **Conectividad Frontend**: Verificar que Nginx esté sirviendo el frontend en puerto 5789
3. **Login falla**: Verificar que las contraseñas estén actualizadas a "alte2025!"
4. **Endpoints protegidos**: Verificar que el token JWT sea válido

## Comandos de verificación rápida

```bash
# Verificar servicios
systemctl status parking-api
systemctl status nginx

# Verificar puertos
netstat -tlnp | grep :6001
netstat -tlnp | grep :5789

# Verificar logs
journalctl -u parking-api -f
tail -f /var/log/nginx/error.log
```

## Credenciales de prueba

- **Toni Alos**: toni.alos@swat-id.com / alte2025!
- **Iván Martí**: ivan.marti@swat-id.com / alte2025! 