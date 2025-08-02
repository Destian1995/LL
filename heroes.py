from db_lerdon_connect import *
from kivy.uix.popup import Popup
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.scrollview import ScrollView
from kivy.uix.image import Image
from kivy.uix.floatlayout import FloatLayout
from kivy.graphics import Color, RoundedRectangle
from kivy.clock import Clock
from kivy.metrics import dp
import sqlite3

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
                   season_name, season_bonus_multiplier, image_url, cost
            FROM artifacts
            -- WHERE ... -- Добавить условия, если нужно
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
                "cost": row[12] if row[12] is not None else 0 # Добавлено поле cost
            }
            print(f'Загруженный артефакт:{artifact}')
            stats = [
                artifact['attack'], artifact['defense'], artifact['health'],
                artifact['army_consumption'], artifact['crystal_bonus'],
                artifact['coins_bonus'], artifact['workers_bonus']
            ]
            if any(stat != 0 for stat in stats):
                artifacts.append(artifact)
    except sqlite3.Error as e:
        print(f"Ошибка при загрузке артефактов: {e}")
    print(f'Данные артефактов на возврат из load_artifacts_from_db {artifacts}')
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
    Сохраняет/обновляет экипировку героя в БД.
    """
    try:
        cursor = faction.conn.cursor()
        if artifact_id is None:
            # Удаление записи, если artifact_id None
            cursor.execute('''
                 DELETE FROM hero_equipment
                 WHERE faction_name = ? AND slot_type = ?
             ''', (faction.faction, slot_type))
        else:
            # Используем INSERT OR REPLACE для обновления или вставки
            cursor.execute('''
                INSERT OR REPLACE INTO hero_equipment (faction_name, slot_type, artifact_id)
                VALUES (?, ?, ?)
            ''', (faction.faction, slot_type, artifact_id))
        faction.conn.commit()
    except sqlite3.Error as e:
        print(f"Ошибка при сохранении экипировки героя: {e}")
        faction.conn.rollback()

def load_hero_image_from_db(faction):
    """
    Загружает изображение героя из таблицы garrisons.
    """
    try:
        cursor = faction.conn.cursor()
        cursor.execute('''
            SELECT image_path FROM garrisons
            WHERE faction = ? AND unit_name IN (?, 'Герой')
            LIMIT 1
        ''', (faction.faction, faction.faction))
        row = cursor.fetchone()
        if row and row[0]:
            return row[0]
        else:
            return "files/pict/garrisons/default_hero.png"
    except sqlite3.Error as e:
        print(f"Ошибка при загрузке изображения героя: {e}")
        return "files/pict/garrisons/default_hero.png"

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
                stats.append(f"{label} +{effective_value}%")
            else:
                stats.append(f"{label} +{value}%")

    if not stats:
        return None  # Пропустить артефакт, если все характеристики нулевые

    # Формируем суффикс для времени действия бонуса
    season = artifact.get('season_name')
    if season:
        suffix = f"во время {season}"
    else:
        suffix = "всегда"

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

# --- Основная функция открытия попапа ---

def open_artifacts_popup(faction):
    """
    Открывает Popup с артефактами и экипировкой героя.
    :param faction: Экземпляр класса Faction
    """
    # --- Загрузка данных ---
    artifacts_list = load_artifacts_from_db(faction)
    hero_equipment = load_hero_equipment_from_db(faction)
    hero_image_path = load_hero_image_from_db(faction)

    # --- Создание Popup ---
    popup_layout = BoxLayout(orientation='horizontal', padding=dp(10), spacing=dp(10))

    # --- Левая часть: Список артефактов (улучшенная вертикальная таблица) ---
    left_panel = BoxLayout(orientation='vertical', size_hint=(0.5, 1))  # Немного увеличил ширину
    left_panel.add_widget(Label(text="Артефакты", size_hint_y=None, height=dp(40), bold=True, font_size='18sp'))
    scroll_view = ScrollView(do_scroll_x=False)
    artifacts_list_layout = BoxLayout(orientation='vertical', size_hint_y=None, spacing=dp(2))
    artifacts_list_layout.bind(minimum_height=artifacts_list_layout.setter('height'))

    # --- Создание виджетов для артефактов ---
    artifact_widgets = {}
    selected_artifact_id = None

    def on_artifact_selected(artifact_data):
        """Обработчик выбора артефакта из списка."""
        nonlocal selected_artifact_id
        selected_artifact_id = artifact_data['id']
        print(f"Выбран артефакт: {artifact_data['name']} (ID: {artifact_data['id']})")

    # --- Заголовок таблицы ---
    # Создаем фиксированную ширину для панели заголовков
    header_width_container = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(30), spacing=dp(1))

    # Фиксированные ширины для колонок (в dp)
    NAME_COL_WIDTH_DP = 150
    STATS_COL_WIDTH_DP = 300
    COST_COL_WIDTH_DP = 70

    header_name = Label(
        text="Имя",
        halign='left',
        valign='middle',
        font_size='12sp',
        bold=True,
        size_hint_x=None,  # Отключаем size_hint_x
        width=dp(NAME_COL_WIDTH_DP)  # Устанавливаем фиксированную ширину
    )
    header_name.bind(size=header_name.setter('text_size'))  # Для текста внутри

    header_stats = Label(
        text="Характеристики",
        halign='left',
        valign='middle',
        font_size='12sp',
        bold=True,
        size_hint_x=None,
        width=dp(STATS_COL_WIDTH_DP)
    )
    header_stats.bind(size=header_stats.setter('text_size'))

    header_cost = Label(
        text="Стоимость",
        halign='right',  # Выравнивание текста внутри ячейки
        valign='middle',
        font_size='12sp',
        bold=True,
        size_hint_x=None,
        width=dp(COST_COL_WIDTH_DP)
    )
    header_cost.bind(size=header_cost.setter('text_size'))

    header_width_container.add_widget(header_name)
    header_width_container.add_widget(header_stats)
    header_width_container.add_widget(header_cost)
    artifacts_list_layout.add_widget(header_width_container)  # Добавляем контейнер с фикс. ширинами

    # --- Заполнение таблицы артефактами ---
    for artifact in artifacts_list:
        description = format_artifact_description(artifact)
        if not description:  # Пропустить, если описание пустое (все бонусы 0)
            continue

        # Создаем контейнер строки с фиксированными ширинами колонок
        artifact_row_container = BoxLayout(
            orientation='horizontal',
            size_hint_y=None,  # Отключаем size_hint_y
            spacing=dp(4),  # Уменьшил отступы между ячейками
            padding=(dp(5), dp(5))  # Добавляем внутренний отступ
        )

        # --- Ячейки строки с фиксированной шириной ---
        name_cell = BoxLayout(size_hint_x=None, width=dp(NAME_COL_WIDTH_DP))
        stats_cell = BoxLayout(size_hint_x=None, width=dp(STATS_COL_WIDTH_DP))
        cost_cell = BoxLayout(size_hint_x=None, width=dp(COST_COL_WIDTH_DP))

        # --- Содержимое ячеек ---
        # Название артефакта
        name_label = Label(
            text=artifact['name'],
            halign='left',
            valign='top',  # Верхнее выравнивание текста
            font_size='14sp',
            size_hint_y=None,  # Отключаем size_hint_y
            height=dp(60)  # Фиксированная высота для имени
        )
        name_label.bind(size=name_label.setter('text_size'))
        name_cell.add_widget(name_label)

        # Характеристики артефакта
        stats_label = Label(
            text=description,
            halign='left',
            valign='top',  # Верхнее выравнивание текста
            font_size='12sp',
            color=(0.8, 0.8, 0.8, 1),  # Светло-серый цвет для бонусов
            size_hint_y=None,  # Отключаем size_hint_y
            height=dp(60)  # Фиксированная высота для характеристик
        )
        stats_label.bind(size=stats_label.setter('text_size'))
        stats_cell.add_widget(stats_label)

        # Стоимость артефакта
        cost_label = Label(
            text=str(artifact.get('cost', 0)),
            halign='right',  # Выравнивание текста внутри ячейки
            valign='top',  # Верхнее выравнивание текста
            font_size='14sp',
            size_hint_y=None,  # Отключаем size_hint_y
            height=dp(60)  # Фиксированная высота для стоимости
        )
        cost_label.bind(size=cost_label.setter('text_size'))
        cost_cell.add_widget(cost_label)

        # --- Добавление ячеек в контейнер строки ---
        artifact_row_container.add_widget(name_cell)
        artifact_row_container.add_widget(stats_cell)
        artifact_row_container.add_widget(cost_cell)

        # --- Определение реальной высоты строки ---
        # Автоматически рассчитываем высоту строки на основе максимальной высоты ячеек
        max_height = max(name_label.height, stats_label.height, cost_label.height)
        artifact_row_container.height = max_height + dp(10)  # Добавляем небольшой отступ

        # --- Применение стиля к контейнеру строки ---
        artifact_row_container = create_artifact_button_style(artifact_row_container)

        # --- Сделать строку кликабельной ---
        artifact_button = Button(background_normal='', background_color=(0, 0, 0, 0), size_hint=(1, 1))
        artifact_button.add_widget(artifact_row_container)
        artifact_button.bind(on_release=lambda btn, a=artifact: on_artifact_selected(a))

        artifacts_list_layout.add_widget(artifact_button)
        artifact_widgets[artifact['id']] = artifact_button  # Сохраняем ссылку на виджет
    scroll_view.add_widget(artifacts_list_layout)
    left_panel.add_widget(scroll_view)

    # --- Правая часть: Герой и экипировка ---
    right_panel = FloatLayout(size_hint=(0.6, 1))

    try:
        hero_image = Image(source=hero_image_path, size_hint=(None, None), size=(dp(150), dp(150)))
        hero_image.pos_hint = {'center_x': 0.5, 'center_y': 0.5}
        right_panel.add_widget(hero_image)
    except Exception as e:
        print(f"Ошибка загрузки изображения героя {hero_image_path}: {e}")
        hero_placeholder = Label(text="[b]Изображение\nГероя[/b]", markup=True, halign='center', valign='middle')
        hero_placeholder.size_hint = (None, None)
        hero_placeholder.size = (dp(150), dp(150))
        hero_placeholder.center = (right_panel.center_x, right_panel.center_y)
        right_panel.add_widget(hero_placeholder)
        hero_image = hero_placeholder

    slot_size = (dp(50), dp(50))
    equipment_slots = {}

    def update_equipment_slot(slot_type, artifact_data=None):
        """Обновляет виджет слота экипировки."""
        if slot_type in equipment_slots:
            slot_widget = equipment_slots[slot_type]
            slot_widget.clear_widgets()
            if artifact_data:
                try:
                    img_source = artifact_data.get('image_url')
                    if not img_source:
                        img_source = "files/pict/artifacts/default.png"
                    slot_image = Image(source=img_source, allow_stretch=True, keep_ratio=True)
                    slot_widget.add_widget(slot_image)
                except Exception as e:
                    print(f"Ошибка загрузки изображения для слота {slot_type}: {e}")
                    slot_widget.add_widget(Label(text="?", font_size='20sp'))
            else:
                slot_widget.add_widget(Label(text=f"[{slot_type[:3].upper()}]", markup=True, font_size='10sp'))

    def on_equip_button_click(slot_type):
        """Обработчик нажатия на слот экипировки."""
        nonlocal selected_artifact_id
        if selected_artifact_id:
            print(f"Попытка экипировать артефакт ID {selected_artifact_id} в слот {slot_type}")
            save_hero_equipment_to_db(faction, slot_type, selected_artifact_id)
            hero_equipment[slot_type] = selected_artifact_id
            equipped_artifact = next((a for a in artifacts_list if a['id'] == selected_artifact_id), None)
            if equipped_artifact:
                update_equipment_slot(slot_type, equipped_artifact)
            selected_artifact_id = None  # Сбросить выбор после экипировки
        else:
            # Снятие экипировки
            if slot_type in hero_equipment:
                print(f"Снятие экипировки из слота {slot_type}")
                save_hero_equipment_to_db(faction, slot_type, None)
                hero_equipment.pop(slot_type, None)
                update_equipment_slot(slot_type, None)

    for slot_type in ['weapon', 'boots', 'armor', 'helmet', 'accessory']:
        slot_widget = Button(
            size_hint=(None, None),
            size=slot_size,
            pos=(0, 0),
            background_color=(0.3, 0.3, 0.3, 1),
            background_normal=''
        )
        with slot_widget.canvas.before:
            Color(0.4, 0.4, 0.4, 1)
            slot_widget.rect = RoundedRectangle(pos=slot_widget.pos, size=slot_widget.size, radius=[8])
        def update_slot_rect(instance, value):
            instance.rect.pos = instance.pos
            instance.rect.size = instance.size
        slot_widget.bind(pos=update_slot_rect, size=update_slot_rect)

        artifact_id_in_slot = hero_equipment.get(slot_type)
        artifact_data_in_slot = next((a for a in artifacts_list if a['id'] == artifact_id_in_slot),
                                     None) if artifact_id_in_slot else None
        update_equipment_slot(slot_type, artifact_data_in_slot)
        slot_widget.bind(on_release=lambda btn, s=slot_type: on_equip_button_click(s))
        right_panel.add_widget(slot_widget)
        equipment_slots[slot_type] = slot_widget

    # --- Сборка основного макета ---
    popup_layout.add_widget(left_panel)
    popup_layout.add_widget(right_panel)

    # --- Создание и открытие Popup ---
    artifacts_popup = Popup(
        title="Артефакты и Герой",
        content=popup_layout,
        size_hint=(0.95, 0.95),
        title_align='center',
        separator_color=(0.5, 0.3, 0.7, 1)
    )

    def position_slots(dt):
        """Позиционирует слоты экипировки относительно центра правой панели."""
        right_panel_width = right_panel.width
        right_panel_height = right_panel.height
        right_panel_x = right_panel.x
        right_panel_y = right_panel.y
        center_x = right_panel_x + right_panel_width / 2
        center_y = right_panel_y + right_panel_height / 2
        slot_positions = {
            'weapon': (center_x - dp(100) - slot_size[0]/2, center_y - slot_size[1]/2),
            'boots': (center_x - slot_size[0]/2, center_y - dp(100) - slot_size[1]/2),
            'armor': (center_x + dp(100) - slot_size[0]/2, center_y - slot_size[1]/2),
            'helmet': (center_x - slot_size[0]/2, center_y + dp(100) - slot_size[1]/2),
            'accessory': (center_x + dp(80) - slot_size[0]/2, center_y + dp(80) - slot_size[1]/2),
        }
        for slot_type, pos in slot_positions.items():
            if slot_type in equipment_slots:
                equipment_slots[slot_type].pos = pos

    Clock.schedule_once(position_slots, 0)
    artifacts_popup.bind(on_open=lambda *args: Clock.schedule_once(position_slots, 0.1))
    artifacts_popup.open()
