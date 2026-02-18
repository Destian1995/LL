from db_lerdon_connect import *
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.graphics import Color, RoundedRectangle
from kivy.metrics import dp, sp
from kivy.uix.popup import Popup
from kivy.uix.behaviors import ButtonBehavior
from kivy.core.window import Window
import sqlite3
import threading

from economic import format_number
# Глобальная блокировка для работы с БД
db_lock = threading.Lock()
from nobles import show_nobles_window
from diversion import show_diversion_window

translation_dict = {
    "Север": "arkadia",
    "Эльфы": "celestia",
    "Адепты": "eteria",
    "Вампиры": "giperion",
    "Элины": "halidon",
}

# Словарь для перевода названий файлов в русскоязычные названия фракций
faction_names = {
    "arkadia_in_city": "Север",
    "celestia_in_city": "Эльфы",
    "eteria_in_city": "Адепты",
    "giperion_in_city": "Вампиры",
    "halidon_in_city": "Элины"
}

faction_names_build = {
    "arkadia_buildings_city": "Север",
    "celestia_buildings_city": "Эльфы",
    "eteria_buildings_city": "Адепты",
    "giperion_buildings_city": "Вампиры",
    "halidon_buildings_city": "Элины"
}

def transform_filename(file_path):
    path_parts = file_path.split('/')
    for i, part in enumerate(path_parts):
        for ru_name, en_name in translation_dict.items():
            if ru_name in part:
                path_parts[i] = part.replace(ru_name, en_name)
    return '/'.join(path_parts)


reverse_translation_dict = {v: k for k, v in translation_dict.items()}

def all_factions(cursor):
    """
    Выгружает список активных фракций из таблицы diplomacies.
    Возвращает уникальный список фракций, у которых статус в relationship не равен "уничтожена".
    :param cursor: Курсор для работы с базой данных
    :return: Список активных фракций
    """
    try:
        # Запрос для получения всех уникальных фракций, кроме тех, что имеют статус "уничтожена"
        query = """
            SELECT DISTINCT faction 
            FROM (
                SELECT faction1 AS faction, relationship FROM diplomacies
                UNION
                SELECT faction2 AS faction, relationship FROM diplomacies
            ) AS all_factions
            WHERE relationship != 'уничтожена' AND faction != 'Мятежники'
        """
        cursor.execute(query)
        factions = [row[0] for row in cursor.fetchall()]
        return factions
    except sqlite3.Error as e:
        print(f"Ошибка при получении списка активных фракций: {e}")
        return []

# Функция для расчета базового размера шрифта
def calculate_font_size():
    """Рассчитывает базовый размер шрифта на основе высоты окна."""
    base_height = 720  # Базовая высота окна для нормального размера шрифта
    default_font_size = 16  # Базовый размер шрифта
    scale_factor = Window.height / base_height  # Коэффициент масштабирования
    return max(8, int(default_font_size * scale_factor))  # Минимальный размер шрифта — 8

def get_relation_level(conn, f1, f2):
    cursor = conn.cursor()
    cursor.execute("""
        SELECT relationship FROM relations 
        WHERE (faction1=? AND faction2=?) OR (faction1=? AND faction2=?)
    """, (f1, f2, f2, f1))
    row = cursor.fetchone()
    return int(row[0]) if row else 0


def calculate_coefficient(rel):
    rel = int(rel)
    if rel < 15:
        return 0
    if 15 <= rel < 25:
        return 0.1
    if 25 <= rel < 35:
        return 0.4
    if 35 <= rel < 54:
        return 0.95
    if 54 <= rel < 65:
        return 1.5
    if 65 <= rel < 75:
        return 2
    if 75 <= rel < 90:
        return 3.1
    if 90 <= rel <= 100:
        return 4
    return 0


# Класс для управления дипломатическими отношениями
class DiplomacyManager:
    def __init__(self, faction, db_connection, cursor):
        self.faction = faction
        self.db_connection = db_connection
        self.cursor = cursor

    def get_diplomatic_relations(self):
        """Получает дипломатические отношения текущей фракции с другими"""
        try:
            # Получаем все активные фракции кроме текущей и Мятежников
            query = """
                SELECT DISTINCT faction 
                FROM (
                    SELECT faction1 AS faction FROM diplomacies
                    UNION
                    SELECT faction2 AS faction FROM diplomacies
                ) AS all_factions
                WHERE faction != ? AND faction != 'Мятежники' AND faction IN (
                    SELECT faction1 FROM diplomacies WHERE relationship != 'уничтожена'
                    UNION
                    SELECT faction2 FROM diplomacies WHERE relationship != 'уничтожена'
                )
            """
            self.cursor.execute(query, (self.faction,))
            all_factions = [row[0] for row in self.cursor.fetchall()]

            relations = {}

            for other_faction in all_factions:
                # Получаем дипломатический статус из таблицы diplomacies
                self.cursor.execute("""
                    SELECT relationship FROM diplomacies 
                    WHERE (faction1 = ? AND faction2 = ?) OR (faction1 = ? AND faction2 = ?)
                """, (self.faction, other_faction, other_faction, self.faction))

                status_row = self.cursor.fetchone()
                diplomatic_status = status_row[0] if status_row else "нейтралитет"

                # Получаем уровень отношений из таблицы relations
                self.cursor.execute("""
                    SELECT relationship FROM relations 
                    WHERE (faction1 = ? AND faction2 = ?) OR (faction1 = ? AND faction2 = ?)
                """, (self.faction, other_faction, other_faction, self.faction))

                relation_row = self.cursor.fetchone()
                relation_level = int(relation_row[0]) if relation_row else 0

                relations[other_faction] = {
                    "status": diplomatic_status,
                    "level": relation_level,
                    "description": self.get_relation_description(relation_level),
                    "color": self.get_status_color(diplomatic_status)
                }

            return relations

        except sqlite3.Error as e:
            print(f"Ошибка при получении дипломатических отношений: {e}")
            return {}

    def get_relation_description(self, level):
        """Возвращает текстовое описание уровня отношений"""
        if level <= 10:
            return "Ненависть"
        elif level <= 25:
            return "Вражда"
        elif level <= 40:
            return "Неприязнь"
        elif level <= 55:
            return "Нейтралитет"
        elif level <= 70:
            return "Дружелюбие"
        elif level <= 85:
            return "Уважение"
        else:
            return "Союзничество"

    def get_status_color(self, status):
        """Возвращает цвет для статуса отношений"""
        colors = {
            "война": (1.0, 0.2, 0.2, 1),      # Красный
            "нейтралитет": (1.0, 1.0, 0.5, 1), # Желтый
            "союз": (0.2, 0.8, 0.2, 1),        # Зеленый
            "уничтожена": (0.5, 0.5, 0.5, 1)   # Серый
        }
        return colors.get(status, (1.0, 1.0, 1.0, 1))  # Белый по умолчанию

    def show_diplomatic_relations(self):
        """Показывает окно с дипломатическими отношениями"""
        relations = self.get_diplomatic_relations()

        if not relations:
            print(f"Нет данных о дипломатических отношениях для фракции {self.faction}.")
            return

        # Создаем контент для popup
        content = BoxLayout(orientation='vertical', spacing=dp(8), padding=dp(10))

        # Заголовок
        title_label = Label(
            text=f"Дипломатические отношения: {self.faction}",
            font_size='20sp',
            bold=True,
            color=(1, 1, 1, 1),
            halign='center',
            size_hint_y=None,
            height=dp(50)
        )
        content.add_widget(title_label)

        # Создаем таблицу
        table = GridLayout(
            cols=4,
            size_hint_y=None,
            spacing=dp(4),
            row_default_height=dp(45)
        )
        table.bind(minimum_height=table.setter('height'))

        # Заголовки таблицы
        headers = ["Фракция", "Статус", "Уровень", "Отношения"]
        for title in headers:
            table.add_widget(self.create_header(title))

        # Заполняем таблицу данными
        for other_faction, data in sorted(relations.items()):
            status = data["status"]
            level = data["level"]
            description = data["description"]
            status_color = data["color"]

            highlight = False  # Можно добавить подсветку для особых случаев

            # Создаем ячейки
            faction_label = self._create_cell(other_faction, highlight=highlight)

            # Статус с цветом
            status_label = Label(
                text=status,
                font_size='14sp',
                bold=True,
                color=status_color,
                halign='center',
                valign='middle',
                size_hint_y=None,
                height=dp(45),
                outline_color=(0, 0, 0, 1),
                outline_width=2
            )

            # Уровень отношений
            level_label = self._create_cell(str(level), highlight=highlight)

            # Описание отношений
            desc_label = Label(
                text=description,
                font_size='14sp',
                bold=False,
                color=(1, 1, 1, 1),
                halign='center',
                valign='middle',
                size_hint_y=None,
                height=dp(45)
            )

            table.add_widget(faction_label)
            table.add_widget(status_label)
            table.add_widget(level_label)
            table.add_widget(desc_label)

        # Добавляем таблицу в ScrollView
        scroll = ScrollView(
            size_hint=(1, 0.8),
            bar_width=dp(6),
            bar_color=(0.5, 0.5, 0.5, 0.6),
            scroll_type=['bars', 'content']
        )
        scroll.add_widget(table)
        content.add_widget(scroll)

        # Легенда статусов
        legend_layout = BoxLayout(
            orientation='horizontal',
            size_hint=(1, None),
            height=dp(40),
            spacing=dp(10)
        )

        # Кнопка закрытия
        close_button = Button(
            text="Закрыть",
            size_hint=(1, None),
            height=dp(50),
            font_size='18sp',
            background_color=(0.8, 0.2, 0.2, 1),
            color=(1, 1, 1, 1)
        )

        def close_popup(instance):
            if hasattr(self, 'popup'):
                self.popup.dismiss()

        close_button.bind(on_release=close_popup)
        content.add_widget(close_button)

        # Создаем и показываем popup
        self.popup = Popup(
            title="",
            content=content,
            size_hint=(0.85, 0.9),
            auto_dismiss=False,
            background_color=(0.1, 0.1, 0.2, 0.95)
        )
        self.popup.open()

    def create_header(self, text):
        """Создает заголовок таблицы с фоном через canvas"""
        label = Label(
            text=f"[b]{text}[/b]",
            markup=True,
            font_size='16sp',
            bold=True,
            color=(1, 1, 1, 1),
            halign='center',
            valign='middle',
            size_hint_y=None,
            height=dp(50),
            text_size=(None, None),
            outline_color=(0, 0, 0, 1),
            outline_width=2
        )

        # Добавляем фон через canvas
        with label.canvas.before:
            Color(0.2, 0.4, 0.6, 1)  # Темно-синий цвет фона
            label.bg = RoundedRectangle(
                pos=label.pos,
                size=label.size,
                radius=[dp(4)]
            )

        # Обновляем фон при изменении размера
        def update_bg(instance, value):
            instance.bg.pos = instance.pos
            instance.bg.size = instance.size

        label.bind(pos=update_bg, size=update_bg)
        label.bind(size=label.setter('text_size'))
        return label

    def _create_cell(self, text, highlight=False):
        """Создает ячейку таблицы"""
        if highlight:
            bg_color = (0.3, 0.5, 0.7, 0.3)  # Светло-синий фон для подсветки
            text_color = (1, 1, 0.5, 1)  # Желтый текст для подсветки
        else:
            bg_color = (0.1, 0.1, 0.1, 0.2)  # Темный фон для остальных
            text_color = (1, 1, 1, 1)  # Белый текст

        label = Label(
            text=text,
            font_size='14sp',
            bold=True if highlight else False,
            color=text_color,
            halign='center',
            valign='middle',
            size_hint_y=None,
            height=dp(45),
            text_size=(None, None)
        )

        # Добавляем фон
        with label.canvas.before:
            Color(*bg_color)
            label.background = RoundedRectangle(
                pos=label.pos,
                size=label.size,
                radius=[dp(4)]
            )

        # Обновляем фон при изменении размера
        def update_background(instance, value):
            instance.background.pos = instance.pos
            instance.background.size = instance.size

        label.bind(pos=update_background, size=update_background)
        label.bind(size=label.setter('text_size'))

        return label


# Кастомная кнопка с анимациями и эффектами
class StyledButton(ButtonBehavior, BoxLayout):
    def __init__(self, text, font_size, button_color, text_color, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        self.size_hint = (1, None)
        self.height = font_size * 3  # Высота кнопки зависит от размера шрифта
        self.padding = [font_size // 2, font_size // 4]  # Отступы внутри кнопки
        self.normal_color = button_color
        self.hover_color = [c * 0.9 for c in button_color]  # Темнее при наведении
        self.pressed_color = [c * 0.8 for c in button_color]  # Еще темнее при нажатии
        self.current_color = self.normal_color

        with self.canvas.before:
            Color(*self.current_color)
            self.rect = RoundedRectangle(size=self.size, pos=self.pos, radius=[font_size // 2])

        self.bind(pos=self.update_rect, size=self.update_rect)

        self.label = Label(
            text=text,
            font_size=font_size * 1.2,
            color=text_color,
            bold=True,
            halign='center',
            valign='middle'
        )
        self.label.bind(size=self.label.setter('text_size'))
        self.add_widget(self.label)

        self.bind(on_press=self.on_press_effect, on_release=self.on_release_effect)
        self.bind(on_touch_move=self.on_hover, on_touch_up=self.on_leave)

    def update_rect(self, *args):
        self.rect.pos = self.pos
        self.rect.size = self.size

    def on_press_effect(self, instance):
        """Эффект затемнения при нажатии"""
        anim = Animation(current_color=self.pressed_color, duration=0.1)
        anim.start(self)
        self.update_color()

    def on_release_effect(self, instance):
        """Возвращаем цвет после нажатия"""
        anim = Animation(current_color=self.normal_color, duration=0.1)
        anim.start(self)
        self.update_color()

    def on_hover(self, instance, touch):
        """Эффект при наведении"""
        if self.collide_point(*touch.pos):
            anim = Animation(current_color=self.hover_color, duration=0.1)
            anim.start(self)
            self.update_color()

    def on_leave(self, instance, touch):
        """Возвращаем цвет, если курсор ушел с кнопки"""
        if not self.collide_point(*touch.pos):
            anim = Animation(current_color=self.normal_color, duration=0.1)
            anim.start(self)
        self.update_color()

    def update_color(self):
        """Обновляет цвет фона"""
        self.canvas.before.clear()
        with self.canvas.before:
            Color(*self.current_color)
            self.rect = RoundedRectangle(size=self.size, pos=self.pos, radius=[self.height // 4])



def calculate_peace_army_points(conn, faction):
    """
    Вычисляет общую силу армии фракции с локальными бонусами:
    - Герои 2 и 3 класса усиливают ТОЛЬКО юнитов 1 класса из своего гарнизона
    - Бонусы не распространяются между городами
    """
    cursor = conn.cursor()

    try:
        # Получаем данные с привязкой к городу
        cursor.execute("""
            SELECT g.city_name, g.unit_name, g.unit_count, u.attack, u.defense, u.durability, u.unit_class 
            FROM garrisons g
            JOIN units u ON g.unit_name = u.unit_name
            WHERE u.faction = ?
        """, (faction,))
        units_data = cursor.fetchall()

        # Группируем юниты по городам
        cities_data = {}

        for row in units_data:
            city_name, unit_name, unit_count, attack, defense, durability, unit_class = row

            if city_name not in cities_data:
                cities_data[city_name] = {
                    "class_1": {"count": 0, "total_stats": 0},
                    "heroes": {"total_stats": 0},   # классы 2 и 3
                    "others": {"total_stats": 0}    # классы 4 и выше
                }

            stats_sum = attack + defense + durability

            if unit_class == "1":
                cities_data[city_name]["class_1"]["count"] += unit_count
                cities_data[city_name]["class_1"]["total_stats"] += stats_sum * unit_count
            elif unit_class in ("2", "3"):
                cities_data[city_name]["heroes"]["total_stats"] += stats_sum * unit_count
            else:
                cities_data[city_name]["others"]["total_stats"] += stats_sum * unit_count

        # Рассчитываем силу для каждого города отдельно
        total_strength = 0

        for city, data in cities_data.items():
            class_1_count = data["class_1"]["count"]
            base_stats = data["class_1"]["total_stats"]
            hero_bonus = data["heroes"]["total_stats"]
            others_stats = data["others"]["total_stats"]

            city_strength = 0

            # Бонусы героев применяются ТОЛЬКО к юнитам 1 класса в этом городе
            if class_1_count > 0:
                city_strength += base_stats + hero_bonus * class_1_count

            # Юниты 4+ класса добавляются без бонусов
            city_strength += others_stats

            total_strength += city_strength

        return total_strength

    except Exception as e:
        print(f"Ошибка при вычислении очков армии: {e}")
        return 0


def calculate_army_strength(conn):
    """Рассчитывает силу армий для каждой фракции с локальными бонусами по гарнизонам."""

    army_strength = {}

    try:
        cursor = conn.cursor()

        # Получаем все юниты с привязкой к городу
        cursor.execute("""
            SELECT g.city_name, g.unit_name, g.unit_count, u.faction, u.attack, u.defense, u.durability, u.unit_class 
            FROM garrisons g
            JOIN units u ON g.unit_name = u.unit_name
        """)
        garrison_data = cursor.fetchall()

        # Собираем данные по фракциям и городам
        factions_data = {}

        for row in garrison_data:
            city_name, unit_name, unit_count, faction, attack, defense, durability, unit_class = row

            if not faction:
                continue

            if faction not in factions_data:
                factions_data[faction] = {}

            if city_name not in factions_data[faction]:
                factions_data[faction][city_name] = {
                    "class_1": {"count": 0, "total_stats": 0},
                    "heroes": {"total_stats": 0},  # герои класса 2 и 3
                    "others": {"total_stats": 0}   # юниты класса 4 и выше
                }

            stats_sum = attack + defense + durability
            city_data = factions_data[faction][city_name]

            if unit_class == "1":
                city_data["class_1"]["count"] += unit_count
                city_data["class_1"]["total_stats"] += stats_sum * unit_count
            elif unit_class in ("2", "3"):
                city_data["heroes"]["total_stats"] += stats_sum * unit_count
            else:  # класс 4 и выше
                city_data["others"]["total_stats"] += stats_sum * unit_count

        # Рассчитываем силу для каждой фракции
        for faction, cities in factions_data.items():
            faction_strength = 0

            for city, data in cities.items():
                class_1_count = data["class_1"]["count"]
                base_stats = data["class_1"]["total_stats"]
                hero_bonus = data["heroes"]["total_stats"]
                others_stats = data["others"]["total_stats"]

                city_strength = 0

                # Локальное применение бонусов: только внутри города
                if class_1_count > 0:
                    city_strength += base_stats + hero_bonus * class_1_count

                city_strength += others_stats
                faction_strength += city_strength

            army_strength[faction] = faction_strength

    except Exception as e:
        print(f"Ошибка при работе с базой данных: {e}")
        return {}

    # Возвращаем два словаря: один с числовыми значениями, другой с отформатированными строками
    formatted_army_strength = {faction: format_number(strength) for faction, strength in army_strength.items()}
    return army_strength, formatted_army_strength

def create_army_rating_table(conn):
    """Создает таблицу с показателями силы: Мощь отряда героя и Общая мощь фракции."""

    # Получаем список всех активных фракций
    cursor = conn.cursor()
    cursor.execute("""
        SELECT DISTINCT faction 
        FROM (
            SELECT faction1 AS faction FROM diplomacies
            UNION
            SELECT faction2 AS faction FROM diplomacies
        ) AS all_factions
        WHERE faction != 'Мятежники' AND faction IN (
            SELECT faction1 FROM diplomacies WHERE relationship != 'уничтожена'
            UNION
            SELECT faction2 FROM diplomacies WHERE relationship != 'уничтожена'
        )
    """)
    all_factions = [row[0] for row in cursor.fetchall()]

    if not all_factions:
        return GridLayout()

    # === Расчёт двух показателей для каждой фракции ===
    faction_ratings = []

    for faction in all_factions:
        # Могущество (локальные бонусы)
        local_power = calculate_peace_army_points(conn, faction)

        # Общая мощь (глобальные бонусы)
        global_power = calculate_total_faction_power(conn, faction)

        faction_ratings.append({
            "faction": faction,
            "local_power": local_power,
            "global_power": global_power
        })

    # Сортируем по общей мощи (убывание) — рейтинг как таковой больше не нужен
    faction_ratings.sort(key=lambda x: x["global_power"], reverse=True)

    # === Создаём таблицу ===
    # ИЗМЕНЕНО: cols=3 вместо 4, так как убрали колонку с процентами
    layout = GridLayout(
        cols=3,
        size_hint_y=None,
        spacing=dp(10),
        padding=[dp(10), dp(5), dp(10), dp(5)],
        row_default_height=dp(50),
        row_force_default=True
    )
    layout.bind(minimum_height=layout.setter('height'))

    # Цвета
    header_color = (0.1, 0.5, 0.9, 1)
    row_colors = [
        (1, 1, 1, 1), (0.8, 0.9, 1, 1), (0.6, 0.8, 1, 1),
        (0.4, 0.7, 1, 1), (0.2, 0.6, 1, 1)
    ]

    def create_label(text, color, halign="left", valign="middle", bold=False, font_size=14):
        lbl = Label(
            text=text,
            color=(0, 0, 0, 1),
            font_size=sp(font_size),
            size_hint_y=None,
            height=dp(50),
            halign=halign,
            valign=valign,
            bold=bold
        )
        lbl.bind(size=lbl.setter('text_size'))
        with lbl.canvas.before:
            Color(*color)
            lbl.rect = RoundedRectangle(pos=lbl.pos, size=lbl.size, radius=[dp(8)])
        lbl.bind(
            pos=lambda _, value: setattr(lbl.rect, 'pos', value),
            size=lambda _, value: setattr(lbl.rect, 'size', value)
        )
        return lbl

    # === Заголовки таблицы (3 колонки) ===
    layout.add_widget(create_label("Раса", header_color, halign="center", bold=True))
    layout.add_widget(create_label("Мощь отряда героя", header_color, halign="center", bold=True, font_size=12))
    layout.add_widget(create_label("Общая мощь фракции", header_color, halign="center", bold=True, font_size=12))

    # === Заполнение данными ===
    for rank, data in enumerate(faction_ratings):
        faction = data["faction"]
        local = data["local_power"]
        global_p = data["global_power"]

        # УДАЛЕНО: расчет rating = (global_p / max_power) * 100

        faction_name = faction_names.get(faction, faction)
        color = row_colors[rank % len(row_colors)]

        # Ячейки строки (теперь добавляем только 3 виджета)
        layout.add_widget(create_label(f"  {faction_name}", color, halign="left"))
        # УДАЛЕНО: layout.add_widget(create_label(f"{rating:.1f}%", ...))
        layout.add_widget(create_label(format_number(int(local)), color, halign="right", font_size=12))
        layout.add_widget(create_label(format_number(int(global_p)), color, halign="right", bold=True, font_size=13))

    return layout

def calculate_total_faction_power(conn, faction):
    """
    Вычисляет ОБЩУЮ мощь фракции с ГЛОБАЛЬНЫМИ бонусами:
    - Главный герой фракции (класс 3, или класс 2 если нет класса 3)
      усиливает ВСЕХ юнитов 1-го класса во ВСЕХ гарнизонах фракции
    """
    cursor = conn.cursor()

    try:
        # === ШАГ 1: Находим главного героя фракции ===
        # Приоритет: класс 3 > класс 2 > первый попавшийся герой
        cursor.execute("""
            SELECT u.attack, u.defense, u.durability, u.unit_class
            FROM garrisons g
            JOIN units u ON g.unit_name = u.unit_name
            WHERE u.faction = ? AND u.unit_class IN ('2', '3')
            ORDER BY 
                CASE u.unit_class WHEN '3' THEN 0 WHEN '2' THEN 1 END,
                (u.attack + u.defense + u.durability) DESC
            LIMIT 1
        """, (faction,))

        hero_row = cursor.fetchone()

        if hero_row:
            hero_attack, hero_defense, hero_durability, hero_class = hero_row
            hero_total_stats = hero_attack + hero_defense + hero_durability
        else:
            # Нет героев — бонус 0
            hero_total_stats = 0

        # === ШАГ 2: Считаем ВСЕ юниты фракции ===
        cursor.execute("""
            SELECT g.unit_name, g.unit_count, u.attack, u.defense, u.durability, u.unit_class 
            FROM garrisons g
            JOIN units u ON g.unit_name = u.unit_name
            WHERE u.faction = ?
        """, (faction,))

        units_data = cursor.fetchall()

        total_class_1_count = 0      # Общее количество юнитов 1-го класса по всей фракции
        total_class_1_stats = 0      # Сумма характеристик всех юнитов 1-го класса
        total_others_stats = 0       # Сумма характеристик юнитов 4+ класса

        for row in units_data:
            unit_name, unit_count, attack, defense, durability, unit_class = row
            stats_sum = attack + defense + durability

            if unit_class == "1":
                total_class_1_count += unit_count
                total_class_1_stats += stats_sum * unit_count
            elif unit_class in ("2", "3"):
                # Герои не учитываются в базе, только как источник бонуса
                pass
            else:  # класс 4 и выше
                total_others_stats += stats_sum * unit_count

        # === ШАГ 3: Применяем ГЛОБАЛЬНЫЙ бонус героя ===
        # Бонус героя умножается на ОБЩЕЕ количество юнитов 1-го класса фракции
        global_bonus = hero_total_stats * total_class_1_count

        # Итоговая формула:
        # Общая мощь = (база юнитов 1-го класса) + (глобальный бонус героя) + (юниты 4+ класса)
        total_power = total_class_1_stats + global_bonus + total_others_stats

        return total_power

    except Exception as e:
        print(f"Ошибка при вычислении общей мощи фракции {faction}: {e}")
        return 0

def show_ratings_popup(conn):
    """Открывает всплывающее окно с рейтингом армий."""
    from kivy.core.window import Window
    from kivy.utils import platform

    is_android = platform == 'android'

    table_layout = create_army_rating_table(conn)

    # === Легенда под таблицей ===
    legend = BoxLayout(
        orientation='horizontal',
        size_hint=(1, None),
        height=dp(40),
        spacing=dp(20),
        padding=[dp(10), 0]
    )

    legend.add_widget(Label(
        text="⚔️ Могущество: локальные бонусы",
        font_size=sp(11),
        color=(0.7, 0.7, 0.7, 1),
        halign='left'
    ))
    legend.add_widget(Label(
        text="🌟 Общая мощь: глобальные бонусы",
        font_size=sp(11),
        color=(0.9, 0.9, 0.5, 1),
        halign='right'
    ))

    # === Основной контейнер — ВАЖНО: size_hint_y=None ===
    main_layout = BoxLayout(
        orientation='vertical',
        size_hint=(1, None),  # ← Ключевое исправление!
        padding=[dp(5), dp(5), dp(5), dp(10)]
    )
    main_layout.add_widget(table_layout)
    main_layout.add_widget(legend)

    # Привязываем высоту контейнера к сумме высот детей
    main_layout.bind(minimum_height=main_layout.setter('height'))

    # === ScrollView с улучшенными настройками для Android ===
    scroll_view = ScrollView(
        size_hint=(1, 1),
        bar_width=dp(12) if is_android else dp(8),      # Шире полоса на Android
        bar_color=(0.6, 0.6, 0.6, 0.9),                  # Более контрастный цвет
        bar_inactive_color=(0.4, 0.4, 0.4, 0.5),         # Цвет неактивной полосы
        scroll_type=['bars', 'content'],                 # Прокрутка и полосой, и контентом
        effect_cls='ScrollEffect',                       # Плавная прокрутка
        do_scroll_x=False                                # Отключаем горизонтальную прокрутку
    )
    scroll_view.add_widget(main_layout)

    # === Popup ===
    popup = Popup(
        title="Рейтинг армий",
        content=scroll_view,
        size_hint=(0.95, 0.85),
        pos_hint={'center_x': 0.5, 'center_y': 0.5},
        background_color=(0.1, 0.1, 0.1, 0.95),
        separator_color=(0.2, 0.6, 1, 1),
        title_color=(1, 1, 1, 1),
        title_size=sp(20)
    )

    # Обновляем полосу прокрутки при изменении размера окна (для Android)
    def on_popup_open(*args):
        scroll_view.update_bar_pos()

    popup.bind(on_open=on_popup_open)
    popup.open()

# Функция для показа окна дипломатических отношений
def show_diplomacy_window(faction, conn):
    """Показывает окно с дипломатическими отношениями"""
    cursor = conn.cursor()
    manager = DiplomacyManager(faction, conn, cursor)
    manager.show_diplomatic_relations()


#------------------------------------------------------------------
def start_politic_mode(faction, game_area, class_faction, conn):
    """Инициализация политического режима для выбранной фракции"""

    from kivy.metrics import dp, sp
    from kivy.uix.widget import Widget

    is_android = platform == 'android'

    politics_layout = BoxLayout(
        orientation='horizontal',
        size_hint=(1, None),
        height=dp(70) if is_android else 60,
        pos_hint={'x': -0.34, 'y': 0},
        spacing=dp(10) if is_android else 10,
        padding=[dp(10), dp(5), dp(10), dp(5)] if is_android else [10, 5, 10, 5]
    )

    # Добавляем пустое пространство слева
    politics_layout.add_widget(Widget(size_hint_x=None, width=dp(20)))

    def styled_btn(text, callback):
        btn = Button(
            text=text,
            size_hint_x=None,
            width=dp(120) if is_android else 100,
            size_hint_y=None,
            height=dp(60) if is_android else 50,
            background_color=(0, 0, 0, 0),
            color=(1, 1, 1, 1),
            font_size=sp(18) if is_android else 16,
            bold=True
        )

        with btn.canvas.before:
            Color(0.2, 0.6, 1, 1)
            btn.rect = RoundedRectangle(pos=btn.pos, size=btn.size, radius=[15])

        def update_rect(instance, value):
            instance.rect.pos = instance.pos
            instance.rect.size = instance.size

        btn.bind(pos=update_rect, size=update_rect)
        btn.bind(on_release=callback)
        return btn

    # Добавляем кнопки в нужном порядке
    btn_army = styled_btn("Сила армий", lambda btn: show_ratings_popup(conn))
    btn_diplomacy = styled_btn("Отношения", lambda btn: show_diplomacy_window(faction, conn))
    btn_nobles = styled_btn("Совет", lambda btn: show_nobles_window(conn, faction, class_faction))
    btn_diversion = styled_btn("Диверсия", lambda btn: show_diversion_window(conn, faction, class_faction))

    politics_layout.add_widget(btn_army)
    politics_layout.add_widget(btn_diplomacy)
    politics_layout.add_widget(btn_nobles)
    politics_layout.add_widget(btn_diversion)

    game_area.add_widget(politics_layout)