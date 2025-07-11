#!/bin/bash

# Script de Despliegue del Sistema de Login - Parking Altea v3.1.0
# Este script valida y despliega el sistema de autenticación completo

set -e  # Salir en caso de error

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Función para imprimir mensajes con colores
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Función para verificar si un comando existe
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Función para verificar si el servidor está ejecutándose
check_server_status() {
    if systemctl is-active --quiet parking-api; then
        return 0
    else
        return 1
    fi
}

# Función para hacer backup de la base de datos
backup_database() {
    print_status "Creando backup de la base de datos..."
    
    TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
    BACKUP_FILE="backup_login_system_${TIMESTAMP}.sql"
    
    if pg_dump parking_altea > "/tmp/${BACKUP_FILE}"; then
        print_success "Backup creado: /tmp/${BACKUP_FILE}"
    else
        print_error "Error creando backup de la base de datos"
        exit 1
    fi
}

# Función para validar la estructura de la base de datos
validate_database_structure() {
    print_status "Validando estructura de la base de datos..."
    
    cd /opt/parking_altea
    
    # Ejecutar script de validación
    if python3 test/validate_login_system.py; then
        print_success "Validación de base de datos completada"
    else
        print_error "Error en la validación de base de datos"
        exit 1
    fi
}

# Función para ejecutar migración
run_migration() {
    print_status "Ejecutando migración del sistema de login..."
    
    cd /opt/parking_altea
    
    # Verificar si el script de migración existe
    if [ ! -f "src/migrate_to_v3_1_0.py" ]; then
        print_error "Script de migración no encontrado: src/migrate_to_v3_1_0.py"
        exit 1
    fi
    
    # Ejecutar migración
    if python3 src/migrate_to_v3_1_0.py; then
        print_success "Migración completada exitosamente"
    else
        print_error "Error durante la migración"
        exit 1
    fi
}

# Función para verificar usuarios iniciales
verify_initial_users() {
    print_status "Verificando usuarios iniciales..."
    
    cd /opt/parking_altea
    
    # Script para verificar usuarios
    python3 -c "
import sys
sys.path.append('src')
from models import User
from config import DB_URL
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

engine = create_engine(DB_URL)
Session = sessionmaker(bind=engine)
session = Session()

users = session.query(User).all()
print(f'Total usuarios encontrados: {len(users)}')

for user in users:
    print(f'ID: {user.id}, Name: {user.name}, Email: {user.email}, Role: {user.role}, Active: {user.is_active}')

session.close()
"
    
    print_success "Verificación de usuarios completada"
}

# Función para validar endpoints de la API
validate_api_endpoints() {
    print_status "Validando endpoints de la API..."
    
    # Verificar que el servidor esté ejecutándose
    if ! check_server_status; then
        print_warning "Servidor no está ejecutándose, iniciando..."
        sudo systemctl start parking-api
        sleep 5
    fi
    
    # Test de endpoint de login
    print_status "Probando endpoint de login..."
    
    LOGIN_RESPONSE=$(curl -s -X POST http://localhost:6001/auth/login \
        -H "Content-Type: application/json" \
        -d '{"email":"info@swat-id.com","password":"admin123"}' || echo "ERROR")
    
    if [[ "$LOGIN_RESPONSE" == "ERROR" ]]; then
        print_error "Error conectando al endpoint de login"
        return 1
    fi
    
    # Extraer token de la respuesta
    TOKEN=$(echo "$LOGIN_RESPONSE" | grep -o '"token":"[^"]*"' | cut -d'"' -f4)
    
    if [ -z "$TOKEN" ]; then
        print_error "No se pudo extraer token de la respuesta"
        echo "Respuesta: $LOGIN_RESPONSE"
        return 1
    fi
    
    # Verificar longitud del token
    TOKEN_LENGTH=${#TOKEN}
    print_status "Longitud del token: $TOKEN_LENGTH caracteres"
    
    if [ "$TOKEN_LENGTH" -le 255 ]; then
        print_error "Token demasiado corto: $TOKEN_LENGTH caracteres"
        return 1
    fi
    
    print_success "Token generado correctamente: $TOKEN_LENGTH caracteres"
    
    # Test de endpoint de permisos
    print_status "Probando endpoint de permisos..."
    
    PERMISSIONS_RESPONSE=$(curl -s -X GET http://localhost:6001/auth/permissions \
        -H "Authorization: Bearer $TOKEN" || echo "ERROR")
    
    if [[ "$PERMISSIONS_RESPONSE" == "ERROR" ]]; then
        print_error "Error en endpoint de permisos"
        return 1
    fi
    
    print_success "Endpoints de API validados correctamente"
}

# Función para reconstruir el frontend
rebuild_frontend() {
    print_status "Reconstruyendo frontend..."
    
    cd /opt/parking_altea/client
    
    # Verificar que npm esté instalado
    if ! command_exists npm; then
        print_error "npm no está instalado"
        exit 1
    fi
    
    # Instalar dependencias si es necesario
    if [ ! -d "node_modules" ]; then
        print_status "Instalando dependencias..."
        npm install
    fi
    
    # Construir el frontend
    print_status "Construyendo aplicación..."
    if npm run build; then
        print_success "Frontend construido exitosamente"
    else
        print_error "Error construyendo el frontend"
        exit 1
    fi
    
    # Verificar que los archivos se generaron
    if [ ! -d "dist" ]; then
        print_error "Directorio dist no encontrado después de la construcción"
        exit 1
    fi
    
    print_success "Frontend listo para despliegue"
}

# Función para verificar configuración de nginx
verify_nginx_config() {
    print_status "Verificando configuración de nginx..."
    
    # Verificar que nginx esté instalado
    if ! command_exists nginx; then
        print_error "nginx no está instalado"
        exit 1
    fi
    
    # Verificar configuración
    if nginx -t; then
        print_success "Configuración de nginx válida"
    else
        print_error "Error en la configuración de nginx"
        exit 1
    fi
    
    # Verificar que el proxy incluya headers de autorización
    if grep -q "proxy_set_header Authorization" /etc/nginx/sites-available/parking_altea; then
        print_success "Headers de autorización configurados en nginx"
    else
        print_warning "Headers de autorización no encontrados en nginx"
        print_status "Asegúrese de que nginx incluya:"
        echo "    proxy_set_header Authorization \$http_authorization;"
        echo "    proxy_pass_header Authorization;"
    fi
}

# Función para reiniciar servicios
restart_services() {
    print_status "Reiniciando servicios..."
    
    # Reiniciar API
    if sudo systemctl restart parking-api; then
        print_success "Servicio parking-api reiniciado"
    else
        print_error "Error reiniciando parking-api"
        exit 1
    fi
    
    # Reiniciar nginx
    if sudo systemctl restart nginx; then
        print_success "Servicio nginx reiniciado"
    else
        print_error "Error reiniciando nginx"
        exit 1
    fi
    
    # Esperar a que los servicios estén listos
    sleep 3
}

# Función para validación final
final_validation() {
    print_status "Ejecutando validación final..."
    
    cd /opt/parking_altea
    
    # Ejecutar tests completos
    if python3 test/validate_login_system.py; then
        print_success "Validación final completada exitosamente"
    else
        print_error "Error en la validación final"
        exit 1
    fi
    
    # Verificar logs
    print_status "Verificando logs del sistema..."
    
    if sudo journalctl -u parking-api --no-pager -n 20 | grep -q "ERROR"; then
        print_warning "Se encontraron errores en los logs de parking-api"
        sudo journalctl -u parking-api --no-pager -n 10
    else
        print_success "No se encontraron errores críticos en los logs"
    fi
}

# Función para mostrar información de acceso
show_access_info() {
    print_success "Despliegue del sistema de login completado exitosamente!"
    echo ""
    echo "📋 INFORMACIÓN DE ACCESO:"
    echo "URL: http://157.180.91.63"
    echo ""
    echo "🔑 CREDENCIALES DE PRUEBA:"
    echo "Superadmin: info@swat-id.com / admin123"
    echo "Usuario: user@test.com / test123"
    echo ""
    echo "📊 MONITOREO:"
    echo "- Logs de API: sudo journalctl -u parking-api -f"
    echo "- Logs de nginx: sudo tail -f /var/log/nginx/access.log"
    echo "- Estado de servicios: sudo systemctl status parking-api nginx"
    echo ""
    echo "🔧 COMANDOS ÚTILES:"
    echo "- Reiniciar API: sudo systemctl restart parking-api"
    echo "- Reiniciar nginx: sudo systemctl restart nginx"
    echo "- Verificar BD: python3 test/validate_login_system.py"
}

# Función principal
main() {
    echo "🚀 DESPLIEGUE DEL SISTEMA DE LOGIN - PARKING ALTEA v3.1.0"
    echo "=================================================="
    echo ""
    
    # Verificar que estamos en el directorio correcto
    if [ ! -f "src/auth.py" ]; then
        print_error "Este script debe ejecutarse desde el directorio raíz del proyecto"
        exit 1
    fi
    
    # Verificar permisos de sudo
    if ! sudo -n true 2>/dev/null; then
        print_error "Este script requiere permisos de sudo"
        exit 1
    fi
    
    # Paso 1: Backup de la base de datos
    backup_database
    
    # Paso 2: Validar estructura de la base de datos
    validate_database_structure
    
    # Paso 3: Ejecutar migración
    run_migration
    
    # Paso 4: Verificar usuarios iniciales
    verify_initial_users
    
    # Paso 5: Validar endpoints de la API
    validate_api_endpoints
    
    # Paso 6: Reconstruir frontend
    rebuild_frontend
    
    # Paso 7: Verificar configuración de nginx
    verify_nginx_config
    
    # Paso 8: Reiniciar servicios
    restart_services
    
    # Paso 9: Validación final
    final_validation
    
    # Paso 10: Mostrar información de acceso
    show_access_info
    
    print_success "¡Despliegue completado exitosamente!"
}

# Ejecutar función principal
main "$@" 