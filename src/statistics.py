#!/usr/bin/env python3
"""
Módulo para gestión de estadísticas y logs del sistema Parking Altea
"""

import json
from datetime import datetime, timedelta
from sqlalchemy import func, and_, desc
from sqlalchemy.orm import Session
from models import (
    Parking, ParkingStatistics, DailyStatistics, ActivityLog, 
    PanelMessageLog, VehicleCount, OccupancyHistory, Panel
)
import logging

logger = logging.getLogger(__name__)

class StatisticsManager:
    """Gestor de estadísticas del sistema"""
    
    def __init__(self, session: Session):
        self.session = session
    
    def log_activity(self, user_id=None, parking_id=None, panel_id=None, 
                    action_type='', action_details=None, ip_address=None, user_agent=None):
        """Registrar una actividad en el sistema"""
        try:
            log = ActivityLog(
                user_id=user_id,
                parking_id=parking_id,
                panel_id=panel_id,
                action_type=action_type,
                action_details=json.dumps(action_details) if action_details else None,
                ip_address=ip_address,
                user_agent=user_agent
            )
            self.session.add(log)
            self.session.commit()
            return True
        except Exception as e:
            logger.error(f"Error registrando actividad: {e}")
            self.session.rollback()
            return False
    
    def log_panel_message(self, panel_id, parking_id, user_id, message, duration, status='sent', response_time=None):
        """Registrar envío de mensaje a panel"""
        try:
            log = PanelMessageLog(
                panel_id=panel_id,
                parking_id=parking_id,
                user_id=user_id,
                message=message,
                duration=duration,
                status=status,
                response_time=response_time
            )
            self.session.add(log)
            self.session.commit()
            return True
        except Exception as e:
            logger.error(f"Error registrando mensaje de panel: {e}")
            self.session.rollback()
            return False
    
    def log_vehicle_count(self, access_id, parking_id, vehicles_in=0, vehicles_out=0, 
                         total_vehicles_in=None, total_vehicles_out=None):
        """Registrar conteo de vehículos"""
        try:
            # Si no se proporcionan totales, calcularlos
            if total_vehicles_in is None or total_vehicles_out is None:
                last_count = self.session.query(VehicleCount)\
                    .filter(VehicleCount.access_id == access_id)\
                    .order_by(desc(VehicleCount.timestamp))\
                    .first()
                
                if last_count:
                    total_vehicles_in = last_count.total_vehicles_in + vehicles_in
                    total_vehicles_out = last_count.total_vehicles_out + vehicles_out
                else:
                    total_vehicles_in = vehicles_in
                    total_vehicles_out = vehicles_out
            
            count = VehicleCount(
                access_id=access_id,
                parking_id=parking_id,
                vehicles_in=vehicles_in,
                vehicles_out=vehicles_out,
                total_vehicles_in=total_vehicles_in,
                total_vehicles_out=total_vehicles_out
            )
            self.session.add(count)
            self.session.commit()
            return True
        except Exception as e:
            logger.error(f"Error registrando conteo de vehículos: {e}")
            self.session.rollback()
            return False
    
    def update_hourly_statistics(self, parking_id, date=None):
        """Actualizar estadísticas por hora para un parking"""
        try:
            if date is None:
                date = datetime.now().replace(minute=0, second=0, microsecond=0)
            
            # Obtener datos de ocupación de la hora actual
            hour_start = date.replace(minute=0, second=0, microsecond=0)
            hour_end = hour_start + timedelta(hours=1)
            
            # Obtener historial de ocupación de la hora
            occupancy_data = self.session.query(OccupancyHistory)\
                .filter(and_(
                    OccupancyHistory.parking_id == parking_id,
                    OccupancyHistory.timestamp >= hour_start,
                    OccupancyHistory.timestamp < hour_end
                )).all()
            
            if not occupancy_data:
                return False
            
            # Calcular estadísticas
            occupancies = [data.occupancy for data in occupancy_data]
            avg_occupancy = sum(occupancies) / len(occupancies)
            max_occupancy = max(occupancies)
            min_occupancy = min(occupancies)
            
            # Obtener parking para umbrales
            parking = self.session.query(Parking).filter(Parking.id == parking_id).first()
            if not parking:
                return False
            
            # Calcular tiempo en cada estado
            time_libre = time_denso = time_completo = 0
            for data in occupancy_data:
                if data.occupancy < parking.threshold_dense:
                    time_libre += 1
                elif data.occupancy < parking.threshold_full:
                    time_denso += 1
                else:
                    time_completo += 1
            
            # Obtener conteo de vehículos de la hora
            vehicle_counts = self.session.query(VehicleCount)\
                .filter(and_(
                    VehicleCount.parking_id == parking_id,
                    VehicleCount.timestamp >= hour_start,
                    VehicleCount.timestamp < hour_end
                )).all()
            
            total_vehicles_in = sum(count.vehicles_in for count in vehicle_counts)
            total_vehicles_out = sum(count.vehicles_out for count in vehicle_counts)
            
            # Crear o actualizar estadísticas por hora
            stats = self.session.query(ParkingStatistics)\
                .filter(and_(
                    ParkingStatistics.parking_id == parking_id,
                    ParkingStatistics.date == hour_start.replace(hour=0),
                    ParkingStatistics.hour == hour_start.hour
                )).first()
            
            if stats:
                # Actualizar estadísticas existentes
                stats.avg_occupancy = avg_occupancy
                stats.max_occupancy = max_occupancy
                stats.min_occupancy = min_occupancy
                stats.total_vehicles_in = total_vehicles_in
                stats.total_vehicles_out = total_vehicles_out
                stats.time_libre = time_libre
                stats.time_denso = time_denso
                stats.time_completo = time_completo
                stats.updated_at = datetime.now()
            else:
                # Crear nuevas estadísticas
                stats = ParkingStatistics(
                    parking_id=parking_id,
                    date=hour_start.replace(hour=0),
                    hour=hour_start.hour,
                    avg_occupancy=avg_occupancy,
                    max_occupancy=max_occupancy,
                    min_occupancy=min_occupancy,
                    total_vehicles_in=total_vehicles_in,
                    total_vehicles_out=total_vehicles_out,
                    time_libre=time_libre,
                    time_denso=time_denso,
                    time_completo=time_completo
                )
                self.session.add(stats)
            
            self.session.commit()
            return True
            
        except Exception as e:
            logger.error(f"Error actualizando estadísticas por hora: {e}")
            self.session.rollback()
            return False
    
    def update_daily_statistics(self, parking_id, date=None):
        """Actualizar estadísticas diarias para un parking"""
        try:
            if date is None:
                date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            
            # Obtener estadísticas por hora del día
            hourly_stats = self.session.query(ParkingStatistics)\
                .filter(and_(
                    ParkingStatistics.parking_id == parking_id,
                    ParkingStatistics.date == date
                )).all()
            
            if not hourly_stats:
                return False
            
            # Calcular estadísticas diarias
            avg_occupancy = sum(stat.avg_occupancy for stat in hourly_stats) / len(hourly_stats)
            max_occupancy = max(stat.max_occupancy for stat in hourly_stats)
            min_occupancy = min(stat.min_occupancy for stat in hourly_stats)
            
            # Encontrar hora pico
            peak_hour = max(hourly_stats, key=lambda x: x.avg_occupancy).hour
            
            # Sumar vehículos
            total_vehicles_in = sum(stat.total_vehicles_in for stat in hourly_stats)
            total_vehicles_out = sum(stat.total_vehicles_out for stat in hourly_stats)
            
            # Sumar tiempos por estado
            time_libre = sum(stat.time_libre for stat in hourly_stats)
            time_denso = sum(stat.time_denso for stat in hourly_stats)
            time_completo = sum(stat.time_completo for stat in hourly_stats)
            
            # Crear o actualizar estadísticas diarias
            daily_stats = self.session.query(DailyStatistics)\
                .filter(and_(
                    DailyStatistics.parking_id == parking_id,
                    DailyStatistics.date == date
                )).first()
            
            if daily_stats:
                # Actualizar estadísticas existentes
                daily_stats.avg_occupancy = avg_occupancy
                daily_stats.max_occupancy = max_occupancy
                daily_stats.min_occupancy = min_occupancy
                daily_stats.peak_hour = peak_hour
                daily_stats.total_vehicles_in = total_vehicles_in
                daily_stats.total_vehicles_out = total_vehicles_out
                daily_stats.time_libre = time_libre
                daily_stats.time_denso = time_denso
                daily_stats.time_completo = time_completo
                daily_stats.updated_at = datetime.now()
            else:
                # Crear nuevas estadísticas
                daily_stats = DailyStatistics(
                    parking_id=parking_id,
                    date=date,
                    avg_occupancy=avg_occupancy,
                    max_occupancy=max_occupancy,
                    min_occupancy=min_occupancy,
                    peak_hour=peak_hour,
                    total_vehicles_in=total_vehicles_in,
                    total_vehicles_out=total_vehicles_out,
                    time_libre=time_libre,
                    time_denso=time_denso,
                    time_completo=time_completo
                )
                self.session.add(daily_stats)
            
            self.session.commit()
            return True
            
        except Exception as e:
            logger.error(f"Error actualizando estadísticas diarias: {e}")
            self.session.rollback()
            return False
    
    def get_parking_statistics(self, parking_id, days=7):
        """Obtener estadísticas de un parking para los últimos N días"""
        try:
            end_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            start_date = end_date - timedelta(days=days)
            
            # Obtener estadísticas diarias
            daily_stats = self.session.query(DailyStatistics)\
                .filter(and_(
                    DailyStatistics.parking_id == parking_id,
                    DailyStatistics.date >= start_date,
                    DailyStatistics.date <= end_date
                ))\
                .order_by(DailyStatistics.date)\
                .all()
            
            # Obtener estadísticas por hora del último día
            last_day_stats = self.session.query(ParkingStatistics)\
                .filter(and_(
                    ParkingStatistics.parking_id == parking_id,
                    ParkingStatistics.date == end_date
                ))\
                .order_by(ParkingStatistics.hour)\
                .all()
            
            return {
                'daily_stats': [
                    {
                        'date': stat.date.strftime('%Y-%m-%d'),
                        'avg_occupancy': stat.avg_occupancy,
                        'max_occupancy': stat.max_occupancy,
                        'min_occupancy': stat.min_occupancy,
                        'peak_hour': stat.peak_hour,
                        'total_vehicles_in': stat.total_vehicles_in,
                        'total_vehicles_out': stat.total_vehicles_out,
                        'time_libre': stat.time_libre,
                        'time_denso': stat.time_denso,
                        'time_completo': stat.time_completo
                    }
                    for stat in daily_stats
                ],
                'hourly_stats': [
                    {
                        'hour': stat.hour,
                        'avg_occupancy': stat.avg_occupancy,
                        'max_occupancy': stat.max_occupancy,
                        'min_occupancy': stat.min_occupancy,
                        'total_vehicles_in': stat.total_vehicles_in,
                        'total_vehicles_out': stat.total_vehicles_out
                    }
                    for stat in last_day_stats
                ]
            }
            
        except Exception as e:
            logger.error(f"Error obteniendo estadísticas: {e}")
            return None
    
    def get_all_parkings_statistics(self, days=7):
        """Obtener estadísticas de todos los parkings"""
        try:
            parkings = self.session.query(Parking).all()
            result = {}
            
            for parking in parkings:
                stats = self.get_parking_statistics(parking.id, days)
                if stats:
                    result[parking.id] = {
                        'parking_name': parking.name,
                        'statistics': stats
                    }
            
            return result
            
        except Exception as e:
            logger.error(f"Error obteniendo estadísticas de todos los parkings: {e}")
            return None
    
    def get_activity_logs(self, user_id=None, parking_id=None, action_type=None, 
                         start_date=None, end_date=None, limit=100):
        """Obtener logs de actividad"""
        try:
            query = self.session.query(ActivityLog)
            
            if user_id:
                query = query.filter(ActivityLog.user_id == user_id)
            if parking_id:
                query = query.filter(ActivityLog.parking_id == parking_id)
            if action_type:
                query = query.filter(ActivityLog.action_type == action_type)
            if start_date:
                query = query.filter(ActivityLog.timestamp >= start_date)
            if end_date:
                query = query.filter(ActivityLog.timestamp <= end_date)
            
            logs = query.order_by(desc(ActivityLog.timestamp)).limit(limit).all()
            
            return [
                {
                    'id': log.id,
                    'user_id': log.user_id,
                    'parking_id': log.parking_id,
                    'panel_id': log.panel_id,
                    'action_type': log.action_type,
                    'action_details': json.loads(log.action_details) if log.action_details else None,
                    'ip_address': log.ip_address,
                    'user_agent': log.user_agent,
                    'timestamp': log.timestamp.isoformat()
                }
                for log in logs
            ]
            
        except Exception as e:
            logger.error(f"Error obteniendo logs de actividad: {e}")
            return None
    
    def get_panel_message_logs(self, panel_id=None, parking_id=None, 
                              start_date=None, end_date=None, limit=100):
        """Obtener logs de mensajes de paneles"""
        try:
            query = self.session.query(PanelMessageLog)
            
            if panel_id:
                query = query.filter(PanelMessageLog.panel_id == panel_id)
            if parking_id:
                query = query.filter(PanelMessageLog.parking_id == parking_id)
            if start_date:
                query = query.filter(PanelMessageLog.sent_at >= start_date)
            if end_date:
                query = query.filter(PanelMessageLog.sent_at <= end_date)
            
            logs = query.order_by(desc(PanelMessageLog.sent_at)).limit(limit).all()
            
            return [
                {
                    'id': log.id,
                    'panel_id': log.panel_id,
                    'parking_id': log.parking_id,
                    'user_id': log.user_id,
                    'message': log.message,
                    'duration': log.duration,
                    'status': log.status,
                    'response_time': log.response_time,
                    'sent_at': log.sent_at.isoformat()
                }
                for log in logs
            ]
            
        except Exception as e:
            logger.error(f"Error obteniendo logs de mensajes de paneles: {e}")
            return None 