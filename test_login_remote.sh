#!/bin/bash

echo "Testing login for Toni Alos..."
curl -X POST http://localhost:6001/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"toni.alos@swat-id.com","password":"alte2025!"}'

echo -e "\n\nTesting login for Iván Martí..."
curl -X POST http://localhost:6001/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"ivan.marti@swat-id.com","password":"alte2025!"}' 