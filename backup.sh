#!/bin/bash

# Konfiguracja
BACKUP_DIR="./backups"
TIMESTAMP=$(date +"%Y-%m-%d_%H-%M-%S")
DB_CONTAINER="testy-db"
DB_NAME="testy_db"
DB_USER="root"
DB_PASS="twoje_haslo_z_configa" # Zmień na właściwe!

# Tworzenie folderu na backupy
mkdir -p $BACKUP_DIR

echo "--- Start backupu: $TIMESTAMP ---"

# 1. Zrzut bazy danych (SQL dump)
docker exec $DB_CONTAINER mariadb-dump -u $DB_USER -p$DB_PASS $DB_NAME > "$BACKUP_DIR/db_dump_$TIMESTAMP.sql"

# 2. Pakowanie wszystkiego (SQL + Grafiki)
tar -czvf "$BACKUP_DIR/full_backup_$TIMESTAMP.tar.gz" "$BACKUP_DIR/db_dump_$TIMESTAMP.sql" ./uploads

# 3. Usuwanie tymczasowego pliku SQL
rm "$BACKUP_DIR/db_dump_$TIMESTAMP.sql"

# 4. Opcjonalnie: Usuwanie backupów starszych niż 7 dni
find $BACKUP_DIR -type f -name "*.tar.gz" -mtime +7 -exec rm {} \;

echo "--- Backup zakończony: $BACKUP_DIR/full_backup_$TIMESTAMP.tar.gz ---"