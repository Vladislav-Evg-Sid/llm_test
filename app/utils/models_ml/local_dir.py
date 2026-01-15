from pathlib import Path


def check_folder(folder_path: str) -> bool:
    """Проверяет наличие папки и то, что она не пуста

    Args:
        path (str): Путь к папке

    Returns:
        bool: Вердикт
    """
    path = Path(folder_path)
    if not path.exists():
        return False
    
    if not path.is_dir():
        return False
    
    try:
        next(path.iterdir())
        return True
    except:
        return False