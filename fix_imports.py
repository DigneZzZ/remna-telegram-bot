#!/usr/bin/env python3
"""
Скрипт для исправления импортов в файлах handlers 
(замена modules.handlers_aiogram на modules.handlers)
"""

import os
import re

def fix_imports_in_file(file_path):
    """
    Исправляет импорты в файле, заменяя modules.handlers_aiogram на modules.handlers
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Заменяем импорты
    modified_content = content.replace('modules.handlers_aiogram', 'modules.handlers')
    
    if content != modified_content:
        print(f"Исправляю импорты в файле: {file_path}")
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(modified_content)
        return True
    return False

def process_directory(directory_path):
    """
    Рекурсивно обрабатывает все файлы в директории
    """
    fixed_files = 0
    
    for root, dirs, files in os.walk(directory_path):
        for file in files:
            if file.endswith('.py'):
                file_path = os.path.join(root, file)
                if fix_imports_in_file(file_path):
                    fixed_files += 1
    
    return fixed_files

if __name__ == "__main__":
    handlers_dir = os.path.join('modules', 'handlers')
    fixed_count = process_directory(handlers_dir)
    
    main_file = 'main.py'
    if os.path.exists(main_file):
        if fix_imports_in_file(main_file):
            fixed_count += 1

    test_files = [
        'test_aiogram_migration.py',
        'test_aiogram_basic.py',
        'quick_test.py',
        'migration_test.py'
    ]
    
    for test_file in test_files:
        if os.path.exists(test_file):
            if fix_imports_in_file(test_file):
                fixed_count += 1
    
    print(f"\nГотово! Всего исправлено {fixed_count} файлов")
