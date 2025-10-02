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
    # === Определение устройства ===
    is_android = hasattr(Window, 'keyboard')

    # === Адаптивные размеры ===
    font_title = sp(16) if not is_android else sp(14)
    font_normal = sp(12) if not is_android else sp(10)
    font_small = sp(10) if not is_android else sp(8)

    padding_main = dp(8) if is_android else dp(12)
    spacing_main = dp(4) if is_android else dp(6)
    btn_height = dp(30) if is_android else dp(35)
    input_height = dp(25) if is_android else dp(30)
    label_height = dp(20) if is_android else dp(25)

    # === Создание всплывающего окна ===
    workshop_popup = Popup(
        title="Мастерская артефактов",
        size_hint=(0.98, 0.95),
        title_size=font_title,
        title_align='center',
        title_color=(0.9, 0.9, 0.9, 1),
        background_color=(0.08, 0.08, 0.08, 0.98),  # Темнее
        separator_color=(0.3, 0.3, 0.3, 1),
        auto_dismiss=False
    )

    # === Данные между экранами ===
    current_data = {
        'icon': None,
        'name': '',
        'attack': 0,
        'defense': 0,
        'season': 'Нет',
        'slot': 'Руки'  # По умолчанию
    }

    # === Список изображений ===
    artifact_images_path = r"files/pict/artifacts/custom"
    if os.path.exists(artifact_images_path):
        image_files = [f for f in os.listdir(artifact_images_path) if
                       f.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp'))]
    else:
        image_files = []

    selected_image = [None]
    current_index = [0]

    # === Функция переключения экрана ===
    def switch_to_screen(screen_func):
        layout = BoxLayout(orientation='vertical', padding=padding_main, spacing=spacing_main)
        screen_func(layout)
        workshop_popup.content = layout

    # === Функция генерации случайного названия ===
    def generate_random_name():
        prefixes = ["Артефакт", "Амулет", "Сердце", "Душа", "Звезда", "Секира", "Меч", "Клинок", "Винтовка", "Мушкет",
                    "Броня", "Панцирь", "Шлем", "Каска", "Сапоги"]
        suffixes = ["Силы", "Защиты", "Мудрости", "Света", "Тьмы", "Мощи", "Вампиров", "Эльфов", "Просветления",
                    "Судьбы", "Веры", "Смерти", "Багровой крови", "Мастеров"]
        prefix = random.choice(prefixes)
        suffix = random.choice(suffixes)
        return f"{prefix} {suffix}"

    # === Экран 1: Выбор иконки и названия ===
    def screen1(layout):
        # Информация о средствах
        info_layout = BoxLayout(orientation='horizontal', spacing=dp(3), size_hint_y=None, height=label_height)
        money_label = Label(
            text=f"Баланс: {format_number(faction.money)}",
            font_size=font_small,
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
            font_size=font_small,
            color=(0.7, 0.7, 0.7, 1),  # Светлее
            halign='right',
            valign='middle',
            size_hint_y=None,
            height=label_height
        )
        cost_label.bind(size=lambda inst, val: setattr(inst, 'text_size', (inst.width, inst.height)))
        info_layout.add_widget(cost_label)
        layout.add_widget(info_layout)

        # Заголовок
        title = Label(
            text="Выберите иконку и название",
            font_size=font_normal,
            color=(0.9, 0.9, 0.9, 1),  # Ярче
            size_hint_y=None,
            height=label_height,
            halign='center',
            valign='middle'
        )
        title.bind(size=lambda inst, val: setattr(inst, 'text_size', (inst.width, inst.height)))
        layout.add_widget(title)

        # Кнопки навигации
        nav_layout = BoxLayout(size_hint_y=None, height=dp(25), spacing=dp(3))
        prev_btn = Button(
            text="<",
            size_hint_x=0.3,
            font_size=font_small,
            background_color=(0.2, 0.2, 0.2, 1),
            background_normal='',
            size_hint_y=None,
            height=dp(25)
        )
        next_btn = Button(
            text=">",
            size_hint_x=0.3,
            font_size=font_small,
            background_color=(0.2, 0.2, 0.2, 1),
            background_normal='',
            size_hint_y=None,
            height=dp(25)
        )
        nav_layout.add_widget(prev_btn)
        nav_layout.add_widget(next_btn)
        layout.add_widget(nav_layout)

        # Отображение текущей иконки
        current_icon_display = Image(
            source="" if not image_files else os.path.join(artifact_images_path, image_files[0]),
            size_hint_y=None,
            height=dp(50) if is_android else dp(60),
            width=dp(50) if is_android else dp(60),
            allow_stretch=True,
            keep_ratio=True
        )
        layout.add_widget(current_icon_display)

        def update_current_icon():
            if not image_files:
                current_icon_display.source = ""
                selected_image[0] = None
                return
            idx = current_index[0] % len(image_files)
            img_path = os.path.join(artifact_images_path, image_files[idx])
            current_icon_display.source = img_path
            selected_image[0] = image_files[idx]

        def on_prev(instance):
            current_index[0] -= 1
            update_current_icon()

        def on_next(instance):
            current_index[0] += 1
            update_current_icon()

        prev_btn.bind(on_release=on_prev)
        next_btn.bind(on_release=on_next)
        update_current_icon()

        # Название
        name_label = Label(
            text="Название артефакта:",
            font_size=font_small,
            color=(0.9, 0.9, 0.9, 1),
            size_hint_y=None,
            height=label_height,
            halign='left',
            valign='middle'
        )
        name_label.bind(size=lambda inst, val: setattr(inst, 'text_size', (inst.width, inst.height)))
        layout.add_widget(name_label)

        name_input = TextInput(
            hint_text="Введите название или оставьте пустым",
            font_size=font_small,
            multiline=False,
            size_hint_y=None,
            height=input_height,
            padding=[dp(5), dp(3)],
            background_color=(0.15, 0.15, 0.15, 1),
            foreground_color=(0.9, 0.9, 0.9, 1),
            cursor_color=(0.9, 0.9, 0.9, 1),
            size_hint_x=1
        )
        layout.add_widget(name_input)

        # Кнопка случайного названия
        random_name_btn = Button(
            text="Случайное",
            size_hint_y=None,
            height=btn_height * 0.8,
            background_normal='',
            background_color=(0.2, 0.5, 0.5, 1),
            font_size=font_small,
            size_hint_x=1
        )
        layout.add_widget(random_name_btn)

        # Кнопки навигации внизу
        btn_box = BoxLayout(orientation='horizontal', spacing=dp(3), size_hint=(1, None), height=btn_height)
        close_btn = Button(
            text="Закрыть",
            size_hint=(0.5, 1),
            background_normal='',
            background_color=(0.7, 0.2, 0.2, 1),
            font_size=font_normal,
            color=(1, 1, 1, 1)
        )
        next_scr_btn = Button(
            text="Далее",
            size_hint=(0.5, 1),
            background_normal='',
            background_color=(0.2, 0.6, 0.2, 1),
            font_size=font_normal,
            color=(1, 1, 1, 1)
        )
        btn_box.add_widget(close_btn)
        btn_box.add_widget(next_scr_btn)
        layout.add_widget(btn_box)

        # Привязка событий
        def on_next_screen(instance):
            current_data['icon'] = selected_image[0]
            current_data['name'] = name_input.text
            if not current_data['icon']:
                show_message("Ошибка", "Пожалуйста, выберите иконку")
                return
            switch_to_screen(screen2)

        def on_random_name(instance):
            name_input.text = generate_random_name()
            current_data['name'] = name_input.text

        close_btn.bind(on_release=lambda x: workshop_popup.dismiss())
        next_scr_btn.bind(on_release=on_next_screen)
        random_name_btn.bind(on_release=on_random_name)

    # === Экран 2: Выбор характеристик ===
    def screen2(layout):
        # Заголовок
        title = Label(
            text="Выберите характеристики",
            font_size=font_normal,
            color=(0.9, 0.9, 0.9, 1),
            size_hint_y=None,
            height=label_height,
            halign='center',
            valign='middle'
        )
        title.bind(size=lambda inst, val: setattr(inst, 'text_size', (inst.width, inst.height)))
        layout.add_widget(title)

        # Атака
        attack_label = Label(
            text="Атака (%):",
            font_size=font_small,
            color=(0.9, 0.9, 0.9, 1),
            size_hint_y=None,
            height=label_height,
            halign='left',
            valign='middle'
        )
        attack_label.bind(size=lambda inst, val: setattr(inst, 'text_size', (inst.width, inst.height)))
        layout.add_widget(attack_label)

        attack_input = TextInput(
            text=str(current_data['attack']),
            font_size=font_small,
            multiline=False,
            input_filter='int',
            size_hint_y=None,
            height=input_height,
            padding=[dp(5), dp(3)],
            background_color=(0.15, 0.15, 0.15, 1),
            foreground_color=(0.9, 0.9, 0.9, 1),
            cursor_color=(0.9, 0.9, 0.9, 1)
        )
        layout.add_widget(attack_input)

        # Защита
        defense_label = Label(
            text="Защита (%):",
            font_size=font_small,
            color=(0.9, 0.9, 0.9, 1),
            size_hint_y=None,
            height=label_height,
            halign='left',
            valign='middle'
        )
        defense_label.bind(size=lambda inst, val: setattr(inst, 'text_size', (inst.width, inst.height)))
        layout.add_widget(defense_label)

        defense_input = TextInput(
            text=str(current_data['defense']),
            font_size=font_small,
            multiline=False,
            input_filter='int',
            size_hint_y=None,
            height=input_height,
            padding=[dp(5), dp(3)],
            background_color=(0.15, 0.15, 0.15, 1),
            foreground_color=(0.9, 0.9, 0.9, 1),
            cursor_color=(0.9, 0.9, 0.9, 1)
        )
        layout.add_widget(defense_input)

        # Сезон — теперь кнопки с комбинациями
        season_label = Label(
            text="Сезон артефакта:",
            font_size=font_small,
            color=(0.9, 0.9, 0.9, 1),
            size_hint_y=None,
            height=label_height,
            halign='left',
            valign='middle'
        )
        season_label.bind(size=lambda inst, val: setattr(inst, 'text_size', (inst.width, inst.height)))
        layout.add_widget(season_label)

        # Кнопки для выбора сезона
        season_layout = BoxLayout(orientation='horizontal', spacing=dp(3), size_hint_y=None, height=dp(25))
        prev_season_btn = Button(
            text="<",
            size_hint_x=0.2,
            font_size=font_small,
            background_color=(0.2, 0.2, 0.2, 1),
            background_normal='',
            size_hint_y=None,
            height=dp(25)
        )
        current_season_label = Label(
            text=current_data['season'],
            font_size=font_small,
            color=(0.9, 0.9, 0.9, 1),
            halign='center',
            valign='middle',
            size_hint_x=0.6
        )
        current_season_label.bind(size=lambda inst, val: setattr(inst, 'text_size', (inst.width, inst.height)))
        next_season_btn = Button(
            text=">",
            size_hint_x=0.2,
            font_size=font_small,
            background_color=(0.2, 0.2, 0.2, 1),
            background_normal='',
            size_hint_y=None,
            height=dp(25)
        )
        season_layout.add_widget(prev_season_btn)
        season_layout.add_widget(current_season_label)
        season_layout.add_widget(next_season_btn)
        layout.add_widget(season_layout)

        # Список комбинаций сезонов
        seasons = [
            'Нет', 'Весна', 'Лето', 'Осень', 'Зима',
            'Весна, Лето', 'Весна, Осень', 'Весна, Зима',
            'Лето, Осень', 'Лето, Зима', 'Осень, Зима',
            'Весна, Лето, Осень', 'Весна, Лето, Зима',
            'Весна, Осень, Зима', 'Лето, Осень, Зима',
            'Все'
        ]
        season_index = [seasons.index(current_data['season']) if current_data['season'] in seasons else 0]

        def update_season_label():
            current_season_label.text = seasons[season_index[0]]

        def on_prev_season(instance):
            season_index[0] = (season_index[0] - 1) % len(seasons)
            update_season_label()

        def on_next_season(instance):
            season_index[0] = (season_index[0] + 1) % len(seasons)
            update_season_label()

        prev_season_btn.bind(on_release=on_prev_season)
        next_season_btn.bind(on_release=on_next_season)

        # Кнопки навигации
        btn_box = BoxLayout(orientation='horizontal', spacing=dp(3), size_hint=(1, None), height=btn_height)
        back_btn = Button(
            text="Назад",
            size_hint=(0.5, 1),
            background_normal='',
            background_color=(0.6, 0.6, 0.2, 1),
            font_size=font_normal,
            color=(1, 1, 1, 1)
        )
        next_scr_btn = Button(
            text="Далее",
            size_hint=(0.5, 1),
            background_normal='',
            background_color=(0.2, 0.6, 0.2, 1),
            font_size=font_normal,
            color=(1, 1, 1, 1)
        )
        btn_box.add_widget(back_btn)
        btn_box.add_widget(next_scr_btn)
        layout.add_widget(btn_box)

        # Привязка событий
        def on_back(instance):
            switch_to_screen(screen1)

        def on_next_screen(instance):
            try:
                current_data['attack'] = int(attack_input.text) if attack_input.text else 0
                current_data['defense'] = int(defense_input.text) if defense_input.text else 0
            except ValueError:
                show_message("Ошибка", "Атака и защита должны быть числами")
                return
            current_data['season'] = seasons[season_index[0]]
            switch_to_screen(screen3)

        back_btn.bind(on_release=on_back)
        next_scr_btn.bind(on_release=on_next_screen)

    # === Экран 3: Выбор слота и создание ===
    def screen3(layout):
        # Заголовок
        title = Label(
            text="Выберите слот и создайте чертеж артефакта",
            font_size=font_normal,
            color=(0.9, 0.9, 0.9, 1),
            size_hint_y=None,
            height=label_height,
            halign='center',
            valign='middle'
        )
        title.bind(size=lambda inst, val: setattr(inst, 'text_size', (inst.width, inst.height)))
        layout.add_widget(title)

        # Слот — теперь кнопки
        slot_label = Label(
            text="Слот артефакта:",
            font_size=font_small,
            color=(0.9, 0.9, 0.9, 1),
            size_hint_y=None,
            height=label_height,
            halign='left',
            valign='middle'
        )
        slot_label.bind(size=lambda inst, val: setattr(inst, 'text_size', (inst.width, inst.height)))
        layout.add_widget(slot_label)

        # Кнопки для выбора слота
        slot_layout = BoxLayout(orientation='horizontal', spacing=dp(3), size_hint_y=None, height=dp(25))
        prev_slot_btn = Button(
            text="<",
            size_hint_x=0.2,
            font_size=font_small,
            background_color=(0.2, 0.2, 0.2, 1),
            background_normal='',
            size_hint_y=None,
            height=dp(25)
        )
        current_slot_label = Label(
            text=current_data['slot'],
            font_size=font_small,
            color=(0.9, 0.9, 0.9, 1),
            halign='center',
            valign='middle',
            size_hint_x=0.6
        )
        current_slot_label.bind(size=lambda inst, val: setattr(inst, 'text_size', (inst.width, inst.height)))
        next_slot_btn = Button(
            text=">",
            size_hint_x=0.2,
            font_size=font_small,
            background_color=(0.2, 0.2, 0.2, 1),
            background_normal='',
            size_hint_y=None,
            height=dp(25)
        )
        slot_layout.add_widget(prev_slot_btn)
        slot_layout.add_widget(current_slot_label)
        slot_layout.add_widget(next_slot_btn)
        layout.add_widget(slot_layout)

        # Список слотов
        slots = ['Руки', 'Голова', 'Ноги', 'Туловище', 'Аксессуар']
        slot_index = [slots.index(current_data['slot']) if current_data['slot'] in slots else 0]

        def update_slot_label():
            current_slot_label.text = slots[slot_index[0]]

        def on_prev_slot(instance):
            slot_index[0] = (slot_index[0] - 1) % len(slots)
            update_slot_label()

        def on_next_slot(instance):
            slot_index[0] = (slot_index[0] + 1) % len(slots)
            update_slot_label()

        prev_slot_btn.bind(on_release=on_prev_slot)
        next_slot_btn.bind(on_release=on_next_slot)

        # === Отображение итогового артефакта ===
        artifact_title = Label(
            text="Итоговый артефакт:",
            font_size=font_normal,
            color=(0.9, 0.9, 0.9, 1),
            size_hint_y=None,
            height=label_height,
            halign='center',
            valign='middle'
        )
        artifact_title.bind(size=lambda inst, val: setattr(inst, 'text_size', (inst.width, inst.height)))
        layout.add_widget(artifact_title)

        artifact_display = BoxLayout(orientation='horizontal', spacing=dp(5), size_hint_y=None, height=dp(45))

        # Подгружаем иконку правильно — с полным путем
        full_icon_path = os.path.join(artifact_images_path, current_data['icon']) if current_data['icon'] else ''
        artifact_image = Image(
            source=full_icon_path,
            size_hint_x=None,
            width=dp(35),
            allow_stretch=True,
            keep_ratio=True
        )
        artifact_display.add_widget(artifact_image)

        artifact_info = BoxLayout(orientation='vertical', spacing=dp(1))
        artifact_name_label = Label(
            text=current_data['name'] if current_data['name'] else "Название не задано",
            font_size=font_small,
            color=(0.9, 0.9, 0.9, 1),
            halign='left',
            valign='middle',
            size_hint_y=None,
            height=dp(18)
        )
        artifact_name_label.bind(size=lambda inst, val: setattr(inst, 'text_size', (inst.width, inst.height)))
        artifact_info.add_widget(artifact_name_label)

        # Расчет стоимости
        attack_bonus = current_data['attack']
        defense_bonus = current_data['defense']

        # Преобразуем строку сезонов в список
        if current_data['season'] == 'Нет':
            seasons_bonus = []
        elif current_data['season'] == 'Все':
            seasons_bonus = ['Весна', 'Лето', 'Осень', 'Зима']
        else:
            seasons_bonus = [s.strip() for s in current_data['season'].split(',')]

        # Логика расчета стоимости
        attack_cost = abs(attack_bonus) * random.uniform(0.4, 1.0) * 1000000
        defense_cost = abs(defense_bonus) * random.uniform(0.6, 1.1) * 1000000
        base_cost = attack_cost + defense_cost

        # === Расчет скидки по сезонам ===
        season_discount = 0
        if len(seasons_bonus) == 0:
            base_cost *= 1.12  # Нет влияния сезонов + 12%
        elif len(seasons_bonus) == 1:
            season_discount = 0.75  # 1 сезон = -75%
        elif len(seasons_bonus) == 2:
            # Проверим, идут ли сезоны подряд
            consecutive_pairs = [
                ['Весна', 'Лето'],
                ['Лето', 'Осень'],
                ['Осень', 'Зима'],
                ['Зима', 'Весна']
            ]
            if sorted(seasons_bonus) in [sorted(p) for p in consecutive_pairs]:
                season_discount = 0.25  # 2 сезона подряд = -25%
            else:
                season_discount = 0.45  # 2 сезона раздельно = -45%
        elif len(seasons_bonus) == 3:
            season_discount = 0.10  # 3 сезона = -10%
        elif len(seasons_bonus) == 4:
            season_discount = 0.10  # Все 4 сезона = -10%

        negative_modifier = 1.0
        if attack_bonus < 0 or defense_bonus < 0:
            negative_count = sum(1 for x in [attack_bonus, defense_bonus] if x < 0)
            negative_modifier = 1 - (negative_count * 0.3)

        total_cost = base_cost * (1 - season_discount) * negative_modifier
        min_cost = 500000
        total_cost = max(min_cost, total_cost)

        artifact_cost_label = Label(
            text=f"Стоимость: {format_number(int(total_cost))} крон",
            font_size=font_small,
            color=(0.9, 0.9, 0.9, 1),
            halign='left',
            valign='middle',
            size_hint_y=None,
            height=dp(18)
        )
        artifact_cost_label.bind(size=lambda inst, val: setattr(inst, 'text_size', (inst.width, inst.height)))
        artifact_info.add_widget(artifact_cost_label)

        artifact_display.add_widget(artifact_info)
        layout.add_widget(artifact_display)

        # Кнопка создания
        create_btn = Button(
            text="Создать чертеж артефакта",
            size_hint_y=None,
            height=btn_height * 0.9,
            background_normal='',
            background_color=(0.6, 0.2, 0.6, 1),
            font_size=font_normal,
            bold=True,
            size_hint_x=1
        )
        layout.add_widget(create_btn)

        # Кнопки навигации — добавим кнопку "Назад"
        btn_box = BoxLayout(orientation='horizontal', spacing=dp(3), size_hint=(1, None), height=btn_height)
        back_btn = Button(
            text="Назад",
            size_hint=(0.5, 1),
            background_normal='',
            background_color=(0.6, 0.6, 0.2, 1),
            font_size=font_normal,
            color=(1, 1, 1, 1)
        )
        close_btn = Button(
            text="Закрыть",
            size_hint=(0.5, 1),
            background_normal='',
            background_color=(0.7, 0.2, 0.2, 1),
            font_size=font_normal,
            color=(1, 1, 1, 1)
        )
        btn_box.add_widget(back_btn)
        btn_box.add_widget(close_btn)
        layout.add_widget(btn_box)

        # Привязка событий
        def on_back(instance):
            current_data['slot'] = slots[slot_index[0]]  # Сохраняем слот перед возвратом
            switch_to_screen(screen2)

        def on_close(instance):
            workshop_popup.dismiss()

        def on_create(instance):
            current_data['slot'] = slots[slot_index[0]]  # Обновляем слот перед созданием
            if total_cost > 20000000000:
                show_message("Ошибка",
                             "Стоимость производства артефакта превышает 20 млрд. крон. \nПожалуйста, уменьшите параметры артефакта.")
                return

            if faction.money < 35000000:
                show_message("Ошибка", "Недостаточно средств для создания чертежа артефакта (требуется 35 млн крон)")
                return

            faction.money -= 35000000
            money_label = Label(
                text=f"Баланс: {format_number(faction.money)}",
                font_size=font_small,
                color=(0.9, 0.9, 0.9, 1),
                halign='left',
                valign='middle',
                size_hint_y=None,
                height=label_height
            )
            money_label.bind(size=lambda inst, val: setattr(inst, 'text_size', (inst.width, inst.height)))

            artifact_name = current_data['name']
            if not artifact_name:
                artifact_name = generate_random_name()

            image_path = os.path.join(artifact_images_path, current_data['icon'])

            artifact_type_map = {
                'Руки': 0,
                'Голова': 1,
                'Ноги': 2,
                'Туловище': 3,
                'Аксессуар': 4
            }

            # Добавляем в базу
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
                    attack_bonus,
                    defense_bonus,
                    ', '.join(seasons_bonus),
                    image_path,
                    artifact_name,
                    int(total_cost),
                    artifact_type_map[current_data['slot']]
                ))

                db_conn.commit()
                show_message("Успех", f"Артефакт '{artifact_name}' (ID: {new_artifact_id}) добавлен в лавку!")
                workshop_popup.dismiss()
            except Exception as e:
                show_message("Ошибка", f"Не удалось добавить артефакт в базу данных: {str(e)}")

        back_btn.bind(on_release=on_back)
        close_btn.bind(on_release=on_close)
        create_btn.bind(on_release=on_create)

    # === Открываем первый экран ===
    switch_to_screen(screen1)
    workshop_popup.open()
