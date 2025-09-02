# nobles_generator.py
import random
import sqlite3
import json # Для хранения сложных данных о продажных дворянах

# Список рас (5 штук)
RACES = ['Люди', 'Эльфы', 'Адепты', 'Вампиры', 'Элины']

# Список идеологий (всего 2)
IDEOLOGIES = ['Борьба', 'Смирение']

# Список имен для каждой расы
NAMES = {
    'Люди': ['Николай', 'Леонид', 'Карами', 'Генрих', 'Уильям', 'Мирослав'],
    'Эльфы': ['Закани', 'Миордания', 'Риндайли', 'Широни', 'Глория', 'Амрелия'],
    'Адепты': ['Серафим', 'Михаил', 'Гавриил', 'Рафаил', 'Уриил', 'Иоанн'],
    'Вампиры': ['Люци', 'Стефан', 'Вильгельм', 'Виктор', 'Бальтазар', 'Габриэль'],
    'Элины': ['Ария', 'Шакира', 'Селена', 'Элион', 'Мирана', 'Фаари']
}

# --- Вспомогательные функции ---

def get_player_faction(conn):
    """Получение фракции игрока из БД"""
    cursor = conn.cursor()
    cursor.execute("SELECT faction_name FROM user_faction")
    result = cursor.fetchone()
    return result[0] if result else None

def get_faction_ideology(conn, faction_name):
    """Получение идеологии фракции из БД"""
    cursor = conn.cursor()
    cursor.execute("SELECT system FROM political_systems WHERE faction = ?", (faction_name,))
    result = cursor.fetchone()
    return result[0] if result else 'Борьба' # По умолчанию 'Борьба'

def get_player_ideology(conn):
    """Получает текущую идеологию фракции игрока."""
    faction = get_player_faction(conn)
    if faction:
        return get_faction_ideology(conn, faction)
    return 'Борьба'

def get_diplomacy_relation(conn, faction1, faction2):
    """Получение статуса отношений между двумя фракциями."""
    cursor = conn.cursor()
    cursor.execute("""
        SELECT relationship FROM diplomacies 
        WHERE (faction1 = ? AND faction2 = ?) OR (faction1 = ? AND faction2 = ?)
    """, (faction1, faction2, faction2, faction1))
    result = cursor.fetchone()
    return result[0] if result else 'нейтралитет' # По умолчанию нейтралитет

def get_noble_traits(ideology_str):
    """
    Парсит строку ideology и возвращает словарь с типом и значением черты.
    Примеры:
    - "Борьба" -> {'type': 'ideology', 'value': 'Борьба'}
    - "Любит Эльфы" -> {'type': 'race_love', 'value': 'Эльфы'}
    - '{"type": "greed", "demand": 5000000}' -> {'type': 'greed', 'demand': 5000000}
    """
    if ideology_str.startswith('{'):
        try:
            return json.loads(ideology_str)
        except json.JSONDecodeError:
            return {'type': 'ideology', 'value': 'Борьба'} # fallback
    elif ideology_str.startswith("Любит "):
        race = ideology_str.split(" ", 1)[1]
        return {'type': 'race_love', 'value': race}
    else: # Простая идеология
        return {'type': 'ideology', 'value': ideology_str}

def record_coup_attempt(conn, is_successful):
    """
    Записывает результат попытки переворота в таблицу coup_attempts.
    Записывает только успешные перевороты.

    Args:
        conn: Соединение с БД
        is_successful (bool): True если переворот успешен, False если провален
    """
    if is_successful:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO coup_attempts (status) VALUES (?)", ('successful',))
        conn.commit()
        print("✅ Успешный переворот записан в базу данных")


# --- Основные функции управления дворянами ---

def generate_initial_nobles(conn):
    """Генерация начальных советников при старте игры"""
    cursor = conn.cursor()

    # Проверяем, есть ли уже советники
    cursor.execute("SELECT COUNT(*) FROM nobles")
    count = cursor.fetchone()[0]

    if count > 0:
        return  # Советники уже существуют

    # Получаем фракцию игрока
    faction_race = get_player_faction(conn)
    if not faction_race:
        return

    # Генерируем 3 случайных советника из фракции игрока
    available_names = NAMES[faction_race].copy()
    random.shuffle(available_names)

    for i in range(3):
        # Гарантируем, что имя уникально для этого набора
        if i < len(available_names):
            name = available_names[i]
        else:
            # На случай, если имен меньше 3, берем случайное из всех
            name = random.choice(NAMES[faction_race])

        loyalty = 60.0  # Начальная лояльность
        priority = i
        status = 'active'

        # Выбираем случайную черту характера
        trait_type = random.choice(['ideology', 'race_love', 'greed'])
        if trait_type == 'ideology':
            ideology = random.choice(IDEOLOGIES)
        elif trait_type == 'race_love':
            loved_race = random.choice([r for r in RACES if r != faction_race])
            ideology = f"Любит {loved_race}"
        else: # greed
            # Генерируем требование: 1,000,000 + 35%-75% от 10,000,000
            base_demand = 1_000_000
            percentage = random.uniform(0.35, 0.75)
            additional_demand = int(10_000_000 * percentage)
            total_demand = base_demand + additional_demand
            ideology = json.dumps({'type': 'greed', 'demand': total_demand})

        # История посещений мероприятий (пустая строка для начала)
        attendance_history = ""

        cursor.execute("""
            INSERT INTO nobles (priority, loyalty, status, name, ideology, attendance_history) 
            VALUES (?, ?, ?, ?, ?, ?)
        """, (priority, loyalty, status, name, ideology, attendance_history))

    conn.commit()
    print("Начальные советники (дворяне) инициализированы.")


def update_nobles_periodically(conn, current_turn):
    """
    Периодическое обновление состояния дворян.
    Вызывается из process_turn.
    """
    # 1. Снижение лояльности (каждые ход)
    if current_turn % 1 == 0:
        decrease_loyalty_over_time(conn)

    # 2. Проверка попыток переворота
    check_coup_attempts(conn) # Проверяем каждый ход

    # 3. Смена приоритетов (каждые 13 ходов)
    if current_turn % 13 == 0 and current_turn > 0:
        change_noble_priorities(conn)


def decrease_loyalty_over_time(conn):
    """Снижение лояльности всех дворян на 3% за ход, с учетом идеологии."""
    cursor = conn.cursor()
    cursor.execute("SELECT id, loyalty, ideology FROM nobles WHERE status = 'active'")
    nobles = cursor.fetchall()

    player_ideology = get_player_ideology(conn)

    for noble_id, current_loyalty, ideology_str in nobles:
        noble_traits = get_noble_traits(ideology_str)

        # Базовое снижение
        decrease = 3.0

        # Если идеология совпадает — снижение меньше
        if noble_traits['type'] == 'ideology' and noble_traits['value'] == player_ideology:
            decrease = 1.5  # Меньше, если совпадает идеология

        new_loyalty = max(0.0, current_loyalty - decrease)
        cursor.execute("UPDATE nobles SET loyalty = ? WHERE id = ?", (new_loyalty, noble_id))

    conn.commit()


def calculate_attendance_probability(conn, noble_id, player_faction, event_type, event_season):
    """
    Рассчитывает вероятность посещения мероприятия дворянином.
    Учитывает актуальную идеологию фракции игрока.
    """
    cursor = conn.cursor()
    cursor.execute("SELECT name, ideology, attendance_history FROM nobles WHERE id = ?", (noble_id,))
    result = cursor.fetchone()

    if not result:
        return 1.0 # Если не найден, считаем 100%

    name, ideology_str, attendance_history = result
    noble_traits = get_noble_traits(ideology_str)

    # --- НОВАЯ ЛОГИКА: Проверка оплаты продажного дворянина ---
    # Предположим, что оплата действует N ходов (например, 4 хода = 2 мероприятия)
    # Мы будем искать специальный маркер 'P' в истории.
    # Для простоты, если 'P' есть в последних N записях, считаем оплаченым.
    TURNS_PAID_EFFECT_LASTS = 4 # Эффект оплаты длится 4 хода
    RECENT_HISTORY_LENGTH = TURNS_PAID_EFFECT_LASTS # Проверяем последние N записей

    if noble_traits['type'] == 'greed' and attendance_history:
        history_list = attendance_history.split(',')
        # Проверяем последние RECENT_HISTORY_LENGTH записей
        recent_history = history_list[-RECENT_HISTORY_LENGTH:]
        if 'P' in recent_history:
            # print(f"DEBUG: Noble {noble_id} оплачен, вероятность посещения 100%")
            return 1.0 # 100% посещение для оплаченного продажного

    # --- КОНЕЦ НОВОЙ ЛОГИКИ ---

    probability = 1.0 # Базовая вероятность

    # Проверка на продажность (если не оплачен)
    if noble_traits['type'] == 'greed':
        # print(f"DEBUG: Noble {noble_id} продажный, но не оплачен, вероятность 40%")
        return 0.4 # 40% если продажный и не оплачен

    # Проверка идеологии
    if noble_traits['type'] == 'ideology':
        player_ideology = get_player_ideology(conn)  # АКТУАЛЬНАЯ идеология
        if noble_traits['value'] != player_ideology:
            probability *= 0.4 # 40% если не совпадает

    # Проверка любви к расе (если мероприятие связано с сезоном)
    if noble_traits['type'] == 'race_love':
        loved_race = noble_traits['value']
        # Предположим, что сезон связан с расой (упрощение)
        season_to_race_map = {
            'Зима': 'Люди', 'Весна': 'Эльфы', 'Лето': 'Элины', 'Осень': 'Вампиры'
        }
        event_race = season_to_race_map.get(event_season)
        if event_race and loved_race != event_race:
            # Проверяем дипломатические отношения
            relation = get_diplomacy_relation(conn, player_faction, loved_race)
            if relation in ['вражда', 'холодно']:
                probability *= 0.4 # 40% если отношения плохие

    final_prob = max(0.0, min(1.0, probability))
    # print(f"DEBUG: Noble {noble_id} финальная вероятность {final_prob}")
    return final_prob


def update_noble_loyalty_for_event(conn, noble_id, player_faction, event_type, event_season):
    """
    Обновление лояльности конкретного советника после мероприятия.
    """
    cursor = conn.cursor()
    cursor.execute("SELECT loyalty, attendance_history, ideology FROM nobles WHERE id = ?", (noble_id,))
    result = cursor.fetchone()

    if not result:
        return

    loyalty, history_str, ideology_str = result

    # Рассчитываем вероятность посещения
    attendance_prob = calculate_attendance_probability(conn, noble_id, player_faction, event_type, event_season)

    # Определяем, посетил ли мероприятие
    attended = random.random() < attendance_prob

    # Изменение лояльности
    loyalty_change = 0
    if attended:
        loyalty_change = 2.0
    else:
        loyalty_change = -1.0 # Небольшое снижение, если не посетил

    new_loyalty = max(0.0, min(100.0, loyalty + loyalty_change))

    # Обновляем историю посещений
    history_list = history_str.split(',') if history_str else []
    history_list.append('1' if attended else '0')
    # Ограничиваем историю 10 последними записями
    if len(history_list) > 10:
        history_list = history_list[-10:]
    new_history_str = ','.join(history_list)

    cursor.execute("UPDATE nobles SET loyalty = ?, attendance_history = ? WHERE id = ?", (new_loyalty, new_history_str, noble_id))
    conn.commit()


def check_coup_attempts(conn):
    """
    Проверка попыток переворота.
    """
    cursor = conn.cursor()
    cursor.execute("SELECT id, loyalty FROM nobles WHERE status = 'active'")
    all_nobles = cursor.fetchall()

    disloyal_count = sum(1 for _, loyalty in all_nobles if loyalty < 50)
    very_disloyal_count = sum(1 for _, loyalty in all_nobles if loyalty < 35)

    coup_occurred = False
    coup_successful = False

    # Условие 1: 2+ дворян с лояльностью < 50
    if disloyal_count >= 2:
        if random.random() < 0.5: # 50% шанс
            coup_occurred = True
            coup_successful = True
            print("⚠️ Попытка переворота (2+ дворян с лояльностью < 50)!")
            # Записываем успешный переворот
            record_coup_attempt(conn, True)

    # Условие 2: 1+ дворян с лояльностью < 35
    elif very_disloyal_count >= 1:
        if random.random() < 0.3: # 30% шанс
            coup_occurred = True
            coup_successful = True
            print("⚠️ Попытка переворота (1+ дворян с лояльностью < 35)!")
            # Записываем успешный переворот
            record_coup_attempt(conn, True)

    if coup_occurred:
        # Отмечаем в БД, что была попытка (например, меняем status одного из них)
        # Или просто логируем. Проверка на поражение будет в основном цикле игры.
        # Для простоты, просто установим флаг в отдельной таблице или переменной
        # Здесь просто выводим сообщение. Логика поражения должна быть в GameScreen.
        pass

    return coup_occurred


def change_noble_priorities(conn):
    """Смена приоритетов дворян каждые 13 ходов"""
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM nobles WHERE status = 'active'")
    noble_ids = [row[0] for row in cursor.fetchall()]

    if len(noble_ids) >= 2:
        new_priorities = list(range(len(noble_ids)))
        random.shuffle(new_priorities)

        for i, noble_id in enumerate(noble_ids):
            cursor.execute("UPDATE nobles SET priority = ? WHERE id = ?", (new_priorities[i], noble_id))

        conn.commit()
        print("Приоритеты дворян изменены.")


def get_all_nobles(conn):
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, priority, loyalty, status, name, ideology, attendance_history
        FROM nobles
        WHERE status = 'active'
        ORDER BY priority ASC
    """)
    rows = cursor.fetchall()
    nobles = []
    for row in rows:
        nobles.append({
            'id': row[0],
            'priority': row[1],
            'loyalty': row[2],
            'status': row[3],
            'name': row[4],
            'ideology': row[5],
            'attendance_history': row[6]
        })
    return nobles


def attempt_secret_service_action(conn, player_faction=None, target_noble_id=None):
    """
    Попытка устранения конкретного дворянина Тайной Службой.
    """
    cursor = conn.cursor()

    if target_noble_id is None:
        return {'success': False, 'message': "Цель не указана.", 'noble_name': None}

    # Получаем имя дворянина по ID
    cursor.execute("SELECT name FROM nobles WHERE id = ?", (target_noble_id,))
    name_result = cursor.fetchone()
    if not name_result:
        return {'success': False, 'message': "Цель не найдена.", 'noble_name': None}

    noble_name = name_result[0]

    # Проверяем, что этот дворянин активен
    cursor.execute("SELECT id FROM nobles WHERE id = ? AND status = 'active'", (target_noble_id,))
    result = cursor.fetchone()
    if not result:
        return {'success': False, 'message': f"{noble_name} недоступен или уже устранён.", 'noble_name': noble_name}

    noble_to_eliminate_id = target_noble_id

    # Шанс успеха от 55% до 70%
    success_chance = random.uniform(0.55, 0.70)
    is_success = random.random() <= success_chance

    if not is_success:
        # 50% шанс, что узнают о провале
        is_discovered = random.random() <= 0.5
        if is_discovered:
            decrease_all_loyalty(conn, 11.0)
            return {
                'success': False,
                'message': f"Операция против {noble_name} провалена и раскрыта! Лояльность знати снизилась на 11%.",
                'noble_name': noble_name
            }
        else:
            return {
                'success': False,
                'message': f"Операция против {noble_name} провалена, но осталась незамеченной.",
                'noble_name': noble_name
            }

    # Операция успешна
    # Устраняем выбранного дворянина
    cursor.execute(
        "UPDATE nobles SET status = 'eliminated' WHERE id = ?",
        (noble_to_eliminate_id,)
    )

    # Генерация нового дворянина
    faction_race = get_player_faction(conn)
    if not faction_race:
        faction_race = 'Люди'  # fallback

    available_names = [
        n for n in NAMES[faction_race]
        if n not in [noble['name'] for noble in get_all_nobles(conn) if noble['status'] != 'eliminated']
    ]
    if not available_names:
        available_names = NAMES[faction_race]

    new_name = random.choice(available_names)
    new_loyalty = random.uniform(55, 75)
    new_priority = 99  # Будет пересчитан
    new_status = 'active'

    # Новая черта характера
    trait_type = random.choice(['ideology', 'race_love', 'greed'])
    if trait_type == 'ideology':
        new_ideology = random.choice(IDEOLOGIES)
    elif trait_type == 'race_love':
        new_ideology = f"Любит {random.choice([r for r in RACES if r != faction_race])}"
    else:  # greed
        base_demand = 1_000_000
        percentage = random.uniform(0.35, 0.75)
        additional_demand = int(10_000_000 * percentage)
        total_demand = base_demand + additional_demand
        new_ideology = json.dumps({'type': 'greed', 'demand': total_demand})

    new_attendance_history = ""

    cursor.execute("""
        INSERT INTO nobles (priority, loyalty, status, name, ideology, attendance_history) 
        VALUES (?, ?, ?, ?, ?, ?)
    """, (new_priority, new_loyalty, new_status, new_name, new_ideology, new_attendance_history))

    conn.commit()

    # 50% шанс, что узнают об успешной операции
    is_discovered = random.random() <= 0.5
    if is_discovered:
        increase_all_loyalty(conn, 6.0)
        message_suffix = " Операция раскрыта! Акция устрашения повысила лояльность парламента на 6%."
    else:
        message_suffix = " Операция прошла незамеченной. Лояльность осталась на прежнем уровне"

    return {
        'success': True,
        'message': f"Цель {noble_name} устранена.{message_suffix}",
        'noble_name': noble_name
    }


def increase_all_loyalty(conn, amount):
    """Повышение лояльности всех активных дворян."""
    cursor = conn.cursor()
    cursor.execute("UPDATE nobles SET loyalty = MIN(100.0, loyalty + ?) WHERE status = 'active'", (amount,))
    conn.commit()

def decrease_all_loyalty(conn, amount):
    """Снижение лояльности всех активных дворян."""
    cursor = conn.cursor()
    cursor.execute("UPDATE nobles SET loyalty = MAX(0.0, loyalty - ?) WHERE status = 'active'", (amount,))
    conn.commit()

def pay_greedy_noble(conn, noble_id, amount):
    """
    Обрабатывает оплату продажному дворянину.
    Увеличивает вероятность его посещения мероприятий.

    Args:
        conn: Соединение с БД.
        noble_id (int): ID дворянина.
        amount (int): Сумма оплаты (пока не используется для проверки, но может быть в будущем).

    Returns:
        bool: True, если оплата успешна, False в противном случае.
    """
    cursor = conn.cursor()

    # 1. Проверяем, существует ли дворянин и является ли он продажным
    cursor.execute("SELECT ideology FROM nobles WHERE id = ?", (noble_id,))
    result = cursor.fetchone()

    if not result:
        print(f"Ошибка: Дворянин с ID {noble_id} не найден.")
        return False

    ideology_str = result[0]
    noble_traits = get_noble_traits(ideology_str)

    if noble_traits['type'] != 'greed':
        print(f"Ошибка: Дворянин с ID {noble_id} не является продажным.")
        return False

    # 2. (Опционально) Проверить, соответствует ли amount требованию.
    # Для простоты пропустим эту проверку, предполагая, что UI уже показал правильную сумму.
    required_amount = noble_traits.get('demand', 0)
    if amount < required_amount:
        print(f"Ошибка: Предложена сумма {amount}, требуется {required_amount}.")
        # Можно вернуть False, но для простоты продолжим.
        # return False

    # 3. "Запоминаем" оплату.
    # Добавляем специальный маркер 'P' в историю посещений.
    # Это немного хак, но работает с текущей схемой.
    cursor.execute("SELECT attendance_history FROM nobles WHERE id = ?", (noble_id,))
    history_result = cursor.fetchone()
    current_history = history_result[0] if history_result and history_result[0] else ""

    # Добавляем маркер оплаты. Он будет действовать TURNS_PAID_EFFECT_LASTS ходов.
    history_list = current_history.split(',') if current_history else []
    history_list.append('P') # Маркер оплаты

    # Ограничиваем длину истории, чтобы не разрасталась бесконечно
    # Будем хранить последние 20 записей (больше, чем TURNS_PAID_EFFECT_LASTS)
    MAX_HISTORY_LENGTH = 20
    if len(history_list) > MAX_HISTORY_LENGTH:
        history_list = history_list[-MAX_HISTORY_LENGTH:]

    new_history_str = ','.join(history_list)

    cursor.execute("UPDATE nobles SET attendance_history = ? WHERE id = ?", (new_history_str, noble_id))
    conn.commit()

    return True

# --- Функции для интеграции с GameScreen ---

def initialize_nobles_if_needed(conn):
    """Инициализация дворян при старте игры."""
    generate_initial_nobles(conn)

def process_nobles_turn(conn, current_turn):
    """Обработка хода для дворян."""
    update_nobles_periodically(conn, current_turn)