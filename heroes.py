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
    Теперь включает image_url и координаты pos_x, pos_y.
    Возвращает словарь, где ключ - slot_type, а значение - словарь с 'id', 'image_url', 'pos_x', 'pos_y'.
    Если координаты NULL, они будут None.
    """
    equipment = {}
    try:
        cursor = faction.conn.cursor()
        # Добавлены pos_x, pos_y в SELECT
        cursor.execute('''
            SELECT slot_type, artifact_id, image_url, pos_x, pos_y
            FROM hero_equipment
            WHERE faction_name = ?
        ''', (faction.faction,))
        rows = cursor.fetchall()
        for slot_type, artifact_id, image_url, pos_x, pos_y in rows:
            # Сохраняем всю информацию, включая координаты (даже если они None)
            equipment[slot_type] = {
                "id": artifact_id,
                "image_url": image_url,
                "pos_x": pos_x, # Может быть None
                "pos_y": pos_y  # Может быть None
            }
    except sqlite3.Error as e:
        print(f"Ошибка при загрузке экипировки героя: {e}")
    print(f"[DEBUG] load_hero_equipment_from_db: Загружена экипировка для {faction.faction}: {equipment}")
    return equipment

def save_hero_equipment_to_db(faction, slot_type, artifact_id, pos_x=None, pos_y=None):
    """
    Обновляет экипировку героя в БД, устанавливая artifact_id, image_url и координаты для заданного слота.
    """
    try:
        cursor = faction.conn.cursor()
        # Получаем image_url для артефакта
        cursor.execute("SELECT image_url FROM artifacts WHERE id = ?", (artifact_id,))
        row = cursor.fetchone()
        image_url = row[0] if row and row[0] else "files/pict/artifacts/default.png"
        # Обновляем запись, включая координаты
        cursor.execute('''
            UPDATE hero_equipment 
            SET artifact_id = ?, image_url = ?, pos_x = ?, pos_y = ?
            WHERE faction_name = ? AND slot_type = ?
        ''', (artifact_id, image_url, pos_x, pos_y, faction.faction, slot_type)) # Добавлены pos_x, pos_y
        faction.conn.commit()
        print(f"[DEBUG] save_hero_equipment_to_db: Экипировка обновлена для {faction.faction}, слот {slot_type}, артефакт {artifact_id}, позиция ({pos_x}, {pos_y})")
    except sqlite3.Error as e:
        print(f"[ERROR] save_hero_equipment_to_db: Ошибка при обновлении экипировки героя: {e}")
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
        'health': 'Здоровье'
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
        from kivy.graphics import Color, RoundedRectangle
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
            from kivy.graphics import Color, RoundedRectangle
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

# --- Основная функция сборки и построения интерфейса артефактов---


def open_artifacts_popup(faction):
    """
    Открывает Popup с артефактами и экипировкой героя.
    :param faction: Экземпляр класса Faction
    """
    from kivy.metrics import dp
    from kivy.utils import platform

    # Проверяем, запущено ли приложение на Android
    is_android = platform == 'android'

    # Адаптируем размеры под мобильные устройства
    if is_android:
        artifact_row_height = dp(70)
        button_width = dp(70)
        button_height = dp(50)
        font_size_large = '14sp'
        font_size_medium = '12sp'
        font_size_small = '11sp'
        filter_height = dp(100)
        filter_spacing = dp(3)
        slot_size = (dp(70), dp(70))
        name_label_height = dp(15)
        offset = dp(10)
        padding_small = dp(5)
        padding_medium = dp(10)
        spacing_small = dp(5)
        spacing_medium = dp(10)
    else:
        artifact_row_height = dp(90)
        button_width = dp(90)
        button_height = dp(60)
        font_size_large = '16sp'
        font_size_medium = '14sp'
        font_size_small = '14sp'
        filter_height = dp(120)
        filter_spacing = dp(5)
        slot_size = (dp(90), dp(90))
        name_label_height = dp(20)
        offset = dp(20)
        padding_small = dp(5)
        padding_medium = dp(10)
        spacing_small = dp(5)
        spacing_medium = dp(10)

    artifacts_list = load_artifacts_from_db(faction)
    hero_equipment = load_hero_equipment_from_db(faction)
    hero_image_path = load_hero_image_from_db(faction)
    popup_layout = BoxLayout(orientation='horizontal', padding=padding_small if is_android else padding_medium,
                             spacing=spacing_small if is_android else spacing_medium)
    left_panel = BoxLayout(orientation='vertical', size_hint=(0.5, 1))
    filters_container = BoxLayout(orientation='vertical', size_hint_y=None,
                                  height=filter_height, spacing=filter_spacing)

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
            if season_ok and type_ok:
                filtered_artifacts.append(artifact)
        if filter_states['cost_sort'] == 'asc':
            filtered_artifacts.sort(key=lambda art: art.get('cost', 0))
        elif filter_states['cost_sort'] == 'desc':
            filtered_artifacts.sort(key=lambda art: art.get('cost', 0), reverse=True)
        for artifact in filtered_artifacts:
            description = format_artifact_description(artifact)
            if not description:
                continue
            artifact_row_container = BoxLayout(orientation='horizontal', size_hint_y=None,
                                               height=artifact_row_height,
                                               padding=(dp(3) if is_android else dp(5),
                                                        dp(3) if is_android else dp(5)),
                                               spacing=dp(5) if is_android else dp(10))

            artifact_info_container = BoxLayout(orientation='vertical', size_hint_x=0.75)
            name_label = Label(text=artifact['name'], halign='left', valign='middle',
                               font_size=font_size_large, bold=True,
                               size_hint_y=None, height=dp(20) if is_android else dp(25),
                               color=(1, 1, 0.6, 1))
            name_label.bind(size=name_label.setter('text_size'))
            stats_label = Label(text=description, halign='left', valign='top',
                                font_size=font_size_medium if is_android else font_size_medium,
                                bold=True,
                                color=(0.9, 0.9, 0.9, 1), size_hint_y=None,
                                height=dp(40) if is_android else dp(50))
            stats_label.bind(size=stats_label.setter('text_size'))
            artifact_info_container.add_widget(name_label)
            artifact_info_container.add_widget(stats_label)
            cost = artifact.get('cost', 0)
            formatted_cost = format_number(cost)
            buy_button = Button(
                text=f"Купить\n({formatted_cost})",
                size_hint_x=None,
                width=button_width,
                height=button_height,
                font_size=font_size_small if is_android else font_size_medium,
                bold=True
            )
            style_rounded_button(buy_button, bg_color=(0.2, 0.7, 0.3, 1),
                                 radius=dp(6) if is_android else dp(8),
                                 has_shadow=True)

            def make_buy_handler(art_data):
                def on_buy(instance):
                    if 'fraction_instance' not in locals() and 'fraction_instance' not in globals():
                        pass
                    current_fraction_instance = faction

                    print(f"[DEBUG] Покупка артефакта: {art_data['name']} (ID: {art_data['id']}, Тип: {art_data['artifact_type']})")

                    try:
                        check_cursor = current_fraction_instance.conn.cursor()
                        check_cursor.execute(
                            "SELECT COUNT(*) FROM hero_equipment WHERE faction_name = ?",
                            (current_fraction_instance.faction,)
                        )
                        hero_count = check_cursor.fetchone()[0]
                        if hero_count == 0:
                            print("[INFO] Попытка покупки артефакта без нанятого героя.")
                            show_popup_message("Ошибка", "Герой еще не нанят, покупать артефакт некому!")
                            return
                    except sqlite3.Error as e:
                        print(f"[ERROR] Ошибка при проверке наличия героя: {e}")
                        show_popup_message("Ошибка", "Ошибка проверки данных героя.")
                        return

                    artifact_type_to_slot = {
                        0: '0',
                        1: '1',
                        2: '2',
                        3: '3',
                        4: '4'
                    }
                    slot_type = artifact_type_to_slot.get(art_data['artifact_type'])

                    if slot_type is None:
                        print(f"[ERROR] Неизвестный тип артефакта: {art_data['artifact_type']}")
                        show_popup_message("Ошибка", "Невозможно экипировать этот артефакт.")
                        return

                    print(f"[DEBUG] Целевой слот: {slot_type}")

                    artifact_entry = hero_equipment.get(slot_type)
                    current_artifact_id_in_slot = None
                    if isinstance(artifact_entry, dict):
                        current_artifact_id_in_slot = artifact_entry.get('id')
                    print(f"[DEBUG] Текущий артефакт в слоте {slot_type}: {current_artifact_id_in_slot}")

                    def deduct_coins_local(fraction_obj, amount):
                        try:
                            current_money = getattr(fraction_obj, 'money', 0)
                            print(f"[DEBUG] [deduct_coins_local] Текущие монеты: {current_money}, Списание: {amount}")
                            if current_money >= amount:
                                new_amount = current_money - amount
                                fraction_obj.update_resource_now('Кроны', new_amount)
                                print(f"[DEBUG] [deduct_coins_local] Новые монеты: {new_amount}")
                                return True
                            else:
                                print(f"[INFO] [deduct_coins_local] Недостаточно крон. Нужно: {amount}, Есть: {current_money}")
                                return False
                        except Exception as e:
                            print(f"[ERROR] [deduct_coins_local] Ошибка при списании: {e}")
                            import traceback
                            traceback.print_exc()
                            return False

                    def add_coins_local(fraction_obj, amount):
                        try:
                            current_money = getattr(fraction_obj, 'money', 0)
                            print(f"[DEBUG] [add_coins_local] Текущие кроны: {current_money}, Начисление: {amount}")
                            new_amount = current_money + amount
                            fraction_obj.update_resource_now('Кроны', new_amount)
                            print(f"[DEBUG] [add_coins_local] Новые кроны: {new_amount}")
                            return True
                        except Exception as e:
                            print(f"[ERROR] [add_coins_local] Ошибка при начислении: {e}")
                            import traceback
                            traceback.print_exc()
                            return False

                    try:
                        artifact_cost = art_data['cost']
                        print(f"[DEBUG] Цена нового артефакта: {artifact_cost}")

                        if current_artifact_id_in_slot is None:
                            print("[DEBUG] Слот пуст. Покупаем новый артефакт.")
                            if deduct_coins_local(current_fraction_instance, artifact_cost):
                                hero_equipment[slot_type] = {
                                    "id": art_data['id'],
                                    "image_url": art_data.get('image_url'),
                                    "pos_x": None,
                                    "pos_y": None
                                }
                                update_equipment_slot_visual(slot_type, hero_equipment[slot_type])
                                save_hero_equipment_to_db(current_fraction_instance, slot_type, art_data['id'], None, None)
                                print(f"[SUCCESS] Артефакт {art_data['name']} куплен и экипирован в слот {slot_type}.")
                                show_popup_message("Успех", f"Артефакт {art_data['name']} куплен!")
                                update_hero_stats_display()
                            else:
                                print("[INFO] Недостаточно монет для покупки.")
                                show_popup_message("Ошибка", "Недостаточно Крон!")

                        else:
                            print(f"[DEBUG] Слот {slot_type} занят. Запрашиваем подтверждение замены.")

                            old_artifact_data = None
                            try:
                                cursor = current_fraction_instance.conn.cursor()
                                cursor.execute("SELECT * FROM artifacts WHERE id = ?", (current_artifact_id_in_slot,))
                                old_artifact_row = cursor.fetchone()
                                if old_artifact_row:
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
                                print(f"[WARNING] Данные старого артефакта (ID: {current_artifact_id_in_slot}) не найдены. Заменяем без возврата.")
                                old_artifact_cost = 0
                            else:
                                old_artifact_cost = old_artifact_data.get('cost', 0)

                            sell_price = int(old_artifact_cost * 0.65)
                            net_cost = artifact_cost - sell_price
                            print(f"[DEBUG] Цена старого артефакта: {old_artifact_cost}, Цена продажи: {sell_price}, Чистая стоимость: {net_cost}")

                            def confirm_replace(instance):
                                confirm_popup.dismiss()
                                if deduct_coins_local(current_fraction_instance, net_cost):
                                    if sell_price > 0:
                                        add_coins_local(current_fraction_instance, sell_price)
                                        print(f"[DEBUG] Вернули {sell_price} монет за старый артефакт.")
                                    save_hero_equipment_to_db(current_fraction_instance, slot_type, art_data['id'], None, None)
                                    hero_equipment[slot_type] = {
                                        "id": art_data['id'],
                                        "image_url": art_data.get('image_url'),
                                        "pos_x": None,
                                        "pos_y": None
                                    }

                                    update_equipment_slot_visual(slot_type, hero_equipment[slot_type])

                                    print(f"[SUCCESS] Артефакт {art_data['name']} куплен и экипирован в слот {slot_type} (старый заменен).")
                                    show_popup_message("Успех", f"Артефакт {art_data['name']} куплен! Старый артефакт продан.")
                                    update_hero_stats_display()
                                else:
                                    print("[INFO] Недостаточно монет для замены.")
                                    show_popup_message("Ошибка", "Недостаточно Крон для замены!")

                            def cancel_replace(instance):
                                confirm_popup.dismiss()
                                print("[INFO] Замена артефакта отменена пользователем.")

                            content = BoxLayout(orientation='vertical', padding=5 if is_android else 10,
                                                spacing=5 if is_android else 10)
                            old_art_name = old_artifact_data.get('name', 'Неизвестный артефакт') if old_artifact_data else 'Неизвестный артефакт'
                            message = (f"Заменить артефакт '{old_art_name}'\n"
                                       f"на '{art_data['name']}'?\n"
                                       f"Цена нового: {format_number(artifact_cost)}\n"
                                       f"Вы получите за старый: {format_number(sell_price)}\n"
                                       f"К оплате: {format_number(net_cost)}")
                            message_label = Label(text=message, text_size=(None, None), halign='center',
                                                  font_size=font_size_small if is_android else '15sp')
                            message_label.bind(
                                size=lambda instance, value: setattr(instance, 'text_size', (value[0] * 0.9, None)))
                            content.add_widget(message_label)

                            btn_layout = BoxLayout(size_hint_y=None, height=dp(40) if is_android else dp(50),
                                                   spacing=dp(5) if is_android else dp(10))
                            btn_yes = Button(text="Да", background_color=(0.4, 0.7, 0.4, 1),
                                             font_size=font_size_small if is_android else '15sp')
                            btn_no = Button(text="Нет", background_color=(0.7, 0.4, 0.4, 1),
                                            font_size=font_size_small if is_android else '15sp')
                            btn_yes.bind(on_release=confirm_replace)
                            btn_no.bind(on_release=cancel_replace)
                            btn_layout.add_widget(btn_yes)
                            btn_layout.add_widget(btn_no)
                            content.add_widget(btn_layout)

                            confirm_popup = Popup(title="Подтверждение замены",
                                                  content=content,
                                                  size_hint=(0.9 if is_android else 0.8, 0.7 if is_android else 0.6),
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
            button_wrapper = BoxLayout(size_hint_x=None, width=button_width,
                                       padding=(0, dp(10) if is_android else dp(15), 0, dp(10) if is_android else dp(15)))
            button_wrapper.add_widget(buy_button)
            artifact_row_container.add_widget(button_wrapper)
            artifacts_list_layout.add_widget(artifact_row_container)
        artifacts_list_layout.height = len(artifacts_list_layout.children) * artifact_row_height + (
                len(artifacts_list_layout.children) - 1) * (dp(3) if is_android else dp(5)) if artifacts_list_layout.children else dp(1)

    # Фильтры
    season_filter_layout = BoxLayout(orientation='horizontal', size_hint_y=None,
                                     height=dp(25) if is_android else dp(30))
    season_filter_layout.add_widget(Label(text="Сезон:", size_hint_x=None,
                                          width=dp(50) if is_android else dp(60), halign='left',
                                          font_size=font_size_small if is_android else '15sp'))
    season_spinner = Spinner(
        text='Все',
        values=('Все', 'Есть влияние', 'Нет влияния'),
        size_hint=(1, None),
        height=dp(25) if is_android else dp(30),
        font_size=font_size_small if is_android else '15sp'
    )
    style_rounded_spinner(season_spinner, bg_color=(0.3, 0.5, 0.7, 1),
                          text_color=(1, 1, 1, 1), radius=dp(4) if is_android else dp(6))

    def on_season_spinner_select(spinner, text):
        mapping = {'Все': 'all', 'Есть влияние': 'has_influence', 'Нет влияния': 'no_influence'}
        filter_states['season_influence'] = mapping.get(text, 'all')
        update_artifact_list()

    season_spinner.bind(text=on_season_spinner_select)
    season_filter_layout.add_widget(season_spinner)
    filters_container.add_widget(season_filter_layout)

    type_filter_layout = BoxLayout(orientation='horizontal', size_hint_y=None,
                                   height=dp(25) if is_android else dp(30))
    type_filter_layout.add_widget(Label(text="Тип:", size_hint_x=None,
                                        width=dp(50) if is_android else dp(60), halign='left',
                                        font_size=font_size_small if is_android else '15sp'))
    type_spinner = Spinner(
        text='Все',
        values=('Все', 'Оружие', 'Сапоги', 'Туловище', 'Голова', 'Аксессуар'),
        size_hint=(1, None),
        height=dp(25) if is_android else dp(30),
        font_size=font_size_small if is_android else '15sp'
    )
    style_rounded_spinner(type_spinner, bg_color=(0.3, 0.5, 0.7, 1),
                          text_color=(1, 1, 1, 1), radius=dp(4) if is_android else dp(6))

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

    cost_filter_layout = BoxLayout(orientation='horizontal', size_hint_y=None,
                                   height=dp(25) if is_android else dp(30))
    cost_filter_layout.add_widget(Label(text="Цена:", size_hint_x=None,
                                        width=dp(50) if is_android else dp(60), halign='left',
                                        font_size=font_size_small if is_android else '15sp'))
    cost_spinner = Spinner(
        text='Все',
        values=('Все', 'По возрастанию', 'По убыванию'),
        size_hint=(1, None),
        height=dp(25) if is_android else dp(30),
        font_size=font_size_small if is_android else '15sp'
    )
    style_rounded_spinner(cost_spinner, bg_color=(0.3, 0.5, 0.7, 1),
                          text_color=(1, 1, 1, 1), radius=dp(4) if is_android else dp(6))

    def on_cost_spinner_select(spinner, text):
        mapping = {'Все': 'all', 'По возрастанию': 'asc', 'По убыванию': 'desc'}
        filter_states['cost_sort'] = mapping.get(text, 'all')
        update_artifact_list()

    cost_spinner.bind(text=on_cost_spinner_select)
    cost_filter_layout.add_widget(cost_spinner)
    filters_container.add_widget(cost_filter_layout)

    left_panel.add_widget(filters_container)
    left_panel.add_widget(Label(text="Артефакты", size_hint_y=None,
                                height=dp(30) if is_android else dp(40), bold=True,
                                font_size=font_size_large if is_android else '18sp'))
    scroll_view = ScrollView(do_scroll_x=False)
    artifacts_list_layout = BoxLayout(orientation='vertical', size_hint_y=None,
                                      spacing=dp(3) if is_android else dp(5))
    artifacts_list_layout.bind(minimum_height=artifacts_list_layout.setter('height'))
    scroll_view.add_widget(artifacts_list_layout)
    left_panel.add_widget(scroll_view)

    # Правая панель
    right_panel = FloatLayout(size_hint=(0.5, 1))
    hero_image_widget = None
    equipment_slots = {}
    slot_name_labels = {}

    def apply_slot_style(slot_widget):
        slot_widget.background_normal = ''
        slot_widget.background_color = (0, 0, 0, 0)

        if not hasattr(slot_widget, 'rect') or slot_widget.rect is None:
            with slot_widget.canvas.before:
                from kivy.graphics import Color, RoundedRectangle
                Color(0.4, 0.4, 0.4, 1)
                slot_widget.rect = RoundedRectangle(pos=slot_widget.pos, size=slot_widget.size,
                                                    radius=[dp(6) if is_android else dp(8)])

        def update_slot_rect(instance, value):
            if hasattr(instance, 'rect') and instance.rect is not None:
                instance.rect.pos = instance.pos
                instance.rect.size = instance.size
            else:
                with instance.canvas.before:
                    from kivy.graphics import Color, RoundedRectangle
                    Color(0.4, 0.4, 0.4, 1)
                    instance.rect = RoundedRectangle(pos=instance.pos, size=instance.size,
                                                     radius=[dp(6) if is_android else dp(8)])

        slot_widget.unbind(pos=update_slot_rect, size=update_slot_rect)
        slot_widget.bind(pos=update_slot_rect, size=update_slot_rect)

    if hero_image_path and os.path.exists(hero_image_path):
        try:
            hero_image_width = dp(200) if is_android else dp(300)
            hero_image_height = dp(200) if is_android else dp(300)
            hero_image_size = (hero_image_width, hero_image_height)

            hero_image_widget = Image(
                source=hero_image_path,
                size_hint=(None, None),
                size=hero_image_size
            )
            hero_image_widget.pos_hint = {'center_x': 0.5, 'center_y': 0.5}
            right_panel.add_widget(hero_image_widget)

            slot_types = ['0', '2', '3', '1', '4']
            for slot_type in slot_types:
                slot_widget = Button(
                    size_hint=(None, None),
                    size=slot_size,
                    background_normal='',
                    background_down='',
                    background_color=(1, 1, 1, 1)
                )

                apply_slot_style(slot_widget)
                right_panel.add_widget(slot_widget)
                equipment_slots[slot_type] = slot_widget
                name_label = Label(
                    text="",
                    size_hint=(None, None),
                    size=(slot_size[0], name_label_height),
                    font_size=font_size_small if is_android else '14sp',
                    halign='center',
                    color=(1, 1, 1, 1)
                )
                name_label.bind(size=name_label.setter('text_size'))
                name_label.text_size = (slot_size[0], None)
                slot_name_labels[slot_type] = name_label

            def initialize_equipment_visual(dt):
                print("[DEBUG] initialize_equipment_visual: Вызываем update_all_equipment_slots")
                update_all_equipment_slots()

            Clock.schedule_once(initialize_equipment_visual, 0.2)

        except Exception as e:
            print(f"Ошибка загрузки изображения героя {hero_image_path}: {e}")
            import traceback
            traceback.print_exc()
            hero_image_widget = None
            hero_placeholder = Label(
                text="[b]Ошибка загрузки\nизображения[/b]",
                markup=True,
                halign='center',
                valign='middle',
                font_size=font_size_medium if is_android else '16sp'
            )
            hero_placeholder.pos_hint = {'center_x': 0.5, 'center_y': 0.5}
            right_panel.add_widget(hero_placeholder)

    else:
        no_hero_label = Label(
            text="[b]Герой не нанят[/b]\nНаймите героя\nдля доступа к экипировке",
            markup=True,
            halign='center',
            valign='middle',
            font_size=font_size_medium if is_android else '16sp'
        )
        no_hero_label.pos_hint = {'center_x': 0.5, 'center_y': 0.5}
        right_panel.add_widget(no_hero_label)
        hero_image_widget = None

    # Характеристики героя
    hero_stats_container = BoxLayout(
        orientation='vertical',
        size_hint=(1, None),
        height=dp(100) if is_android else dp(150),
        padding=dp(10) if is_android else dp(15),
        spacing=dp(15) if is_android else dp(25)
    )
    hero_stats_label = Label(
        text="",
        halign='right',
        valign='top',
        font_size=font_size_large if is_android else '27sp',
        bold=False,
        color=(1, 1, 1, 1),
        markup=True
    )
    hero_stats_label.bind(size=hero_stats_label.setter('text_size'))
    hero_stats_container.add_widget(hero_stats_label)
    hero_stats_container.pos_hint = {'x': -0.65 if is_android else -0.65, 'y': 0}
    right_panel.add_widget(hero_stats_container)
    hero_stats_widget = hero_stats_label

    def position_slots(dt):
        if not hero_image_widget:
            print("[DEBUG] position_slots: Герой отсутствует, позиционирование пропущено.")
            return

        if not right_panel or not hasattr(right_panel, 'width') or right_panel.width == 0:
            print("[DEBUG] position_slots: Размеры панели не готовы, повтор через 0.1с.")
            Clock.schedule_once(position_slots, 0.1)
            return

        panel_width = right_panel.width
        panel_height = right_panel.height
        panel_x = right_panel.x
        panel_y = right_panel.y

        center_x = panel_x + panel_width / 2
        center_y = panel_y + panel_height / 2

        hero_width, hero_height = hero_image_size
        slot_w, slot_h = slot_size

        half_hero_w = hero_width / 2
        half_hero_h = hero_height / 2
        half_slot_w = slot_w / 2
        half_slot_h = slot_h / 2

        # Позиции слотов (вокруг героя)
        slot_positions = {
            '0': (center_x - half_hero_w - slot_w - offset, center_y - half_slot_h),
            '3': (center_x + half_hero_w + offset, center_y - half_slot_h),
            '1': (center_x - half_slot_w, center_y + half_hero_h + offset),
            '2': (center_x - half_slot_w, center_y - half_hero_h - slot_h - offset),
            '4': (center_x + half_hero_w + offset, center_y + half_hero_h + offset),
        }

        print("[DEBUG] position_slots: Установка позиций слотов...")
        for slot_type, pos in slot_positions.items():
            if slot_type in slot_name_labels:
                name_label = slot_name_labels[slot_type]
                name_label.pos = (pos[0], pos[1] - (dp(20) if is_android else dp(25)))
                if name_label.parent is None:
                    right_panel.add_widget(name_label)
            if slot_type in equipment_slots:
                widget = equipment_slots[slot_type]
                widget.pos = pos
                print(f"[DEBUG] position_slots: Слот {slot_type} позиционирован в {pos}")

                artifact_entry = hero_equipment.get(slot_type)
                if isinstance(artifact_entry, dict) and artifact_entry.get('id'):
                    pos_x, pos_y = pos
                    hero_equipment[slot_type]['pos_x'] = pos_x
                    hero_equipment[slot_type]['pos_y'] = pos_y
                    save_hero_equipment_to_db(faction, slot_type, artifact_entry['id'], pos_x, pos_y)
                    print(f"[DEBUG] position_slots: Позиции для слота {slot_type} с артефактом {artifact_entry['id']} сохранены в БД: ({pos_x}, {pos_y})")

        print("[DEBUG] position_slots: Завершено.")

    def update_equipment_slot_visual(slot_type, artifact_data):
        slot_widget = equipment_slots.get(slot_type)
        name_label = slot_name_labels.get(slot_type)

        if not slot_widget:
            print(f"[WARNING] Слот типа {slot_type} не найден для обновления.")
            return

        if artifact_data and artifact_data.get('id'):
            full_artifact_data = artifact_data
            if 'name' not in artifact_data:
                artifact_id = artifact_data.get('id') or artifact_data.get('artifact_id')
                if artifact_id:
                    full_artifact_data = next((a for a in artifacts_list if a['id'] == artifact_id), None)

            image_url = full_artifact_data.get('image_url') if full_artifact_data else None
            artifact_name = full_artifact_data.get('name') if full_artifact_data else 'Без названия'

            if image_url:
                slot_widget.background_normal = image_url
                slot_widget.background_down = image_url
                slot_widget.background_color = (1, 1, 1, 1)
            else:
                slot_widget.background_normal = ''
                slot_widget.background_down = ''
                slot_widget.background_color = (0.4, 0.4, 0.4, 1)

            if name_label:
                name_label.text_size = (name_label.width, None)
                name_label.text = artifact_name[:15] + "..." if len(artifact_name) > 15 and is_android else artifact_name
                name_label.color = (1, 1, 1, 1)

            print(f"[DEBUG] update_equipment_slot_visual: Слот {slot_type} обновлен. Артефакт: {artifact_name}")
        else:
            slot_widget.background_normal = ''
            slot_widget.background_down = ''
            slot_widget.background_color = (0.4, 0.4, 0.4, 1)
            apply_slot_style(slot_widget)

            if name_label:
                name_label.text = ""

            print(f"[DEBUG] update_equipment_slot_visual: Слот {slot_type} очищен")

    def update_all_equipment_slots():
        print(f"[DEBUG] update_all_equipment_slots: Начало обновления. hero_equipment={ {k: v.get('id') for k, v in hero_equipment.items()} }")
        updated_slots = []
        for slot_type_key in ['0', '1', '2', '3', '4']:
            artifact_entry = hero_equipment.get(slot_type_key)

            if isinstance(artifact_entry, dict) and artifact_entry.get('id'):
                artifact_id = artifact_entry['id']
                full_artifact_data = next((a for a in artifacts_list if a['id'] == artifact_id), None)
                if full_artifact_data:
                    update_equipment_slot_visual(slot_type_key, full_artifact_data)
                    updated_slots.append(slot_type_key)
                else:
                    print(f"[WARNING] Артефакт ID {artifact_id} для слота {slot_type_key} не найден в artifacts_list.")
                    update_equipment_slot_visual(slot_type_key, artifact_entry)
                    updated_slots.append(slot_type_key)
            else:
                update_equipment_slot_visual(slot_type_key, None)
        print(f"[DEBUG] update_all_equipment_slots: Обновление завершено. Обновлены слоты: {updated_slots}")

    def update_hero_stats_display():
        if hero_stats_widget:
            try:
                hero_stats_data = load_hero_stats_from_db(faction)
                formatted_stats = format_hero_stats(hero_stats_data)
                hero_stats_widget.text = formatted_stats
                print(f"[DEBUG] update_hero_stats_display: Характеристики обновлены: {formatted_stats}")
            except Exception as e:
                print(f"Ошибка обновления характеристик героя: {e}")
                import traceback
                traceback.print_exc()
                hero_stats_widget.text = "Ошибка загрузки"

    popup_layout.add_widget(left_panel)
    popup_layout.add_widget(right_panel)

    artifacts_popup = Popup(
        title="Лавка артефактов",
        content=popup_layout,
        size_hint=(0.98 if is_android else 0.95, 0.98 if is_android else 0.95),
        title_align='center',
        separator_color=(0.5, 0.3, 0.7, 1),
        title_size=font_size_large if is_android else '20sp'
    )

    Clock.schedule_once(lambda dt: update_hero_stats_display(), 0)

    if hero_image_widget:
        print("[DEBUG] artifacts_popup: Привязка on_open для position_slots")
        artifacts_popup.bind(on_open=lambda *args: Clock.schedule_once(position_slots, 0.1))

    update_artifact_list()

    artifacts_popup.open()

# --- Конец open_artifacts_popup ---









