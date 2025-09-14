#!/usr/bin/env python3
"""
Скрипт для создания резервных копий базы данных
"""

import sys
import os
import shutil
import sqlite3
from pathlib import Path
from datetime import datetime

# Добавляем путь к модулям
sys.path.append(os.path.dirname(__file__))

from modules.database import VGTRKDatabase


def create_backup(source_db: str, backup_dir: str = None):
    """
    Создание резервной копии базы данных
    
    Args:
        source_db: Путь к исходной базе данных
        backup_dir: Директория для сохранения резервных копий (по умолчанию data/backups)
    """
    source_path = Path(source_db)
    
    if not source_path.exists():
        print(f"❌ Исходная база данных не найдена: {source_db}")
        return False
    
    # Определяем директорию для резервных копий
    if backup_dir is None:
        backup_dir = source_path.parent / "backups"
    
    backup_path = Path(backup_dir)
    backup_path.mkdir(parents=True, exist_ok=True)
    
    # Создаем имя файла резервной копии с временной меткой
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_filename = f"vgtrk_monitoring_backup_{timestamp}.db"
    backup_file = backup_path / backup_filename
    
    try:
        print(f"📦 Создание резервной копии...")
        print(f"   Исходный файл: {source_path}")
        print(f"   Резервная копия: {backup_file}")
        
        # Копируем файл базы данных
        shutil.copy2(source_path, backup_file)
        
        # Проверяем целостность резервной копии
        print("   🔍 Проверка целостности...")
        conn = sqlite3.connect(str(backup_file))
        cursor = conn.execute("PRAGMA integrity_check")
        result = cursor.fetchone()
        conn.close()
        
        if result[0] == "ok":
            print("   ✅ Резервная копия создана успешно!")
            print(f"   💾 Размер: {backup_file.stat().st_size / (1024*1024):.2f} МБ")
            return True
        else:
            print(f"   ❌ Ошибка целостности: {result[0]}")
            # Удаляем поврежденную копию
            backup_file.unlink()
            return False
            
    except Exception as e:
        print(f"❌ Ошибка при создании резервной копии: {e}")
        # Удаляем частично созданный файл
        if backup_file.exists():
            backup_file.unlink()
        return False


def list_backups(backup_dir: str = None):
    """
    Показать список доступных резервных копий
    
    Args:
        backup_dir: Директория с резервными копиями
    """
    if backup_dir is None:
        backup_dir = Path("data/backups")
    else:
        backup_dir = Path(backup_dir)
    
    if not backup_dir.exists():
        print(f"📁 Директория {backup_dir} не существует")
        return
    
    # Получаем список файлов резервных копий
    backup_files = list(backup_dir.glob("vgtrk_monitoring_backup_*.db"))
    
    if not backup_files:
        print("📭 Нет доступных резервных копий")
        return
    
    print(f"📋 Доступные резервные копии ({len(backup_files)}):")
    print("-" * 80)
    
    # Сортируем по дате создания (новые первые)
    backup_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
    
    for i, backup_file in enumerate(backup_files, 1):
        stat = backup_file.stat()
        size_mb = stat.st_size / (1024 * 1024)
        mod_time = datetime.fromtimestamp(stat.st_mtime)
        
        print(f"{i:2d}. {backup_file.name}")
        print(f"     📅 {mod_time.strftime('%Y-%m-%d %H:%M:%S')}  💾 {size_mb:.2f} МБ")
        print()


def restore_backup(backup_file: str, target_db: str):
    """
    Восстановление базы данных из резервной копии
    
    Args:
        backup_file: Путь к файлу резервной копии
        target_db: Путь к целевой базе данных
    """
    backup_path = Path(backup_file)
    target_path = Path(target_db)
    
    if not backup_path.exists():
        print(f"❌ Резервная копия не найдена: {backup_file}")
        return False
    
    try:
        print(f"🔄 Восстановление базы данных...")
        print(f"   Резервная копия: {backup_path}")
        print(f"   Целевая база: {target_path}")
        
        # Создаем резервную копию текущей базы перед восстановлением
        if target_path.exists():
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_pre_restore")
            pre_restore_backup = target_path.parent / f"backups/vgtrk_monitoring_backup_{timestamp}.db"
            pre_restore_backup.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(target_path, pre_restore_backup)
            print(f"   📦 Создана резервная копия текущей базы: {pre_restore_backup.name}")
        
        # Копируем резервную копию в целевую базу
        shutil.copy2(backup_path, target_path)
        
        # Проверяем целостность восстановленной базы
        print("   🔍 Проверка целостности...")
        conn = sqlite3.connect(str(target_path))
        cursor = conn.execute("PRAGMA integrity_check")
        result = cursor.fetchone()
        conn.close()
        
        if result[0] == "ok":
            print("   ✅ Восстановление завершено успешно!")
            print(f"   💾 Размер: {target_path.stat().st_size / (1024*1024):.2f} МБ")
            return True
        else:
            print(f"   ❌ Ошибка целостности: {result[0]}")
            return False
            
    except Exception as e:
        print(f"❌ Ошибка при восстановлении: {e}")
        return False


def cleanup_old_backups(backup_dir: str = None, keep_days: int = 30):
    """
    Удаление старых резервных копий
    
    Args:
        backup_dir: Директория с резервными копиями
        keep_days: Сколько дней хранить резервные копии
    """
    if backup_dir is None:
        backup_dir = Path("data/backups")
    else:
        backup_dir = Path(backup_dir)
    
    if not backup_dir.exists():
        print(f"📁 Директория {backup_dir} не существует")
        return
    
    # Получаем список файлов резервных копий
    backup_files = list(backup_dir.glob("vgtrk_monitoring_backup_*.db"))
    
    if not backup_files:
        print("📭 Нет доступных резервных копий для очистки")
        return
    
    # Сортируем по дате создания (новые первые)
    backup_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
    
    # Определяем пороговое время
    threshold = datetime.now().timestamp() - (keep_days * 24 * 60 * 60)
    
    deleted_count = 0
    for backup_file in backup_files:
        if backup_file.stat().st_mtime < threshold:
            try:
                backup_file.unlink()
                print(f"🗑️  Удалена старая резервная копия: {backup_file.name}")
                deleted_count += 1
            except Exception as e:
                print(f"❌ Ошибка при удалении {backup_file.name}: {e}")
    
    if deleted_count > 0:
        print(f"✅ Удалено {deleted_count} старых резервных копий")
    else:
        print("✅ Нет старых резервных копий для удаления")


def main():
    """Основная функция"""
    print("=" * 60)
    print("📦 СИСТЕМА РЕЗЕРВНОГО КОПИРОВАНИЯ БАЗЫ ДАННЫХ ВГТРК")
    print("=" * 60)
    
    if len(sys.argv) < 2:
        print("Использование:")
        print("  python backup_database.py create [source_db] [backup_dir]")
        print("  python backup_database.py list [backup_dir]")
        print("  python backup_database.py restore [backup_file] [target_db]")
        print("  python backup_database.py cleanup [backup_dir] [keep_days]")
        return
    
    command = sys.argv[1]
    
    if command == "create":
        source_db = sys.argv[2] if len(sys.argv) > 2 else "data/vgtrk_monitoring.db"
        backup_dir = sys.argv[3] if len(sys.argv) > 3 else None
        create_backup(source_db, backup_dir)
        
    elif command == "list":
        backup_dir = sys.argv[2] if len(sys.argv) > 2 else None
        list_backups(backup_dir)
        
    elif command == "restore":
        if len(sys.argv) < 4:
            print("❌ Недостаточно аргументов для восстановления")
            print("Использование: python backup_database.py restore [backup_file] [target_db]")
            return
        
        backup_file = sys.argv[2]
        target_db = sys.argv[3]
        restore_backup(backup_file, target_db)
        
    elif command == "cleanup":
        backup_dir = sys.argv[2] if len(sys.argv) > 2 else None
        keep_days = int(sys.argv[3]) if len(sys.argv) > 3 else 30
        cleanup_old_backups(backup_dir, keep_days)
        
    else:
        print(f"❌ Неизвестная команда: {command}")
        print("Доступные команды: create, list, restore, cleanup")


if __name__ == "__main__":
    main()