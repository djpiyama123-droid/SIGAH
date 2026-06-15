#!/bin/bash
set -e
: "${DB_PASS:?Define DB_PASS antes de ejecutar (export DB_PASS=...)}"
sudo mysql -e "ALTER USER 'sigab_user'@'localhost' IDENTIFIED WITH mysql_native_password BY '$DB_PASS'; FLUSH PRIVILEGES;"
