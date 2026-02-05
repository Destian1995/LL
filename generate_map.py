
from lerdon_libraries import *

# Список доступных карт
MAP_IMAGES_DIR = "files/map/generate"
AVAILABLE_MAPS = [f for f in os.listdir(MAP_IMAGES_DIR) if f.startswith("map_") and f.endswith(".png")]

# Фракции
FACTIONS = ["Север", "Эльфы", "Вампиры", "Адепты", "Элины"]
# Пул имён для городов
CITY_NAMES_POOL = [
    "Аргенвилль", "Партон", "Миргород", "Владонск", "Эледрин",
    "Селария", "Миреллия", "Каландор", "Валориан", "Гилион",
    "Холмград", "Тарпин", "Бастария", "Дарриан", "Арданис",
    "Ауренбург", "Феррадан", "Альтария", "Терра", "Каларин",
    "Хантир", "Лоредо", "Гарбор", "Новакар", "Сантигон",
    "Ривелло", "Остмара", "Замфир", "Индария", "Талисса",
    "Гельмут", "Виндгар", "Фениксия", "Этернис", "Лирандор",
    "Кальдира", "Солмера", "Ундрия", "Мардрак", "Ориона"
]

# Цвета для фракций
FACTION_COLORS = {
    'Вампиры': 'files/buildings/giperion.png',
    'Север': 'files/buildings/arkadia.png',
    'Эльфы': 'files/buildings/celestia.png',
    'Адепты': 'files/buildings/eteria.png',
    'Элины': 'files/buildings/halidon.png'
}

# Константы
TOTAL_CITIES = 23
FACTION_CITIES = 5
NEUTRAL_CITIES = TOTAL_CITIES - FACTION_CITIES
ALL_CITIES = FACTION_CITIES + TOTAL_CITIES
# Константы
MAX_NEIGHBOURS = 3  # Максимум 3 соседа
MIN_DISTANCE_PX = 120   # <-- Увеличиваем до расстояния между
MAX_DISTANCE_PX = 230   # Можно немного увеличить для большей гибкости
MAP_SIZE = (1200, 800)
MARGIN = 100            # Лучше тоже чуть увеличить, чтобы города не прилипали к краям
MANHATTAN_THRESHOLD = 250  # Синхронизируем с новым масштабом

def generate_city_coords(prev_point=None):
    """Генерирует координаты следующего города относительно предыдущего"""
    if prev_point is None:
        # Первая точка — случайная, но с отступом от края
        x = random.randint(MARGIN, MAP_SIZE[0] - MARGIN)
        y = random.randint(MARGIN, MAP_SIZE[1] - MARGIN)
        return x, y
    else:
        x_prev, y_prev = prev_point
        attempts = 0
        while attempts < 100:
            distance = random.randint(MIN_DISTANCE_PX, MAX_DISTANCE_PX)
            angle = random.uniform(0, 2 * math.pi)
            dx = distance * math.cos(angle)
            dy = distance * math.sin(angle)
            x = x_prev + dx
            y = y_prev + dy
            if MARGIN <= x <= MAP_SIZE[0] - MARGIN and MARGIN <= y <= MAP_SIZE[1] - MARGIN:
                return int(x), int(y)
            attempts += 1
        # Если не получилось — возвращаем случайную точку с отступом
        return (
            random.randint(MARGIN, MAP_SIZE[0] - MARGIN),
            random.randint(MARGIN, MAP_SIZE[1] - MARGIN)
        )

def select_faction_cities(positions):
    """Выбирает 5 городов, все пары которых находятся на расстоянии >= 300 px друг от друга."""
    n = len(positions)
    min_required_distance = 200  # Минимальное расстояние между фракционными городами
    attempts = 0
    max_attempts = 100  # Максимум попыток подбора

    while attempts < max_attempts:
        # Случайно выбираем 5 индексов
        candidate_indices = random.sample(range(n), 5)
        valid = True

        # Проверяем каждую пару
        for i in range(5):
            for j in range(i + 1, 5):
                idx1 = candidate_indices[i]
                idx2 = candidate_indices[j]
                x1, y1 = positions[idx1]
                x2, y2 = positions[idx2]
                dist = math.hypot(x2 - x1, y2 - y1)
                if dist < min_required_distance:
                    valid = False
                    break
            if not valid:
                break

        if valid:
            print(f"[INFO] Найдены 5 фракционных городов, все на расстоянии ≥ {min_required_distance} px.")
            return candidate_indices

        attempts += 1

    # Если за max_attempts не нашлось подходящих — выбрасываем исключение
    raise RuntimeError(
        f"Не удалось найти 5 городов, удовлетворяющих условию минимального расстояния {min_required_distance}px"
    )

def generate_all_cities():
    """Генерирует города с гарантией связности и возможности выбрать 5 фракционных с расстоянием > 300px"""
    while True:
        cities = []
        used_positions = set()
        first_point = generate_city_coords()
        cities.append(first_point)
        used_positions.add(first_point)
        attempts = 0
        while len(cities) < TOTAL_CITIES and attempts < 1000:
            base_point = random.choice(cities)
            new_point = generate_city_coords(base_point)
            if new_point in used_positions:
                attempts += 1
                continue
            too_close = any(
                math.hypot(new_point[0] - p[0], new_point[1] - p[1]) < MIN_DISTANCE_PX
                for p in cities
            )
            if too_close:
                attempts += 1
                continue
            # Проверяем, есть ли хотя бы одна связь по Манхэттену
            if any(manhattan(new_point, p) <= MANHATTAN_THRESHOLD for p in cities):
                cities.append(new_point)
                used_positions.add(new_point)
                attempts = 0  # сбрасываем попытки
            else:
                attempts += 1
        if len(cities) == TOTAL_CITIES:
            print(f"[SUCCESS] Сгенерировано {TOTAL_CITIES} уникальных городов.")
            # Проверяем, можно ли выбрать 5 фракционных с нужным расстоянием
            try:
                select_faction_cities(cities)
                return cities
            except RuntimeError as e:
                print(f"[WARN] Не удалось подобрать фракционные города: {e}. Перегенерация карты...")
        else:
            print("[WARN] Не удалось сгенерировать все города, пробуем заново...")


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
    faction_indices = [i for i, city in enumerate(cities) if city["type"] == "faction"]
    for i in faction_indices:
        for j in faction_indices:
            if i != j and j in graph[i]:
                graph[i].remove(j)
                graph[j].remove(i)

    # Добавляем дополнительные рёбра, чтобы все города имели 2–4 соседа
    for i in range(TOTAL_CITIES):
        current_neighbors = set(graph[i])
        needed = max(0, 2 - len(current_neighbors))  # хотим минимум 2 соседа
        if needed == 0:
            continue
        nearby = sorted(
            [(j, math.hypot(positions[i][0] - positions[j][0], positions[i][1] - positions[j][1]))
             for j in range(TOTAL_CITIES) if j != i and j not in current_neighbors],
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
            # Если это фракционный город — нельзя добавлять других фракционных
            if cities[i]["type"] == "faction" and cities[j]["type"] == "faction":
                continue
            graph[i].append(j)
            graph[j].append(i)
            current_neighbors.add(j)
            added += 1
            if added >= needed:
                break

    # Проверяем, что у каждого фракционного города есть минимум 2 нейтральных соседа
    for idx in faction_indices:
        faction_neighbors = [n for n in graph[idx] if cities[n]["type"] == "neutral"]
        if len(faction_neighbors) < 2:
            missing = 2 - len(faction_neighbors)
            candidates = []
            for i in range(TOTAL_CITIES):
                if i == idx or cities[i]["type"] != "neutral" or i in graph[idx]:
                    continue
                d = math.hypot(positions[idx][0] - positions[i][0], positions[idx][1] - positions[i][1])
                if d <= MAX_DISTANCE_PX:
                    candidates.append((d, i))
            candidates.sort()
            for _, i in candidates[:missing]:
                graph[idx].append(i)
                graph[i].append(idx)
                faction_neighbors.append(i)

    # Ограничиваем максимальное число соседей
    for i in range(TOTAL_CITIES):
        if len(graph[i]) > 4:
            graph[i] = random.sample(graph[i], 4)

    return graph

def assign_factions_to_cities(positions):
    """Назначает фракции 5 наиболее удалённым городам, остальным — нейтралитет"""
    cities = []
    available_names = CITY_NAMES_POOL.copy()
    random.shuffle(available_names)

    # Шаг 1: Выбираем 5 наиболее удалённых городов
    faction_indices = select_faction_cities(positions)

    # Шаг 2: Назначаем им фракции
    assigned = 0
    used_names = set()
    faction_assignments = {}

    # Создаём список фракций в случайном порядке
    shuffled_factions = random.sample(FACTIONS, len(FACTIONS))

    for idx in faction_indices:
        faction = shuffled_factions[assigned % len(FACTIONS)]
        name = None
        while available_names:
            name = available_names.pop()
            if name not in used_names:
                used_names.add(name)
                break
        if not name:
            name = f"Город {idx + 1}"

        city = {
            "type": "faction",
            "name": f"{name}",
            "position": positions[idx],
            "faction": faction,
            "color_faction": FACTION_COLORS[faction]
        }
        cities.append(city)
        faction_assignments[idx] = city
        assigned += 1

    # Шаг 3: Добавляем оставшиеся города как нейтралы
    neutral_cities = []
    for idx in range(len(positions)):
        if idx in faction_assignments:
            continue
        name = None
        while available_names:
            name = available_names.pop()
            if name not in used_names:
                used_names.add(name)
                break
        if not name:
            name = f"Нейтрал Город {idx + 1}"

        city = {
            "type": "neutral",
            "name": f"{name}",
            "position": positions[idx],
            "faction": None,
            "color_faction": "#AAAAAA"
        }
        cities.append(city)

    # Возвращаем список в том же порядке, что и positions
    result = [None] * len(positions)
    for idx in faction_assignments:
        result[idx] = faction_assignments[idx]
    for city in cities:
        if city["position"] in positions and result[positions.index(city["position"])] is None:
            result[positions.index(city["position"])] = city

    return result

def save_to_database(conn, cities, graph):
    """Сохраняет данные о городах и дорогах в базу данных"""
    cursor = conn.cursor()
    cursor.execute("DELETE FROM cities")
    cursor.execute("DELETE FROM roads")

    # Сохраняем города
    for i, city in enumerate(cities):
        faction = city["faction"] if city["faction"] else "Нейтрал"
        coords = str(list(city["position"]))
        icon_coords = str([city["position"][0], city["position"][1]])
        label_coords = str([city["position"][0], city["position"][1] - 30])
        cursor.execute(
            "INSERT INTO cities (id, name, coordinates, faction, icon_coordinates, label_coordinates, color_faction) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (i + 1, city["name"], coords, faction, icon_coords, label_coords, city["color_faction"])
        )

    # Сохраняем дороги
    road_id = 1
    added_roads = set()
    for city_namex, neighbors in graph.items():
        for neighbor_idx in neighbors:
            if (city_namex, neighbor_idx) in added_roads or (neighbor_idx, city_namex) in added_roads:
                continue
            added_roads.add((city_namex, neighbor_idx))
            added_roads.add((neighbor_idx, city_namex))
            cursor.execute(
                "INSERT INTO roads (id, city1, city2) VALUES (?, ?, ?)",
                (road_id, city_namex + 1, neighbor_idx + 1)
            )
            road_id += 1

    # --- НОВАЯ ЛОГИКА: Генерация значений kf_crystal по заданному распределению ---
    total_cities_count = len(cities)
    # Проверяем, что общее количество городов соответствует
    assert total_cities_count == 23, f"Ожидается 23 города, получено {total_cities_count}"

    kf_crystal_values = []

    # 1. Генерируем 10 значений для диапазона [1.0, 1.7)
    for _ in range(13):
        kf_crystal_values.append(round(random.uniform(1.0, 1.1), 2))

    # 2. Генерируем 7 значений для диапазона [1.7, 2.9)
    for _ in range(6):
        kf_crystal_values.append(round(random.uniform(1.1, 1.9), 2))

    # 3. Генерируем 6 значений для диапазона [2.9, 4.8]
    for _ in range(4):
        kf_crystal_values.append(round(random.uniform(1.9, 2.75), 2))

    # Перемешиваем список, чтобы распределение было случайным по городам
    random.shuffle(kf_crystal_values)

    # --- КОНЕЦ НОВОЙ ЛОГИКИ ---

    # Обновляем таблицу cities, устанавливая kf_crystal для каждого id
    for i, kf_val in enumerate(kf_crystal_values):
        city_id = i + 1  # Предполагаем, что id города начинаются с 1
        cursor.execute(
            "UPDATE cities SET kf_crystal = ? WHERE id = ?",
            (kf_val, city_id)
        )

    conn.commit()
    print(f"[INFO] Сохранено {len(cities)} городов и {road_id - 1} дорог.")
    # Опционально: сообщить о заполнении kf_crystal
    print(f"[INFO] Столбец kf_crystal заполнен по заданному распределению: 10 значений [1.0, 1.7), 7 значений [1.7, 2.9), 6 значений [2.9, 4.8].")



def manhattan(a, b):
    """Манхэттенское расстояние между точками a и b."""
    return abs(a[0] - b[0]) + abs(a[1] - b[1])

def is_connected(positions):
    """
    Проверяет, что граф, где ребро между i и j есть если
    manhattan(positions[i], positions[j]) <= MANHATTAN_THRESHOLD,
    связен (от любой вершины достижимы все).
    """
    n = len(positions)
    visited = [False] * n
    queue = deque([0])
    visited[0] = True

    while queue:
        u = queue.popleft()
        for v in range(n):
            if not visited[v] and manhattan(positions[u], positions[v]) <= MANHATTAN_THRESHOLD:
                visited[v] = True
                queue.append(v)

    return all(visited)


def generate_map_and_cities(conn):
    """Основная функция: генерация связного набора городов → остальное."""

    # Шаг 1: Генерация координат городов с гарантией связности по манхэттену
    print("[INFO] Генерация координат городов с гарантией связности...")
    positions = generate_all_cities()

    # Шаг 2: Назначаем фракции и остальные параметры
    cities = assign_factions_to_cities(positions)

    # Шаг 3: Строим граф дорог (можно оставить старый Kruskal‑подход или переделать под манхэттен)
    print("[INFO] Построение графа связей между городами...")
    graph = build_city_graph(cities)

    # Шаг 4: Сохраняем всё в БД
    save_to_database(conn, cities, graph)

    print("[SUCCESS] Координаты для городов успешно сгенерированы!")
    print("[SUCCESS] GENERATE MAP COMPLETE!")
