# ai_models/ui/relations_table.py
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.metrics import dp
from kivy.graphics import Color, Line


class RelationCell(Label):
    """Ячейка таблицы отношений"""
    def __init__(self, text, **kwargs):
        super().__init__(**kwargs)
        self.text = str(text)
        self.size_hint_y = None
        self.height = dp(40)
        self.halign = 'center'
        self.valign = 'middle'
        self.outline_color = (0, 0, 0, 1)
        self.outline_width = 2
        self.bind(size=self.setter('text_size'))


class RelationsTable(GridLayout):
    """Таблица отношений"""
    def __init__(self, relations_data, **kwargs):
        super().__init__(**kwargs)
        self.cols = 4
        self.size_hint_y = None
        self.spacing = dp(4)
        self.row_default_height = dp(40)
        self.bind(minimum_height=self.setter('height'))

        self.relations_data = relations_data
        self.create_table()

    def create_table(self):
        """Создает таблицу отношений"""
        # Заголовки
        headers = ["Фракция", "Отношения", "Торговля", "Статус"]
        for title in headers:
            self.add_widget(self.create_header(title))

        # Данные
        for country, data in self.relations_data.items():
            relation_level = data.get("relation_level", 0)
            status = data.get("status", "нейтралитет")

            # Ячейка фракции
            faction_cell = RelationCell(country)
            faction_cell.color = self.get_status_color(status)

            # Ячейка отношений
            relation_cell = RelationCell(relation_level)
            relation_cell.color = self.get_relation_color(relation_level)
            relation_cell.bold = True

            # Ячейка торговли
            trade_coefficient = self.calculate_coefficient(relation_level)
            trade_cell = RelationCell(f"{trade_coefficient:.1f}x")
            trade_cell.color = self.get_relation_trade_color(trade_coefficient)
            trade_cell.bold = True

            # Ячейка статуса
            status_cell = RelationCell(status)
            status_cell.color = self.get_status_color(status)
            status_cell.bold = True

            self.add_widget(faction_cell)
            self.add_widget(relation_cell)
            self.add_widget(trade_cell)
            self.add_widget(status_cell)

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

    def calculate_coefficient(self, relation_level):
        """Рассчитывает коэффициент торговли"""
        try:
            rel = int(relation_level)
        except (ValueError, TypeError):
            rel = 50

        if rel < 15:
            return 0
        if 15 <= rel < 25:
            return 0.1
        if 25 <= rel < 35:
            return 0.4
        if 35 <= rel < 50:
            return 0.9
        if 50 <= rel < 60:
            return 1.5
        if 60 <= rel < 75:
            return 2
        if 75 <= rel < 90:
            return 3.1
        if 90 <= rel <= 100:
            return 4
        return 0

    def get_status_color(self, status):
        """Определяет цвет на основе статуса"""
        if status == "война":
            return (1, 0, 0, 1)
        elif status == "нейтралитет":
            return (1, 1, 1, 1)
        elif status == "союз":
            return (0, 0.75, 0.8, 1)
        else:
            return (0.5, 0.5, 0.5, 1)

    def get_relation_color(self, value):
        """Возвращает цвет в зависимости от значения"""
        try:
            value = int(value)
        except (ValueError, TypeError):
            value = 50

        if value <= 15:
            return (0.8, 0.1, 0.1, 1)
        elif 15 < value <= 25:
            return (1.0, 0.5, 0.0, 1)
        elif 25 < value <= 35:
            return (1.0, 0.8, 0.0, 1)
        elif 35 < value <= 50:
            return (0.2, 0.7, 0.3, 1)
        elif 50 < value <= 60:
            return (0.0, 0.8, 0.8, 1)
        elif 60 < value <= 75:
            return (0.0, 0.6, 1.0, 1)
        elif 75 < value <= 90:
            return (0.1, 0.3, 0.9, 1)
        else:
            return (1, 1, 1, 1)

    def get_relation_trade_color(self, value):
        """Возвращает цвет для коэффициента торговли"""
        if value <= 0.1:
            return (0.8, 0.1, 0.1, 1)
        elif 0.1 < value <= 0.4:
            return (1.0, 0.5, 0.0, 1)
        elif 0.4 < value <= 0.9:
            return (1.0, 0.8, 0.0, 1)
        elif 0.9 < value <= 1.5:
            return (0.2, 0.7, 0.3, 1)
        elif 1.5 < value <= 2:
            return (0.0, 0.8, 0.8, 1)
        elif 2 < value <= 3.1:
            return (0.0, 0.6, 1.0, 1)
        elif 3.1 < value <= 4:
            return (0.1, 0.3, 0.9, 1)
        else:
            return (1, 1, 1, 1)