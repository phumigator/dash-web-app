#!/bin/bash

# Скрипт для автоматической настройки приложения на сервере

echo "Setting up Dash application..."

# Создание директории если не существует
sudo mkdir -p /var/www/dashapp

# Копирование файлов
sudo cp -r . /var/www/dashapp/

# Установка прав
sudo chown -R www-data:www-data /var/www/dashapp

# Создание виртуального окружения
cd /var/www/dashapp
sudo -u www-data python3 -m venv venv

# Установка зависимостей
sudo -u www-data /var/www/dashapp/venv/bin/pip install -r requirements.txt

# Настройка systemd сервиса
sudo cat > /etc/systemd/system/dashapp.service << 'EOF'
[Unit]
Description=Gunicorn instance to serve Dash app
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/var/www/dashapp
Environment="PATH=/var/www/dashapp/venv/bin"
ExecStart=/var/www/dashapp/venv/bin/gunicorn --workers 3 --bind 127.0.0.1:8050 app:server

[Install]
WantedBy=multi-user.target
EOF

# Перезагрузка systemd и запуск сервиса
sudo systemctl daemon-reload
sudo systemctl enable dashapp
sudo systemctl start dashapp

echo "Setup complete! Service is running."
echo "Check status with: sudo systemctl status dashapp"