
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
TOTAL_CITIES = 17
FACTION_CITIES = 5
NEUTRAL_CITIES = TOTAL_CITIES - FACTION_CITIES
MAX_NEIGHBOURS = 3 # 3 соседей

MIN_DISTANCE_PX = 50    # Минимальное расстояние между двумя городами
MAX_DISTANCE_PX = 150   # Максимальное расстояние для возможности взаимодействия
MAP_SIZE = (700, 400)  # размер карты в пикселях



def generate_random_position():
    return (random.randint(0, MAP_SIZE[0]), random.randint(0, MAP_SIZE[1]))


def distance(p1, p2):
    return math.hypot(p1[0] - p2[0], p1[1] - p2[1])


def generate_cities():
    positions = []
    attempts = 0
    max_attempts = TOTAL_CITIES * 100

    while len(positions) < TOTAL_CITIES and attempts < max_attempts:
        attempts += 1
        pos = generate_random_position()

        # Проверка минимального расстояния
        if any(distance(pos, p) < MIN_DISTANCE_PX for p in positions):
            continue

        positions.append(pos)

    if len(positions) < TOTAL_CITIES:
        print("[WARNING] Не удалось соблюсти минимальные расстояния, добавляем принудительно...")
        while len(positions) < TOTAL_CITIES:
            pos = generate_random_position()
            if all(distance(pos, p) >= MIN_DISTANCE_PX / 2 for p in positions):  # уменьшаем требования
                positions.append(pos)

    print(f"[SUCCESS] Сгенерировано {len(positions)} городов.")

    # Делаем дополнительную проверку: все ли города могут быть соединены?
    def is_all_connected_by_max_distance(poss, threshold=MAX_DISTANCE_PX):
        edges = []
        for i in range(len(poss)):
            for j in range(i + 1, len(poss)):
                if distance(poss[i], poss[j]) <= threshold:
                    edges.append((i, j))

        # Проверяем, является ли граф связным
        parent = list(range(len(poss)))

        def find(u):
            while parent[u] != u:
                parent[u] = parent[parent[u]]
                u = parent[u]
            return u

        def union(u, v):
            pu, pv = find(u), find(v)
            if pu != pv:
                parent[pu] = pv

        for u, v in edges:
            union(u, v)

        root = find(0)
        for i in range(1, len(poss)):
            if find(i) != root:
                return False
        return True

    # Если несвязный — корректируем позиции
    fix_attempts = 0
    while not is_all_connected_by_max_distance(positions) and fix_attempts < 50:
        fix_attempts += 1
        print(f"[INFO] Граф несвязный. Коррекция позиций... ({fix_attempts}/50)")

        # Находим "оторванного" города
        def get_disconnected_components(poss, threshold=MAX_DISTANCE_PX):
            n = len(poss)
            parent = list(range(n))

            def find(u):
                while parent[u] != u:
                    parent[u] = parent[parent[u]]
                    u = parent[u]
                return u

            def union(u, v):
                pu, pv = find(u), find(v)
                if pu != pv:
                    parent[pu] = pv

            for i in range(n):
                for j in range(i + 1, n):
                    if distance(poss[i], poss[j]) <= threshold:
                        union(i, j)

            components = {}
            for i in range(n):
                root = find(i)
                if root not in components:
                    components[root] = []
                components[root].append(i)
            return list(components.values())

        components = get_disconnected_components(positions)
        if len(components) > 1:
            # Берём самый маленький компонент и двигаем его ближе к большому
            small_comp = min(components, key=len)
            big_comp = max(components, key=len)

            # Находим центр большого компонента
            cx = sum(positions[i][0] for i in big_comp) // len(big_comp)
            cy = sum(positions[i][1] for i in big_comp) // len(big_comp)

            # Перемещаем каждый город маленького компонента ближе к центру
            for city_index in small_comp:
                x, y = positions[city_index]
                dx = cx - x
                dy = cy - y
                step_x = dx // 2
                step_y = dy // 2
                new_x = max(0, min(MAP_SIZE[0], x + step_x))
                new_y = max(0, min(MAP_SIZE[1], y + step_y))
                positions[city_index] = (new_x, new_y)

    print(f"[SUCCESS] Все города теперь связаны через MAX_DISTANCE_PX.")
    return positions


def build_city_graph(cities):
    graph = {i: [] for i in range(TOTAL_CITIES)}

    # Список всех пар городов с расстоянием <= MAX_DISTANCE_PX
    edges = []
    for i in range(TOTAL_CITIES):
        for j in range(i + 1, TOTAL_CITIES):
            d = distance(cities[i]["position"], cities[j]["position"])
            if d <= MAX_DISTANCE_PX:
                edges.append((d, i, j))

    # Сортируем по расстоянию
    edges.sort()

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

    # Добавляем рёбра из MST
    mst_edges = set()
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

    # Теперь добавляем дополнительные рёбра, чтобы все города имели 2–4 соседа
    for i in range(TOTAL_CITIES):
        current_neighbors = set(graph[i])
        needed = max(0, 2 - len(current_neighbors))  # хотим минимум 2 соседа
        if needed == 0:
            continue

        # Находим ближайших неподключенных
        nearby = sorted(
            [(j, distance(cities[i]["position"], cities[j]["position"])) for j in range(TOTAL_CITIES)
             if j != i and j not in current_neighbors],
            key=lambda x: x[1]
        )

        added = 0
        for j, d in nearby:
            if d > MAX_DISTANCE_PX:
                break  # дальше не проверяем
            if (i, j) in mst_edges or (j, i) in mst_edges:
                continue  # уже есть в MST
            if j in current_neighbors:
                continue

            # Соединяем
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

def assign_factions_to_cities(positions):
    cities = []

    # Копируем и перемешиваем список имён, чтобы не повторять
    available_names = CITY_NAMES_POOL.copy()
    random.shuffle(available_names)

    # Фракции для первых 5
    for i in range(FACTION_CITIES):
        faction = FACTIONS[i % len(FACTIONS)]
        name = available_names.pop() if available_names else f"Город {i + 1}"
        city = {
            "type": "faction",
            "name": f"{name} ({faction})",
            "position": positions[i],
            "faction": faction,
            "color": FACTION_COLORS[faction],
            "fortress_name": f"{name} ({faction})"
        }
        cities.append(city)

    # Нейтралы
    for i in range(FACTION_CITIES, TOTAL_CITIES):
        name = available_names.pop() if available_names else f"Нейтрал Город {i + 1}"
        city = {
            "type": "neutral",
            "name": f"{name} (Нейтралитет)",
            "position": positions[i],
            "faction": None,
            "color": "#AAAAAA",
            "fortress_name": f"{name} (Нейтралитет)"
        }
        cities.append(city)

    return cities


def save_to_database(conn, cities, graph):
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
    while len(positions) < TOTAL_CITIES:
        print("[WARNING] Не удалось сгенерировать корректные координаты. Перегенерация...")
        positions = generate_cities()

    # Шаг 3: Назначение фракций и параметров городов
    cities = assign_factions_to_cities(positions)

    # Шаг 4: Построение графа связей между городами
    print("[INFO] Построение графа связей между городами...")
    graph = build_city_graph(cities)

    # Шаг 5: Сохранение данных в БД
    save_to_database(conn, cities, graph)

    print("[SUCCESS] Карта, города и дороги успешно сгенерированы!")
    return selected_map