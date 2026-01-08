# ai_models/translation.py
# Словарь для перевода названий
translation_dict = {
    "Север": "people",
    "Эльфы": "elfs",
    "Адепты": "adept",
    "Вампиры": "vampire",
    "Элины": "poly",
}

reverse_translation_dict = {v: k for k, v in translation_dict.items()}


def transform_filename(file_path):
    """Трансформирует имена файлов с русского на английский"""
    path_parts = file_path.split('/')
    for i, part in enumerate(path_parts):
        for ru_name, en_name in translation_dict.items():
            if ru_name in part:
                path_parts[i] = part.replace(ru_name, en_name)
    transformed_path = '/'.join(path_parts)
    return transformed_path