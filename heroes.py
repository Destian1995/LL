from kivy.graphics import PopMatrix, PushMatrix

from db_lerdon_connect import *
def format_number(number):
    """Форматирует число с добавлением приставок (тыс., млн., млрд., трлн., квадр., квинт., секст., септил., октил., нонил., децил., андец.)"""
    if not isinstance(number, (int, float)):
        return str(number)
    if number == 0:
        return "0"

    absolute = abs(number)
    sign = -1 if number < 0 else 1

    if absolute >= 1_000_000_000_000_000_000_000_000_000_000_000_000:  # 1e36
        return f"{sign * absolute / 1e36:.1f} андец."
    elif absolute >= 1_000_000_000_000_000_000_000_000_000_000_000:  # 1e33
        return f"{sign * absolute / 1e33:.1f} децил."
    elif absolute >= 1_000_000_000_000_000_000_000_000_000_000:  # 1e30
        return f"{sign * absolute / 1e30:.1f} нонил."
    elif absolute >= 1_000_000_000_000_000_000_000_000_000:  # 1e27
        return f"{sign * absolute / 1e27:.1f} октил."
    elif absolute >= 1_000_000_000_000_000_000_000_000:  # 1e24
        return f"{sign * absolute / 1e24:.1f} септил."
    elif absolute >= 1_000_000_000_000_000_000_000:  # 1e21
        return f"{sign * absolute / 1e21:.1f} секст."
    elif absolute >= 1_000_000_000_000_000_000:  # 1e18
        return f"{sign * absolute / 1e18:.1f} квинт."
    elif absolute >= 1_000_000_000_000_000:  # 1e15
        return f"{sign * absolute / 1e15:.1f} квадр."
    elif absolute >= 1_000_000_000_000:  # 1e12
        return f"{sign * absolute / 1e12:.1f} трлн."
    elif absolute >= 1_000_000_000:  # 1e9
        return f"{sign * absolute / 1e9:.1f} млрд."
    elif absolute >= 1_000_000:  # 1e6
        return f"{sign * absolute / 1e6:.1f} млн."
    elif absolute >= 1_000:  # 1e3
        return f"{sign * absolute / 1e3:.1f} тыс."
    else:
        return f"{number}"

# --- Вспомогательные функции ---

def load_artifacts_from_db(faction):
    """Загружает список артефактов из таблицы artifacts."""
    artifacts = []
    try:
        cursor = faction.conn.cursor()
        # Добавлено поле cost в SELECT
        cursor.execute('''
            SELECT id, name, attack, defense, health, army_consumption,
                   crystal_bonus, coins_bonus, workers_bonus,
                   season_name, season_bonus_multiplier, image_url, cost, artifact_type
            FROM artifacts
        ''')
        rows = cursor.fetchall()
        for row in rows:
            artifact = {
                "id": row[0],
                "name": row[1],
                "attack": row[2] if row[2] is not None else 0,
                "defense": row[3] if row[3] is not None else 0,
                "health": row[4] if row[4] is not None else 0,
                "army_consumption": row[5] if row[5] is not None else 0,
                "crystal_bonus": row[6] if row[6] is not None else 0,
                "coins_bonus": row[7] if row[7] is not None else 0,
                "workers_bonus": row[8] if row[8] is not None else 0,
                "season_name": row[9] if row[9] is not None else "", # Может быть пустой строкой
                "season_bonus_multiplier": row[10] if row[10] is not None else 1.0,
                "image_url": row[11] if row[11] is not None else "files/pict/artifacts/default.png",
                "cost": row[12] if row[12] is not None else 0,
                "artifact_type": row[13] if row[13] is not None else -1
            }
            #print(f'Загруженный артефакт:{artifact}')
            stats = [
                artifact['attack'], artifact['defense'], artifact['health'],
                artifact['army_consumption'], artifact['crystal_bonus'],
                artifact['coins_bonus'], artifact['workers_bonus']
            ]
            if any(stat != 0 for stat in stats):
                artifacts.append(artifact)
    except sqlite3.Error as e:
        print(f"Ошибка при загрузке артефактов: {e}")
    return artifacts

def load_hero_equipment_from_db(faction):
    """
    Загружает текущую экипировку героя.
    Предполагается существование таблицы hero_equipment
    с полями: faction_name, slot_type, artifact_id.
    slot_type: 'weapon', 'boots', 'armor', 'helmet', 'accessory'
    """
    equipment = {}
    try:
        cursor = faction.conn.cursor()
        cursor.execute('''
            SELECT slot_type, artifact_id
            FROM hero_equipment
            WHERE faction_name = ?
        ''', (faction.faction,))
        rows = cursor.fetchall()
        for slot_type, artifact_id in rows:
            equipment[slot_type] = artifact_id
    except sqlite3.Error as e:
        print(f"Ошибка при загрузке экипировки героя: {e}")
    return equipment

def save_hero_equipment_to_db(faction, slot_type, artifact_id):
    """
    Обновляет экипировку героя в БД, устанавливая artifact_id для заданного слота.
    Предполагается, что запись (faction_name, hero_name, slot_type) уже существует.
    """
    try:
        cursor = faction.conn.cursor()
        # 1. Обновляем запись, устанавливая новый artifact_id или NULL
        # Используем UPDATE, чтобы изменить только artifact_id
        cursor.execute('''UPDATE hero_equipment 
                          SET artifact_id = ?
                          WHERE faction_name = ?  AND slot_type = ?''',
                       (artifact_id, faction.faction, slot_type))

        # Проверим, была ли затронута строка (на случай, если запись не существует)
        if cursor.rowcount == 0:
            print(f"[WARNING] save_hero_equipment_to_db: Запись для {faction.faction}/слот {slot_type} не найдена в hero_equipment. Ничего не обновлено.")
        else:
            faction.conn.commit()
            print(f"[DEBUG] save_hero_equipment_to_db: Экипировка обновлена для {faction.faction}/, слот {slot_type}, артефакт {artifact_id}")

    except sqlite3.Error as e:
        print(f"[ERROR] save_hero_equipment_to_db: Ошибка при обновлении экипировки героя: {e}")
        try:
            faction.conn.rollback()
        except:
            pass # Игнорируем ошибки отката
    except Exception as e:
        print(f"[ERROR] save_hero_equipment_to_db: Неожиданная ошибка: {e}")
        try:
            faction.conn.rollback()
        except:
            pass


def load_hero_image_from_db(faction):
    """
    Загружает изображение героя из таблицы garrisons, предварительно проверив faction героя через таблицу units.
    """
    try:
        cursor = faction.conn.cursor()

        # Сначала определяем faction героя через таблицу units и сравниваем с faction игрока
        cursor.execute('''
            SELECT DISTINCT g.unit_image FROM garrisons g
            LEFT JOIN units u ON g.unit_name = u.unit_name
            WHERE u.faction = ? AND u.unit_class = "3"
            LIMIT 1
        ''', (faction.faction,))  # Добавлена запятая здесь
        row = cursor.fetchone()
        print('Изображение героя:', row)
        if row and row[0]:
            return row[0]
        else:
            return "files/pict/hero/default_image.png"

    except sqlite3.Error as e:
        print(f"Ошибка при загрузке изображения героя: {e}")
        return "files/pict/hero/default_image.png"

def format_artifact_description(artifact):
    """
    Формирует строку описания артефакта на основе его характеристик.
    """
    stat_map = {
        'attack': 'Атака',
        'defense': 'Защита',
        'health': 'Здоровье',
        'army_consumption': 'Содержание армии',
        'crystal_bonus': 'Бонус кристаллов',
        'coins_bonus': 'Бонус монет',
        'workers_bonus': 'Рабочие'
    }
    stats = []
    for key, label in stat_map.items():
        value = artifact.get(key, 0)
        if value and value != 0:
            # Учитываем множитель сезона, если он не равен 1.0
            multiplier = artifact.get('season_bonus_multiplier', 1.0)
            if multiplier != 1.0:
                effective_value = value * multiplier
                # Округляем до целого, если результат целый, иначе до 1 знака после запятой
                if effective_value.is_integer():
                    effective_value = int(effective_value)
                else:
                    effective_value = round(effective_value, 1)
                stats.append(f"{label} {effective_value}%")
            else:
                stats.append(f"{label} {value}%")

    if not stats:
        return None  # Пропустить артефакт, если все характеристики нулевые

    # Формируем суффикс для времени действия бонуса
    season = artifact.get('season_name')
    if season:
        suffix = f"Сезон артефакта: {season}"
    else:
        suffix = "Всегда"

    return f"{', '.join(stats)} {suffix}"

def create_artifact_button_style(btn):
    """Создает стиль для строки артефакта."""
    with btn.canvas.before:
        Color(0.2, 0.2, 0.2, 1) # Темно-серый фон
        btn.rect = RoundedRectangle(pos=btn.pos, size=btn.size, radius=[10])
    def update_rect(instance, value):
        instance.rect.pos = instance.pos
        instance.rect.size = instance.size
    btn.bind(pos=update_rect, size=update_rect)
    return btn


def load_hero_stats_from_db(faction):
    """
    Загружает базовые характеристики героя.
    Сначала проверяет наличие героя в таблице garrisons, связанного с фракцией игрока.
    Если герой найден, загружает его характеристики из таблицы units.
    Герой определяется как юнит с unit_class = '3'.
    """
    stats = {
        "attack": 0,
        "defense": 0,
        "durability": 0, # Или health, в зависимости от вашей БД

    }

    try:
        cursor = faction.conn.cursor()

        cursor.execute('''
            SELECT DISTINCT g.unit_name 
            FROM garrisons g
            LEFT JOIN units u ON g.unit_name = u.unit_name
            WHERE u.faction = ? AND u.unit_class = "3"
            LIMIT 1
        ''', (faction.faction,))

        row = cursor.fetchone()

        if row:
            hero_unit_name = row[0]
            print(f"Найден герой в garrisons/units: {hero_unit_name} для фракции {faction.faction}")

            # 2. Загрузить характеристики найденного героя из таблицы units
            cursor.execute('''
                SELECT attack, defense, durability
                FROM units
                WHERE unit_name = ? AND faction = ? AND unit_class = "3"
                LIMIT 1
            ''', (hero_unit_name, faction.faction)) # Добавляем проверку faction для безопасности

            stats_row = cursor.fetchone()
            if stats_row:
                # Предполагаем, что столбцы идут в порядке SELECT
                stats['attack'] = stats_row[0] if stats_row[0] is not None else 0
                stats['defense'] = stats_row[1] if stats_row[1] is not None else 0
                # Предполагая, что в БД поле называется 'durability', а не 'health'
                stats['durability'] = stats_row[2] if stats_row[2] is not None else 0
                # Добавьте обработку других столбцов, если добавили их в SELECT
                print(f"Характеристики загружены: {stats}")
            else:
                print(f"Характеристики для героя {hero_unit_name} не найдены в units.")
        else:
            print(f"Герой (unit_class='3', связанный с garrisons) не найден для фракции {faction.faction}")

    except sqlite3.Error as e:
        print(f"Ошибка при загрузке характеристик героя: {e}")

    return stats


def format_hero_stats(stats_dict):
    """
    Форматирует словарь характеристик в строку для отображения.
    """
    if not stats_dict:
        return "Нет данных"

    # Пример форматирования, адаптируйте под свои нужды
    lines = []
    if 'attack' in stats_dict:
        lines.append(f"Атака: {stats_dict['attack']}")
    if 'defense' in stats_dict:
        lines.append(f"Защита: {stats_dict['defense']}")
    if 'durability' in stats_dict:
        lines.append(f"Здоровье: {stats_dict['durability']}")
    # Добавьте другие характеристики при необходимости

    if not lines:
        return "Характеристики отсутствуют"

    return '\n'.join(lines)


# --- Основная функция открытия попапа ---
def create_gradient_background(widget, color1, color2, direction='vertical'):
    """Создает градиентный фон для виджета."""
    widget.canvas.before.clear()
    with widget.canvas.before:
        from kivy.graphics import Mesh
        PushMatrix()
        # Создаем простой вертикальный или горизонтальный градиент с помощью Mesh
        if direction == 'vertical':
            vertices = [widget.x, widget.y, 0, 0,  # x, y, u, v
                        widget.x + widget.width, widget.y, 1, 0,
                        widget.x + widget.width, widget.y + widget.height, 1, 1,
                        widget.x, widget.y + widget.height, 0, 1]
        else: # horizontal
            vertices = [widget.x, widget.y, 0, 0,
                        widget.x + widget.width, widget.y, 1, 0,
                        widget.x + widget.width, widget.y + widget.height, 1, 1,
                        widget.x, widget.y + widget.height, 0, 1]

        indices = [0, 1, 2, 3] # Треугольники
        mode = 'triangle_fan'
        # Используем Mesh для градиента (упрощенный подход)
        # Лучше использовать Shader или несколько прямоугольников с разными цветами
        # Но для простоты используем Mesh с двумя цветами
        mesh = Mesh(vertices=vertices, indices=indices, mode=mode, fmt=[('v_pos', 2, 'float'), ('v_tex', 2, 'float')])
        PopMatrix()

def style_rounded_button(button, bg_color=(0.2, 0.6, 0.8, 1), radius=dp(10), has_shadow=True):
    """Применяет стиль скругленной кнопки с тенью."""
    button.background_normal = ''
    button.background_color = (0, 0, 0, 0) # Прозрачный фон по умолчанию
    button.canvas.before.clear()
    with button.canvas.before:
        from kivy.graphics import Color, RoundedRectangle, PushMatrix, PopMatrix, Translate
        if has_shadow:
            # Тень (немного смещенная и затемненная копия)
            Color(0, 0, 0, 0.3) # Цвет тени
            shadow_offset = dp(2)
            RoundedRectangle(pos=(button.pos[0] + shadow_offset, button.pos[1] - shadow_offset),
                             size=button.size, radius=[radius])

        # Основной фон кнопки
        Color(*bg_color)
        button.rect = RoundedRectangle(pos=button.pos, size=button.size, radius=[radius])

    def update_button_graphics(*args):
        button.canvas.before.clear()
        with button.canvas.before:
            from kivy.graphics import Color, RoundedRectangle, PushMatrix, PopMatrix, Translate
            if has_shadow:
                Color(0, 0, 0, 0.3)
                shadow_offset = dp(2)
                RoundedRectangle(pos=(button.pos[0] + shadow_offset, button.pos[1] - shadow_offset),
                                 size=button.size, radius=[radius])
            Color(*bg_color)
            if hasattr(button, 'rect'):
                button.rect.pos = button.pos
                button.rect.size = button.size
            else:
                button.rect = RoundedRectangle(pos=button.pos, size=button.size, radius=[radius])

    button.bind(pos=update_button_graphics, size=update_button_graphics)

def style_rounded_spinner(spinner, bg_color=(0.4, 0.4, 0.4, 1), text_color=(1, 1, 1, 1), radius=dp(8)):
    """Применяет стиль скругленного спиннера."""
    spinner.background_normal = ''
    spinner.background_color = (0, 0, 0, 0) # Прозрачный фон
    spinner.color = text_color
    spinner.canvas.before.clear()
    with spinner.canvas.before:
        from kivy.graphics import Color, RoundedRectangle
        Color(*bg_color)
        spinner.rect = RoundedRectangle(pos=spinner.pos, size=spinner.size, radius=[radius])

    def update_spinner_graphics(*args):
        spinner.canvas.before.clear()
        with spinner.canvas.before:
            from kivy.graphics import Color, RoundedRectangle
            Color(*bg_color)
            if hasattr(spinner, 'rect'):
                spinner.rect.pos = spinner.pos
                spinner.rect.size = spinner.size
            else:
                spinner.rect = RoundedRectangle(pos=spinner.pos, size=spinner.size, radius=[radius])

    spinner.bind(pos=update_spinner_graphics, size=update_spinner_graphics)

# --- Основная функция ---
def open_artifacts_popup(faction):
    """
    Открывает Popup с артефактами и экипировкой героя.
    :param faction: Экземпляр класса Faction
    """
    artifacts_list = load_artifacts_from_db(faction)
    hero_equipment = load_hero_equipment_from_db(faction)
    hero_image_path = load_hero_image_from_db(faction)
    popup_layout = BoxLayout(orientation='horizontal', padding=dp(10), spacing=dp(10))
    left_panel = BoxLayout(orientation='vertical', size_hint=(0.5, 1))
    filters_container = BoxLayout(orientation='vertical', size_hint_y=None, height=dp(120), spacing=dp(5))
    filter_states = {'season_influence': 'all', 'artifact_type': 'all', 'cost_sort': 'all'}

    def update_artifact_list(*args):
        artifacts_list_layout.clear_widgets()
        filtered_artifacts = []
        for artifact in artifacts_list:
            season_ok = True
            if filter_states['season_influence'] == 'has_influence':
                season_name = artifact.get('season_name')
                season_ok = season_name is not None and season_name != ""
            elif filter_states['season_influence'] == 'no_influence':
                season_name = artifact.get('season_name')
                season_ok = season_name is None or season_name == ""
            type_ok = True
            if filter_states['artifact_type'] != 'all':
                type_ok = artifact.get('artifact_type') == filter_states['artifact_type']
            cost_ok = True
            if season_ok and type_ok and cost_ok:
                filtered_artifacts.append(artifact)
        if filter_states['cost_sort'] == 'asc':
            filtered_artifacts.sort(key=lambda art: art.get('cost', 0))
        elif filter_states['cost_sort'] == 'desc':
            filtered_artifacts.sort(key=lambda art: art.get('cost', 0), reverse=True)
        for artifact in filtered_artifacts:
            description = format_artifact_description(artifact)
            if not description:
                continue
            artifact_row_container = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(90), padding=(dp(5), dp(5)), spacing=dp(10))

            artifact_info_container = BoxLayout(orientation='vertical', size_hint_x=0.75)
            name_label = Label(text=artifact['name'], halign='left', valign='middle', font_size='16sp', bold=True, size_hint_y=None, height=dp(25), color=(1, 1, 0.6, 1))
            name_label.bind(size=name_label.setter('text_size'))
            stats_label = Label(text=description, halign='left', valign='top', font_size='14sp', bold=True, color=(0.9, 0.9, 0.9, 1), size_hint_y=None, height=dp(50))
            stats_label.bind(size=stats_label.setter('text_size'))
            artifact_info_container.add_widget(name_label)
            artifact_info_container.add_widget(stats_label)
            cost = artifact.get('cost', 0)
            formatted_cost = format_number(cost)
            buy_button = Button(
                text=f"Купить\n({formatted_cost})",
                size_hint_x=None,
                width=dp(90),
                height=dp(60),
                font_size='14sp',
                bold=True
            )
            # Применяем стиль к кнопке "Купить"
            style_rounded_button(buy_button, bg_color=(0.2, 0.7, 0.3, 1), radius=dp(8), has_shadow=True) # Зеленоватый градиент

            def make_buy_handler(art_data):
                """Создает обработчик для кнопки покупки артефакта."""

                def on_buy(instance):
                    # Проверяем, что fraction_instance доступен
                    if 'fraction_instance' not in locals() and 'fraction_instance' not in globals():
                        pass  # Логика получения будет ниже
                    current_fraction_instance = faction  # Предполагаем, что faction уже правильный объект
                    # Если это не так, замените строку выше на правильное получение объекта

                    print(
                        f"[DEBUG] Покупка артефакта: {art_data['name']} (ID: {art_data['id']}, Тип: {art_data['artifact_type']})")

                    # 1. Определяем slot_type на основе типа артефакта
                    artifact_type_to_slot = {
                        0: '0',  # Оружие -> slot_type 0
                        1: '1',  # Голова -> slot_type 1
                        2: '2',  # Сапоги -> slot_type 2
                        3: '3',  # Туловище -> slot_type 3
                        4: '4'  # Аксессуар -> slot_type 4
                    }
                    slot_type = artifact_type_to_slot.get(art_data['artifact_type'])

                    if slot_type is None:
                        print(f"[ERROR] Неизвестный тип артефакта: {art_data['artifact_type']}")
                        show_popup_message("Ошибка", "Невозможно экипировать этот артефакт.")
                        return

                    print(f"[DEBUG] Целевой слот: {slot_type}")

                    # 2. Проверяем, есть ли уже артефакт в этом слоте
                    current_artifact_id_in_slot = hero_equipment.get(slot_type)
                    print(f"[DEBUG] Текущий артефакт в слоте {slot_type}: {current_artifact_id_in_slot}")

                    # --- Вспомогательные функции для работы с деньгами ---
                    # Работаем напрямую с экземпляром Fraction
                    def deduct_coins_local(fraction_obj, amount):
                        """Списывает монеты, если хватает. Возвращает True при успехе."""
                        try:
                            # Получаем текущее количество монет НАПРЯМУЮ из объекта Fraction
                            current_money = getattr(fraction_obj, 'money', 0)
                            print(f"[DEBUG] [deduct_coins_local] Текущие монеты: {current_money}, Списание: {amount}")
                            if current_money >= amount:
                                new_amount = current_money - amount
                                # Вызываем метод update_resource_now ЭКЗЕМПЛЯРА Fraction
                                fraction_obj.update_resource_now('Кроны', new_amount)
                                print(f"[DEBUG] [deduct_coins_local] Новые монеты: {new_amount}")
                                return True
                            else:
                                print(
                                    f"[INFO] [deduct_coins_local] Недостаточно крон. Нужно: {amount}, Есть: {current_money}")
                                return False
                        except Exception as e:
                            print(f"[ERROR] [deduct_coins_local] Ошибка при списании: {e}")
                            import traceback
                            traceback.print_exc()
                            return False

                    def add_coins_local(fraction_obj, amount):
                        """Начисляет монеты. Возвращает True при успехе."""
                        try:
                            current_money = getattr(fraction_obj, 'money', 0)
                            print(f"[DEBUG] [add_coins_local] Текущие кроны: {current_money}, Начисление: {amount}")
                            new_amount = current_money + amount
                            fraction_obj.update_resource_now('Кроны', new_amount)
                            print(f"[DEBUG] [add_coins_local] Новые кроны: {new_amount}")
                            # fraction_obj.money = new_amount # если update_resource_now не делает это
                            return True
                        except Exception as e:
                            print(f"[ERROR] [add_coins_local] Ошибка при начислении: {e}")
                            import traceback
                            traceback.print_exc()
                            return False

                    # --- Конец вспомогательных функций ---

                    # 3. Логика покупки/замены
                    try:
                        artifact_cost = art_data['cost']
                        print(f"[DEBUG] Цена нового артефакта: {artifact_cost}")

                        if current_artifact_id_in_slot is None:
                            # --- Сценарий 1: Слот пуст, просто покупаем ---
                            print("[DEBUG] Слот пуст. Покупаем новый артефакт.")
                            if deduct_coins_local(current_fraction_instance,
                                                  artifact_cost):  # Используем current_fraction_instance
                                # Сохраняем в БД
                                save_hero_equipment_to_db(current_fraction_instance, slot_type,
                                                          art_data['id'])  # Передаем экземпляр
                                # Обновляем локальный словарь hero_equipment
                                hero_equipment[slot_type] = art_data['id']
                                # Обновляем отображение слота
                                update_equipment_slot(slot_type, art_data)
                                print(f"[SUCCESS] Артефакт {art_data['name']} куплен и экипирован в слот {slot_type}.")
                                show_popup_message("Успех", f"Артефакт {art_data['name']} куплен!")
                            else:
                                print("[INFO] Недостаточно монет для покупки.")
                                show_popup_message("Ошибка", "Недостаточно Крон!")

                        else:
                            # --- Сценарий 2: Слот занят, предлагаем замену ---
                            print(f"[DEBUG] Слот {slot_type} занят. Запрашиваем подтверждение замены.")

                            # Получаем данные старого артефакта из БД
                            old_artifact_data = None
                            try:
                                # Используем соединение из экземпляра Fraction
                                cursor = current_fraction_instance.conn.cursor()
                                cursor.execute("SELECT * FROM artifacts WHERE id = ?", (current_artifact_id_in_slot,))
                                old_artifact_row = cursor.fetchone()
                                if old_artifact_row:
                                    # Предполагаем, что cost находится в 13-м столбце (index 12)
                                    old_artifact_data = {
                                        "id": old_artifact_row[0],
                                        "name": old_artifact_row[1],
                                        "cost": old_artifact_row[12] if len(old_artifact_row) > 12 else 0
                                    }
                                    print(f"[DEBUG] Данные старого артефакта: {old_artifact_data}")
                            except sqlite3.Error as e:
                                print(f"[ERROR] Ошибка при получении данных старого артефакта: {e}")
                                show_popup_message("Ошибка", "Ошибка при проверке старого артефакта.")
                                return

                            if not old_artifact_data:
                                print(
                                    f"[WARNING] Данные старого артефакта (ID: {current_artifact_id_in_slot}) не найдены. Заменяем без возврата.")
                                old_artifact_cost = 0
                            else:
                                old_artifact_cost = old_artifact_data.get('cost', 0)

                            sell_price = int(old_artifact_cost * 0.65)
                            net_cost = artifact_cost - sell_price
                            print(
                                f"[DEBUG] Цена старого артефакта: {old_artifact_cost}, Цена продажи: {sell_price}, Чистая стоимость: {net_cost}")

                            def confirm_replace(instance):
                                confirm_popup.dismiss()
                                if deduct_coins_local(current_fraction_instance, net_cost):  # Используем экземпляр
                                    if sell_price > 0:
                                        add_coins_local(current_fraction_instance, sell_price)  # Используем экземпляр
                                        print(f"[DEBUG] Вернули {sell_price} монет за старый артефакт.")

                                    save_hero_equipment_to_db(current_fraction_instance, slot_type,
                                                              art_data['id'])  # Используем экземпляр
                                    hero_equipment[slot_type] = art_data['id']
                                    update_equipment_slot(slot_type, art_data)
                                    # update_hero_stats_display()
                                    print(
                                        f"[SUCCESS] Артефакт {art_data['name']} куплен и экипирован в слот {slot_type} (старый заменен).")
                                    show_popup_message("Успех",
                                                       f"Артефакт {art_data['name']} куплен! Старый артефакт продан.")
                                else:
                                    print("[INFO] Недостаточно монет для замены.")
                                    show_popup_message("Ошибка", "Недостаточно Крон для замены!")

                            def cancel_replace(instance):
                                confirm_popup.dismiss()
                                print("[INFO] Замена артефакта отменена пользователем.")

                            content = BoxLayout(orientation='vertical', padding=10, spacing=10)
                            old_art_name = old_artifact_data.get('name',
                                                                 'Неизвестный артефакт') if old_artifact_data else 'Неизвестный артефакт'
                            message = (f"Заменить артефакт '{old_art_name}'\n"
                                       f"на '{art_data['name']}'?\n"
                                       f"Цена нового: {artifact_cost}\n"
                                       f"Вы получите за старый: {sell_price}\n"
                                       f"К оплате: {net_cost}")
                            message_label = Label(text=message, text_size=(None, None), halign='center')
                            message_label.bind(
                                size=lambda instance, value: setattr(instance, 'text_size', (value[0] * 0.9, None)))
                            content.add_widget(message_label)

                            btn_layout = BoxLayout(size_hint_y=None, height=dp(50), spacing=dp(10))
                            btn_yes = Button(text="Да", background_color=(0.4, 0.7, 0.4, 1))
                            btn_no = Button(text="Нет", background_color=(0.7, 0.4, 0.4, 1))
                            btn_yes.bind(on_release=confirm_replace)
                            btn_no.bind(on_release=cancel_replace)
                            btn_layout.add_widget(btn_yes)
                            btn_layout.add_widget(btn_no)
                            content.add_widget(btn_layout)

                            confirm_popup = Popup(title="Подтверждение замены",
                                                  content=content,
                                                  size_hint=(0.8, 0.6),
                                                  auto_dismiss=False)
                            confirm_popup.open()

                    except Exception as e:
                        error_msg = f"Произошла ошибка при покупке артефакта: {e}"
                        print(f"[ERROR] {error_msg}")
                        import traceback
                        traceback.print_exc()
                        show_popup_message("Ошибка", error_msg)

                return on_buy
            buy_button.bind(on_release=make_buy_handler(artifact))
            artifact_row_container.add_widget(artifact_info_container)
            button_wrapper = BoxLayout(size_hint_x=None, width=dp(90), padding=(0, dp(15), 0, dp(15)))
            button_wrapper.add_widget(buy_button)
            artifact_row_container.add_widget(button_wrapper)
            artifacts_list_layout.add_widget(artifact_row_container)
        artifacts_list_layout.height = len(artifacts_list_layout.children) * dp(90) + (len(artifacts_list_layout.children) - 1) * dp(5) if artifacts_list_layout.children else dp(1)

    # --- Виджеты фильтров ---
    # 1. Фильтр по сезону
    season_filter_layout = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(30))
    season_filter_layout.add_widget(Label(text="Сезон:", size_hint_x=None, width=dp(60), halign='left'))
    season_spinner = Spinner(
        text='Все',
        values=('Все', 'Есть влияние', 'Нет влияния'),
        size_hint=(1, None),
        height=dp(30)
    )
    # Применяем стиль к спиннеру
    style_rounded_spinner(season_spinner, bg_color=(0.3, 0.5, 0.7, 1), text_color=(1, 1, 1, 1), radius=dp(6))
    def on_season_spinner_select(spinner, text):
        mapping = {'Все': 'all', 'Есть влияние': 'has_influence', 'Нет влияния': 'no_influence'}
        filter_states['season_influence'] = mapping.get(text, 'all')
        update_artifact_list()
    season_spinner.bind(text=on_season_spinner_select)
    season_filter_layout.add_widget(season_spinner)
    filters_container.add_widget(season_filter_layout)

    # 2. Фильтр по типу
    type_filter_layout = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(30))
    type_filter_layout.add_widget(Label(text="Тип:", size_hint_x=None, width=dp(60), halign='left'))
    type_spinner = Spinner(
        text='Все',
        values=('Все', 'Оружие', 'Сапоги', 'Туловище', 'Голова', 'Аксессуар'),
        size_hint=(1, None),
        height=dp(30)
    )
    # Применяем стиль к спиннеру
    style_rounded_spinner(type_spinner, bg_color=(0.3, 0.5, 0.7, 1), text_color=(1, 1, 1, 1), radius=dp(6))
    def on_type_spinner_select(spinner, text):
        mapping = {
            'Все': 'all',
            'Оружие': 0,
            'Голова': 1,
            'Сапоги': 2,
            'Туловище': 3,
            'Аксессуар': 4
        }
        selected_value = mapping.get(text, 'all')
        filter_states['artifact_type'] = selected_value
        update_artifact_list()
    type_spinner.bind(text=on_type_spinner_select)
    type_filter_layout.add_widget(type_spinner)
    filters_container.add_widget(type_filter_layout)

    # 3. Фильтр по стоимости (сортировка)
    cost_filter_layout = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(30))
    cost_filter_layout.add_widget(Label(text="Цена:", size_hint_x=None, width=dp(60), halign='left'))
    cost_spinner = Spinner(
        text='Все',
        values=('Все', 'По возрастанию', 'По убыванию'),
        size_hint=(1, None),
        height=dp(30)
    )
    # Применяем стиль к спиннеру
    style_rounded_spinner(cost_spinner, bg_color=(0.3, 0.5, 0.7, 1), text_color=(1, 1, 1, 1), radius=dp(6))
    def on_cost_spinner_select(spinner, text):
        mapping = {'Все': 'all', 'По возрастанию': 'asc', 'По убыванию': 'desc'}
        filter_states['cost_sort'] = mapping.get(text, 'all')
        update_artifact_list()
    cost_spinner.bind(text=on_cost_spinner_select)
    cost_filter_layout.add_widget(cost_spinner)
    filters_container.add_widget(cost_filter_layout)

    left_panel.add_widget(filters_container)
    left_panel.add_widget(Label(text="Артефакты", size_hint_y=None, height=dp(40), bold=True, font_size='18sp'))
    scroll_view = ScrollView(do_scroll_x=False)
    artifacts_list_layout = BoxLayout(orientation='vertical', size_hint_y=None, spacing=dp(5))
    artifacts_list_layout.bind(minimum_height=artifacts_list_layout.setter('height'))
    scroll_view.add_widget(artifacts_list_layout)
    left_panel.add_widget(scroll_view)

    # --- Правая часть: Герой и экипировка ---
    right_panel = FloatLayout(size_hint=(0.5, 1))
    try:
        hero_image_width = dp(450)
        hero_image_height = dp(450)
        hero_image = Image(source=hero_image_path, size_hint=(None, None), size=(hero_image_width, hero_image_height))
        hero_image_size = (hero_image_width, hero_image_height)
        hero_image.pos_hint = {'center_x': 0.5, 'center_y': 0.5}
        right_panel.add_widget(hero_image)
    except Exception as e:
        print(f"Ошибка загрузки изображения героя {hero_image_path}: {e}")
        hero_placeholder = Label(
            text="[b]Изображение\nГероя[/b]",
            markup=True,
            halign='center',
            valign='middle'
        )
        hero_placeholder.size_hint = (None, None)
        hero_placeholder.size = (dp(450), dp(450))
        def set_placeholder_center(*args):
            if hasattr(right_panel, 'center_x') and hasattr(right_panel, 'center_y'):
                hero_placeholder.center_x = right_panel.center_x
                hero_placeholder.center_y = right_panel.center_y
        right_panel.bind(parent=set_placeholder_center)
        right_panel.add_widget(hero_placeholder)

    slot_size = (dp(90), dp(90))
    equipment_slots = {}

    def update_equipment_slot(slot_type, artifact_data=None):
        """Обновляет виджет слота экипировки."""
        if slot_type in equipment_slots:
            def _update(dt):
                slot_widget = equipment_slots[slot_type]
                slot_widget.clear_widgets()
                slot_widget.canvas.before.clear()  # Очищаем старый стиль

                if artifact_data:
                    try:
                        img_source = artifact_data.get('image_url')
                        print(f'[DEBUG] Загружаем изображение для слота {slot_type}: {img_source}')
                        if not img_source:
                            img_source = "files/pict/artifacts/default.png"

                        # Создаем Image-виджет
                        slot_image = Image(source=img_source, allow_stretch=True, keep_ratio=True)

                        # Проверяем, загружено ли изображение
                        if not slot_image.texture:
                            print(f'[WARNING] Изображение {img_source} не загружено')
                            slot_widget.add_widget(Label(text="?", font_size='20sp'))
                        else:
                            print(f'[DEBUG] Изображение {img_source} успешно загружено')
                            slot_widget.add_widget(slot_image)
                    except Exception as e:
                        print(f"Ошибка загрузки изображения для слота {slot_type}: {e}")
                        slot_widget.add_widget(Label(text="?", font_size='20sp'))
                else:
                    slot_widget.add_widget(Label(text=f"[{slot_type[:3].upper()}]", markup=True, font_size='10sp'))

                # Применяем стиль к слоту после очистки
                apply_slot_style(slot_widget)

            # Выполняем обновление UI через главный поток
            Clock.schedule_once(_update)

    def apply_slot_style(slot_widget):
        """Применяет стиль к слоту экипировки."""
        slot_widget.background_normal = ''
        slot_widget.background_color = (0, 0, 0, 0)
        with slot_widget.canvas.before:
            from kivy.graphics import Color, RoundedRectangle
            Color(0.4, 0.4, 0.4, 1) # Серый фон
            slot_widget.rect = RoundedRectangle(pos=slot_widget.pos, size=slot_widget.size, radius=[dp(8)])

        def update_slot_rect(instance, value):
            if hasattr(instance, 'rect'):
                instance.rect.pos = instance.pos
                instance.rect.size = instance.size
            else:
                with instance.canvas.before:
                    from kivy.graphics import Color, RoundedRectangle
                    Color(0.4, 0.4, 0.4, 1)
                    instance.rect = RoundedRectangle(pos=instance.pos, size=instance.size, radius=[dp(8)])
        slot_widget.bind(pos=update_slot_rect, size=update_slot_rect)

    # --- Создание слотов экипировки ---
    for slot_type in ['0', '2', '3', '1', '4']:
        slot_widget = Button(
            size_hint=(None, None),
            size=slot_size,
            pos=(0, 0),
            # background_color и background_normal будут установлены в apply_slot_style
        )
        apply_slot_style(slot_widget) # Применяем стиль сразу

        artifact_id_in_slot = hero_equipment.get(slot_type)
        print(f"[DEBUG] Слот {slot_type}: artifact_id = {artifact_id_in_slot}")
        artifact_data_in_slot = next((a for a in artifacts_list if a['id'] == artifact_id_in_slot),
                                     None) if artifact_id_in_slot else None
        print(f"[DEBUG] Слот {slot_type}: artifact_data = {artifact_data_in_slot}")
        update_equipment_slot(slot_type, artifact_data_in_slot)

        right_panel.add_widget(slot_widget)
        equipment_slots[slot_type] = slot_widget

        # --- Создание блока характеристик героя ---
        hero_stats_container = BoxLayout(
            orientation='vertical',
            size_hint=(1, None),
            height=dp(150),
            padding=dp(15),
            spacing=dp(25)
        )
        hero_stats_label = Label(
            text="",
            halign='right',
            valign='top',
            font_size='27sp',
            bold=False,
            color=(1, 1, 1, 1),
            markup=True
        )
        hero_stats_label.bind(size=hero_stats_label.setter('text_size'))
        hero_stats_container.add_widget(hero_stats_label)
        hero_stats_container.pos_hint = {'x': -0.43, 'y': 0}
        right_panel.add_widget(hero_stats_container)
        hero_stats_widget = hero_stats_label

    popup_layout.add_widget(left_panel)
    popup_layout.add_widget(right_panel)

    artifacts_popup = Popup(
        title="Артефакты и Герой",
        content=popup_layout,
        size_hint=(0.95, 0.95),
        title_align='center',
        separator_color=(0.5, 0.3, 0.7, 1)
    )

    def position_slots(dt):
        if not right_panel or not hasattr(right_panel, 'width') or right_panel.width == 0:
            return
        right_panel_width = right_panel.width
        right_panel_height = right_panel.height
        right_panel_x = right_panel.x
        right_panel_y = right_panel.y
        center_x = right_panel_x + right_panel_width / 2
        center_y = right_panel_y + right_panel_height / 2

        half_hero_width = hero_image_size[0] / 2
        half_slot_width = slot_size[0] / 2
        min_distance_from_center = half_hero_width + half_slot_width + dp(10)
        distance_horizontal = max(dp(200), min_distance_from_center)
        distance_vertical = max(dp(200), min_distance_from_center)
        distance_above_head = distance_vertical + dp(80)

        slot_positions = {
            '0': (center_x - distance_horizontal, center_y - slot_size[1] / 2),
            '2': (center_x - slot_size[0] / 2, center_y - distance_vertical),
            '3': (center_x + distance_horizontal - slot_size[0], center_y - slot_size[1] / 2),
            '1': (center_x - slot_size[0] / 2, center_y + distance_vertical - slot_size[1]),
            '4': (center_x + distance_horizontal - slot_size[0], center_y + distance_above_head - slot_size[1]),
        }

        for slot_type, pos in slot_positions.items():
            if slot_type in equipment_slots:
                equipment_slots[slot_type].pos = pos

    def update_hero_stats_display():
        if hero_stats_widget:
            try:
                hero_stats_data = load_hero_stats_from_db(faction)
                formatted_stats = format_hero_stats(hero_stats_data)
                hero_stats_widget.text = formatted_stats
            except Exception as e:
                print(f"Ошибка обновления характеристик героя: {e}")
                hero_stats_widget.text = "Ошибка загрузки"

    Clock.schedule_once(lambda dt: update_hero_stats_display(), 0)
    Clock.schedule_once(position_slots, -1)
    artifacts_popup.bind(on_open=lambda *args: Clock.schedule_once(position_slots, 0.1))

    # Вызываем update_artifact_list один раз в конце, чтобы заполнить список с начальными стилями
    update_artifact_list()

    artifacts_popup.open()


def show_popup_message(title, message):
    """
    Отображает всплывающее окно с сообщением, расположенным по центру,
    с белым цветом текста и стандартным размером шрифта.
    :param title: Заголовок окна.
    :param message: Текст сообщения.
    """
    # Основной контейнер: заполняет всё пространство popup
    content = BoxLayout(
        orientation='vertical',
        padding=dp(15),
        spacing=dp(10),
        size_hint=(1, 1)
    )

    # Label с сообщением: белый цвет, по центру
    message_label = Label(
        text=message,
        size_hint=(1, 1),
        # Используем dp для размера шрифта для лучшей адаптации
        font_size=dp(18),
        color=(1, 1, 1, 1), # Чисто белый
        halign='center',
        valign='middle'
    )
    # Чтобы текст правильно оборачивался и центрировался внутри Label:
    # связываем text_size с размером самой метки
    message_label.bind(size=lambda instance, value: setattr(instance, 'text_size', (value[0], None)))
    # Или более явно:
    # message_label.bind(size=message_label.setter('text_size'))
    content.add_widget(message_label)

    # Кнопка «Закрыть» внизу
    close_button = Button(
        text="Закрыть",
        size_hint_y=None,
        height=dp(50),
        background_color=get_color_from_hex("#4CAF50"), # Зеленоватый цвет по умолчанию
        background_normal='',
        color=(1, 1, 1, 1),
        font_size=dp(16),
        bold=True
    )
    content.add_widget(close_button)

    # --- Определение размера Popup ---
    from kivy.core.window import Window
    # Размер popup: максимум 90% ширины и 70% высоты экрана, но с ограничениями
    popup_width = min(dp(500), Window.width * 0.9)
    popup_height = min(dp(600), Window.height * 0.7)

    # Создаём само окно. Фон сделаем тёмным, чтобы белый текст был хорошо виден.
    popup = Popup(
        title=title,
        title_size=dp(18),
        title_align='center',
        title_color=get_color_from_hex("#FFFFFF"), # Белый заголовок
        content=content,

        separator_color=get_color_from_hex("#FFFFFF"), # Белая линия под заголовком
        separator_height=dp(1),

        size_hint=(None, None),
        size=(popup_width, popup_height),

        background_color=(0.15, 0.15, 0.15, 1), # тёмно-серый фон (чтобы белый текст читался)
        overlay_color=(0, 0, 0, 0.5), # Полупрозрачный чёрный оверлей

        auto_dismiss=False # Запрещаем закрытие кликом вне окна
    )

    # --- Обработчик изменения размера окна ---
    # (если пользователь повернёт экран или сменит размер)
    def update_size(*args):
        new_w = min(dp(500), Window.width * 0.9)
        new_h = min(dp(600), Window.height * 0.7)
        popup.size = (new_w, new_h)
        # Центрируем окно после изменения размера
        popup.pos_hint = {'center_x': 0.5, 'center_y': 0.5}

    # Привязываем обработчик к событию изменения размера окна
    from kivy.core.window import Window
    Window.bind(on_resize=update_size)
    # Отвязываем обработчик при закрытии popup, чтобы избежать утечек памяти
    popup.bind(on_dismiss=lambda *x: Window.unbind(on_resize=update_size))

    # --- Привязываем действие к кнопке закрытия ---
    close_button.bind(on_release=popup.dismiss)

    # --- Открываем popup ---
    popup.open()
