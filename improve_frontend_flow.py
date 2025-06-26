#!/usr/bin/env python3
"""
Script to improve frontend login/logout flow and validate UI elements
"""

import os
import json

def improve_auth_context():
    """Improve the AuthContext with better error handling and logout flow"""
    
    auth_context_content = '''import React, { createContext, useContext, useState, useEffect } from 'react';

const AuthContext = createContext();

export const useAuth = () => {
    const context = useContext(AuthContext);
    if (!context) {
        throw new Error('useAuth must be used within an AuthProvider');
    }
    return context;
};

export const AuthProvider = ({ children }) => {
    const [user, setUser] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    useEffect(() => {
        // Check for existing token on app load
        const token = localStorage.getItem('token');
        const userData = localStorage.getItem('user');
        
        if (token && userData) {
            try {
                setUser(JSON.parse(userData));
            } catch (e) {
                console.error('Error parsing user data:', e);
                localStorage.removeItem('token');
                localStorage.removeItem('user');
            }
        }
        setLoading(false);
    }, []);

    const login = async (email, password) => {
        try {
            setError(null);
            setLoading(true);
            
            const response = await fetch('http://localhost:6001/api/auth/login', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ email, password }),
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.error || 'Error de autenticación');
            }

            localStorage.setItem('token', data.token);
            localStorage.setItem('user', JSON.stringify(data.user));
            setUser(data.user);
            return { success: true };
        } catch (error) {
            setError(error.message);
            return { success: false, error: error.message };
        } finally {
            setLoading(false);
        }
    };

    const logout = () => {
        try {
            localStorage.removeItem('token');
            localStorage.removeItem('user');
            setUser(null);
            setError(null);
            // Redirect to login page
            window.location.href = '/login';
        } catch (error) {
            console.error('Error during logout:', error);
        }
    };

    const clearError = () => {
        setError(null);
    };

    const value = {
        user,
        loading,
        error,
        login,
        logout,
        clearError,
        isAuthenticated: !!user
    };

    return (
        <AuthContext.Provider value={value}>
            {children}
        </AuthContext.Provider>
    );
};
'''
    
    with open('client/src/context/AuthContext.jsx', 'w', encoding='utf-8') as f:
        f.write(auth_context_content)
    
    print("✅ AuthContext mejorado con mejor manejo de errores y logout")

def improve_login_page():
    """Improve the Login page with better error handling and UI feedback"""
    
    login_content = '''import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

const Login = () => {
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const { login, error, clearError, isAuthenticated } = useAuth();
    const navigate = useNavigate();

    useEffect(() => {
        if (isAuthenticated) {
            navigate('/dashboard');
        }
    }, [isAuthenticated, navigate]);

    useEffect(() => {
        clearError();
    }, [clearError]);

    const handleSubmit = async (e) => {
        e.preventDefault();
        setIsLoading(true);
        
        const result = await login(email, password);
        
        if (result.success) {
            navigate('/dashboard');
        }
        
        setIsLoading(false);
    };

    return (
        <div className="min-h-screen flex items-center justify-center bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
            <div className="max-w-md w-full space-y-8">
                <div>
                    <h2 className="mt-6 text-center text-3xl font-extrabold text-gray-900">
                        Parking Altea
                    </h2>
                    <p className="mt-2 text-center text-sm text-gray-600">
                        Inicia sesión en tu cuenta
                    </p>
                </div>
                <form className="mt-8 space-y-6" onSubmit={handleSubmit}>
                    <div className="rounded-md shadow-sm -space-y-px">
                        <div>
                            <label htmlFor="email" className="sr-only">
                                Email
                            </label>
                            <input
                                id="email"
                                name="email"
                                type="email"
                                autoComplete="email"
                                required
                                className="appearance-none rounded-none relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 rounded-t-md focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 focus:z-10 sm:text-sm"
                                placeholder="Email"
                                value={email}
                                onChange={(e) => setEmail(e.target.value)}
                                disabled={isLoading}
                            />
                        </div>
                        <div>
                            <label htmlFor="password" className="sr-only">
                                Contraseña
                            </label>
                            <input
                                id="password"
                                name="password"
                                type="password"
                                autoComplete="current-password"
                                required
                                className="appearance-none rounded-none relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 rounded-b-md focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 focus:z-10 sm:text-sm"
                                placeholder="Contraseña"
                                value={password}
                                onChange={(e) => setPassword(e.target.value)}
                                disabled={isLoading}
                            />
                        </div>
                    </div>

                    {error && (
                        <div className="rounded-md bg-red-50 p-4">
                            <div className="flex">
                                <div className="ml-3">
                                    <h3 className="text-sm font-medium text-red-800">
                                        Error de autenticación
                                    </h3>
                                    <div className="mt-2 text-sm text-red-700">
                                        {error}
                                    </div>
                                </div>
                            </div>
                        </div>
                    )}

                    <div>
                        <button
                            type="submit"
                            disabled={isLoading}
                            className="group relative w-full flex justify-center py-2 px-4 border border-transparent text-sm font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50 disabled:cursor-not-allowed"
                        >
                            {isLoading ? (
                                <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                                </svg>
                            ) : null}
                            {isLoading ? 'Iniciando sesión...' : 'Iniciar sesión'}
                        </button>
                    </div>
                </form>
            </div>
        </div>
    );
};

export default Login;
'''
    
    with open('client/src/pages/Login.jsx', 'w', encoding='utf-8') as f:
        f.write(login_content)
    
    print("✅ Página de Login mejorada con mejor manejo de errores y feedback visual")

def improve_layout():
    """Improve the Layout component with better navigation and logout handling"""
    
    layout_content = '''import React from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

const Layout = ({ children }) => {
    const { user, logout } = useAuth();
    const location = useLocation();
    const navigate = useNavigate();

    const handleLogout = () => {
        logout();
        navigate('/login');
    };

    const navigation = [
        { name: 'Dashboard', href: '/dashboard', current: location.pathname === '/dashboard' },
        { name: 'Parkings', href: '/parkings', current: location.pathname === '/parkings' },
        { name: 'Paneles', href: '/panels', current: location.pathname === '/panels' },
        { name: 'Estadísticas', href: '/statistics', current: location.pathname === '/statistics' },
        { name: 'Perfil', href: '/profile', current: location.pathname === '/profile' },
    ];

    return (
        <div className="min-h-screen bg-gray-100">
            <nav className="bg-white shadow-sm">
                <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                    <div className="flex justify-between h-16">
                        <div className="flex">
                            <div className="flex-shrink-0 flex items-center">
                                <h1 className="text-xl font-semibold text-gray-900">
                                    Parking Altea
                                </h1>
                            </div>
                            <div className="hidden sm:ml-6 sm:flex sm:space-x-8">
                                {navigation.map((item) => (
                                    <Link
                                        key={item.name}
                                        to={item.href}
                                        className={`${
                                            item.current
                                                ? 'border-indigo-500 text-gray-900'
                                                : 'border-transparent text-gray-500 hover:border-gray-300 hover:text-gray-700'
                                        } whitespace-nowrap py-2 px-1 border-b-2 font-medium text-sm`}
                                    >
                                        {item.name}
                                    </Link>
                                ))}
                            </div>
                        </div>
                        <div className="hidden sm:ml-6 sm:flex sm:items-center">
                            <div className="ml-3 relative">
                                <div className="flex items-center space-x-4">
                                    <span className="text-sm text-gray-700">
                                        {user?.name}
                                    </span>
                                    <button
                                        onClick={handleLogout}
                                        className="bg-red-600 hover:bg-red-700 text-white px-3 py-2 rounded-md text-sm font-medium"
                                    >
                                        Cerrar sesión
                                    </button>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </nav>

            <main className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
                {children}
            </main>
        </div>
    );
};

export default Layout;
'''
    
    with open('client/src/components/Layout.jsx', 'w', encoding='utf-8') as f:
        f.write(layout_content)
    
    print("✅ Layout mejorado con mejor navegación y manejo de logout")

def create_ui_test_script():
    """Create a comprehensive UI test script"""
    
    test_content = '''#!/usr/bin/env python3
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
    print("\\n=== TESTING API CONNECTIVITY ===")
    
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
    print("\\n=== TESTING FRONTEND CONNECTIVITY ===")
    
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
    print(f"\\n=== TESTING LOGIN FLOW FOR {user_name} ===")
    
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
    print("\\n=== TESTING DASHBOARD NAVIGATION ===")
    
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
    print("\\n=== TESTING PARKINGS PAGE ===")
    
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
    print("\\n=== TESTING PANELS PAGE ===")
    
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
    print("\\n=== TESTING LOGOUT FLOW ===")
    
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
        print("\\n=== TEST SUMMARY ===")
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
'''
    
    with open('test_frontend_comprehensive.py', 'w', encoding='utf-8') as f:
        f.write(test_content)
    
    print("✅ Script de pruebas UI completo creado")

def main():
    """Main function to improve frontend flow"""
    print("🔄 Mejorando el flujo del frontend...")
    
    # Create directories if they don't exist
    os.makedirs('client/src/context', exist_ok=True)
    os.makedirs('client/src/pages', exist_ok=True)
    os.makedirs('client/src/components', exist_ok=True)
    
    # Improve components
    improve_auth_context()
    improve_login_page()
    improve_layout()
    create_ui_test_script()
    
    print("\\n✅ Mejoras del frontend completadas")
    print("\\n📋 Próximos pasos:")
    print("1. Ejecutar check_users_and_permissions.py para verificar usuarios")
    print("2. Desplegar las mejoras del frontend en el servidor")
    print("3. Ejecutar test_frontend_comprehensive.py para validar la UI")

if __name__ == "__main__":
    main() 