#!/usr/bin/env python3
"""
Script completo para validar la base de datos Parking Altea
Verifica usuarios, parkings, paneles, programaciones y funcionalidad
"""

import sys
import os
from datetime import datetime
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Agregar el directorio src al path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from config import DB_URL
from models import User, Parking, Panel, PanelSchedule, Camera

def validate_database():
    """Validación completa de la base de datos"""
    
    print("=== VALIDACIÓN COMPLETA DE LA BASE DE DATOS PARKING ALTEA ===")
    print(f"Fecha y hora: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    # Crear conexión a la base de datos
    engine = create_engine(DB_URL)
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        # 1. Verificar conexión a la base de datos
        print("\n🔍 1. VERIFICANDO CONEXIÓN A LA BASE DE DATOS")
        print("-" * 40)
        
        result = session.execute(text("SELECT version()"))
        version = result.fetchone()[0]
        print(f"✅ Conexión exitosa a PostgreSQL")
        print(f"   Versión: {version}")
        
        # 2. Verificar usuarios
        print("\n👥 2. VERIFICANDO USUARIOS")
        print("-" * 40)
        
        users = session.query(User).all()
        print(f"📊 Total de usuarios: {len(users)}")
        
        if users:
            print("📋 Lista de usuarios:")
            for user in users:
                status = "✅ Activo" if user.is_active else "❌ Inactivo"
                print(f"   • ID: {user.id} | {user.name} | {user.email} | {user.role} | {status}")
        else:
            print("⚠️  No hay usuarios en la base de datos")
        
        # 3. Verificar parkings
        print("\n🏢 3. VERIFICANDO PARKINGS")
        print("-" * 40)
        
        parkings = session.query(Parking).all()
        print(f"📊 Total de parkings: {len(parkings)}")
        
        if parkings:
            print("📋 Lista de parkings:")
            for parking in parkings:
                print(f"   • ID: {parking.id} | {parking.name}")
                print(f"     Ubicación: {parking.location}")
                print(f"     Plazas: {parking.total_plazas} | Ocupadas: {parking.plazas_ocupadas} | Libres: {parking.plazas_libres}")
                print(f"     Estado: {parking.estado}")
                print(f"     Thresholds: Dense={parking.threshold_dense}, Full={parking.threshold_full}")
                print()
        else:
            print("⚠️  No hay parkings en la base de datos")
        
        # 4. Verificar paneles
        print("\n📺 4. VERIFICANDO PANELES")
        print("-" * 40)
        
        panels = session.query(Panel).all()
        print(f"📊 Total de paneles: {len(panels)}")
        
        if panels:
            print("📋 Lista de paneles:")
            for panel in panels:
                parking_name = panel.parking.name if panel.parking else "Sin parking"
                status = "✅ Activo" if panel.is_active else "❌ Inactivo"
                print(f"   • ID: {panel.id} | IP: {panel.ip} | Parking: {parking_name} | {status}")
                print(f"     Último mensaje: {panel.last_message}")
                print(f"     Última actualización: {panel.last_updated}")
                print()
        else:
            print("⚠️  No hay paneles en la base de datos")
        
        # 5. Verificar cámaras
        print("\n📹 5. VERIFICANDO CÁMARAS")
        print("-" * 40)
        
        cameras = session.query(Camera).all()
        print(f"📊 Total de cámaras: {len(cameras)}")
        
        if cameras:
            print("📋 Lista de cámaras:")
            for camera in cameras:
                parking_name = camera.parking.name if camera.parking else "Sin parking"
                status = "✅ Activa" if camera.is_active else "❌ Inactiva"
                print(f"   • ID: {camera.id} | IP: {camera.ip} | Parking: {parking_name} | {status}")
                print(f"     Última actualización: {camera.last_updated}")
                print()
        else:
            print("⚠️  No hay cámaras en la base de datos")
        
        # 6. Verificar programaciones
        print("\n⏰ 6. VERIFICANDO PROGRAMACIONES")
        print("-" * 40)
        
        schedules = session.query(PanelSchedule).all()
        print(f"📊 Total de programaciones: {len(schedules)}")
        
        if schedules:
            print("📋 Lista de programaciones:")
            for schedule in schedules:
                parking_name = schedule.parking.name if schedule.parking else "Sin parking"
                status = "✅ Activa" if schedule.is_active else "❌ Inactiva"
                print(f"   • ID: {schedule.id} | {schedule.name}")
                print(f"     Parking: {parking_name} | {status}")
                print(f"     Mensaje: {schedule.message}")
                print(f"     Fechas: {schedule.start_date} - {schedule.end_date}")
                print(f"     Horario: {schedule.start_time} - {schedule.end_time}")
                print(f"     Días: L={schedule.monday} M={schedule.tuesday} X={schedule.wednesday} J={schedule.thursday} V={schedule.friday} S={schedule.saturday} D={schedule.sunday}")
                print()
        else:
            print("⚠️  No hay programaciones en la base de datos")
        
        # 7. Verificar relaciones y integridad
        print("\n🔗 7. VERIFICANDO RELACIONES E INTEGRIDAD")
        print("-" * 40)
        
        # Verificar parkings con paneles
        parkings_with_panels = session.query(Parking).join(Panel).distinct().all()
        print(f"📊 Parkings con paneles: {len(parkings_with_panels)}")
        
        # Verificar parkings con cámaras
        parkings_with_cameras = session.query(Parking).join(Camera).distinct().all()
        print(f"📊 Parkings con cámaras: {len(parkings_with_cameras)}")
        
        # Verificar parkings con programaciones
        parkings_with_schedules = session.query(Parking).join(PanelSchedule).distinct().all()
        print(f"📊 Parkings con programaciones: {len(parkings_with_schedules)}")
        
        # 8. Verificar estadísticas y logs
        print("\n📈 8. VERIFICANDO ESTADÍSTICAS Y LOGS")
        print("-" * 40)
        
        # Verificar tablas de estadísticas
        try:
            result = session.execute(text("SELECT COUNT(*) FROM parking_statistics"))
            stats_count = result.fetchone()[0]
            print(f"📊 Registros en parking_statistics: {stats_count}")
        except Exception as e:
            print(f"⚠️  Tabla parking_statistics no disponible: {e}")
        
        try:
            result = session.execute(text("SELECT COUNT(*) FROM daily_statistics"))
            daily_stats_count = result.fetchone()[0]
            print(f"📊 Registros en daily_statistics: {daily_stats_count}")
        except Exception as e:
            print(f"⚠️  Tabla daily_statistics no disponible: {e}")
        
        try:
            result = session.execute(text("SELECT COUNT(*) FROM activity_logs"))
            activity_logs_count = result.fetchone()[0]
            print(f"📊 Registros en activity_logs: {activity_logs_count}")
        except Exception as e:
            print(f"⚠️  Tabla activity_logs no disponible: {e}")
        
        # 9. Resumen de funcionalidad
        print("\n✅ 9. RESUMEN DE FUNCIONALIDAD")
        print("-" * 40)
        
        functionality_score = 0
        total_checks = 0
        
        # Verificar elementos mínimos necesarios
        if len(users) > 0:
            print("✅ Usuarios: Disponibles")
            functionality_score += 1
        else:
            print("❌ Usuarios: No disponibles")
        total_checks += 1
        
        if len(parkings) > 0:
            print("✅ Parkings: Disponibles")
            functionality_score += 1
        else:
            print("❌ Parkings: No disponibles")
        total_checks += 1
        
        if len(panels) > 0:
            print("✅ Paneles: Disponibles")
            functionality_score += 1
        else:
            print("❌ Paneles: No disponibles")
        total_checks += 1
        
        if len(cameras) > 0:
            print("✅ Cámaras: Disponibles")
            functionality_score += 1
        else:
            print("❌ Cámaras: No disponibles")
        total_checks += 1
        
        if len(schedules) > 0:
            print("✅ Programaciones: Disponibles")
            functionality_score += 1
        else:
            print("❌ Programaciones: No disponibles")
        total_checks += 1
        
        # Calcular porcentaje de funcionalidad
        functionality_percentage = (functionality_score / total_checks) * 100
        
        print(f"\n📊 Puntuación de funcionalidad: {functionality_score}/{total_checks} ({functionality_percentage:.1f}%)")
        
        if functionality_percentage >= 80:
            print("🎉 La base de datos está completamente funcional")
        elif functionality_percentage >= 60:
            print("⚠️  La base de datos está parcialmente funcional")
        else:
            print("❌ La base de datos necesita configuración adicional")
        
        # 10. Recomendaciones
        print("\n💡 10. RECOMENDACIONES")
        print("-" * 40)
        
        if len(users) == 0:
            print("• Crear al menos un usuario administrador")
        
        if len(parkings) == 0:
            print("• Crear al menos un parking para el sistema")
        
        if len(panels) == 0:
            print("• Configurar paneles para los parkings")
        
        if len(cameras) == 0:
            print("• Configurar cámaras para los parkings")
        
        if len(schedules) == 0:
            print("• Crear programaciones de ejemplo para probar el sistema")
        
        print("\n" + "=" * 60)
        print("✅ VALIDACIÓN DE BASE DE DATOS COMPLETADA")
        print("=" * 60)
        
        return True
        
    except Exception as e:
        print(f"❌ Error durante la validación: {e}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        session.close()

if __name__ == "__main__":
    validate_database() 