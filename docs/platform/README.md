# Documentación de la Plataforma Parking Altea

## Índice de Documentación

| Documento | Descripción |
|-----------|-------------|
| [01-descripcion-general.md](./01-descripcion-general.md) | Visión general de la plataforma y arquitectura |
| [02-servicios-y-puertos.md](./02-servicios-y-puertos.md) | Servicios, workers y puertos utilizados |
| [03-estructura-directorios.md](./03-estructura-directorios.md) | Estructura de directorios y ficheros clave |
| [04-base-de-datos.md](./04-base-de-datos.md) | Esquema completo de la base de datos |
| [05-flujos-principales.md](./05-flujos-principales.md) | Flujos de datos y procesos principales |
| [06-despliegue.md](./06-despliegue.md) | Proceso de despliegue y actualización |

## Información Rápida

- **Servidor de Producción**: `ubuntu-16gb-hel1-1`
- **Base de Datos**: PostgreSQL - `parking_db`
- **Framework Backend**: Flask (Python 3.10+)
- **Framework Frontend**: React
- **Repositorio**: `https://github.com/Swat-id/parking_altea`
- **Rama Principal**: `v4.5.0`

## Servicios Principales

| Servicio | Puerto | Descripción |
|----------|--------|-------------|
| parking-api | 6001 | API REST principal |
| parking-panel-protocol | 7110 | Protocolo directo paneles (nuevo) |
| panelsender | 8888 | SDK Java paneles (antiguo) |
| panel-worker | - | Worker actualización paneles |
| panel-type3-4-worker | - | Worker paneles Tipo 3 y 4 |
| schedule-monitor | - | Monitor de programaciones |

---

*Última actualización: Marzo 2026*
*Versión: v4.7*
