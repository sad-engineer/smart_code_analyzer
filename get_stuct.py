import os

filt_fold = [
    "__pycache__",
    "Venv",
    "Venv.bak",
    "venv",
    "env",
    "env.bak",
    ".pytest_cache",
    ".cover",
    ".coverage",
    ".idea",
    ".idea",
    "dist",
    "_temp",
    '.gitignore',
    'get_stuct.py',
    'poetry.lock',
    'pyproject.toml',
    'structure.txt',
    ".git",
]


def name_write(file, current_dir, pref="", visited_dirs=set(), visited_files=set()):
    if current_dir in visited_dirs:
        return
    visited_dirs.add(current_dir)

    for root, dirs, files in os.walk(current_dir):
        # Исключаем посещенные директории для предотвращения за двоения
        dirs[:] = [d for d in dirs if os.path.join(root, d) not in visited_dirs and d not in filt_fold]

        for name in dirs:
            dir_path = os.path.join(root, name)
            if dir_path not in visited_dirs:
                file.write(f"{pref[4:]}{name}\n")
                name_write(file, dir_path, pref=f"    {pref}", visited_dirs=visited_dirs, visited_files=visited_files)

        for name in files:
            file_path = os.path.join(root, name)
            if name not in filt_fold and not name.endswith(".pyc") and file_path not in visited_files:
                file.write(f"{pref[4:]}{name}\n")
                visited_files.add(file_path)

            # Добавляем названия классов и функций
            if name.endswith(".py"):
                with open(file_path, "r", encoding="utf-8") as f:
                    for line in f:
                        if line.strip().startswith("class "):
                            class_name = line.split()[1].split('(')[0]  # Извлекаем только название класса
                            file.write(f"{pref[0:]}class: {class_name}\n")
                        elif line.strip().startswith("def "):
                            function_name = line.split()[1].split('(')[0]  # Извлекаем только название функции
                            # Проверяем, является ли функция внутренней по количеству отступов
                            if len(line) - len(line.lstrip()) > 0:  # Если отступов больше 0, то функция внутренняя
                                file.write(
                                    f"    {pref[0:]}function: {function_name}\n"
                                )  # С отступом для внутренних функций
                            else:
                                file.write(f"{pref[0:]}function: {function_name}\n")  # Без отступа


# Определяем функцию для создания текстового файла
def create_file():
    # Получаем текущую директорию
    current_dir = os.getcwd()

    # Создаём новый файл в текущей директории
    with open("structure.txt", "w", encoding="utf-8") as file:
        # Проходимся по всем файлам и папкам в текущей директории
        name_write(file, current_dir, pref="└---")


# Вызываем функцию
create_file()
