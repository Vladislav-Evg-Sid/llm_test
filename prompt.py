import json
import os

def main():
    # Задаем пути
    input_file = r"C:\Users\VladS\git\dop\data\Председатели предметных комиссий\11_класс\02-Математика\11-2025-mat_prof.jsonc"  # Путь к входному файлу
    output_folder = r"C:\Users\VladS\git\llm_test\app\services\llm_service\texts\section_names"   # Путь к выходной папке
    
    # Создаем выходную папку, если её нет
    os.makedirs(output_folder, exist_ok=True)
    
    # Читаем JSON файл
    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Ищем поле "sections"
    sections = data.get("sections", [])
    
    # Обрабатываем каждый элемент в sections
    for section in sections:
        code = section.get("code")
        text = section.get("name")
        
        # Проверяем, что code и text существуют
        if code is not None and text is not None:
            # Формируем имя файла
            filename = f"{code}.txt"
            filepath = os.path.join(output_folder, filename)
            
            # Записываем text в файл
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(text)
            
            print(f"Создан файл: {filepath}")
        else:
            print(f"Пропущен элемент: отсутствует code или text")

if __name__ == "__main__":
    main()