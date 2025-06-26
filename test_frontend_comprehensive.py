#!/usr/bin/env python3
"""
Comprehensive UI test script for Parking Altea frontend
"""

import time
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException

def setup_driver():
    """Setup Chrome driver with options"""
    chrome_options = Options()
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    
    try:
        driver = webdriver.Chrome(options=chrome_options)
        driver.implicitly_wait(10)
        return driver
    except Exception as e:
        print(f"Error setting up driver: {e}")
        return None

def test_api_connectivity():
    """Test API connectivity"""
    print("\n=== TESTING API CONNECTIVITY ===")
    
    try:
        response = requests.get("http://localhost:6001/api/parkings", timeout=5)
        if response.status_code == 200:
            print("✅ API connectivity: OK")
            return True
        else:
            print(f"❌ API connectivity: Status {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ API connectivity: {e}")
        return False

def test_frontend_connectivity(driver):
    """Test frontend connectivity"""
    print("\n=== TESTING FRONTEND CONNECTIVITY ===")
    
    try:
        driver.get("http://localhost:5789")
        time.sleep(2)
        
        # Check if login page loads
        title = driver.title
        if "Parking Altea" in title or "Login" in title:
            print("✅ Frontend connectivity: OK")
            return True
        else:
            print(f"❌ Frontend connectivity: Unexpected title: {title}")
            return False
    except Exception as e:
        print(f"❌ Frontend connectivity: {e}")
        return False

def test_login_flow(driver, email, password, user_name):
    """Test login flow for a specific user"""
    print(f"\n=== TESTING LOGIN FLOW FOR {user_name} ===")
    
    try:
        # Navigate to login page
        driver.get("http://localhost:5789/login")
        time.sleep(2)
        
        # Find and fill email field
        email_field = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "email"))
        )
        email_field.clear()
        email_field.send_keys(email)
        
        # Find and fill password field
        password_field = driver.find_element(By.ID, "password")
        password_field.clear()
        password_field.send_keys(password)
        
        # Submit form
        submit_button = driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
        submit_button.click()
        
        # Wait for redirect to dashboard
        WebDriverWait(driver, 10).until(
            EC.url_contains("/dashboard")
        )
        
        print(f"✅ Login successful for {user_name}")
        return True
        
    except TimeoutException:
        print(f"❌ Login timeout for {user_name}")
        return False
    except Exception as e:
        print(f"❌ Login failed for {user_name}: {e}")
        return False

def test_dashboard_navigation(driver):
    """Test dashboard navigation and elements"""
    print("\n=== TESTING DASHBOARD NAVIGATION ===")
    
    try:
        # Check if we're on dashboard
        current_url = driver.current_url
        if "/dashboard" not in current_url:
            print("❌ Not on dashboard page")
            return False
        
        # Check for navigation elements
        nav_links = driver.find_elements(By.CSS_SELECTOR, "nav a")
        expected_links = ["Dashboard", "Parkings", "Paneles", "Estadísticas", "Perfil"]
        
        found_links = [link.text for link in nav_links if link.text]
        print(f"Found navigation links: {found_links}")
        
        for expected in expected_links:
            if expected not in found_links:
                print(f"❌ Missing navigation link: {expected}")
                return False
        
        print("✅ Dashboard navigation: OK")
        return True
        
    except Exception as e:
        print(f"❌ Dashboard navigation failed: {e}")
        return False

def test_parkings_page(driver):
    """Test parkings page"""
    print("\n=== TESTING PARKINGS PAGE ===")
    
    try:
        # Navigate to parkings page
        parkings_link = driver.find_element(By.XPATH, "//a[contains(text(), 'Parkings')]")
        parkings_link.click()
        
        # Wait for page to load
        WebDriverWait(driver, 10).until(
            EC.url_contains("/parkings")
        )
        
        # Check for parking cards
        parking_cards = driver.find_elements(By.CSS_SELECTOR, "[data-testid='parking-card']")
        if len(parking_cards) > 0:
            print(f"✅ Parkings page: Found {len(parking_cards)} parking cards")
            return True
        else:
            print("❌ Parkings page: No parking cards found")
            return False
            
    except Exception as e:
        print(f"❌ Parkings page failed: {e}")
        return False

def test_panels_page(driver):
    """Test panels page"""
    print("\n=== TESTING PANELS PAGE ===")
    
    try:
        # Navigate to panels page
        panels_link = driver.find_element(By.XPATH, "//a[contains(text(), 'Paneles')]")
        panels_link.click()
        
        # Wait for page to load
        WebDriverWait(driver, 10).until(
            EC.url_contains("/panels")
        )
        
        # Check for panel elements
        panel_elements = driver.find_elements(By.CSS_SELECTOR, "[data-testid='panel-item']")
        if len(panel_elements) > 0:
            print(f"✅ Panels page: Found {len(panel_elements)} panel elements")
            return True
        else:
            print("❌ Panels page: No panel elements found")
            return False
            
    except Exception as e:
        print(f"❌ Panels page failed: {e}")
        return False

def test_logout_flow(driver):
    """Test logout flow"""
    print("\n=== TESTING LOGOUT FLOW ===")
    
    try:
        # Find and click logout button
        logout_button = driver.find_element(By.XPATH, "//button[contains(text(), 'Cerrar sesión')]")
        logout_button.click()
        
        # Wait for redirect to login page
        WebDriverWait(driver, 10).until(
            EC.url_contains("/login")
        )
        
        print("✅ Logout successful")
        return True
        
    except Exception as e:
        print(f"❌ Logout failed: {e}")
        return False

def run_comprehensive_tests():
    """Run all comprehensive tests"""
    print("🚀 STARTING COMPREHENSIVE UI TESTS")
    
    # Test users
    test_users = [
        {"email": "toni.alos@swat-id.com", "password": "toni123!", "name": "Toni Alos"},
        {"email": "ivan.marti@swat-id.com", "password": "ivan123!", "name": "Iván Martí"}
    ]
    
    # Test API connectivity
    api_ok = test_api_connectivity()
    
    # Setup driver
    driver = setup_driver()
    if not driver:
        print("❌ Failed to setup driver")
        return
    
    try:
        # Test frontend connectivity
        frontend_ok = test_frontend_connectivity(driver)
        
        if not frontend_ok:
            print("❌ Frontend not accessible, stopping tests")
            return
        
        # Test login flows
        login_results = []
        for user in test_users:
            result = test_login_flow(driver, user["email"], user["password"], user["name"])
            login_results.append(result)
            
            if result:
                # Test navigation and pages
                test_dashboard_navigation(driver)
                test_parkings_page(driver)
                test_panels_page(driver)
                test_logout_flow(driver)
        
        # Summary
        print("\n=== TEST SUMMARY ===")
        print(f"API Connectivity: {'✅' if api_ok else '❌'}")
        print(f"Frontend Connectivity: {'✅' if frontend_ok else '❌'}")
        print(f"Login Tests: {sum(login_results)}/{len(login_results)} successful")
        
        if all(login_results):
            print("🎉 All tests passed!")
        else:
            print("⚠️  Some tests failed")
            
    finally:
        driver.quit()

if __name__ == "__main__":
    run_comprehensive_tests() 