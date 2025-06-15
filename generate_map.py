
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
BUFFER = 30
TOTAL_CITIES = 17
FACTION_CITIES = 5
NEUTRAL_CITIES = TOTAL_CITIES - FACTION_CITIES
ALL_CITIES = FACTION_CITIES + TOTAL_CITIES
MAX_NEIGHBOURS = 3  # Максимум 3 соседа
MIN_DISTANCE_PX = 60   # Минимальное расстояние между двумя городами
MAX_DISTANCE_PX = 160  # Максимальное расстояние для возможности взаимодействия

MAP_SIZE = (700, 500)  # размер карты в пикселях


def generate_city_coords(prev_point=None):
    """
    Генерирует координаты следующего города.
    При prev_point=None — полностью случайные в пределах карты с буфером.
    Иначе — случайная точка на расстоянии [MIN_DISTANCE_PX, MAX_DISTANCE_PX]
    от prev_point, но при необходимости повторяем до тех пор,
    пока не попадём внутрь безопасной зоны.
    """
    width, height = MAP_SIZE

    if prev_point is None:
        # Первая точка — чисто случайная внутри буферной зоны
        return (
            random.randint(BUFFER, width  - BUFFER),
            random.randint(BUFFER, height - BUFFER)
        )

    x_prev, y_prev = prev_point
    for _ in range(200):
        # выбираем случайное направление full circle
        angle = random.uniform(0, 2 * math.pi)
        dist  = random.uniform(MIN_DISTANCE_PX, MAX_DISTANCE_PX)

        x = int(x_prev + dist * math.cos(angle))
        y = int(y_prev + dist * math.sin(angle))

        # проверяем буфер
        if BUFFER <= x <= width - BUFFER and BUFFER <= y <= height - BUFFER:
            return x, y

    # если не получилось в разумное число попыток — возвращаем случайную точку
    return (
        random.randint(BUFFER, width  - BUFFER),
        random.randint(BUFFER, height - BUFFER)
    )

def generate_all_cities():
    """
    Генерирует TOTAL_CITIES точек в порядке:
    фракционный, нейтральный, нейтральный, нейтральный, фракционный, ...
    """
    # 1) Формируем шаблон типов
    city_types = []
    f, n = 0, 0
    while len(city_types) < TOTAL_CITIES:
        # один фракционный, если ещё есть
        if f < FACTION_CITIES:
            city_types.append("faction")
            f += 1
        # три нейтральных или пока есть
        for _ in range(3):
            if len(city_types) >= TOTAL_CITIES:
                break
            if n < NEUTRAL_CITIES:
                city_types.append("neutral")
                n += 1
    # 2) Генерим точки подряд, следуя шаблону
    positions = []
    used = set()
    for city_type in city_types:
        prev = positions[-1] if positions else None
        for _ in range(200):
            pt = generate_city_coords(prev)
            # проверяем минимальное расстояние
            if pt in used:
                continue
            if any(math.hypot(pt[0]-q[0], pt[1]-q[1]) < MIN_DISTANCE_PX for q in positions):
                continue
            positions.append(pt)
            used.add(pt)
            break
        else:
            # при неудаче — произвольная точка в буфере
            fallback = (
                random.randint(BUFFER, MAP_SIZE[0] - BUFFER),
                random.randint(BUFFER, MAP_SIZE[1] - BUFFER)
            )
            positions.append(fallback)
            used.add(fallback)

    # 3) Собираем итоговый список городов
    cities = []
    for idx, (ctype, pos) in enumerate(zip(city_types, positions)):
        cities.append({"type": ctype, "position": pos})

    print(f"[SUCCESS] Сгенерировано {len(cities)} городов: "
          f"{city_types.count('faction')} фракционных и {city_types.count('neutral')} нейтральных.")
    return cities



def build_city_graph(cities):
    """Строит граф связей между городами"""
    graph = {i: [] for i in range(TOTAL_CITIES)}
    positions = [city["position"] for city in cities]

    # Список всех пар городов с расстоянием <= MAX_DISTANCE_PX
    edges = []
    for i in range(TOTAL_CITIES):
        for j in range(i + 1, TOTAL_CITIES):
            d = math.hypot(positions[i][0] - positions[j][0], positions[i][1] - positions[j][1])
            if d <= MAX_DISTANCE_PX:
                edges.append((d, i, j))

    # Алгоритм Краскала для MST (минимального связного дерева)
    parent = list(range(TOTAL_CITIES))
    def find(u):
        while parent[u] != u:
            parent[u] = parent[parent[u]]
            u = parent[u]
        return u
    def union(u, v):
        pu, pv = find(u), find(v)
        if pu != pv:
            parent[pu] = pv

    mst_edges = set()
    edges.sort()
    for d, u, v in edges:
        if find(u) != find(v):
            union(u, v)
            graph[u].append(v)
            graph[v].append(u)
            mst_edges.add((u, v))
            mst_edges.add((v, u))

    # Убираем связи между фракционными городами
    faction_indices = [i for i in range(FACTION_CITIES)]
    for i in faction_indices:
        for j in faction_indices:
            if j in graph[i]:
                graph[i].remove(j)
                graph[j].remove(i)

    # Добавляем дополнительные рёбра, чтобы все города имели 2–4 соседа
    for i in range(TOTAL_CITIES):
        current_neighbors = set(graph[i])
        needed = max(0, 2 - len(current_neighbors))  # хотим минимум 2 соседа
        if needed == 0:
            continue
        nearby = sorted(
            [(j, math.hypot(positions[i][0] - positions[j][0], positions[i][1] - positions[j][1])) for j in range(TOTAL_CITIES)
             if j != i and j not in current_neighbors],
            key=lambda x: x[1]
        )
        added = 0
        for j, d in nearby:
            if d > MAX_DISTANCE_PX:
                break
            if (i, j) in mst_edges or (j, i) in mst_edges:
                continue
            if j in current_neighbors:
                continue
            graph[i].append(j)
            graph[j].append(i)
            current_neighbors.add(j)
            added += 1
            if added >= needed:
                break

    # Ограничиваем максимальное число соседей
    for i in range(TOTAL_CITIES):
        if len(graph[i]) > 4:
            graph[i] = random.sample(graph[i], 4)

    return graph


# Пул имён для городов
CITY_NAMES_POOL = [
    "Аргенвилль", "Партон", "Миргород", "Владонск", "Эледрин",
    "Селария", "Миреллия", "Каландор", "Валориан", "Гилион",
    "Штормград", "Тарпин", "Бастария", "Дарриан", "Арданис",
    "Ауренбург", "Феррадан", "Бальтарис", "Терра", "Каларин", "Хантир", "Лоредо"
]


def assign_factions_to_cities(cities_with_types):
    """
    Назначает фракции первым 5 фракционным городам,
    остальным — нейтралитет
    """
    faction_indices = [i for i, c in enumerate(cities_with_types) if c["type"] == "faction"]
    random.shuffle(faction_indices)  # перемешиваем позиции фракций

    cities = []
    available_names = CITY_NAMES_POOL.copy()
    random.shuffle(available_names)

    faction_assignments = FACTIONS[:FACTION_CITIES]
    random.shuffle(faction_assignments)

    faction_count = 0
    for idx, city_info in enumerate(cities_with_types):
        if city_info["type"] == "faction":
            faction = faction_assignments[faction_count % len(FACTIONS)]
            faction_count += 1
            name = available_names.pop() if available_names else f"Город {idx + 1}"
            city = {
                "type": "faction",
                "name": f"{name} ({faction})",
                "position": city_info["position"],
                "faction": faction,
                "color": FACTION_COLORS[faction],
                "fortress_name": f"{name} ({faction})"
            }
        else:
            name = available_names.pop() if available_names else f"Нейтрал Город {idx + 1}"
            city = {
                "type": "neutral",
                "name": f"{name} (Нейтралитет)",
                "position": city_info["position"],
                "faction": None,
                "color": "#AAAAAA",
                "fortress_name": f"{name} (Нейтралитет)"
            }
        cities.append(city)

    print("[INFO] Фракции успешно назначены.")
    return cities

def save_to_database(conn, cities, graph):
    """Сохраняет данные о городах и дорогах в базу данных"""
    cursor = conn.cursor()
    cursor.execute("DELETE FROM city")
    cursor.execute("DELETE FROM cities")
    cursor.execute("DELETE FROM roads")

    # Сохраняем города
    for i, city in enumerate(cities):
        kingdom = city["faction"] if city["faction"] else "Нейтралитет"
        coords = str(list(city["position"]))
        cursor.execute(
            "INSERT INTO city (id, kingdom, color, fortress_name, coordinates) VALUES (?, ?, ?, ?, ?)",
            (i + 1, kingdom, city["color"], city["fortress_name"], coords)
        )
        icon_coords = str([city["position"][0], city["position"][1]])
        label_coords = str([city["position"][0], city["position"][1] - 30])
        cursor.execute(
            "INSERT INTO cities (id, name, coordinates, faction, icon_coordinates, label_coordinates) VALUES (?, ?, ?, ?, ?, ?)",
            (i + 1, city["name"], coords, city["faction"], icon_coords, label_coords)
        )

    # Сохраняем дороги
    road_id = 1
    added_roads = set()
    for city_idx, neighbors in graph.items():
        for neighbor_idx in neighbors:
            if (city_idx, neighbor_idx) in added_roads or (neighbor_idx, city_idx) in added_roads:
                continue
            added_roads.add((city_idx, neighbor_idx))
            added_roads.add((neighbor_idx, city_idx))
            cursor.execute(
                "INSERT INTO roads (id, city1, city2) VALUES (?, ?, ?)",
                (road_id, city_idx + 1, neighbor_idx + 1)
            )
            road_id += 1
    conn.commit()
    print(f"[INFO] Сохранено {len(cities)} городов и {road_id - 1} дорог.")


def select_random_map_image():
    """Выбирает случайную карту из доступных"""
    selected_map = random.choice(AVAILABLE_MAPS)
    map_path = os.path.join(MAP_IMAGES_DIR, selected_map)
    print(f"[INFO] Выбрана карта: {selected_map}")
    return map_path


def generate_map_and_cities(conn):
    print("[INFO] Начинается генерация карты...")

    selected_map = select_random_map_image()

    print("[INFO] Генерация координат городов...")
    cities_with_types = generate_all_cities()  # теперь содержит типы

    print("[INFO] Назначение фракций и параметров городов...")
    cities = assign_factions_to_cities(cities_with_types)

    print("[INFO] Построение графа связей между городами...")
    graph = build_city_graph(cities)

    save_to_database(conn, cities, graph)

    print("[SUCCESS] Карта, города и дороги успешно сгенерированы!")
    return selected_map