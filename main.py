#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import subprocess
import sys
from pathlib import Path
from typing import AnyStr, List, Set, Optional
import argparse
from datetime import datetime
import re

from info import VERSION


class CodebaseConverter:
    """Основной класс для конвертации кодбазы в текстовый формат."""
    
    def __init__(self, output_file: str = "codebase_export.txt", output_dir: str = None):
        """
        Инициализация конвертера.
        
        Args:
            output_file: Имя файла для сохранения результата
            output_dir: Путь до директории в которую будет сохранен файл
            regex_blacklist: Regex для фильтрации имен файлов
        """
        
        if output_dir is not None:
            self.output_file = output_dir + os.sep + output_file
        else:
            self.output_file = output_file
        
        self.processed_files = 0
        self.skipped_files = 0
        self.errors = []
        
    def get_git_files(self) -> List[str]:
        """
        Получить список файлов из Git репозитория.
        
        Returns:
            Список путей к файлам в репозитории
            
        Raises:
            subprocess.CalledProcessError: Если команда git завершилась с ошибкой
            FileNotFoundError: Если git не установлен
        """
        try:
            # Выполняем команду git ls-tree для получения списка файлов
            result = subprocess.run(
                ["git", "ls-tree", "-r", "HEAD", "--name-only"],
                capture_output=True,
                text=True,
                check=True
            )
            
            # Разделяем вывод на строки и убираем пустые строки
            files = [line.strip() for line in result.stdout.split('\n') if line.strip()]
            
            print(f"✓ Найдено {len(files)} файлов в Git репозитории")
            return files
            
        except subprocess.CalledProcessError as e:
            error_msg = f"Ошибка выполнения команды git: {e.stderr}"
            print(f"✗ {error_msg}")
            raise
            
        except FileNotFoundError:
            error_msg = "Git не установлен или не найден в PATH"
            print(f"✗ {error_msg}")
            raise

    def filter_files_by_extensions(self, files: List[str], extensions: Set[str]) -> List[str]:
        """
        Фильтрация файлов по расширениям.
        
        Args:
            files: Список путей к файлам
            extensions: Множество расширений для фильтрации (например, {'.py', '.js'})
            
        Returns:
            Отфильтрованный список файлов
        """
        if not extensions:
            return files
            
        filtered_files = []
        for file_path in files:
            file_ext = Path(file_path).suffix.lower()
            if file_ext in extensions:
                filtered_files.append(file_path)
                
        print(f"✓ После фильтрации по расширениям осталось {len(filtered_files)} файлов")
        return filtered_files
    
    def filter_files_by_regex(self, files: List[str], regex: re.Pattern) -> List[str]:
        """
        Фильтрация имен файлов по Regex.
        
        Args:
            files: Список путей к файлам
            regex: Regex паттерн
            
        Returns:
            Отфильтрованный список файлов
        """
        
        filtered_files = []
        for file_path in files:
            if not regex.match(file_path):
                filtered_files.append(file_path)
        
        print(f"✓ После фильтрации по Regex осталось {len(filtered_files)} файлов")
        return filtered_files

    def create_file_tree(self, files: List[str]) -> str:
        """
        Создать дерево файлов в читаемом формате.
        
        Args:
            files: Список путей к файлам
            
        Returns:
            Строковое представление дерева файлов
        """
        print("📁 Создание дерева файлов...")
        
        tree_lines = ["СТРУКТУРА ПРОЕКТА:", "=" * 50, ""]
        
        # Сортируем файлы для красивого отображения
        sorted_files = sorted(files)
        
        # Группируем файлы по директориям
        dirs = {}
        for file_path in sorted_files:
            path_parts = Path(file_path).parts
            
            # Обрабатываем каждый уровень вложенности
            current_dict = dirs
            for part in path_parts[:-1]:  # Все части кроме имени файла
                if part not in current_dict:
                    current_dict[part] = {}
                current_dict = current_dict[part]
            
            # Добавляем файл
            filename = path_parts[-1]
            current_dict[filename] = None
        
        # Рекурсивно строим дерево
        def build_tree(d: dict, prefix: str = "") -> List[str]:
            lines = []
            items = sorted(d.items())
            
            for i, (name, subdirs) in enumerate(items):
                is_last = i == len(items) - 1
                current_prefix = "└── " if is_last else "├── "
                lines.append(f"{prefix}{current_prefix}{name}")
                
                if subdirs is not None:  # Это директория
                    next_prefix = prefix + ("    " if is_last else "│   ")
                    lines.extend(build_tree(subdirs, next_prefix))
                    
            return lines
        
        tree_lines.extend(build_tree(dirs))
        tree_lines.extend(["", "=" * 50, "", ""])
        
        return "\n".join(tree_lines)

    def read_file_safely(self, file_path: str) -> Optional[str]:
        """
        Безопасное чтение файла с обработкой различных типов ошибок.
        
        Args:
            file_path: Путь к файлу
            
        Returns:
            Содержимое файла или None в случае ошибки
        """
        try:
            # Проверяем существование файла
            if not os.path.exists(file_path):
                self.errors.append(f"Файл не существует: {file_path}")
                return None
            
            # Пытаемся прочитать как текстовый файл с разными кодировками
            encodings = ['utf-8', 'cp1251', 'latin1', 'ascii']
            
            for encoding in encodings:
                try:
                    with open(file_path, 'r', encoding=encoding, errors='strict') as f:
                        content = f.read()
                        
                    # Проверяем, что файл не слишком большой (> 1MB)
                    if len(content) > 1024 * 1024:
                        self.errors.append(f"Файл слишком большой (>1MB): {file_path}")
                        return f"[ФАЙЛ СЛИШКОМ БОЛЬШОЙ - СОДЕРЖИМОЕ ПРОПУЩЕНО]\nРазмер: {len(content)} символов"
                    
                    return content
                    
                except UnicodeDecodeError:
                    continue
                except UnicodeError:
                    continue
            
            # Если не удалось прочитать ни с одной кодировкой - вероятно бинарный файл
            self.errors.append(f"Бинарный файл или неподдерживаемая кодировка: {file_path}")
            return "[БИНАРНЫЙ ФАЙЛ ИЛИ НЕПОДДЕРЖИВАЕМАЯ КОДИРОВКА]"
            
        except PermissionError:
            self.errors.append(f"Нет прав доступа к файлу: {file_path}")
            return "[НЕТ ПРАВ ДОСТУПА К ФАЙЛУ]"
            
        except Exception as e:
            self.errors.append(f"Неожиданная ошибка при чтении {file_path}: {str(e)}")
            return f"[ОШИБКА ЧТЕНИЯ ФАЙЛА: {str(e)}]"

    def process_files(self, files: List[str]) -> str:
        """
        Обработать список файлов и создать единый текстовый документ.
        
        Args:
            files: Список путей к файлам
            
        Returns:
            Содержимое всех файлов в едином формате
        """
        print(f"📄 Обработка {len(files)} файлов...")
        
        content_parts = []
        separator = "=" * 80
        
        for i, file_path in enumerate(files, 1):
            print(f"  Обрабатываю ({i}/{len(files)}): {file_path}")
            
            # Читаем содержимое файла
            file_content = self.read_file_safely(file_path)
            
            if file_content is None:
                self.skipped_files += 1
                
                continue
            
            # Формируем блок с информацией о файле
            file_block = [
                separator,
                f"ФАЙЛ: {file_path}",
                f"РАЗМЕР: {len(file_content)} символов",
                f"ОБРАБОТАН: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                separator,
                "",
                file_content,
                "",
                ""
            ]
            
            content_parts.extend(file_block)
            self.processed_files += 1
        
        return "\n".join(content_parts)

    def create_header(self) -> str:
        """
        Создать заголовок документа с метаинформацией.
        
        Returns:
            Заголовок документа
        """
        current_dir = os.getcwd()
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        header = f"""
Директория: {current_dir}
Дата создания: {timestamp}
Создано программой: To LLM View {VERSION}

СТАТИСТИКА:
- Обработано файлов: {self.processed_files}
- Пропущено файлов: {self.skipped_files}
- Ошибок обработки: {len(self.errors)}

{'=' * 80}

"""
        return header

    def create_footer(self) -> str:
        """
        Создать подвал документа с информацией об ошибках.
        
        Returns:
            Подвал документа
        """
        footer_parts = [
            "=" * 80,
            "ЗАВЕРШЕНИЕ ОБРАБОТКИ",
            "=" * 80,
            "",
            f"Всего обработано файлов: {self.processed_files}",
            f"Пропущено файлов: {self.skipped_files}",
            f"Общее количество ошибок: {len(self.errors)}",
            ""
        ]
        
        if self.errors:
            footer_parts.extend([
                "ДЕТАЛИ ОШИБОК:",
                "-" * 40,
                ""
            ])
            
            for error in self.errors:
                footer_parts.append(f"• {error}")
            
            footer_parts.append("")
        
        footer_parts.extend([
            f"Экспорт завершен: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "=" * 80
        ])
        
        return "\n".join(footer_parts)

    def convert(self, extensions: Optional[Set[str]] = None, regex: Optional[re.Pattern] = None) -> None:
        """
        Выполнить полную конвертацию кодбазы.
        
        Args:
            extensions: Множество расширений для фильтрации (например, {'.py', '.js'})
            regex: Regex паттерн для фильтрации
        """
        try:
            print("🚀 Запуск конвертера кодбазы...")
            
            # Получаем список файлов из Git
            files = self.get_git_files()
            
            # Фильтруем
            if extensions:
                files = self.filter_files_by_extensions(files, extensions)
            
            if regex:
                files = self.filter_files_by_regex(files, regex)
            
            if not files:
                print("⚠️  Нет файлов для обработки после фильтрации")
                return
            
            # Создаем дерево файлов
            file_tree = self.create_file_tree(files)
            
            # Обрабатываем файлы
            files_content = self.process_files(files)
            
            # Собираем финальный документ
            print(f"💾 Сохранение результата в файл: {self.output_file}")
            
            with open(self.output_file, 'w', encoding='utf-8') as f:
                # Записываем заголовок (после обработки, чтобы была статистика)
                f.write(self.create_header())
                
                # Записываем дерево файлов
                f.write(file_tree)
                
                # Записываем содержимое файлов
                f.write(files_content)
                
                # Записываем подвал
                f.write(self.create_footer())
            
            print(f"✅ Конвертация завершена успешно!")
            print(f"   📄 Обработано файлов: {self.processed_files}")
            print(f"   ⚠️  Пропущено файлов: {self.skipped_files}")
            print(f"   📁 Результат сохранен в: {self.output_file}")
            
            if self.errors:
                print(f"   ⚠️  Обнаружено ошибок: {len(self.errors)} (детали в файле)")
            
        except Exception as e:
            print(f"💥 Критическая ошибка: {str(e)}")
            sys.exit(1)


def parse_extensions(ext_string: str) -> Set[str]:
    """
    Парсинг строки с расширениями файлов.
    
    Args:
        ext_string: Строка с расширениями через запятую (например, "py,js,html")
        
    Returns:
        Множество расширений с точками
    """
    if not ext_string:
        return set()
    
    extensions = set()
    for ext in ext_string.split(','):
        ext = ext.strip()
        if ext and not ext.startswith('.'):
            ext = '.' + ext
        if ext:
            extensions.add(ext.lower())
    
    return extensions


def main():
    """Главная функция программы."""
    parser = argparse.ArgumentParser(
        description="Конвертер кодбазы в единый текстовый документ для работы с нейросетями",
        epilog="Пример: python codebase_converter.py -o my_codebase.txt -w py,js,html"
    )
    
    parser.add_argument(
        '-o', '--output',
        default='codebase_export.txt',
        help='Имя выходного файла (по умолчанию: codebase_export.txt)'
    )
    
    parser.add_argument(
        '-r', '--root',
        action='store_true',
        help='Создание выходного файла на одном уровне с текущей папкой, а не в ней'
    )
    
    parser.add_argument(
        '-w', '--whitelist',
        help='Расширения файлов для включения (через запятую, например: py,js,html)'
    )
    
    parser.add_argument(
        '-rb', '--regex-blacklist',
        default=r'.*',
        help='Regex для фильтрации имен файлов'
    )
    
    args = parser.parse_args()
    
    # Парсим расширения
    extensions = parse_extensions(args.whitelist) if args.whitelist else None
    
    if extensions:
        print(f"🔍 Фильтрация по расширениям: {', '.join(sorted(extensions))}")
    
    # Проверяем, что мы находимся в Git репозитории
    if not os.path.exists('.git'):
        print("❌ Ошибка: текущая директория не является Git репозиторием")
        print("   Перейдите в корень Git репозитория и запустите программу снова")
        return 1
    
    output_name = args.output
    root_path = None
    if args.root:
        p = os.getcwd()
        root_path = p[:p.rfind(os.sep)]
        
        output_name = p[p.rfind(os.sep)+len(os.sep):]+"."+output_name
    
    # Создаем и запускаем конвертер
    converter = CodebaseConverter(output_name, root_path)
    converter.convert(extensions, re.compile(args.regex_blacklist, re.IGNORECASE))
    
    return 0


if __name__ == "__main__":
    main()