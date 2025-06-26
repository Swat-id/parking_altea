#!/bin/bash

# Script de despliegue para Parking Altea v2.1
# Actualiza el servidor remoto con la nueva versión

set -e  # Salir si hay algún error

echo "🚀 Iniciando despliegue de Parking Altea v2.1..."
echo "=================================================="

# Variables de configuración
REMOTE_HOST="your-server.com"  # Cambiar por la IP/hostname del servidor
REMOTE_USER="parking_user"     # Cambiar por el usuario del servidor
REMOTE_PATH="/opt/parking_altea"  # Cambiar por la ruta en el servidor
BRANCH="v2.1"

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Función para imprimir mensajes con colores
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Verificar que estamos en la rama correcta
print_status "Verificando rama actual..."
CURRENT_BRANCH=$(git branch --show-current)
if [ "$CURRENT_BRANCH" != "$BRANCH" ]; then
    print_error "No estás en la rama $BRANCH. Cambiando a $BRANCH..."
    git checkout $BRANCH
fi

# Verificar que no hay cambios pendientes
print_status "Verificando cambios pendientes..."
if ! git diff-index --quiet HEAD --; then
    print_error "Hay cambios pendientes. Por favor, haz commit antes de desplegar."
    exit 1
fi

# Verificar que la rama está actualizada
print_status "Verificando que la rama está actualizada..."
git fetch origin
LOCAL_COMMIT=$(git rev-parse HEAD)
REMOTE_COMMIT=$(git rev-parse origin/$BRANCH)
if [ "$LOCAL_COMMIT" != "$REMOTE_COMMIT" ]; then
    print_error "La rama local no está actualizada con el remoto. Haciendo pull..."
    git pull origin $BRANCH
fi

# Conectar al servidor remoto y actualizar
print_status "Conectando al servidor remoto ($REMOTE_HOST)..."
ssh $REMOTE_USER@$REMOTE_HOST << 'EOF'
    set -e
    
    echo "🔧 Actualizando código en el servidor..."
    cd /opt/parking_altea
    
    # Hacer backup de la configuración actual
    echo "📦 Creando backup de configuración..."
    if [ -f .env ]; then
        cp .env .env.backup.$(date +%Y%m%d_%H%M%S)
    fi
    
    # Actualizar código desde Git
    echo "📥 Actualizando código desde Git..."
    git fetch origin
    git reset --hard origin/v2.1
    
    # Instalar/actualizar dependencias
    echo "📦 Instalando dependencias..."
    pip install -r requirements.txt
    
    # Actualizar base de datos
    echo "🗄️  Actualizando base de datos..."
    cd src
    python update_database.py
    
    # Verificar acceso de usuarios
    echo "🔍 Verificando acceso de usuarios..."
    python verify_user_access.py
    
    # Reiniciar servicios
    echo "🔄 Reiniciando servicios..."
    sudo systemctl restart parking-api || echo "⚠️  No se pudo reiniciar parking-api"
    sudo systemctl restart parking-camera || echo "⚠️  No se pudo reiniciar parking-camera"
    
    echo "✅ Despliegue completado en el servidor"
EOF

if [ $? -eq 0 ]; then
    print_status "🎉 ¡Despliegue completado exitosamente!"
    print_status "El servidor está actualizado con la versión v2.1"
    
    echo ""
    echo "📋 Próximos pasos:"
    echo "1. Verificar que la API responde correctamente"
    echo "2. Probar autenticación con los usuarios:"
    echo "   - Toni Alos: atea.dti@altea.es / altea2025!"
    echo "   - Iván Martí: gerenciapstd@altea.es / altea2025!"
    echo "3. Verificar que las rutas protegidas funcionan"
    echo "4. Comprobar que los usuarios tienen acceso a todos los recursos"
    
else
    print_error "❌ Error durante el despliegue"
    exit 1
fi

echo ""
print_status "Despliegue finalizado. Revisa los logs del servidor si hay problemas." 