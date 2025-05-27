#!/usr/bin/env python3
"""
Скрипт для обновления импортов после переименования директории
handlers_aiogram в handlers
"""

import os
import re

def update_file_content(file_path):
    """Обновляет импорты в файле"""
    with open(file_path, 'r', encoding='utf-8') as file:
        content = file.read()
    
    # Заменяем импорты
    updated_content = content.replace('modules.handlers_aiogram', 'modules.handlers')
    
    if content != updated_content:
        print(f"Обновляю файл: {file_path}")
        with open(file_path, 'w', encoding='utf-8') as file:
            file.write(updated_content)
        return True
    return False

def process_directory(directory):
    """Рекурсивно обрабатывает директорию"""
    updated_count = 0
    
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith('.py'):
                file_path = os.path.join(root, file)
                if update_file_content(file_path):
                    updated_count += 1
    
    return updated_count

def main():
    """Основная функция"""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    
    print("Обновление импортов после переименования директории...")
    count = process_directory(base_dir)
    print(f"Обновлено {count} файлов")

if __name__ == "__main__":
    main()
