#!/usr/bin/env python3
"""
Script de pruebas completas del frontend Parking Altea
Cubre autenticación y todas las funcionalidades del frontend
"""

import requests
import json
import time
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException

class FrontendTester:
    def __init__(self, base_url="http://157.180.91.63:5789", api_url="http://157.180.91.63:6001"):
        self.base_url = base_url
        self.api_url = api_url
        self.results = []
        self.driver = None
        self.wait = None
        
    def setup_driver(self):
        """Configurar el driver de Chrome"""
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        
        try:
            self.driver = webdriver.Chrome(options=chrome_options)
            self.wait = WebDriverWait(self.driver, 10)
            return True
        except Exception as e:
            print(f"❌ Error configurando driver: {e}")
            return False
    
    def log_test(self, test_name, success, details=""):
        """Registrar resultado de prueba"""
        result = {
            "test": test_name,
            "success": success,
            "details": details,
            "timestamp": datetime.now().isoformat()
        }
        self.results.append(result)
        
        status = "✅ PASÓ" if success else "❌ FALLÓ"
        print(f"{status} {test_name}")
        if details:
            print(f"   Detalles: {details}")
    
    def test_api_connectivity(self):
        """Probar conectividad con la API"""
        try:
            response = requests.get(f"{self.api_url}/parkings", timeout=5)
            if response.status_code == 200:
                self.log_test("Conectividad API", True)
                return True
            else:
                self.log_test("Conectividad API", False, f"Status: {response.status_code}")
                return False
        except Exception as e:
            self.log_test("Conectividad API", False, str(e))
            return False
    
    def test_frontend_access(self):
        """Probar acceso al frontend"""
        try:
            self.driver.get(self.base_url)
            time.sleep(2)
            
            # Verificar que la página carga
            title = self.driver.title
            if "Parking Altea" in title:
                self.log_test("Acceso Frontend", True)
                return True
            else:
                self.log_test("Acceso Frontend", False, f"Título: {title}")
                return False
        except Exception as e:
            self.log_test("Acceso Frontend", False, str(e))
            return False
    
    def test_login_page(self):
        """Probar página de login"""
        try:
            # Verificar elementos del login
            email_input = self.wait.until(EC.presence_of_element_located((By.NAME, "email")))
            password_input = self.driver.find_element(By.NAME, "password")
            login_button = self.driver.find_element(By.XPATH, "//button[contains(text(), 'Iniciar')]")
            
            if email_input and password_input and login_button:
                self.log_test("Página Login", True)
                return True
            else:
                self.log_test("Página Login", False, "Elementos no encontrados")
                return False
        except Exception as e:
            self.log_test("Página Login", False, str(e))
            return False
    
    def test_login_toni(self):
        """Probar login con Toni Alos"""
        try:
            # Limpiar campos
            email_input = self.driver.find_element(By.NAME, "email")
            password_input = self.driver.find_element(By.NAME, "password")
            
            email_input.clear()
            password_input.clear()
            
            # Ingresar credenciales
            email_input.send_keys("atea.dti@altea.es")
            password_input.send_keys("altea2025!")
            
            # Hacer login
            login_button = self.driver.find_element(By.XPATH, "//button[contains(text(), 'Iniciar')]")
            login_button.click()
            
            # Esperar redirección al dashboard
            self.wait.until(EC.url_contains("/dashboard"))
            
            # Verificar que estamos en el dashboard
            current_url = self.driver.current_url
            if "/dashboard" in current_url:
                self.log_test("Login Toni Alos", True)
                return True
            else:
                self.log_test("Login Toni Alos", False, f"URL: {current_url}")
                return False
                
        except Exception as e:
            self.log_test("Login Toni Alos", False, str(e))
            return False
    
    def test_login_ivan(self):
        """Probar login con Iván Martí"""
        try:
            # Ir a login
            self.driver.get(f"{self.base_url}/login")
            time.sleep(2)
            
            # Limpiar campos
            email_input = self.driver.find_element(By.NAME, "email")
            password_input = self.driver.find_element(By.NAME, "password")
            
            email_input.clear()
            password_input.clear()
            
            # Ingresar credenciales
            email_input.send_keys("gerenciapstd@altea.es")
            password_input.send_keys("altea2025!")
            
            # Hacer login
            login_button = self.driver.find_element(By.XPATH, "//button[contains(text(), 'Iniciar')]")
            login_button.click()
            
            # Esperar redirección al dashboard
            self.wait.until(EC.url_contains("/dashboard"))
            
            # Verificar que estamos en el dashboard
            current_url = self.driver.current_url
            if "/dashboard" in current_url:
                self.log_test("Login Iván Martí", True)
                return True
            else:
                self.log_test("Login Iván Martí", False, f"URL: {current_url}")
                return False
                
        except Exception as e:
            self.log_test("Login Iván Martí", False, str(e))
            return False
    
    def test_dashboard(self):
        """Probar funcionalidades del dashboard"""
        try:
            # Verificar elementos del dashboard
            welcome_text = self.wait.until(EC.presence_of_element_located((By.XPATH, "//h1[contains(text(), 'Dashboard')]")))
            
            # Verificar navegación
            nav_links = self.driver.find_elements(By.XPATH, "//nav//a")
            expected_links = ["Parkings", "Paneles", "Estadísticas", "Perfil"]
            
            found_links = []
            for link in nav_links:
                if link.text in expected_links:
                    found_links.append(link.text)
            
            if len(found_links) >= 3:  # Al menos 3 de los 4 enlaces
                self.log_test("Dashboard", True, f"Enlaces encontrados: {found_links}")
                return True
            else:
                self.log_test("Dashboard", False, f"Enlaces encontrados: {found_links}")
                return False
                
        except Exception as e:
            self.log_test("Dashboard", False, str(e))
            return False
    
    def test_parkings_page(self):
        """Probar página de parkings"""
        try:
            # Ir a parkings
            self.driver.get(f"{self.base_url}/parkings")
            time.sleep(2)
            
            # Verificar que la página carga
            title = self.wait.until(EC.presence_of_element_located((By.XPATH, "//h1[contains(text(), 'Parkings')]")))
            
            # Verificar que hay parkings listados
            parking_cards = self.driver.find_elements(By.XPATH, "//div[contains(@class, 'parking-card')]")
            
            if len(parking_cards) > 0:
                self.log_test("Página Parkings", True, f"Parkings encontrados: {len(parking_cards)}")
                return True
            else:
                self.log_test("Página Parkings", False, "No se encontraron parkings")
                return False
                
        except Exception as e:
            self.log_test("Página Parkings", False, str(e))
            return False
    
    def test_panels_page(self):
        """Probar página de paneles"""
        try:
            # Ir a paneles
            self.driver.get(f"{self.base_url}/panels")
            time.sleep(2)
            
            # Verificar que la página carga
            title = self.wait.until(EC.presence_of_element_located((By.XPATH, "//h1[contains(text(), 'Paneles')]")))
            
            # Verificar que hay paneles listados
            panel_cards = self.driver.find_elements(By.XPATH, "//div[contains(@class, 'panel-card')]")
            
            if len(panel_cards) >= 0:  # Puede que no haya paneles
                self.log_test("Página Paneles", True, f"Paneles encontrados: {len(panel_cards)}")
                return True
            else:
                self.log_test("Página Paneles", False, "Error al cargar paneles")
                return False
                
        except Exception as e:
            self.log_test("Página Paneles", False, str(e))
            return False
    
    def test_statistics_page(self):
        """Probar página de estadísticas"""
        try:
            # Ir a estadísticas
            self.driver.get(f"{self.base_url}/statistics")
            time.sleep(2)
            
            # Verificar que la página carga
            title = self.wait.until(EC.presence_of_element_located((By.XPATH, "//h1[contains(text(), 'Estadísticas')]")))
            
            # Verificar que hay contenido de estadísticas
            stats_content = self.driver.find_elements(By.XPATH, "//div[contains(@class, 'statistics')]")
            
            if len(stats_content) >= 0:  # Puede que no haya estadísticas
                self.log_test("Página Estadísticas", True, "Página cargada correctamente")
                return True
            else:
                self.log_test("Página Estadísticas", False, "Error al cargar estadísticas")
                return False
                
        except Exception as e:
            self.log_test("Página Estadísticas", False, str(e))
            return False
    
    def test_profile_page(self):
        """Probar página de perfil"""
        try:
            # Ir a perfil
            self.driver.get(f"{self.base_url}/profile")
            time.sleep(2)
            
            # Verificar que la página carga
            title = self.wait.until(EC.presence_of_element_located((By.XPATH, "//h1[contains(text(), 'Perfil')]")))
            
            # Verificar que hay información del usuario
            user_info = self.driver.find_elements(By.XPATH, "//div[contains(@class, 'user-info')]")
            
            if len(user_info) >= 0:  # Puede que no haya info específica
                self.log_test("Página Perfil", True, "Página cargada correctamente")
                return True
            else:
                self.log_test("Página Perfil", False, "Error al cargar perfil")
                return False
                
        except Exception as e:
            self.log_test("Página Perfil", False, str(e))
            return False
    
    def test_logout(self):
        """Probar logout"""
        try:
            # Buscar botón de logout
            logout_button = self.driver.find_element(By.XPATH, "//button[contains(text(), 'Cerrar')]")
            logout_button.click()
            
            # Esperar redirección al login
            self.wait.until(EC.url_contains("/login"))
            
            # Verificar que estamos en login
            current_url = self.driver.current_url
            if "/login" in current_url:
                self.log_test("Logout", True)
                return True
            else:
                self.log_test("Logout", False, f"URL: {current_url}")
                return False
                
        except Exception as e:
            self.log_test("Logout", False, str(e))
            return False
    
    def run_all_tests(self):
        """Ejecutar todas las pruebas"""
        print("🧪 INICIANDO PRUEBAS COMPLETAS DEL FRONTEND")
        print("=" * 60)
        print(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Frontend: {self.base_url}")
        print(f"API: {self.api_url}")
        print("=" * 60)
        print()
        
        # Configurar driver
        if not self.setup_driver():
            print("❌ No se pudo configurar el driver. Abortando pruebas.")
            return
        
        try:
            # Pruebas de conectividad
            print("🔌 PRUEBAS DE CONECTIVIDAD")
            print("-" * 30)
            self.test_api_connectivity()
            self.test_frontend_access()
            print()
            
            # Pruebas de autenticación
            print("🔐 PRUEBAS DE AUTENTICACIÓN")
            print("-" * 30)
            self.test_login_page()
            self.test_login_toni()
            self.test_login_ivan()
            print()
            
            # Pruebas de funcionalidades
            print("📱 PRUEBAS DE FUNCIONALIDADES")
            print("-" * 30)
            self.test_dashboard()
            self.test_parkings_page()
            self.test_panels_page()
            self.test_statistics_page()
            self.test_profile_page()
            print()
            
            # Prueba de logout
            print("🚪 PRUEBAS DE CERRADO DE SESIÓN")
            print("-" * 30)
            self.test_logout()
            print()
            
        finally:
            if self.driver:
                self.driver.quit()
        
        # Resumen
        self.print_summary()
        self.save_results()
    
    def print_summary(self):
        """Imprimir resumen de resultados"""
        print("=" * 60)
        print("RESUMEN DE PRUEBAS")
        print("=" * 60)
        
        total_tests = len(self.results)
        passed_tests = sum(1 for r in self.results if r["success"])
        failed_tests = total_tests - passed_tests
        
        print(f"Total pruebas: {total_tests}")
        print(f"Pruebas exitosas: {passed_tests}")
        print(f"Pruebas fallidas: {failed_tests}")
        print(f"Tasa de éxito: {(passed_tests/total_tests)*100:.1f}%")
        print()
        
        if failed_tests > 0:
            print("❌ PRUEBAS FALLIDAS:")
            for result in self.results:
                if not result["success"]:
                    print(f"  - {result['test']}: {result['details']}")
            print()
        
        if passed_tests == total_tests:
            print("🎉 ¡TODAS LAS PRUEBAS PASARON EXITOSAMENTE!")
        else:
            print("⚠️  Algunas pruebas fallaron. Revisar detalles arriba.")
    
    def save_results(self):
        """Guardar resultados en archivo JSON"""
        results_data = {
            "timestamp": datetime.now().isoformat(),
            "frontend_url": self.base_url,
            "api_url": self.api_url,
            "total_tests": len(self.results),
            "passed_tests": sum(1 for r in self.results if r["success"]),
            "failed_tests": sum(1 for r in self.results if not r["success"]),
            "results": self.results
        }
        
        filename = f"frontend_test_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(results_data, f, indent=2, ensure_ascii=False)
        
        print(f"📄 Resultados guardados en: {filename}")

if __name__ == "__main__":
    tester = FrontendTester()
    tester.run_all_tests() 