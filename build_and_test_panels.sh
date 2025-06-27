#!/bin/bash

echo "🚦 COMPILANDO Y EJECUTANDO TEST DE PANELES C#"
echo "============================================================"

# Verificar que estamos en el directorio correcto
if [ ! -f "PanelTest.cs" ]; then
    echo "❌ Error: No se encuentra PanelTest.cs"
    exit 1
fi

# Verificar que existe CP5200.dll
if [ ! -f "docs/Rotuloselectronicos.NET_API+ejemplos/Rotuloselectronicos.NET API/Rotuloselectronicos.NET API SDK/CP5200.dll" ]; then
    echo "❌ Error: No se encuentra CP5200.dll"
    exit 1
fi

echo "1. Copiando CP5200.dll al directorio actual..."
cp "docs/Rotuloselectronicos.NET_API+ejemplos/Rotuloselectronicos.NET API/Rotuloselectronicos.NET API SDK/CP5200.dll" .

echo "2. Compilando aplicación C#..."
dotnet build PanelTest.csproj

if [ $? -eq 0 ]; then
    echo "✅ Compilación exitosa"
    
    echo "3. Ejecutando test de paneles..."
    echo "============================================================"
    dotnet run --project PanelTest.csproj
    
    echo "============================================================"
    echo "✅ Test completado"
else
    echo "❌ Error en la compilación"
    exit 1
fi

echo "4. Limpiando archivos temporales..."
rm -f CP5200.dll

echo "🎯 Proceso completado" 