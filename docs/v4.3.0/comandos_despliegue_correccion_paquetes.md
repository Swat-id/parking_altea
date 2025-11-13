# Comandos de Despliegue - Corrección de Paquetes y Aumento de Latencia

## Fecha: 2025-11-13
## Versión: v4.3.0
## Descripción: Corrección de estructura de paquetes según panel_protocol.py y aumento de timeouts

---

## BLOQUE 1: Preparación y Actualización del Código

```bash
# Conectar al servidor
ssh root@157.180.91.63

# Ir al directorio del proyecto
cd /opt/parking_altea

# Descartar cambios locales si existen
git fetch origin
git reset --hard origin/v4.3.0
git clean -fd

# Actualizar código desde git
git pull origin v4.3.0

# Verificar que los cambios están presentes
git log --oneline -3
```

---

## BLOQUE 2: Verificación de Archivos Modificados

```bash
# Verificar que los archivos clave están actualizados
ls -la src/panel_protocol/packet_builder.py
ls -la src/panel_protocol/packet_parser.py
ls -la src/panel_protocol/constants.py
ls -la src/panel_type4_update_service.py

# Verificar contenido de constants.py (debe tener DEFAULT_TIMEOUT = 30.0)
grep "DEFAULT_TIMEOUT" src/panel_protocol/constants.py

# Verificar contenido de packet_builder.py (debe tener struct.pack('<H' para Network Length)
grep -A 2 "Network Length" src/panel_protocol/packet_builder.py | head -5
```

---

## BLOQUE 3: Reinicio del Worker Type 3/4

```bash
# Detener el worker
sudo systemctl stop parking-panel-type3-and-4-worker

# Verificar que se detuvo correctamente
sudo systemctl status parking-panel-type3-and-4-worker

# Iniciar el worker
sudo systemctl start parking-panel-type3-and-4-worker

# Verificar que se inició correctamente
sudo systemctl status parking-panel-type3-and-4-worker

# Verificar que el servicio está activo
sudo systemctl is-active parking-panel-type3-and-4-worker
```

---

## BLOQUE 4: Verificación de Logs

```bash
# Ver logs en tiempo real
tail -f logs/panel_type3_and_4_worker.log

# O ver las últimas 50 líneas
tail -n 50 logs/panel_type3_and_4_worker.log

# Verificar que no hay errores críticos
grep -i "error\|exception\|traceback" logs/panel_type3_and_4_worker.log | tail -20

# Verificar que los paquetes se están enviando correctamente
grep "Enviando.*bytes" logs/panel_type3_and_4_worker.log | tail -10
```

---

## BLOQUE 5: Verificación de Estructura de Paquetes

```bash
# Verificar que los paquetes tienen la estructura correcta
# Buscar en los logs el formato hexadecimal de los paquetes
grep "Datos a enviar (hex)" logs/panel_type3_and_4_worker.log | tail -5

# Verificar que los paquetes tienen Network Length de 2 bytes
# Los paquetes deben empezar con: ffffffff [2 bytes length] 0000 68...
# Ejemplo correcto: ffffffff 1e00 0000 6832...
```

---

## BLOQUE 6: Verificación de Respuestas

```bash
# Verificar si hay respuestas del panel
grep -i "respuesta\|response" logs/panel_type3_and_4_worker.log | tail -20

# Verificar timeouts (deben ser de 30s ahora)
grep -i "timeout" logs/panel_type3_and_4_worker.log | tail -10

# Verificar éxitos parciales
grep -i "éxito parcial\|success\|actualizada" logs/panel_type3_and_4_worker.log | tail -10
```

---

## BLOQUE 7: Verificación de Base de Datos

```bash
# Verificar que los últimos mensajes se están actualizando
cd /opt/parking_altea/src
python3 << 'EOF'
import sys
sys.path.insert(0, '.')
from config import DB_URL
from sqlalchemy import create_engine, text

engine = create_engine(DB_URL)
with engine.connect() as conn:
    # Verificar paneles Tipo 3 actualizados recientemente
    result = conn.execute(text("""
        SELECT id, name, last_message, last_message_window_0, last_message_window_1, 
               last_update, last_update_window_0, last_update_window_1
        FROM panels
        WHERE panel_type_id = 3
        ORDER BY last_update DESC
        LIMIT 5
    """))
    print("\n=== Paneles Tipo 3 - Últimos Mensajes ===")
    for row in result:
        print(f"Panel {row[0]} ({row[1]}):")
        print(f"  Último mensaje: {row[2]}")
        print(f"  V0: {row[3]} (actualizado: {row[6]})")
        print(f"  V1: {row[4]} (actualizado: {row[7]})")
        print(f"  Última actualización: {row[5]}")
        print()
EOF
```

---

## BLOQUE 8: Prueba Manual de Envío (Opcional)

```bash
# Si quieres probar manualmente el envío de un paquete
cd /opt/parking_altea
python3 << 'EOF'
import sys
sys.path.insert(0, 'src')
from panel_protocol.packet_builder import PacketBuilder

# Construir un paquete de prueba
packet = PacketBuilder.build_send_text_packet(
    card_id=0x01,
    window_id=0,
    text="90",
    color=2,  # Verde
    font_size=2,  # 16px
    effect=0,
    alignment=0,
    speed=0x03,
    stay_time=3,
    request_confirmation=True
)

print(f"Paquete generado: {len(packet)} bytes")
print(f"Hex: {packet.hex()}")

# Verificar estructura
print("\n=== Estructura del Paquete ===")
print(f"[0-3]   ID Code: {packet[0:4].hex()}")
print(f"[4-5]   Network Length: {packet[4:6].hex()} ({int.from_bytes(packet[4:6], 'little')} bytes)")
print(f"[6-7]   Reserved: {packet[6:8].hex()}")
print(f"[8]     Packet Type: {packet[8]:02x}")
print(f"[9]     Card Type: {packet[9]:02x}")
print(f"[10]    Card ID: {packet[10]:02x}")
print(f"[11]    Protocol: {packet[11]:02x}")
print(f"[12]    Additional Info: {packet[12]:02x}")
EOF
```

---

## BLOQUE 9: Monitoreo Continuo

```bash
# Monitorear logs en tiempo real durante 2 minutos
timeout 120 tail -f logs/panel_type3_and_4_worker.log

# O en una sesión separada de screen/tmux
screen -S panel_monitor
tail -f logs/panel_type3_and_4_worker.log
# Presionar Ctrl+A luego D para detach
```

---

## BLOQUE 10: Verificación Final

```bash
# Verificar estado del servicio
sudo systemctl status parking-panel-type3-and-4-worker --no-pager

# Verificar que el proceso está corriendo
ps aux | grep panel_type3_and_4_worker

# Verificar puertos en uso
netstat -tuln | grep 5200 || ss -tuln | grep 5200

# Verificar espacio en disco
df -h /opt/parking_altea

# Verificar permisos de logs
ls -la logs/panel_type3_and_4_worker.log
```

---

## Notas Importantes

1. **Estructura de Paquetes Corregida:**
   - Network Length: 2 bytes (no 4)
   - Reserved: 2 bytes (0x00, 0x00) después del Network Length
   - Estructura: ID Code (4) + Network Length (2) + Reserved (2) + Packet Data

2. **Timeouts Aumentados:**
   - DEFAULT_TIMEOUT: 30 segundos
   - DEFAULT_CONNECTION_TIMEOUT: 10 segundos
   - read_timeout: 30 segundos

3. **Tolerancia a Respuestas:**
   - Acepta respuestas parciales o mal formateadas
   - Considera éxito si hay cualquier respuesta
   - Considera éxito parcial si el paquete se envía pero no hay respuesta

4. **Verificación Física:**
   - Verificar físicamente si los paneles muestran el texto correctamente
   - Aunque no haya respuesta, el panel puede haber procesado el mensaje

---

## Comandos Rápidos (Copy-Paste)

```bash
# Todo en uno (ejecutar bloque por bloque)
cd /opt/parking_altea && git pull origin v4.3.0 && sudo systemctl restart parking-panel-type3-and-4-worker && tail -f logs/panel_type3_and_4_worker.log
```

