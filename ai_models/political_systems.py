# ai_models/political_systems.py
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.graphics import Color, Line
from kivy.metrics import dp
from kivy.clock import Clock
import random
import sqlite3

from .translation import translation_dict


class PoliticalSystemsManager:
    def __init__(self, advisor_view):
        self.advisor = advisor_view
        self.faction = advisor_view.faction
        self.db_connection = advisor_view.db_connection
        self.cursor = advisor_view.cursor

    def load_political_system(self):
        """Загружает текущую политическую систему фракции"""
        try:
            query = "SELECT system FROM political_systems WHERE faction = ?"
            self.cursor.execute(query, (self.faction,))
            result = self.cursor.fetchone()
            return result[0] if result else "Смирение"
        except sqlite3.Error as e:
            print(f"Ошибка при загрузке политической системы: {e}")
            return "Смирение"

    def load_political_systems(self):
        """Загружает данные о политических системах всех фракций"""
        try:
            query = "SELECT faction, system FROM political_systems WHERE faction != 'Мятежники'"
            self.cursor.execute(query)
            rows = self.cursor.fetchall()

            systems = {}
            for faction, system in rows:
                systems[faction] = {
                    "system": system,
                    "influence": self.get_influence_description(system)
                }
            return systems
        except sqlite3.Error as e:
            print(f"Ошибка при загрузке политических систем: {e}")
            return {}

    def get_influence_description(self, system):
        """Возвращает текстовое описание влияния политической системы"""
        if system == "Смирение":
            return 15
        elif system == "Борьба":
            return 15
        else:
            return "Неизвестное влияние"

    def initialize_political_systems(self):
        """Инициализирует таблицу political_systems значениями по умолчанию"""
        try:
            # Проверяем, есть ли записи в таблице
            self.cursor.execute("SELECT COUNT(*) FROM political_systems")
            count = self.cursor.fetchone()[0]
            if count == 0:
                # Список всех фракций
                factions = ["Север", "Эльфы", "Вампиры", "Адепты", "Элины"]

                # Список возможных политических систем
                systems = ["Смирение", "Борьба"]

                # Функция для проверки распределения
                def is_valid_distribution(distribution):
                    counts = {system: distribution.count(system) for system in systems}
                    return all(2 <= count <= 3 for count in counts.values())

                # Генерация случайного распределения
                while True:
                    default_systems = [(faction, random.choice(systems)) for faction in factions]
                    distribution = [system for _, system in default_systems]

                    if is_valid_distribution(distribution):
                        break

                # Вставляем данные в таблицу
                self.cursor.executemany(
                    "INSERT INTO political_systems (faction, system) VALUES (?, ?)",
                    default_systems
                )
                self.db_connection.commit()
                print("Таблица political_systems инициализирована случайными значениями.")
        except sqlite3.Error as e:
            print(f"Ошибка при инициализации таблицы political_systems: {e}")

    def update_political_system(self, new_system):
        """Обновляет политическую систему фракции"""
        try:
            query = """
                INSERT INTO political_systems (faction, system)
                VALUES (?, ?)
                ON CONFLICT(faction) DO UPDATE SET system = excluded.system
            """
            self.cursor.execute(query, (self.faction, new_system))
            self.db_connection.commit()
            print(f"Политическая система обновлена: {new_system}")

            if self.advisor.game_screen:
                print("Уведомление GameScreen об изменении идеологии...")
                self.advisor.game_screen.refresh_player_ideology()
            else:
                print("Предупреждение: Ссылка на GameScreen не передана, обновление иконок невозможно.")

            self.show_political_systems()

        except sqlite3.Error as e:
            print(f"Ошибка при обновлении политической системы: {e}")

    def show_political_systems(self):
        """Показывает окно политических систем"""
        political_systems = self.load_political_systems()
        print("Загруженные данные о политических системах:", political_systems)

        if not political_systems:
            print(f"Нет данных о политических системах для фракции {self.faction}.")
            return

        # Очищаем текущее содержимое popup
        content = BoxLayout(orientation='vertical', spacing=dp(8), padding=dp(10))

        table = GridLayout(
            cols=3,
            size_hint_y=None,
            spacing=dp(4),
            row_default_height=dp(40)
        )
        table.bind(minimum_height=table.setter('height'))

        for title in ["Фракция", "Идеология", "Отношения"]:
            table.add_widget(self.create_header(title))

        for faction, data in political_systems.items():
            system = data["system"]
            highlight = faction == self.faction
            is_improving = system == self.load_political_system()
            influence_text = "Улучшаются" if system == self.load_political_system() else "Ухудшаются"
            influence_color = (0.2, 0.8, 0.2, 1) if is_improving else (0.9, 0.2, 0.2, 1)

            influence_label = Label(
                text=influence_text,
                font_size='14sp',
                bold=True,
                color=influence_color,
                halign='center',
                valign='middle',
                size_hint_y=None,
                height=dp(40),
                outline_color=(0, 0, 0, 1),
                outline_width=2
            )

            faction_label = self._create_cell(faction, highlight=highlight)
            system_label = self._create_cell(system, highlight=highlight)

            table.add_widget(faction_label)
            table.add_widget(system_label)
            table.add_widget(influence_label)

        scroll = ScrollView(
            size_hint=(1, 0.6),
            bar_width=dp(6),
            bar_color=(0.5, 0.5, 0.5, 0.6),
            scroll_type=['bars', 'content']
        )
        scroll.add_widget(table)
        content.add_widget(scroll)

        # Панель выбора идеологии
        system_layout = BoxLayout(
            orientation='horizontal',
            size_hint=(1, None),
            height=dp(60),
            spacing=dp(10)
        )

        # Кнопки выбор идеологии
        from .advisor_view import calculate_font_size

        capitalism_button = Button(
            text="Смирение",
            background_color=(0.2, 0.7, 0.3, 1),
            font_size='18sp',
            size_hint=(0.5, None),
            height=calculate_font_size() * 1,
            color=(1, 1, 1, 1),
            background_normal='',
            background_down=''
        )

        communism_button = Button(
            text="Борьба",
            background_color=(0.8, 0.2, 0.2, 1),
            font_size='18sp',
            size_hint=(0.5, None),
            height=calculate_font_size() * 1,
            color=(1, 1, 1, 1),
            background_normal='',
            background_down=''
        )

        # Функции-обработчики
        def schedule_return_to_main(dt):
            self.advisor.return_to_main_tab()

        capitalism_button.bind(
            on_release=lambda x: [
                self.update_political_system("Смирение"),
                Clock.schedule_once(schedule_return_to_main, 2.0)
            ]
        )

        communism_button.bind(
            on_release=lambda x: [
                self.update_political_system("Борьба"),
                Clock.schedule_once(schedule_return_to_main, 2.0)
            ]
        )

        # Добавляем рамки вокруг кнопок
        for btn in (capitalism_button, communism_button):
            with btn.canvas.after:
                Color(0.1, 0.1, 0.1, 1)
                btn.border_line = Line(
                    rectangle=(btn.x, btn.y, btn.width, btn.height), width=1.5)
            btn.bind(
                size=lambda inst, val: setattr(inst.border_line, "rectangle",
                                               (inst.x, inst.y, inst.width, inst.height))
            )
            btn.bind(
                pos=lambda inst, val: setattr(inst.border_line, "rectangle",
                                              (inst.x, inst.y, inst.width, inst.height))
            )

        system_layout.add_widget(capitalism_button)
        system_layout.add_widget(communism_button)
        content.add_widget(system_layout)

        # Обновляем содержимое popup
        self.advisor.popup.content = content

    def create_header(self, text):
        """Создает заголовок таблицы"""
        label = Label(
            text=f"[b]{text}[/b]",
            markup=True,
            font_size='14sp',
            bold=True,
            color=(1, 1, 1, 1),
            halign='center',
            valign='middle',
            size_hint_y=None,
            height=dp(40),
            text_size=(None, None),
            outline_color=(0, 0, 0, 1),
            outline_width=2
        )
        label.bind(size=label.setter('text_size'))
        return label

    def _create_cell(self, text, highlight=False):
        """Создает ячейку таблицы"""
        text_color = self.advisor.colors['accent'] if highlight else (1, 1, 1, 1)
        return Label(
            text=f"[b]{text}[/b]" if highlight else text,
            markup=True,
            font_size='14sp',
            bold=True,
            color=text_color,
            halign='center',
            valign='middle',
            size_hint_y=None,
            height=dp(40),
            text_size=(None, None),
            outline_color=(0, 0, 0, 1),
            outline_width=2
        )