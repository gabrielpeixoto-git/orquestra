#!/usr/bin/env python
"""Script para criar usuário admin"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.local')
django.setup()

from django.contrib.auth import get_user_model

User = get_user_model()

if User.objects.filter(username='admin').exists():
    print("Usuário admin já existe")
else:
    user = User.objects.create_superuser(
        username='admin',
        email='admin@orquestra.com',
        password='Admin123!'
    )
    print(f"Usuário admin criado: {user.username}")
