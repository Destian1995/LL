# ai_models/advisor_view.py
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.image import Image
from kivy.uix.popup import Popup
from kivy.uix.textinput import TextInput
from kivy.uix.spinner import Spinner
from kivy.graphics import Color, Rectangle, Line, RoundedRectangle, Ellipse
from kivy.core.window import Window
from kivy.metrics import dp
from kivy.clock import Clock
from kivy.uix.behaviors import ButtonBehavior
from datetime import datetime
import os
import random
import sqlite3

from .quick_actions import QuickActions
from .diplomacy_chat import DiplomacyChat
from .political_systems import PoliticalSystemsManager
from .relations_manager import RelationsManager
from .diplomacy_ai import DiplomacyAI

def calculate_font_size():
    from kivy.utils import platform
    base_height = 360
    default_font_size = 14
    scale_factor = Window.height / base_height

    # Увеличиваем шрифт на Android
    if platform == 'android':
        scale_factor *= 1.5

    return max(14, int(default_font_size * scale_factor))


# Словарь для перевода названий
translation_dict = {
    "Север": "people",
    "Эльфы": "elfs",
    "Адепты": "adept",
    "Вампиры": "vampire",
    "Элины": "poly",
}


def transform_filename(file_path):
    path_parts = file_path.split('/')
    for i, part in enumerate(path_parts):
        for ru_name, en_name in translation_dict.items():
            if ru_name in part:
                path_parts[i] = part.replace(ru_name, en_name)
    transformed_path = '/'.join(path_parts)
    return transformed_path


reverse_translation_dict = {v: k for k, v in translation_dict.items()}


class ClickableImage(ButtonBehavior, Image):
    pass

class AdvisorView(FloatLayout):
    def __init__(self, faction, conn, game_screen_instance=None, **kwargs):
        super(AdvisorView, self).__init__(**kwargs)

        self.faction = faction
        self.db_connection = conn
        self.cursor = self.db_connection.cursor()
        self.game_screen = game_screen_instance

        # Инициализация менеджеров
        self.political_manager = PoliticalSystemsManager(self)
        self.relations_manager = RelationsManager(self)
        self.diplomacy_chat = DiplomacyChat(self)
        self.quick_actions = QuickActions(self)
        self.diplomacy_ai = DiplomacyAI(self)

        # Цветовая тема интерфейса
        self.colors = {
            'background': (0.95, 0.95, 0.95, 1),
            'primary': (0.118, 0.255, 0.455, 1),
            'accent': (0.227, 0.525, 0.835, 1),
            'text': (1, 1, 1, 1),
            'card': (1, 1, 1, 1)
        }

        # Инициализация таблицы политических систем
        self.political_manager.initialize_political_systems()

        # Главное окно интерфейса
        self.create_main_interface()

    def create_main_interface(self):
        """Создает главный интерфейс советника"""
        self.interface_window = FloatLayout(size_hint=(1, 1))

        # === Основной контейнер ===
        main_layout = BoxLayout(
            orientation='horizontal',
            spacing=dp(20),
            padding=dp(20),
            size_hint=(1, 1)
        )

        # Левая панель (изображение, инфо и т.п.)
        left_panel = FloatLayout(size_hint=(0.45, 1))

        # Правая панель (таблицы и вкладки)
        right_panel = BoxLayout(
            orientation='vertical',
            size_hint=(0.55, 1),
            spacing=0,
            padding=0
        )

        # === Панель вкладок ===
        tabs_panel = ScrollView(
            size_hint=(1, None),
            height=Window.height * 0.3,
            bar_width=dp(8),
            bar_color=(0.5, 0.5, 0.5, 0.5)
        )

        self.tabs_content = GridLayout(
            cols=1,
            size_hint_y=None,
            spacing=dp(10),
            padding=dp(5)
        )
        self.tabs_content.bind(minimum_height=self.tabs_content.setter('height'))
        tabs_panel.add_widget(self.tabs_content)
        right_panel.add_widget(tabs_panel)

        # Сборка основной панели
        main_layout.add_widget(left_panel)
        main_layout.add_widget(right_panel)

        # === Нижняя панель с кнопками ===
        bottom_panel = self.create_bottom_panel()

        # === КНОПКА ЧАТА С ИИ ===
        self.create_ai_chat_button()

        # === Финальная сборка ===
        self.interface_window.add_widget(main_layout)
        self.interface_window.add_widget(bottom_panel)
        self.interface_window.add_widget(self.ai_chat_button)

        # === Popup ===
        self.create_main_popup()

    def create_bottom_panel(self):
        """Создает нижнюю панель с кнопками"""
        bottom_panel = BoxLayout(
            size_hint=(1, None),
            height=Window.height * 0.09,
            padding=dp(6),
            spacing=dp(6),
            pos_hint={'x': 0, 'y': 0}
        )

        button_style = {
            "size_hint": (1, 1),
            "background_normal": '',
            "color": (1, 1, 1, 1),
            "font_size": calculate_font_size() * 0.9,
            "bold": True,
            "border": (0, 0, 0, 0)
        }

        political_system_button = Button(
            text="Идеология",
            background_color=(0.227, 0.525, 0.835, 1),
            **button_style
        )
        political_system_button.bind(on_release=lambda x: self.show_political_systems())

        relations_button = Button(
            text="Отношения",
            background_color=(0.118, 0.255, 0.455, 1),
            **button_style
        )
        relations_button.bind(on_release=lambda x: self.show_relations("Состояние отношений"))

        # Добавляем рамку вокруг кнопок
        for btn in (political_system_button, relations_button):
            with btn.canvas.after:
                Color(0.1, 0.1, 0.1, 1)
                btn.border_line = Line(rectangle=(btn.x, btn.y, btn.width, btn.height), width=1.5)
            btn.bind(
                size=lambda inst, val: setattr(inst.border_line, "rectangle", (inst.x, inst.y, inst.width, inst.height))
            )
            btn.bind(
                pos=lambda inst, val: setattr(inst.border_line, "rectangle", (inst.x, inst.y, inst.width, inst.height))
            )

        bottom_panel.add_widget(political_system_button)
        bottom_panel.add_widget(relations_button)

        return bottom_panel

    def create_ai_chat_button(self):
        """Создает кнопку чата с ИИ"""
        self.ai_chat_button = ClickableImage(
            source="files/pict/sov/letter.png",
            size_hint=(None, None),
            size=(dp(110), dp(110)),
            pos_hint={'right': 0.90, 'top': 0.90},
            allow_stretch=True
        )

        # Обновляем фон при изменении позиции/размера
        def update_ai_chat_bg(instance, value):
            instance.canvas.before.clear()
            with instance.canvas.before:
                Color(0.2, 0.6, 0.9, 0.9)
                Ellipse(pos=instance.pos, size=instance.size)

        self.ai_chat_button.bind(pos=update_ai_chat_bg, size=update_ai_chat_bg)
        self.ai_chat_button.bind(on_press=self.open_ai_chat)

    def create_main_popup(self):
        """Создает главное всплывающее окно"""
        background = f'files/sov/parlament/{translation_dict.get(self.faction)}_palace.jpg'
        if not os.path.exists(background):
            background = ''

        self.popup = Popup(
            title="",
            title_size=Window.height * 0.03,
            title_align="center",
            content=self.interface_window,
            size_hint=(0.7, 0.7),
            separator_height=dp(0),
            background=background
        )
        self.popup.open()

    def open_ai_chat(self, instance):
        """Открывает окно дипломатических переговоров"""
        self.diplomacy_chat.open_diplomacy_window()

    def show_political_systems(self):
        """Показывает политические системы"""
        self.political_manager.show_political_systems()

    def show_relations(self, instance=None):
        """Показывает отношения"""
        self.relations_manager.show_relations()

    def return_to_main_tab(self, *args):
        """Возвращает к главному интерфейсу"""
        self.popup.content = self.interface_window

    def close_window(self, instance):
        """Закрытие окна"""
        print("Метод close_window вызван.")
        if hasattr(self, 'popup') and self.popup:
            self.popup.dismiss()
        else:
            print("Ошибка: Попап не найден.")