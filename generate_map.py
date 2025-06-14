
from lerdon_libraries import *

# Список доступных карт
MAP_IMAGES_DIR = "files/map/generate"
AVAILABLE_MAPS = [f for f in os.listdir(MAP_IMAGES_DIR) if f.startswith("map_") and f.endswith(".png")]

# Фракции
FACTIONS = ["Люди", "Эльфы", "Вампиры", "Адепты", "Полукровки"]

# Цвета для фракций
FACTION_COLORS = {
    'Вампиры': 'files/buildings/giperion.png',
    'Люди': 'files/buildings/arkadia.png',
    'Эльфы': 'files/buildings/celestia.png',
    'Адепты': 'files/buildings/eteria.png',
    'Полукровки': 'files/buildings/halidon.png'
}

# Константы
TOTAL_CITIES = 14
FACTION_CITIES = 5
NEUTRAL_CITIES = TOTAL_CITIES - FACTION_CITIES
MIN_DISTANCE = 6
MAX_NEIGHBOURS = 5
MAX_DISTANCE = 8
MAP_SIZE = (700, 390)  # размер карты в пикселях


def generate_random_position():
    return (random.randint(0, MAP_SIZE[0]), random.randint(0, MAP_SIZE[1]))


def distance(p1, p2):
    return math.hypot(p1[0] - p2[0], p1[1] - p2[1])

def generate_cities():
    """Генерируем TOTAL_CITIES точек, соблюдая мин. расстояние и наличие хотя бы одного соседа."""
    positions = []
    attempts = 0
    max_attempts = TOTAL_CITIES * 200  # Увеличили число попыток

    while len(positions) < TOTAL_CITIES and attempts < max_attempts:
        attempts += 1
        pos = generate_random_position()

        # Проверяем минимальное расстояние до всех уже существующих
        if any(distance(pos, p) < MIN_DISTANCE for p in positions):
            continue

        # Проверяем, есть ли хотя бы один сосед в пределах MAX_DISTANCE
        has_neighbor = False
        for p in positions:
            d = distance(pos, p)
            if d <= MAX_DISTANCE:
                has_neighbor = True
                break

        # Если нет позиций или есть подходящий сосед — добавляем
        if not positions or has_neighbor:
            positions.append(pos)

    # Если не уложились в попытки — делаем понижение требований
    while len(positions) < TOTAL_CITIES:
        print(f"[WARNING] Не удалось сгенерировать все города. Пытаемся понизить MIN_DISTANCE...")
        new_min_distance = max(MIN_DISTANCE - 1, 2)  # не меньше 2
        # Перегенерация с новым MIN_DISTANCE
        pos = generate_random_position()
        if all(distance(pos, p) >= new_min_distance for p in positions):
            positions.append(pos)

    print(f"[SUCCESS] Сгенерировано {len(positions)} городов.")
    return positions

def assign_factions_to_cities(positions):
    cities = []

    # Назначаем фракции первым 5 городам
    for i in range(FACTION_CITIES):
        faction = FACTIONS[i % len(FACTIONS)]
        city = {
            "type": "faction",
            "name": f"{faction} Город {i + 1}",
            "position": positions[i],
            "faction": faction,
            "color": FACTION_COLORS[faction],
            "fortress_name": f"Крепость {faction} {i + 1}"
        }
        cities.append(city)

    # Остальные — нейтральные
    for i in range(FACTION_CITIES, TOTAL_CITIES):
        city = {
            "type": "neutral",
            "name": f"Нейтральный Город {i + 1}",
            "position": positions[i],
            "faction": None,
            "color": "#AAAAAA",
            "fortress_name": f"Крепость Нейтралитета {i + 1}"
        }
        cities.append(city)

    return cities


def save_to_database(conn, cities):
    cursor = conn.cursor()

    # Очистка таблиц перед записью
    cursor.execute("DELETE FROM city")
    cursor.execute("DELETE FROM cities")

    for i, city in enumerate(cities):
        # city
        kingdom = city["faction"] if city["faction"] else "Нейтралитет"
        coords = str(list(city["position"]))
        cursor.execute(
            "INSERT INTO city (id, kingdom, color, fortress_name, coordinates) VALUES (?, ?, ?, ?, ?)",
            (i + 1, kingdom, city["color"], city["fortress_name"], coords)
        )

        # cities
        icon_coords = str([city["position"][0], city["position"][1]])
        label_coords = str([city["position"][0], city["position"][1] - 30])
        cursor.execute(
            "INSERT INTO cities (id, name, coordinates, faction, icon_coordinates, label_coordinates) VALUES (?, ?, ?, ?, ?, ?)",
            (i + 1, city["name"], coords, city["faction"], icon_coords, label_coords)
        )

    conn.commit()
    print(f"[INFO] Сохранено {len(cities)} городов в базу данных.")


def select_random_map_image():
    selected_map = random.choice(AVAILABLE_MAPS)
    print('AVAILABLE_MAPS', AVAILABLE_MAPS)
    map_path = os.path.join(MAP_IMAGES_DIR, selected_map)
    print(f"[INFO] Выбрана карта: {selected_map}")
    return map_path


def generate_map_and_cities(conn):
    print("[INFO] Начинается генерация карты...")

    # Шаг 1: Выбор случайной карты
    selected_map = select_random_map_image()

    # Шаг 2: Генерация координат городов
    print("[INFO] Генерация координат городов...")
    positions = generate_cities()
    while positions is None:
        print("[WARNING] Не удалось сгенерировать корректные координаты. Перегенерация...")
        positions = generate_cities()

    # Шаг 3: Назначение фракций и параметров городов
    cities = assign_factions_to_cities(positions)

    # Шаг 4: Запись в БД
    save_to_database(conn, cities)

    print("[SUCCESS] Карта и города успешно сгенерированы!")
    return selected_map