#!/usr/bin/env python3
"""
Script to replace all occurrences of 'docker-compose' with 'docker compose' in all project files
"""
import os
import re
from pathlib import Path

def should_process_file(file_path):
    """Check if file should be processed"""
    # Skip binary files, images, etc.
    skip_extensions = {'.pyc', '.git', '.jpg', '.png', '.gif', '.pdf', '.zip', '.tar', '.gz'}
    skip_dirs = {'.git', '__pycache__', 'node_modules', '.vscode'}
    
    # Check extension
    if file_path.suffix.lower() in skip_extensions:
        return False
    
    # Check if any parent directory is in skip_dirs
    for part in file_path.parts:
        if part in skip_dirs:
            return False
    
    return True

def replace_docker_compose_in_file(file_path):
    """Replace docker-compose with docker compose in a single file"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Count occurrences before replacement
        count_before = content.count('docker-compose')
        if count_before == 0:
            return 0
        
        # Replace docker-compose with docker compose
        # Use word boundaries to avoid replacing in filenames
        new_content = re.sub(r'\bdocker-compose\b', 'docker compose', content)
        
        # Count changes
        count_after = new_content.count('docker-compose')
        changes = count_before - count_after
        
        if changes > 0:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(new_content)
            print(f"✅ {file_path}: {changes} замен")
        
        return changes
    
    except Exception as e:
        print(f"❌ Ошибка в {file_path}: {e}")
        return 0

def main():
    """Main function"""
    print("🔄 Замена 'docker-compose' на 'docker compose' во всех файлах проекта...")
    print("=" * 60)
    
    project_root = Path('.')
    total_changes = 0
    processed_files = 0
    
    # Process all files recursively
    for file_path in project_root.rglob('*'):
        if file_path.is_file() and should_process_file(file_path):
            try:
                changes = replace_docker_compose_in_file(file_path)
                if changes > 0:
                    total_changes += changes
                    processed_files += 1
            except Exception as e:
                print(f"❌ Не удалось обработать {file_path}: {e}")
    
    print("=" * 60)
    print(f"🎉 Завершено!")
    print(f"📁 Обработано файлов: {processed_files}")
    print(f"🔄 Всего замен: {total_changes}")
    
    if total_changes > 0:
        print("\n📝 Рекомендуется проверить изменения:")
        print("   git diff")

if __name__ == "__main__":
    main()
