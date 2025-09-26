# Comandos de Despliegue Frontend v4.2.0 - FINAL

## 🎯 **Comandos Probados y Exitosos**

### **FASE 1: PREPARACIÓN Y ACTUALIZACIÓN GIT**
```bash
# Conectar al servidor
ssh root@157.180.91.63
cd /opt/parking_altea

# Actualizar código desde git
git stash  # Solo si hay cambios locales
git pull origin v4.1.0
git status  # Verificar actualización
```

### **FASE 2: COMPILACIÓN DEL FRONTEND**
```bash
# Ir al directorio del cliente
cd /opt/parking_altea/client

# Limpiar compilaciones anteriores
rm -rf dist/
rm -rf node_modules/.cache/ 2>/dev/null || true

# Instalar dependencias necesarias
npm install react-bootstrap bootstrap

# Corregir permisos de vite (CRÍTICO)
chmod +x node_modules/.bin/vite

# Compilar para producción
NODE_ENV=production npm run build

# Verificar compilación exitosa
ls -la dist/
ls -la dist/assets/
du -sh dist/  # Debe mostrar ~700K
```

### **FASE 3: DESPLIEGUE CON NGINX**
```bash
# Crear directorio estático si no existe
mkdir -p /opt/parking_altea/static

# Copiar archivos compilados
cp -r dist/* /opt/parking_altea/static/

# Verificar archivos copiados
ls -la /opt/parking_altea/static/
ls -la /opt/parking_altea/static/assets/

# Configurar permisos para nginx
chown -R www-data:www-data /opt/parking_altea/static/
chmod -R 755 /opt/parking_altea/static/
```

### **FASE 4: CONFIGURACIÓN Y INICIO DE NGINX**
```bash
# Verificar estado de nginx
systemctl status nginx --no-pager

# Iniciar nginx si no está activo
systemctl start nginx
systemctl enable nginx

# Verificar configuración
nginx -t

# Si la configuración es correcta, recargar
if [ $? -eq 0 ]; then
    systemctl reload nginx
    echo "✅ Nginx recargado correctamente"
else
    echo "❌ Error en configuración nginx"
fi

# Verificar estado final
systemctl status nginx --no-pager
netstat -tlnp | grep :80
```

### **FASE 5: VERIFICACIÓN COMPLETA**
```bash
echo "========================================="
echo "🎉 VERIFICACIÓN FINAL v4.2.0"
echo "========================================="

echo "🔸 Estado de servicios:"
echo "   - Nginx: $(systemctl is-active nginx)"
echo "   - API: $(systemctl is-active parking-api.service)"

echo "🔸 Tests de conectividad:"
echo "   - Frontend principal:"
curl -s -I http://localhost/ | head -1

echo "   - Ruta React (/parkings):"
curl -s -I http://localhost/parkings | head -1

echo "   - API través nginx:"
curl -s -I http://localhost/api/parkings | head -1

echo ""
echo "🌐 URLs DE ACCESO:"
echo "   - Frontend: http://157.180.91.63/"
echo "   - Parkings: http://157.180.91.63/parkings"
echo "   - Sensores: http://157.180.91.63/sensors"
echo "   - Dashboard: http://157.180.91.63/dashboard"
echo "   - Login: http://157.180.91.63/login"
echo "========================================="
```

## 🔧 **Problemas Comunes y Soluciones**

### **Error: "vite: Permission denied"**
```bash
chmod +x node_modules/.bin/vite
chmod +x node_modules/.bin/*
```

### **Error: "react-bootstrap not found"**
```bash
npm install react-bootstrap bootstrap
npm list react-bootstrap  # Verificar instalación
```

### **Error: "nginx.service is not active, cannot reload"**
```bash
systemctl start nginx
systemctl enable nginx
systemctl status nginx --no-pager
```

### **Error: "target '/opt/parking_altea/static/': No such file or directory"**
```bash
mkdir -p /opt/parking_altea/static
cp -r dist/* /opt/parking_altea/static/
```

### **Error: archivos corruptos (tsconfig.json con caracteres raros)**
```bash
# Eliminar archivo corrupto
rm tsconfig.json
# El archivo se regenerará automáticamente o usar git checkout
git checkout -- tsconfig.json
```

## 📋 **Configuración Nginx Mínima (si no existe)**
```bash
# Solo ejecutar si no existe /etc/nginx/sites-available/parking_altea
cat > /etc/nginx/sites-available/parking_altea << 'EOF'
server {
    listen 80;
    server_name 157.180.91.63;
    
    # API endpoints
    location /api/ {
        proxy_pass http://127.0.0.1:6001/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    # Frontend - React SPA
    location / {
        root /opt/parking_altea/static;
        try_files $uri $uri/ /index.html;
        
        # Sin caché para HTML
        location ~* \.(html)$ {
            add_header Cache-Control "no-cache, no-store, must-revalidate";
        }
        
        # Caché para assets estáticos
        location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg)$ {
            expires 1y;
            add_header Cache-Control "public, immutable";
        }
    }
    
    error_page 404 /index.html;
}
EOF

# Habilitar sitio
ln -sf /etc/nginx/sites-available/parking_altea /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default
```

## ✅ **Checklist de Verificación**

- [ ] Git actualizado con últimos cambios
- [ ] Dependencias npm instaladas (react-bootstrap, bootstrap)
- [ ] Permisos de vite corregidos
- [ ] Compilación exitosa (dist/ generado)
- [ ] Archivos copiados a /opt/parking_altea/static/
- [ ] Permisos de archivos configurados (www-data:www-data)
- [ ] Nginx iniciado y funcionando
- [ ] Configuración nginx válida
- [ ] URLs accesibles desde navegador

## 🎯 **Resultado Esperado**

- **Frontend accesible en:** `http://157.180.91.63/`
- **Todas las rutas React funcionando** (parkings, sensors, dashboard, login)
- **API proxy funcionando** a través de nginx
- **Funcionalidad de edición de ocupación** corregida
- **Servicios auto-reiniciables** en caso de fallo

---

**Tiempo estimado de ejecución:** 5-10 minutos  
**Última actualización:** 26/09/2025 - v4.2.0 Final
