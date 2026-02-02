#!/usr/bin/env python3
"""
Generate bcrypt password hash for admin user
"""
import sys
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

if len(sys.argv) < 2:
    password = "admin123"  # Default
else:
    password = sys.argv[1]

hashed = pwd_context.hash(password)
print(f"Password: {password}")
print(f"Hash: {hashed}")
