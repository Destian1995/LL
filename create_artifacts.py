import os
import sqlite3
from kivy.uix.popup import Popup
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.spinner import Spinner
from kivy.uix.image import Image
from kivy.uix.scrollview import ScrollView
from kivy.graphics import Color, RoundedRectangle
from kivy.metrics import dp, sp
from kivy.core.window import Window
import random

def show_message(title, message):
    # === Оценка высоты текста ===
    lines = message.count('\n') + 1
    text_height = max(dp(100), dp(lines * 25))  # минимум 100dp, дальше по строкам
    popup_height = text_height + dp(110)        # + кнопка и отступы

    # === Стилизованный Label с переносом текста и выравниванием по центру ===
    label = Label(
        text=message,
        size_hint_y=None,
        height=text_height,
        text_size=(None, None),
        halign='center',
        valign='middle',
        font_size='16sp',
        padding=(dp(10), dp(10))
    )

    # Обновляем текстуру после изменения размера
    def update_label_width(instance, width):
        instance.text_size = (instance.width * 0.9, None)
        instance.texture_update()

    label.bind(width=update_label_width)

    # === Кнопка "Закрыть" с минимальной высотой и стилем ===
    close_btn = Button(
        text="Закрыть",
        size_hint=(1, None),
        height=dp(48),
        background_color=(0.2, 0.6, 0.8, 1),
        background_normal='',
        font_size='16sp'
    )

    # === Основной макет ===
    layout = BoxLayout(orientation='vertical', padding=dp(10), spacing=dp(10))
    layout.add_widget(label)
    layout.add_widget(close_btn)

    # === Всплывающее окно ===
    popup = Popup(
        title=title,
        content=layout,
        size_hint=(0.7, None),
        height=popup_height,
        auto_dismiss=False
    )
    close_btn.bind(on_release=popup.dismiss)

    popup.open()

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
    elif absolute >= 1_000_000_000_000_000_000_000_000_000:  # 1e24
        return f"{sign * absolute / 1e24:.1f} септил."
    elif absolute >= 1_000_000_000_000_000_000_000_000_000:  # 1e21
        return f"{sign * absolute / 1e21:.1f} секст."
    elif absolute >= 1_000_000_000_000_000_000_000_000:  # 1e18
        return f"{sign * absolute / 1e18:.1f} квинт."
    elif absolute >= 1_000_000_000_000_000_000_000:  # 1e15
        return f"{sign * absolute / 1e15:.1f} квадр."
    elif absolute >= 1_000_000_000_000_000_000:  # 1e12
        return f"{sign * absolute / 1e12:.1f} трлн."
    elif absolute >= 1_000_000_000:  # 1e9
        return f"{sign * absolute / 1e9:.1f} млрд."
    elif absolute >= 1_000_000:  # 1e6
        return f"{sign * absolute / 1e6:.1f} млн."
    elif absolute >= 1_000:  # 1e3
        return f"{sign * absolute / 1e3:.1f} тыс."
    else:
        return f"{number}"


def workshop(faction, db_conn):
    # === Адаптивные размеры для мобильных устройств ===
    # Определяем, является ли устройство мобильным
    is_mobile = Window.width <= 480  # порог для мобильных устройств

    # Адаптивные размеры
    popup_width = 0.95 if is_mobile else 0.8
    popup_height = 0.95 if is_mobile else 0.9
    title_font_size = sp(18) if is_mobile else sp(20)
    normal_font_size = sp(14) if is_mobile else sp(16)
    small_font_size = sp(12) if is_mobile else sp(14)

    # Высоты элементов
    btn_height = dp(40) if is_mobile else dp(50)
    input_height = dp(35) if is_mobile else dp(40)
    label_height = dp(25) if is_mobile else dp(30)

    # === Создание всплывающего окна ===
    workshop_popup = Popup(
        title="Мастерская артефактов",
        size_hint=(popup_width, popup_height),
        title_size=title_font_size,
        title_align='center',
        title_color=(1, 1, 1, 1),
        background_color=(0.1, 0.1, 0.1, 0.95),
        separator_color=(0.3, 0.3, 0.3, 1),
        auto_dismiss=False
    )

    # Основной макет с ScrollView для мобильных устройств
    if is_mobile:
        main_scroll = ScrollView(do_scroll_x=False)
        main_layout = BoxLayout(orientation='vertical', spacing=dp(8), padding=dp(12), size_hint_y=None)
        main_layout.bind(minimum_height=main_layout.setter('height'))
    else:
        main_layout = BoxLayout(orientation='vertical', spacing=dp(12), padding=dp(16))

    # === Информация о средствах - адаптивный макет ===
    if is_mobile:
        info_layout = BoxLayout(orientation='vertical', size_hint_y=None, height=dp(60), spacing=dp(5))
    else:
        info_layout = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(40), spacing=dp(10))

    money_label = Label(
        text=f"Баланс: {format_number(faction.money)}",
        font_size=small_font_size,
        color=(0.9, 0.9, 0.9, 1),
        halign='left',
        valign='middle',
        size_hint_y=None,
        height=label_height
    )
    money_label.bind(size=lambda inst, val: setattr(inst, 'text_size', (inst.width, inst.height)))
    info_layout.add_widget(money_label)

    cost_label = Label(
        text="Создание: 35 млн",
        font_size=small_font_size,
        color=(0.9, 0.9, 0.9, 1),
        halign='right' if not is_mobile else 'left',
        valign='middle',
        size_hint_y=None,
        height=label_height
    )
    cost_label.bind(size=lambda inst, val: setattr(inst, 'text_size', (inst.width, inst.height)))
    info_layout.add_widget(cost_label)

    main_layout.add_widget(info_layout)

    # === Основная сетка - адаптивная для мобильных ===
    if is_mobile:
        # Для мобильных - вертикальная компоновка
        content_layout = BoxLayout(orientation='vertical', spacing=dp(10), size_hint_y=None)
        content_layout.bind(minimum_height=content_layout.setter('height'))
    else:
        # Для десктопа - горизонтальная сетка
        content_layout = GridLayout(cols=2, spacing=dp(12), size_hint_y=1)

    # === Левая колонка - выбор иконки и параметров ===
    left_col = BoxLayout(orientation='vertical', spacing=dp(8))

    # Выбор иконки
    icon_title = Label(
        text="Выберите иконку артефакта:",
        font_size=normal_font_size,
        color=(0.8, 0.8, 0.8, 1),
        size_hint_y=None,
        height=label_height,
        halign='center',
        valign='middle'
    )
    icon_title.bind(size=lambda inst, val: setattr(inst, 'text_size', (inst.width, inst.height)))
    left_col.add_widget(icon_title)

    # Загрузка изображений из папки
    artifact_images_path = r"files/pict/artifacts/custom"
    if os.path.exists(artifact_images_path):
        image_files = [f for f in os.listdir(artifact_images_path) if f.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp'))]
    else:
        image_files = []

    # === Скроллируемый контейнер для сетки изображений ===
    scroll_container = ScrollView(
        size_hint_y=0.4 if is_mobile else 0.5,
        do_scroll_x=False,
        bar_width=dp(6) if is_mobile else dp(8)
    )

    # Адаптивное количество колонок для изображений
    image_cols = 2 if is_mobile else 3
    image_grid = GridLayout(
        cols=image_cols,
        spacing=dp(6) if is_mobile else dp(10),
        size_hint_y=None
    )
    image_grid.bind(minimum_height=image_grid.setter('height'))

    selected_image = [None]

    class ImageButton(BoxLayout):
        selected_button = None

        def __init__(self, image_path, file_name, **kwargs):
            super().__init__(**kwargs)
            self.image_path = image_path
            self.file_name = file_name
            self.orientation = 'vertical'
            self.size_hint_y = None
            self.height = dp(70) if is_mobile else dp(80)  # Уменьшенная высота для мобильных
            self.padding = [dp(3)] if is_mobile else [dp(5)]
            self.selected = False

            # Изображение
            img_widget = Image(
                source=image_path,
                size_hint_y=None,
                height=dp(50) if is_mobile else dp(60),  # Уменьшенное изображение
                allow_stretch=True,
                keep_ratio=True
            )
            self.add_widget(img_widget)

            # Фон
            with self.canvas.before:
                self.bg_color = Color(0.3, 0.3, 0.3, 1)
                self.rect = RoundedRectangle(pos=self.pos, size=self.size, radius=[dp(6)])
            self.bind(pos=self.update_graphics, size=self.update_graphics)

        def on_touch_down(self, touch):
            if self.collide_point(*touch.pos):
                if ImageButton.selected_button and ImageButton.selected_button != self:
                    ImageButton.selected_button.set_selected(False)

                self.set_selected(True)
                ImageButton.selected_button = self
                select_image(self.file_name)
                return True
            return super().on_touch_down(touch)

        def set_selected(self, value: bool):
            self.selected = value
            if value:
                self.bg_color.rgba = (0.8, 0.6, 0.2, 1)
            else:
                self.bg_color.rgba = (0.3, 0.3, 0.3, 1)

        def update_graphics(self, *args):
            self.rect.pos = self.pos
            self.rect.size = self.size

    def select_image(image_file):
        selected_image[0] = image_file
        for child in image_grid.children:
            if isinstance(child, ImageButton):
                child.set_selected(child.file_name == image_file)

    for img_file in image_files:
        img_path = os.path.join(artifact_images_path, img_file)
        img_btn = ImageButton(image_path=img_path, file_name=img_file)
        image_grid.add_widget(img_btn)

    scroll_container.add_widget(image_grid)
    left_col.add_widget(scroll_container)

    # Выбор слота
    slot_label = Label(
        text="Выберите слот:",
        font_size=small_font_size,
        color=(0.8, 0.8, 0.8, 1),
        size_hint_y=None,
        height=label_height,
        halign='left',
        valign='middle'
    )
    slot_label.bind(size=lambda inst, val: setattr(inst, 'text_size', (inst.width, inst.height)))
    left_col.add_widget(slot_label)

    slot_spinner = Spinner(
        text='Выберите слот',
        values=['Руки', 'Голова', 'Ноги', 'Туловище', 'Аксессуар'],
        size_hint_y=None,
        height=input_height,
        font_size=small_font_size
    )
    left_col.add_widget(slot_spinner)

    # Название
    name_label = Label(
        text="Название артефакта:",
        font_size=small_font_size,
        color=(0.8, 0.8, 0.8, 1),
        size_hint_y=None,
        height=label_height,
        halign='left',
        valign='middle'
    )
    name_label.bind(size=lambda inst, val: setattr(inst, 'text_size', (inst.width, inst.height)))
    left_col.add_widget(name_label)

    name_input = TextInput(
        hint_text="Введите название или оставьте пустым для случайного",
        font_size=small_font_size,
        multiline=False,
        size_hint_y=None,
        height=input_height,
        padding=[dp(8), dp(6)] if is_mobile else [dp(10), dp(8)],
        background_color=(0.2, 0.2, 0.2, 1),
        foreground_color=(1, 1, 1, 1),
        cursor_color=(1, 1, 1, 1)
    )
    left_col.add_widget(name_input)

    # Кнопка генерации случайного названия
    random_name_btn = Button(
        text="Случайное название",
        size_hint_y=None,
        height=btn_height,
        background_normal='',
        background_color=(0.2, 0.6, 0.6, 1),
        font_size=small_font_size
    )
    left_col.add_widget(random_name_btn)

    if is_mobile:
        content_layout.add_widget(left_col)
    else:
        content_layout.add_widget(left_col)

    # === Правая колонка - параметры артефакта ===
    right_col = BoxLayout(orientation='vertical', spacing=dp(8))

    # Параметры
    params_label = Label(
        text="Параметры артефакта:",
        font_size=normal_font_size,
        color=(0.8, 0.8, 0.8, 1),
        size_hint_y=None,
        height=label_height,
        halign='center',
        valign='middle'
    )
    params_label.bind(size=lambda inst, val: setattr(inst, 'text_size', (inst.width, inst.height)))
    right_col.add_widget(params_label)

    # Сетка для параметров
    params_grid = GridLayout(
        cols=2,
        spacing=dp(4) if is_mobile else dp(5),
        size_hint_y=None,
        padding=[dp(5)] if is_mobile else [0]
    )
    params_grid.bind(minimum_height=params_grid.setter('height'))

    # Параметры
    attack_bonus = [0]
    defense_bonus = [0]
    seasons_bonus = [[]]

    # Атака
    attack_label = Label(
        text="Атака (%):",
        font_size=small_font_size,
        size_hint_y=None,
        height=label_height
    )
    params_grid.add_widget(attack_label)
    attack_input = TextInput(
        text='0',
        font_size=small_font_size,
        multiline=False,
        size_hint_y=None,
        height=input_height,
        input_filter='int',
        padding=[dp(8), dp(6)] if is_mobile else [dp(10), dp(8)],
        background_color=(0.2, 0.2, 0.2, 1),
        foreground_color=(1, 1, 1, 1),
        cursor_color=(1, 1, 1, 1)
    )
    def update_attack(instance, value):
        try:
            attack_bonus[0] = int(value) if value else 0
        except ValueError:
            attack_bonus[0] = 0
    attack_input.bind(text=update_attack)
    params_grid.add_widget(attack_input)

    # Защита
    defense_label = Label(
        text="Защита (%):",
        font_size=small_font_size,
        size_hint_y=None,
        height=label_height
    )
    params_grid.add_widget(defense_label)
    defense_input = TextInput(
        text='0',
        font_size=small_font_size,
        multiline=False,
        size_hint_y=None,
        height=input_height,
        input_filter='int',
        padding=[dp(8), dp(6)] if is_mobile else [dp(10), dp(8)],
        background_color=(0.2, 0.2, 0.2, 1),
        foreground_color=(1, 1, 1, 1),
        cursor_color=(1, 1, 1, 1)
    )
    def update_defense(instance, value):
        try:
            defense_bonus[0] = int(value) if value else 0
        except ValueError:
            defense_bonus[0] = 0
    defense_input.bind(text=update_defense)
    params_grid.add_widget(defense_input)

    # Сезоны
    season_label = Label(
        text="Сезоны:",
        font_size=small_font_size,
        size_hint_y=None,
        height=label_height
    )
    params_grid.add_widget(season_label)

    # Упрощенные значения сезонов для мобильных
    if is_mobile:
        season_values = ['Нет', 'Весна', 'Лето', 'Осень', 'Зима', 'Все']
    else:
        season_values = ['Нет', 'Весна', 'Лето', 'Осень', 'Зима', 'Весна, Лето', 'Весна, Осень', 'Весна, Зима',
                         'Лето, Осень', 'Лето, Зима', 'Осень, Зима', 'Весна, Лето, Осень',
                         'Весна, Лето, Зима', 'Весна, Осень, Зима', 'Лето, Осень, Зима', 'Все']

    season_spinner = Spinner(
        text='Нет',
        values=season_values,
        size_hint_y=None,
        height=input_height,
        font_size=small_font_size
    )
    def update_seasons(value):
        if value == 'Нет':
            seasons_bonus[0] = []
        elif value == 'Все':
            seasons_bonus[0] = ['Весна', 'Лето', 'Осень', 'Зима']
        else:
            seasons_bonus[0] = [s.strip() for s in value.split(',')]
    season_spinner.bind(text=lambda spinner, value: update_seasons(value))
    params_grid.add_widget(season_spinner)

    right_col.add_widget(params_grid)

    # Кнопка создания артефакта
    create_btn = Button(
        text="Создать чертеж артефакта",
        size_hint_y=None,
        height=btn_height,
        background_normal='',
        background_color=(0.6, 0.2, 0.6, 1),
        font_size=normal_font_size,
        bold=True
    )
    right_col.add_widget(create_btn)

    if is_mobile:
        content_layout.add_widget(right_col)
    else:
        content_layout.add_widget(right_col)

    main_layout.add_widget(content_layout)

    # === Блок созданного артефакта ===
    artifact_box_height = dp(150) if is_mobile else dp(200)
    artifact_box = BoxLayout(
        orientation='vertical',
        spacing=dp(8),
        size_hint_y=None,
        height=artifact_box_height
    )

    artifact_title = Label(
        text="Артефакт:",
        font_size=normal_font_size,
        color=(0.8, 0.8, 0.8, 1),
        size_hint_y=None,
        height=label_height,
        halign='center',
        valign='middle'
    )
    artifact_title.bind(size=lambda inst, val: setattr(inst, 'text_size', (inst.width, inst.height)))
    artifact_box.add_widget(artifact_title)

    # Отображение артефакта
    artifact_display_height = dp(80) if is_mobile else dp(120)
    artifact_display = BoxLayout(
        orientation='horizontal',
        spacing=dp(8),
        size_hint_y=None,
        height=artifact_display_height
    )

    # Изображение артефакта
    artifact_image_width = dp(60) if is_mobile else dp(100)
    artifact_image = Image(
        source="",
        size_hint_x=None,
        width=artifact_image_width,
        allow_stretch=True,
        keep_ratio=True
    )
    artifact_display.add_widget(artifact_image)

    # Информация об артефакте
    artifact_info = BoxLayout(orientation='vertical', spacing=dp(3))
    artifact_name_label = Label(
        text="",
        font_size=small_font_size,
        color=(1, 1, 1, 1),
        halign='left',
        valign='middle'
    )
    artifact_name_label.bind(size=lambda inst, val: setattr(inst, 'text_size', (inst.width, inst.height)))
    artifact_info.add_widget(artifact_name_label)

    artifact_cost_label = Label(
        text="",
        font_size=small_font_size,
        color=(1, 1, 1, 1),
        halign='left',
        valign='middle'
    )
    artifact_cost_label.bind(size=lambda inst, val: setattr(inst, 'text_size', (inst.width, inst.height)))
    artifact_info.add_widget(artifact_cost_label)

    artifact_display.add_widget(artifact_info)
    artifact_box.add_widget(artifact_display)

    # Кнопка добавления в лавку
    add_to_shop_btn = Button(
        text="Добавить чертеж в лавку",
        size_hint_y=None,
        height=btn_height,
        background_normal='',
        background_color=(0.2, 0.6, 0.2, 1),
        font_size=small_font_size,
        disabled=True
    )
    artifact_box.add_widget(add_to_shop_btn)

    main_layout.add_widget(artifact_box)

    # === Кнопки управления ===
    btn_box_height = dp(40) if is_mobile else dp(50)
    btn_box = BoxLayout(
        orientation='horizontal',
        spacing=dp(8) if is_mobile else dp(12),
        size_hint=(1, None),
        height=btn_box_height
    )

    close_btn = Button(
        text="Закрыть",
        size_hint=(0.5, 1),
        background_normal='',
        background_color=(0.7, 0.2, 0.2, 1),
        font_size=normal_font_size,
        bold=True,
        color=(1, 1, 1, 1)
    )
    close_btn.bind(on_release=lambda x: workshop_popup.dismiss())

    btn_box.add_widget(close_btn)
    main_layout.add_widget(btn_box)

    # Добавляем ScrollView для мобильных устройств
    if is_mobile:
        main_scroll.add_widget(main_layout)
        workshop_popup.content = main_scroll
    else:
        workshop_popup.content = main_layout

    workshop_popup.open()

    # === Внутренние функции (остаются без изменений) ===
    def generate_random_name():
        prefixes = ["Артефакт", "Амулет", "Сердце", "Душа", "Звезда"]
        suffixes = ["Силы", "Защиты", "Мудрости", "Света", "Тьмы", "Скорости", "Ловкости", "Выносливости", "Удачи", "Судьбы"]
        prefix = random.choice(prefixes)
        suffix = random.choice(suffixes)
        return f"{prefix} {suffix}"

    def calculate_cost():
        # ... (остается без изменений)
        attack_cost = abs(attack_bonus[0]) * random.uniform(0.4, 1.0) * 1000000
        defense_cost = abs(defense_bonus[0]) * random.uniform(0.6, 1.1) * 1000000

        base_cost = attack_cost + defense_cost

        season_discount = 0
        if len(seasons_bonus[0]) == 1:
            season_discount = 0.65
        elif len(seasons_bonus[0]) == 2:
            if 'Весна' in seasons_bonus[0] and 'Лето' in seasons_bonus[0]:
                season_discount = 0.25
            elif 'Лето' in seasons_bonus[0] and 'Осень' in seasons_bonus[0]:
                season_discount = 0.25
            elif 'Осень' in seasons_bonus[0] and 'Зима' in seasons_bonus[0]:
                season_discount = 0.25
            else:
                season_discount = 0.45
        elif len(seasons_bonus[0]) == 3:
            season_discount = 0.10
        elif len(seasons_bonus[0]) == 4:
            season_discount = 0.10
        elif len(seasons_bonus[0]) == 0:
            base_cost *= 1.12

        negative_modifier = 1.0
        if attack_bonus[0] < 0 or defense_bonus[0] < 0:
            negative_count = sum(1 for x in [attack_bonus[0], defense_bonus[0]] if x < 0)
            negative_modifier = 1 - (negative_count * 0.3)

        total_cost = base_cost * (1 - season_discount) * negative_modifier

        min_cost = 500000
        total_cost = max(min_cost, total_cost)

        return total_cost

    current_artifact_data = [None]

    def create_artifact():
        # ... (остается без изменений)
        if faction.money < 35000000:
            show_message("Ошибка", "Недостаточно средств для создания артефакта (требуется 35 млн крон)")
            return

        if selected_image[0] is None:
            show_message("Ошибка", "Пожалуйста, выберите изображение для артефакта")
            return

        if slot_spinner.text == 'Выберите слот':
            show_message("Ошибка", "Пожалуйста, выберите слот для артефакта")
            return

        try:
            attack_value = int(attack_input.text) if attack_input.text else 0
            defense_value = int(defense_input.text) if defense_input.text else 0
        except ValueError:
            show_message("Ошибка", "Значения атаки и защиты должны быть числами")
            return

        attack_bonus[0] = attack_value
        defense_bonus[0] = defense_value

        total_cost = calculate_cost()

        if total_cost > 20000000000:
            show_message("Ошибка",
                         "Стоимость производства артефакта превышает 20 млрд. крон. \nПожалуйста, уменьшите параметры артефакта.")
            return

        faction.money -= 35000000
        money_label.text = f"Баланс: {format_number(faction.money)}"

        artifact_name = name_input.text
        if not artifact_name:
            artifact_name = generate_random_name()

        image_path = os.path.join(artifact_images_path, selected_image[0])
        artifact_image.source = image_path
        artifact_name_label.text = f"{artifact_name}"
        artifact_cost_label.text = f"Стоимость: {format_number(int(total_cost))} крон"

        add_to_shop_btn.disabled = False

        artifact_type_map = {
            'Руки': 0,
            'Голова': 1,
            'Ноги': 2,
            'Туловище': 3,
            'Аксессуар': 4
        }

        current_artifact_data[0] = {
            'attack': attack_bonus[0],
            'defense': defense_bonus[0],
            'season_name': ', '.join(seasons_bonus[0]),
            'image_url': image_path,
            'name': artifact_name,
            'cost': int(total_cost),
            'artifact_type': artifact_type_map[slot_spinner.text]
        }

    def add_to_shop(instance):
        artifact_data = current_artifact_data[0]
        if artifact_data is None:
            return

        try:
            cursor = db_conn.cursor()
            cursor.execute("SELECT MAX(id) FROM artifacts")
            result = cursor.fetchone()
            current_max_id = result[0]

            if current_max_id is None:
                new_artifact_id = 1
            else:
                new_artifact_id = current_max_id + 1

            cursor.execute('''
                INSERT INTO artifacts (id, attack, defense, season_name, image_url, name, cost, artifact_type)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                new_artifact_id,
                artifact_data['attack'],
                artifact_data['defense'],
                artifact_data['season_name'],
                artifact_data['image_url'],
                artifact_data['name'],
                artifact_data['cost'],
                artifact_data['artifact_type']
            ))

            db_conn.commit()
            current_artifact_data[0] = None
            add_to_shop_btn.disabled = True

            show_message("Успех", f"Артефакт '{artifact_data['name']}' (ID: {new_artifact_id}) добавлен в лавку!")
        except Exception as e:
            show_message("Ошибка", f"Не удалось добавить артефакт в базу данных: {str(e)}")

    def generate_random_name_handler(instance):
        name_input.text = generate_random_name()

    # Привязка событий
    create_btn.bind(on_release=lambda x: create_artifact())
    random_name_btn.bind(on_release=generate_random_name_handler)
    add_to_shop_btn.bind(on_release=add_to_shop)
    