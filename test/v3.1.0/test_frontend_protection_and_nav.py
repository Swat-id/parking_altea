#!/usr/bin/env python3
"""
Test script para verificar la protección de rutas y navegación adaptativa en el frontend (T3.6)
"""

import sys
import os
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
import time

FRONTEND_URL = 'http://localhost:5173'

# Configuración de Selenium para modo headless
chrome_options = Options()
chrome_options.add_argument('--headless')
chrome_options.add_argument('--no-sandbox')
chrome_options.add_argument('--disable-dev-shm-usage')


def test_frontend_protection_and_nav():
    print("=" * 60)
    print("TESTING FRONTEND PROTECCIÓN DE RUTAS Y NAVEGACIÓN - T3.6")
    print("=" * 60)
    results = []

    # 1. Probar acceso a ruta protegida sin login
    print("\n1. Probar acceso a /dashboard sin login...")
    driver = webdriver.Chrome(options=chrome_options)
    driver.get(FRONTEND_URL + '/dashboard')
    time.sleep(2)
    if '/login' in driver.current_url:
        print("✓ Redirigido a login correctamente")
        results.append(("protection_no_login", "PASS"))
    else:
        print(f"✗ No redirigido a login: {driver.current_url}")
        results.append(("protection_no_login", "FAIL"))

    # 2. Login como usuario normal
    print("\n2. Login como usuario normal...")
    driver.get(FRONTEND_URL + '/login')
    time.sleep(1)
    email_input = driver.find_element(By.ID, 'email')
    password_input = driver.find_element(By.ID, 'password')
    email_input.send_keys('frontend_user@test.com')
    password_input.send_keys('test123')
    password_input.send_keys(Keys.RETURN)
    time.sleep(3)
    if '/dashboard' in driver.current_url:
        print("✓ Login usuario normal exitoso")
        results.append(("login_user", "PASS"))
    else:
        print(f"✗ Login usuario normal falló: {driver.current_url}")
        results.append(("login_user", "FAIL"))

    # 3. Verificar que no aparece menú de administración
    print("\n3. Verificar menú de administración para usuario normal...")
    nav_html = driver.page_source
    if 'Administración' not in nav_html:
        print("✓ Menú de administración oculto para usuario normal")
        results.append(("nav_no_admin_user", "PASS"))
    else:
        print("✗ Menú de administración visible para usuario normal")
        results.append(("nav_no_admin_user", "FAIL"))

    # 4. Logout
    driver.delete_all_cookies()
    driver.get(FRONTEND_URL + '/login')
    time.sleep(1)

    # 5. Login como superadmin
    print("\n5. Login como superadmin...")
    email_input = driver.find_element(By.ID, 'email')
    password_input = driver.find_element(By.ID, 'password')
    email_input.send_keys('frontend_admin@test.com')
    password_input.send_keys('test123')
    password_input.send_keys(Keys.RETURN)
    time.sleep(3)
    if '/dashboard' in driver.current_url:
        print("✓ Login superadmin exitoso")
        results.append(("login_superadmin", "PASS"))
    else:
        print(f"✗ Login superadmin falló: {driver.current_url}")
        results.append(("login_superadmin", "FAIL"))

    # 6. Verificar que aparece menú de administración
    print("\n6. Verificar menú de administración para superadmin...")
    nav_html = driver.page_source
    if 'Administración' in nav_html:
        print("✓ Menú de administración visible para superadmin")
        results.append(("nav_admin_superadmin", "PASS"))
    else:
        print("✗ Menú de administración no visible para superadmin")
        results.append(("nav_admin_superadmin", "FAIL"))

    # 7. Probar acceso a ruta protegida tras login
    print("\n7. Probar acceso a /profile tras login...")
    driver.get(FRONTEND_URL + '/profile')
    time.sleep(2)
    if '/profile' in driver.current_url:
        print("✓ Acceso a /profile permitido tras login")
        results.append(("protection_profile", "PASS"))
    else:
        print(f"✗ Acceso a /profile falló: {driver.current_url}")
        results.append(("protection_profile", "FAIL"))

    driver.quit()

    # Resumen de resultados
    print("\n" + "=" * 60)
    print("RESUMEN DE RESULTADOS")
    print("=" * 60)
    passed = 0
    failed = 0
    for test_name, result in results:
        status_icon = "✓" if result == "PASS" else "✗"
        print(f"{status_icon} {test_name}: {result}")
        if result == "PASS":
            passed += 1
        else:
            failed += 1
    print(f"\nTotal: {len(results)} tests")
    print(f"✓ Pasados: {passed}")
    print(f"✗ Fallidos: {failed}")
    if failed == 0:
        print("\n🎉 TODOS LOS TESTS PASARON - T3.6 COMPLETADA")
        return True
    else:
        print(f"\n⚠️  {failed} TESTS FALLARON")
        return False

if __name__ == "__main__":
    success = test_frontend_protection_and_nav()
    sys.exit(0 if success else 1) 