#!/bin/bash
set -e
: "${DB_PASS:?Define DB_PASS antes de ejecutar (export DB_PASS=...)}"
sudo service mysql start
sudo mysql -e "CREATE DATABASE IF NOT EXISTS sigab;"
sudo mysql -e "CREATE USER IF NOT EXISTS 'sigab_user'@'localhost' IDENTIFIED BY '$DB_PASS';"
sudo mysql -e "GRANT ALL PRIVILEGES ON sigab.* TO 'sigab_user'@'localhost';"
sudo mysql -e "FLUSH PRIVILEGES;"
mysql -u sigab_user -p"$DB_PASS" sigab < sigab_schema_fresh.sql
mysql -u sigab_user -p"$DB_PASS" sigab < seed_data.sql
echo "Base de datos inicializada y poblada exitosamente."
