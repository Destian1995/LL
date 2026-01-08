# ai_models/ui/political_ui.py
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.scrollview import ScrollView
from kivy.metrics import dp
from kivy.graphics import Color, Line


class PoliticalSystemTable(GridLayout):
    """Таблица политических систем"""
    def __init__(self, systems_data, current_faction, **kwargs):
        super().__init__(**kwargs)
        self.cols = 3
        self.size_hint_y = None
        self.spacing = dp(4)
        self.row_default_height = dp(40)
        self.bind(minimum_height=self.setter('height'))

        self.systems_data = systems_data
        self.current_faction = current_faction
        self.create_table()

    def create_table(self):
        """Создает таблицу политических систем"""
        # Заголовки
        headers = ["Фракция", "Идеология", "Отношения"]
        for title in headers:
            self.add_widget(self.create_header(title))

        # Данные
        for faction, data in self.systems_data.items():
            system = data.get("system", "Неизвестно")
            highlight = faction == self.current_faction

            # Ячейка фракции
            faction_cell = self.create_cell(faction, highlight)

            # Ячейка идеологии
            system_cell = self.create_cell(system, highlight)

            # Ячейка влияния
            influence_text = "Улучшаются" if system == self.get_current_system() else "Ухудшаются"
            influence_color = (0.2, 0.8, 0.2, 1) if system == self.get_current_system() else (0.9, 0.2, 0.2, 1)

            influence_cell = Label(
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

            self.add_widget(faction_cell)
            self.add_widget(system_cell)
            self.add_widget(influence_cell)

    def get_current_system(self):
        """Получает текущую систему фракции"""
        return self.systems_data.get(self.current_faction, {}).get("system", "Неизвестно")

    def create_header(self, text):
        """Создает заголовок таблицы"""
        header = Label(
            text=f"[b]{text}[/b]",
            markup=True,
            font_size='14sp',
            bold=True,
            color=(1, 1, 1, 1),
            size_hint_y=None,
            height=dp(40),
            halign='center',
            valign='middle',
            outline_color=(0, 0, 0, 1),
            outline_width=2
        )
        header.bind(size=header.setter('text_size'))
        return header

    def create_cell(self, text, highlight=False):
        """Создает ячейку таблицы"""
        from ..advisor_view import calculate_font_size
        text_color = (0.227, 0.525, 0.835, 1) if highlight else (1, 1, 1, 1)
        return Label(
            text=f"[b]{text}[/b]" if highlight else text,
            markup=True,
            font_size='14sp',
            bold=True if highlight else False,
            color=text_color,
            halign='center',
            valign='middle',
            size_hint_y=None,
            height=dp(40),
            text_size=(None, None),
            outline_color=(0, 0, 0, 1),
            outline_width=2
        )


class IdeologyButtons(BoxLayout):
    """Кнопки выбора идеологии"""
    def __init__(self, update_callback, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'horizontal'
        self.size_hint = (1, None)
        self.height = dp(60)
        self.spacing = dp(10)

        self.update_callback = update_callback
        self.create_buttons()

    def create_buttons(self):
        """Создает кнопки выбора идеологии"""
        from ..advisor_view import calculate_font_size

        # Кнопка "Смирение"
        self.capitalism_button = Button(
            text="Смирение",
            background_color=(0.2, 0.7, 0.3, 1),
            font_size='18sp',
            size_hint=(0.5, None),
            height=calculate_font_size() * 1,
            color=(1, 1, 1, 1),
            background_normal='',
            background_down=''
        )

        # Кнопка "Борьба"
        self.communism_button = Button(
            text="Борьба",
            background_color=(0.8, 0.2, 0.2, 1),
            font_size='18sp',
            size_hint=(0.5, None),
            height=calculate_font_size() * 1,
            color=(1, 1, 1, 1),
            background_normal='',
            background_down=''
        )

        # Привязываем обработчики
        if self.update_callback:
            self.capitalism_button.bind(
                on_release=lambda x: self.update_callback("Смирение")
            )
            self.communism_button.bind(
                on_release=lambda x: self.update_callback("Борьба")
            )

        # Добавляем рамки
        for btn in (self.capitalism_button, self.communism_button):
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

        self.add_widget(self.capitalism_button)
        self.add_widget(self.communism_button)