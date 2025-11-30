from game_process import GameScreen
from ui import *
from db_lerdon_connect import *
from generate_map import generate_map_and_cities

RANK_TO_FILENAME = {
    # Группа 1: Военные
    "Главнокомандующий": "19.png",   # старший
    "Верховный маршал": "18.png",
    "Генерал-фельдмаршал": "17.png",
    "Генерал армии": "16.png",
    "Генерал-полковник": "15.png",
    "Генерал-лейтенант": "14.png",
    "Генерал-майор": "13.png",
    "Бригадный генерал": "12.png",
    "Коммандер": "11.png",
    "Полковник": "10.png",
    "Подполковник": "9.png",
    "Майор": "8.png",
    "Капитан-лейтенант": "7.png",
    "Капитан": "6.png",
    "Платиновый лейтенант": "5.png",
    "Серебряный лейтенант": "4.png",
    "Сержант": "3.png",
    "Прапорщик": "2.png",
    "Рядовой": "1.png",               # младший

    # Группа 2: Тьма
    "Владыка ночи": "19.png",
    "Вечный граф": "18.png",
    "Темный лорд": "17.png",
    "Князь тьмы": "16.png",
    "Старший вампир": "15.png",
    "Ночной страж": "14.png",
    "Теневой охотник": "13.png",
    "Призрачный убийца": "12.png",
    "Темный воитель": "11.png",
    "Ночной рейнджер": "10.png",
    "Младший вампир": "9.png",
    "Темный слуга": "8.png",
    "Младший слуга вампира": "7.png",
    "Ночная тень": "6.png",
    "Плутонический следопыт": "5.png",
    "Серебряный следопыт": "4.png",
    "Вестник смерти": "3.png",
    "Пепел прошлого": "2.png",
    "Укушенный": "1.png",

    # Группа 3: Лесные
    "Верховный правитель": "19.png",
    "Лесной повелитель": "18.png",
    "Вечный страж": "17.png",
    "Магистр природы": "16.png",
    "Лесной воевода": "15.png",
    "Хранитель лесов": "14.png",
    "Мастер стрелы": "13.png",
    "Лесной командир": "12.png",
    "Древесный защитник": "11.png",
    "Мастер лука": "10.png",
    "Ловкий стрелок": "9.png",
    "Юркий воин": "8.png",
    "Стремительный охотник": "7.png",
    "Зеленый страж": "6.png",
    "Природный следопыт": "5.png",
    "Ученик жрицы": "4.png",
    "Начинающий охотник": "3.png",
    "Молодой эльф": "2.png",
    "Младший ученик эльфа": "1.png",

    # Группа 4: Инквизиция
    "Верховный Инквизитор": "19.png",
    "Великий Охотник на Еретиков": "18.png",
    "Магистр Святого Огня": "17.png",
    "Гранд-Инквизитор": "16.png",
    "Судья Правой Руки": "15.png",
    "Главный Следователь": "14.png",
    "Огонь Вердикта": "13.png",
    "Страж Чистоты": "12.png",
    "Палач Ереси": "11.png",
    "Исполнитель Клятвы": "10.png",
    "Сержант Ордена": "9.png",
    "Офицер Инквизиции": "8.png",
    "Кандидат Света": "7.png",
    "Новичок Клятвы": "6.png",
    "Причастный Костра": "5.png",
    "Ученик Веры": "4.png",
    "Искренний": "3.png",
    "Слушающий Слово": "2.png",
    "Пепел Греха": "1.png",

    # Группа 5: Пустыня
    "Повелитель Огня и Пустыни": "19.png",
    "Око Бури": "18.png",
    "Хранитель Песков": "17.png",
    "Гнев Ветров": "16.png",
    "Тень Дракона": "15.png",
    "Жар Пустыни": "14.png",
    "Клинок Вечного Солнца": "13.png",
    "Степной Судья": "12.png",
    "Мастер Ярости": "11.png",
    "Искра Пламени": "10.png",
    "Бегущий по Пескам": "9.png",
    "Вестник Жара": "8.png",
    "Порождение Торнадо": "7.png",
    "Песчаный Странник": "6.png",
    "Пыль Гривы": "5.png",
    "Песчинка": "4.png",
    "Забытый Ветром": "3.png",
    "Проклятый Солнцем": "2.png",
    "Пепел Пустыни": "1.png",
}

def save_last_clicked_city(conn, city_name: str):
    """
    Сохраняет последний выбранный город в базу данных.
    :param conn: Активное соединение с базой данных.
    :param city_name: Название города.
    """
    cur = conn.cursor()
    cur.execute("INSERT OR REPLACE INTO last_click (id, city_name) VALUES (1, ?)", (city_name,))
    conn.commit()


def load_cities_from_db(conn, selected_kingdom):
    """
    Загружает данные о городах для выбранного княжества.
    :param conn: Активное соединение с базой данных.
    :param selected_kingdom: Название княжества.
    :return: Список словарей с данными о городах.
    """
    cursor = conn.cursor()
    try:
        query = ("SELECT id, name, coordinates, faction, icon_coordinates, label_coordinates, color_faction FROM cities "
                 "WHERE faction = ?")
        cursor.execute(query, (selected_kingdom,))
        rows = cursor.fetchall()
        cities = []
        for row in rows:
            cities.append({
                'id': row[0],
                'name': row[1],
                'coordinates': row[2],
                'faction': row[3],
                'icon_coordinates': row[4],
                'label_coordinates': row[5],
                'color_faction': row[6]
            })
        return cities
    except sqlite3.Error as e:
        print(f"Ошибка при загрузке данных о городах: {e}")
        return []


def restore_from_backup(conn):
    """
    Восстанавливает данные из стандартных таблиц в рабочие.
    :param conn: Активное соединение с базой данных.
    """
    cursor = conn.cursor()
    tables_to_restore = [
        ("diplomacies_default", "diplomacies"),
        ("relations_default", "relations"),
        ("resources_default", "resources"),
        ("units_default", "units"),
        ("artifacts_default", "artifacts"),
        ("artifacts_ai_default", "artifacts_ai")
    ]

    try:
        cursor.execute("BEGIN IMMEDIATE")  # Блокируем на время восстановления

        for default_table, working_table in tables_to_restore:
            cursor.execute(f"DELETE FROM {working_table}")
            cursor.execute(f"INSERT INTO {working_table} SELECT * FROM {default_table}")

        conn.commit()
        print("Данные успешно восстановлены из бэкапа.")
    except sqlite3.Error as e:
        conn.rollback()
        print(f"Ошибка восстановления данных: {e}")


def clear_tables(conn):
    """
    Очищает данные из указанных таблиц базы данных.
    :param conn: Подключение к базе данных SQLite.
    """
    tables_to_clear = [
        "buildings",
        "cities",
        "diplomacies",
        "garrisons",
        "resources",
        "trade_agreements",
        "turn",
        "turn_save",
        "armies",
        "political_systems",
        "karma",
        "user_faction",
        "units",
        "queries",
        "results",
        "auto_build_settings",
        "interface_coord",
        "hero_equipment",
        "ai_hero_equipment",
        "effects_seasons",
        "nobles",
        "noble_events",
        "coup_attempts",
        "artifacts",
        "artifacts_ai",
        "artifact_effects_log",
    ]

    cursor = conn.cursor()

    try:
        for table in tables_to_clear:
            # Используем TRUNCATE или DELETE для очистки таблицы
            cursor.execute(f"DELETE FROM {table};")
            print(f"Таблица '{table}' успешно очищена.")

        # Фиксируем изменения
        conn.commit()
    except sqlite3.Error as e:
        print(f"Ошибка при очистке таблиц: {e}")
        conn.rollback()  # Откат изменений в случае ошибки

class AuthorScreen(Screen):
    def __init__(self, conn, **kwargs):
        super(AuthorScreen, self).__init__(**kwargs)
        self.conn = conn
        root = FloatLayout()

        # === Статичный фон ===
        # Замените 'files/menu/author.jpg' на путь к вашему изображению-фону.
        # Рекомендуется использовать изображение в формате .jpg или .png.
        self.bg_image = Image(
            source='files/menu/author.jpg', # <- Укажите путь к вашему изображению
            allow_stretch=True, # Растягивать под размер виджета
            keep_ratio=False,   # Игнорировать соотношение сторон
            size_hint=(1, 1),   # Занимает весь родительский контейнер
            pos_hint={'center_x': 0.5, 'center_y': 0.5}
        )
        root.add_widget(self.bg_image)
        # ---

        # Прозрачный слой с контентом (остается без изменений)
        layout = BoxLayout(orientation='vertical',
                           padding=dp(20),
                           spacing=dp(20),
                           size_hint=(0.9, 0.8),
                           pos_hint={'center_x': 0.5, 'center_y': 0.5})

        # Заголовок (остается без изменений)
        title_label = Label(
            text="[b]Сообщество Лэрдона[/b]",
            markup=True,
            font_size='28sp',
            size_hint_y=None,
            height=dp(50),
            outline_color=(0, 0, 0, 1),
            outline_width=2,
            color=(1, 1, 1, 1),
            halign="center"
        )
        layout.add_widget(title_label)

        top_layout = BoxLayout(
            orientation='vertical',
            size_hint=(1, None),
            height=dp(60),  # Высота окантовки
            pos_hint={'top': 1}  # Прижимаем к верху экрана
        )

        # Создаем фон для окантовки (остается без изменений)
        from kivy.graphics import Color, Rectangle
        with top_layout.canvas.before:
            Color(0, 0, 0, 0.5)  # Черный цвет с 50% прозрачностью
            self.top_bg_rect = Rectangle(size=top_layout.size, pos=top_layout.pos)

        # Обновляем размер и позицию фона при изменении размера виджета (остается без изменений)
        def update_top_bg_rect(instance, value):
            self.top_bg_rect.pos = instance.pos
            self.top_bg_rect.size = instance.size
        top_layout.bind(pos=update_top_bg_rect, size=update_top_bg_rect)

        # Создаем саму надпись (остается без изменений)
        greeting_label = Label(
            text="[b][color=#FFD700]Желаю Вам приятно провести время в моем мире![/color][/b]",
            markup=True,
            font_size='18sp',
            outline_color=(0, 0, 0, 1),
            outline_width=1.5,
            halign="center",
            valign="middle"
        )
        greeting_label.bind(size=greeting_label.setter('text_size'))
        top_layout.add_widget(greeting_label)
        root.add_widget(top_layout)

        # Ссылки-карточки (остается без изменений)
        link_box = BoxLayout(orientation='vertical', spacing=dp(10), size_hint_y=None, height=dp(100))

        vk_label = Label(
            text="[ref=https://vk.com/destianfarbius  ][color=#00aaff]Страница автора ВКонтакте[/color][/ref]",
            markup=True,
            font_size='18sp',
            size_hint_y=None,
            height=dp(40),
            outline_color=(0, 0, 0, 1),
            outline_width=2,
            halign="center",
            valign="middle"
        )
        vk_label.bind(on_ref_press=self.open_link)

        tg_label = Label(
            text="[ref=https://t.me/+scOGK6ph6r03YmU6  ][color=#00aaff]Присоединиться к Telegram[/color][/ref]",
            markup=True,
            font_size='18sp',
            size_hint_y=None,
            height=dp(40),
            outline_color=(0, 0, 0, 1),
            outline_width=2,
            halign="center",
            valign="middle"
        )
        tg_label.bind(on_ref_press=self.open_link)

        link_box.add_widget(vk_label)
        link_box.add_widget(tg_label)
        layout.add_widget(link_box)

        # Новая желтая подпись внизу (остается без изменений)
        credits_label = Label(
            text="[color=#FFD700]Все иконки и изображения были разработаны с использованием ресурсов: \n Flaticon.com, Qwen, ChatGPT, а так же Шедеврума.[/color]",
            markup=True,
            font_size='12sp',
            size_hint_y=None,
            height=dp(40),
            outline_color=(0, 0, 0, 1),
            outline_width=2,
            halign="center",
            valign="middle"
        )
        layout.add_widget(credits_label)

        # Кнопка "Назад" — уменьшена (остается без изменений)
        back_button = Button(
            text="Назад",
            size_hint=(0.3, None),
            height=dp(40),
            pos_hint={'center_x': 0.5},
            background_color=(0.2, 0.6, 1, 0.8),
            color=(1, 1, 1, 1),
            font_size='14sp'
        )
        back_button.bind(on_press=self.go_back)
        layout.add_widget(back_button)

        root.add_widget(layout)
        self.add_widget(root)

    def go_back(self, instance):
        # Нет видео для остановки, упрощаем функцию
        app = App.get_running_app()
        app.root.clear_widgets()
        app.root.add_widget(MenuWidget(self.conn))

    def open_link(self, instance, url):
        webbrowser.open(url)


class LoadingScreen(FloatLayout):
    def __init__(self, conn, selected_map=None, **kwargs):
        super(LoadingScreen, self).__init__(**kwargs)
        self.conn = conn
        self.selected_map = selected_map

        # === Фон ===
        with self.canvas.before:
            self.bg_rect = Rectangle(
                source='files/menu/loading_bg.jpg',
                pos=self.pos,
                size=self.size
            )
        self.bind(pos=self._update_bg, size=self._update_bg)

        # === Контейнер шкалы ===
        self.pb_container = FloatLayout(
            size_hint=(0.8, None),
            height=dp(30),
            pos_hint={'center_x': 0.5, 'center_y': 0.2}
        )

        with self.pb_container.canvas.before:
            # === Фон прогресс-бара ===
            Color(0.1, 0.1, 0.1, 0.8)
            self.pb_rect = Rectangle(size=self.pb_container.size, pos=self.pb_container.pos)

            # === Заливка прогресса ===
            Color(1, 1, 1, 1)  # Начальный белый цвет
            self.pb_fill = Rectangle(size=(0, self.pb_container.height), pos=self.pb_container.pos)

            # === Обводка ===
            Color(1, 1, 1, 0.9)
            self.pb_border = Line(
                rectangle=(
                    self.pb_container.x - dp(1),
                    self.pb_container.y - dp(1),
                    self.pb_container.width + dp(2),
                    self.pb_container.height + dp(2)
                ),
                width=dp(1.3)
            )

        self.pb_container.bind(pos=self.update_pb_canvas, size=self.update_pb_canvas)
        self.add_widget(self.pb_container)

        # === Текст загрузки ===
        self.label = Label(
            markup=True,
            text="[color=#00ccff]Готовим ресурсы... 0%[/color]",
            font_size='19sp',
            pos_hint={'center_x': 0.5, 'center_y': 0.11},
            size_hint=(1, None),
            halign='center'
        )
        self.add_widget(self.label)

        # === Прогресс ===
        self.current_progress = 0
        self.target_progress = 0

        # === Шаги загрузки ===
        self.loading_steps = [
            self.step_check_db,
            self.step_cleanup_cache,
            self.step_restore_backup,
            self.step_load_assets,
            self.step_complete
        ]
        Clock.schedule_once(self.start_loading)

    # === Обновление заливки и рамки ===
    def update_pb_canvas(self, *args):
        self.pb_rect.pos = self.pb_container.pos
        self.pb_rect.size = self.pb_container.size

        fill_width = (self.current_progress / 100) * self.pb_container.width
        self.pb_fill.pos = self.pb_container.pos
        self.pb_fill.size = (fill_width, self.pb_container.height)

        # === Плавный переход цвета от белого → голубого → синего ===
        progress_ratio = self.current_progress / 100.0
        if progress_ratio <= 0.5:
            # От белого к голубому (0–50%)
            r = 1 - progress_ratio * 0.5       # 1 → 0.75
            g = 1 - progress_ratio * 0.3       # 1 → 0.85
            b = 1                              # остаётся бело-голубым
        else:
            # От голубого к насыщенно-синему (50–100%)
            t = (progress_ratio - 0.5) * 2     # нормализуем вторую половину
            r = 0.75 - t * 0.55                # 0.75 → 0.2
            g = 0.85 - t * 0.65                # 0.85 → 0.2
            b = 1 - t * 0.3                    # 1 → 0.7

        with self.pb_container.canvas:
            Color(r, g, b, 1)
            self.pb_fill.size = (fill_width, self.pb_container.height)
            self.pb_fill.pos = self.pb_container.pos

        # Обводка
        self.pb_border.rectangle = (
            self.pb_container.x - dp(1),
            self.pb_container.y - dp(1),
            self.pb_container.width + dp(2),
            self.pb_container.height + dp(2)
        )

    # === Логика загрузки ===
    def start_loading(self, dt):
        self.run_next_step()

    def run_next_step(self, *args):
        if self.loading_steps:
            step = self.loading_steps.pop(0)
            step()
        else:
            self.target_progress = 100
            self.smooth_progress_update()

    def update_progress_target(self, delta):
        self.target_progress += delta

    def smooth_progress_update(self, dt=0):
        if abs(self.target_progress - self.current_progress) > 0.5:
            self.current_progress += (self.target_progress - self.current_progress) * 0.1
            percent = int(self.current_progress)
            self.label.text = f"[color=#00ccff]Готовим ресурсы... {percent}%[/color]"
            self.update_pb_canvas()
            Clock.schedule_once(self.smooth_progress_update, 0.016)
        else:
            self.current_progress = self.target_progress
            percent = int(self.current_progress)
            self.label.text = f"[color=#00ccff]Готовим ресурсы... {percent}%[/color]"
            self.update_pb_canvas()

            if self.target_progress >= 100:
                self.label.text = "[color=#ff0000]НАЧИНАЕМ![/color]"
                Clock.schedule_once(self.switch_to_menu, 0.8)

    def update_progress(self, delta):
        self.update_progress_target(delta)
        self.smooth_progress_update()

    # === Шаги ===
    def step_check_db(self):
        print("Шаг 1: Проверка базы данных...")
        self.update_progress(20)
        Clock.schedule_once(self.run_next_step, 0.5)

    def step_cleanup_cache(self):
        print("Шаг 2: Очистка кэша...")
        from threading import Thread
        def cleanup_task():
            clear_tables(self.conn)
            Clock.schedule_once(self.run_next_step, 0)
        Thread(target=cleanup_task, daemon=True).start()

    def step_restore_backup(self):
        print("Шаг 3: Восстановление из бэкапа...")
        self.update_progress(20)
        Clock.schedule_once(self.run_next_step, 0.5)

    def step_load_assets(self):
        print("Шаг 4: Загрузка ресурсов...")
        self.update_progress(10)

        from threading import Thread
        def load_task():
            time.sleep(0.3)
            Clock.schedule_once(lambda dt: self.update_progress(10), 0)
            time.sleep(0.3)
            Clock.schedule_once(self.run_next_step, 0)
        Thread(target=load_task, daemon=True).start()

    def step_complete(self):
        print("Шаг 5: Финализация...")
        self.update_progress(20)
        Clock.schedule_once(self.run_next_step, 0.3)

    # === Вспомогательные ===
    def _update_bg(self, *args):
        self.bg_rect.pos = self.pos
        self.bg_rect.size = self.size

    def switch_to_menu(self, dt):
        self.bg_rect.source = 'files/menu/main_fon.jpg'
        self.bg_rect.texture = CoreImage('files/menu/main_fon.jpg').texture
        self.clear_widgets()
        self.add_widget(MenuWidget(self.conn, self.selected_map))


class MapWidget(Widget):
    def __init__(self, selected_kingdom=None, player_kingdom=None, conn=None, **kwargs):
        super(MapWidget, self).__init__(**kwargs)
        self.conn = conn
        # Храним пары (имя_города, фракция) для отрисовки на canvas
        self.fortress_data_for_canvas = []
        # Храним виджеты иконок отдельно
        self.fortress_icon_widgets = {}
        self.current_player_kingdom = player_kingdom
        self.player_city_icon_widget = None
        # Флаг для однократного запуска мигания
        self.has_blinked = False

        # Хранение идентификатора запланированной задачи
        self.update_cities_event = None

        # Настройки карты
        self.base_map_width = 1200
        self.base_map_height = 800
        self.map_scale = self.calculate_scale()
        self.map_pos = self.calculate_centered_position()

        generate_map_and_cities(self.conn)
        self.random_map_source = self.get_random_map_source()

        # Инициализируем один раз отрисовку
        self.initialize_map()

        # Обновление раз в секунду — как в старом варианте
        # Сохраняем идентификатор задачи
        self.update_cities_event = Clock.schedule_interval(self.update_cities, 1.0)

    def on_parent(self, widget, parent):
        """
        Вызывается Kivy при изменении родительского элемента виджета.
        Используется для отмены задач Clock при удалении виджета.
        """
        # Если виджет удаляется (parent становится None)
        if parent is None:
            from kivy.clock import Clock
            # Отменяем задачу update_cities, если она была запланирована
            if self.update_cities_event:
                Clock.unschedule(self.update_cities_event)
                print(f"[MapWidget] Задача update_cities отменена при удалении виджета.")
            # Сброс ссылки на задачу
            self.update_cities_event = None

    def initialize_map(self, schedule_blink=True):
        """Первоначальная отрисовка карты, дорог и иконок.
        Если schedule_blink=False — не планируем мигание (для повторных перерисовок)."""
        # Пересчёт масштаба/позиции на случай изменения окна
        self.map_scale = self.calculate_scale()
        self.map_pos = self.calculate_centered_position()

        # Полная очистка canvas — будем заново рисовать всё (включая map_image)
        self.canvas.clear()

        with self.canvas:
            Color(1, 1, 1, 1)
            self.map_image = Rectangle(
                source=self.random_map_source,
                pos=self.map_pos,
                size=(self.base_map_width * self.map_scale, self.base_map_height * self.map_scale)
            )

        # Рисуем дороги и иконки
        self.draw_roads()
        self.draw_fortresses()

        # Планируем мигание только при первом запуске (или когда явно разрешено)
        if schedule_blink:
            Clock.schedule_once(self._schedule_blink, 0.2)

    def update_cities(self, dt=None):
        """Полная перерисовка карты раз в секунду (как раньше)."""
        # На случай изменения окна — пересчёт масштаба и позиции
        self.map_scale = self.calculate_scale()
        self.map_pos = self.calculate_centered_position()

        # Полностью чистим canvas и слой after (дороги), но НЕ меняем random_map_source
        self.canvas.clear()
        self.canvas.after.clear()

        # Рисуем фон (map_image) заново
        with self.canvas:
            Color(1, 1, 1, 1)
            self.map_image = Rectangle(
                source=self.random_map_source,
                pos=self.map_pos,
                size=(self.base_map_width * self.map_scale, self.base_map_height * self.map_scale)
            )

        # Рисуем дороги и крепости
        self.draw_roads()
        self.draw_fortresses()

    def draw_fortresses(self):
        """Рисует крепости на карте, создавая виджеты Image для каждой иконки."""
        # Очищаем предыдущие виджеты и данные
        self.clear_widgets()
        self.fortress_icon_widgets.clear()
        self.fortress_data_for_canvas.clear()  # теперь будет хранить и оригинальные координаты

        faction_images = {
            'Вампиры': 'files/buildings/giperion.png',
            'Север': 'files/buildings/arkadia.png',
            'Эльфы': 'files/buildings/celestia.png',
            'Адепты': 'files/buildings/eteria.png',
            'Элины': 'files/buildings/halidon.png'
        }

        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT name, faction, coordinates FROM cities")
            fortresses_data = cursor.fetchall()
        except sqlite3.Error as e:
            print(f"[ERROR] Ошибка при загрузке данных о городах: {e}")
            return
        finally:
            if 'cursor' in locals():
                cursor.close()

        if not fortresses_data:
            print("[DEBUG] Нет данных о крепостях в базе данных.")
            return

        for row in fortresses_data:
            fortress_name, kingdom, coords_str = row
            try:
                coords = ast.literal_eval(coords_str)
                if len(coords) != 2:
                    raise ValueError(f"Координаты должны быть в формате [x, y], получено: {coords}")
            except Exception as e:
                print(f"[ERROR] Ошибка разбора координат для '{fortress_name}': {e}")
                continue

            # Оригинальные (исходные) координаты в пикселях карты (не масштабированные)
            fort_x, fort_y = coords

            # Координаты для рисования (масштаб + смещение)
            drawn_x = fort_x * self.map_scale + self.map_pos[0]
            drawn_y = fort_y * self.map_scale + self.map_pos[1]

            # --- Создание виджета иконки ---
            image_path = faction_images.get(kingdom, 'files/buildings/default.png')
            if not os.path.exists(image_path):
                image_path = 'files/buildings/default.png'

            icon_widget = Image(
                source=image_path,
                size=(77, 77),
                pos=(drawn_x, drawn_y),
                allow_stretch=True,
                keep_ratio=True,
            )
            self.add_widget(icon_widget)
            self.fortress_icon_widgets[fortress_name] = icon_widget

            # --- Сохраняем данные для кликов ---
            self.fortress_data_for_canvas.append((fortress_name, kingdom, fort_x, fort_y, drawn_x, drawn_y))

            # --- Рисуем название города ---
            display_name = f"{fortress_name}({kingdom})"
            label = CoreLabel(text=display_name, font_size=25, color=(0, 0, 0, 1))
            label.refresh()
            text_texture = label.texture
            text_width, text_height = text_texture.size
            text_x = drawn_x + (40 - text_width) / 2
            text_y = drawn_y - text_height - 5

            with self.canvas:
                Color(1, 1, 1, 1)
                Rectangle(texture=text_texture, pos=(text_x, text_y), size=(text_width, text_height))

            # --- Обновляем icon_coordinates в БД ---
            try:
                cursor2 = self.conn.cursor()
                cursor2.execute(
                    "UPDATE cities SET icon_coordinates = ? WHERE name = ?",
                    (str([drawn_x, drawn_y]), fortress_name)
                )
                self.conn.commit()
            except sqlite3.Error as e:
                print(f"[DB ERROR] Не удалось обновить icon_coordinates для {fortress_name}: {e}")
            finally:
                cursor2.close()

    def find_and_set_player_city_icon(self):
        """Ищет и устанавливает ссылку на виджет иконки города игрока."""
        if not self.current_player_kingdom or not self.fortress_icon_widgets:
            print("[MapWidget] Не могу найти иконку: нет данных об игроке или городах (find_and_set).")
            return False

        # Получаем города игрока из БД
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT name FROM cities WHERE faction = ?", (self.current_player_kingdom,))
            player_cities = cursor.fetchall()
        except sqlite3.Error as e:
            print(f"[MapWidget] Ошибка при поиске городов игрока: {e}")
            return False
        finally:
            cursor.close()

        if not player_cities:
            print(f"[MapWidget] У игрока ({self.current_player_kingdom}) нет городов.")
            return False

        # Берем первый город игрока
        player_city_name = player_cities[0][0]
        if player_city_name in self.fortress_icon_widgets:
            self.player_city_icon_widget = self.fortress_icon_widgets[player_city_name]
            print(f"[MapWidget] Иконка города игрока '{player_city_name}' найдена и установлена.")
            return True
        else:
            print(f"[MapWidget] Виджет иконки для города игрока '{player_city_name}' не найден.")
            return False

    def blink_player_city_icon(self, times=5, duration=0.3):
        """Анимирует мигание виджета иконки города игрока."""
        if not self.player_city_icon_widget:
            print("[MapWidget] Иконка города игрока не найдена для мигания.")
            return

        print(f"[MapWidget] Запуск анимации мигания ({times} раз) для виджета {self.player_city_icon_widget}")

        # Создаем цепочку анимаций
        anim = Animation(opacity=0.0, duration=duration) # Исчезновение 1
        for i in range(times - 1): # Остальные (times-1) циклов
            anim += Animation(opacity=1.0, duration=duration) # Появление
            anim += Animation(opacity=0.0, duration=duration) # Исчезновение
        anim += Animation(opacity=1.0, duration=duration) # Последнее появление

        # Запускаем анимацию
        anim.start(self.player_city_icon_widget)
        print("[MapWidget] Анимация мигания запущена для иконки города игрока.")

    def _schedule_blink(self, dt):
        """Вспомогательный метод для планирования мигания."""
        if not self.has_blinked: # Проверяем флаг
            if self.find_and_set_player_city_icon():
                self.blink_player_city_icon()
                self.has_blinked = True # Устанавливаем флаг после запуска
            else:
                print("[MapWidget] Повторная попытка найти иконку через 1 секунду...")
                Clock.schedule_once(
                    lambda dt: (
                            not self.has_blinked and
                            self.find_and_set_player_city_icon() and
                            (self.blink_player_city_icon(), setattr(self, 'has_blinked', True)) or
                            print("[MapWidget] Повторная попытка не удалась.")
                    ), 1.0
                )

    def get_random_map_source(self):
        """Выбирает случайную карту из папки files/map/generate"""
        map_dir = 'files/map/generate'
        map_files = [f for f in os.listdir(map_dir) if f.startswith('map_') and f.endswith('.png')]
        if not map_files:
            raise FileNotFoundError("Не найдено файлов с картами в директории.")
        print("Выбор случайной карты...")
        chosen_map = random.choice(map_files)
        print(f"Карта выбрана: {chosen_map}")
        return os.path.join(map_dir, chosen_map)

    def calculate_scale(self):
        """Рассчитывает масштаб карты под текущий экран"""
        scale_width = Window.width / self.base_map_width
        scale_height = Window.height / self.base_map_height
        return min(scale_width, scale_height) * 0.9  # Добавляем небольшой отступ

    def calculate_centered_position(self):
        """Вычисляет центрированную позицию карты"""
        scaled_width = self.base_map_width * self.map_scale
        scaled_height = self.base_map_height * self.map_scale
        x = (Window.width - scaled_width) / 2
        y = (Window.height - scaled_height) / 2
        return [x, y]

    def draw_roads(self):
        """Рисует дороги между ближайшими городами - вызывается один раз."""
        # Используем self.canvas.after или self.canvas, но не очищаем его в update_cities
        # Для простоты оставим как есть, но будем вызывать только один раз
        self.canvas.after.clear() # Очищаем after только один раз

        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT name, coordinates FROM cities")
            fortresses_data = cursor.fetchall()
        except sqlite3.Error as e:
            print(f"Ошибка при загрузке данных о городах для дорог: {e}")
            return

        cities = []
        for fortress_name, coords_str in fortresses_data:
            try:
                coords = ast.literal_eval(coords_str)
                if len(coords) == 2:
                    cities.append((fortress_name, coords))
            except (ValueError, SyntaxError) as e:
                print(f"Ошибка при разборе координат города '{fortress_name}' для дорог: {e}")
                continue

        with self.canvas.after:
            Color(0.5, 0.5, 0.5, 1)  # Серый цвет для дорог

            for i in range(len(cities)):
                for j in range(i + 1, len(cities)):
                    source_name, source_coords = cities[i]
                    dest_name, dest_coords = cities[j]

                    total_diff = self.calculate_manhattan_distance(source_coords, dest_coords)

                    if total_diff < 280:
                        drawn_x1 = source_coords[0] * self.map_scale + self.map_pos[0]
                        drawn_y1 = source_coords[1] * self.map_scale + self.map_pos[1]
                        drawn_x2 = dest_coords[0] * self.map_scale + self.map_pos[0]
                        drawn_y2 = dest_coords[1] * self.map_scale + self.map_pos[1]

                        Line(points=[drawn_x1, drawn_y1, drawn_x2, drawn_y2], width=1)

    def calculate_manhattan_distance(self, source_coords, destination_coords):
        """Вычисляет манхэттенское расстояние между точками"""
        return abs(source_coords[0] - destination_coords[0]) + abs(source_coords[1] - destination_coords[1])

    def check_fortress_click(self, touch):
        """Проверяет нажатие на крепость (использует сохранённые оригинальные координаты)."""
        # self.fortress_data_for_canvas: [(name, kingdom, fort_x, fort_y, drawn_x, drawn_y), ...]
        for fortress_name, kingdom, fort_x, fort_y, drawn_x, drawn_y in self.fortress_data_for_canvas:
            icon_widget = self.fortress_icon_widgets.get(fortress_name)
            if icon_widget and icon_widget.collide_point(*touch.pos):
                # Используем оригинальные координаты (числа), а не строку из БД
                city_coords_for_popup = (fort_x, fort_y)

                # Сохраняем последний кликнутый город (по имени)
                save_last_clicked_city(self.conn, fortress_name)

                # Создаём popup и передаём координаты как tuple (как в старой версии)
                popup = FortressInfoPopup(
                    ai_fraction=kingdom,
                    city_coords=city_coords_for_popup,
                    player_fraction=self.current_player_kingdom,
                    conn=self.conn
                )
                popup.open()

                print(
                    f"Крепость '{fortress_name}' (координаты: {city_coords_for_popup}) принадлежит "
                    f"{'вашему' if kingdom == self.current_player_kingdom else 'чужому'} королевству ({kingdom})!"
                )
                return

    def on_touch_up(self, touch):
        """Обрабатывает нажатия на карту"""
        self.check_fortress_click(touch)


class RectangularButton(Button):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.background_color = (0, 0, 0, 0)  # Отключаем стандартный фон

    def update_rect(self, *args):
        self.rect.pos = self.pos
        self.rect.size = self.size

        self.border_rect.pos = (
            self.pos[0] - self.border_width / 2,
            self.pos[1] - self.border_width / 2
        )
        self.border_rect.size = (
            self.size[0] + self.border_width,
            self.size[1] + self.border_width
        )

    def show_border(self, show=True):
        """Показываем/скрываем рамку"""
        self.border_rect_color.a = 1 if show else 0


class KingdomSelectionWidget(FloatLayout):
    def __init__(self, conn, selected_map=None, **kwargs):
        super(KingdomSelectionWidget, self).__init__(**kwargs)
        is_android = platform == 'android'
        self.selected_map = selected_map
        # Инициализируем selected_button
        self.selected_button = None

        # ======== ФОН ВИДЕО ========
        self.bg_video = Video(
            source='files/menu/choice.mp4',
            state='play',
            options={'eos': 'loop'},
            allow_stretch=True,
            keep_ratio=False,
            size_hint=(1, 1),
            pos_hint={'x': 0, 'y': 0}
        )
        self.bg_video.bind(on_eos=self.loop_video)
        self.add_widget(self.bg_video)

        # ======== ЗАГОЛОВОК «Выберите сторону» ========
        label_size = '36sp' if is_android else '40sp'
        self.select_side_label = Label(
            text="Выберите сторону",
            font_size=label_size,
            color=(1, 1, 1, 1),
            outline_color=(0, 0, 0, 1),
            outline_width=2,
            markup=True,
            halign='center',
            valign='middle',
            size_hint=(0.8, None),
            height=dp(80) if is_android else 80,
            pos_hint={'center_x': 0.75, 'top': 0.97}
        )
        self.add_widget(self.select_side_label)

        self.buttons_container = FloatLayout()
        self.add_widget(self.buttons_container)

        # PNG-рамка поверх кнопок:
        self.border_image = Image(
            source='files/pict/menu/border.png',
            size_hint=(None, None),
            size=(0, 0),
            pos=(0, 0),
            opacity=0
        )
        self.border_image.disabled = True  # не мешаем кликам на кнопку
        # _ВАЖНО_: добавляем рамку **в buttons_container**, после kingdom_buttons
        self.buttons_container.add_widget(self.border_image)

        # ======== ИНФО О ФРАКЦИИ ========
        self.faction_info_container = BoxLayout(
            orientation='vertical',
            size_hint=(0.15, None),
            height=dp(120),
            pos_hint={'center_x': 0.73, 'center_y': 0.4},
            spacing=dp(8)
        )
        self.add_widget(self.faction_info_container)

        # ======== ИЗОБРАЖЕНИЕ СОВЕТНИКА ========
        advisor_size = (0.3, 0.3)
        self.advisor_image = Image(
            source='files/null.png',
            size_hint=advisor_size,
            pos_hint={'center_x': 0.75, 'center_y': 0.6}
        )
        self.add_widget(self.advisor_image)

        # ======== КОНТЕЙНЕР ДЛЯ КНОПОК ========
        self.buttons_container = FloatLayout()
        self.add_widget(self.buttons_container)

        # ======== ЗАГРУЗКА ДАННЫХ ИЗ БД ========
        self.conn = conn
        self.faction_data = self.load_factions_from_db()

        # ======== ПАНЕЛЬ КНОПОК ФРАКЦИЙ (изначально скрыта) ========
        panel_width = 0.10
        button_height = dp(35) if is_android else 35
        spacing_val = dp(35) if is_android else 35
        padding = [dp(20), dp(20), dp(20), dp(20)] if is_android else [20, 20, 20, 20]

        total_height = self.calculate_panel_height(button_height, spacing_val, padding)

        # Здесь смещаем начальную позицию по Y чуть выше (0.6 вместо 0.5):
        initial_y = Window.height * 0.6 - total_height / 2

        self.kingdom_buttons = BoxLayout(
            orientation='vertical',
            spacing=spacing_val,
            size_hint=(panel_width, None),
            height=total_height,
            pos=(-Window.width * 0.7, initial_y),  # был 0.5, заменили на 0.6
            opacity=1
        )

        try:
            for faction in self.faction_data:
                kingdom = faction.get('name', 'Неизвестная фракция')
                btn = RectangularButton(
                    text=kingdom,
                    size_hint_y=None,
                    height=dp(35),
                    font_size='18sp',
                    opacity=1  # Делаем кнопки сразу видимыми
                )
                btn.bind(on_release=self.select_kingdom)
                self.kingdom_buttons.add_widget(btn)
        except Exception as e:
            print(f"Ошибка при создании кнопок фракций: {e}")

        # ======== КНОПКА «Начать игру» (сразу видна) ========
        self.start_game_button = RoundedButton(
            text="Начать игру",
            size_hint=(0.3, None),
            height=button_height,
            font_size='18sp' if is_android else '16sp',
            bold=True,
            color=(1, 1, 1, 1),
            background_color=(0.2, 0.8, 0.2, 1),
            pos_hint={'center_x': 0.75, 'y': 0.1},
            opacity=1
        )
        self.start_game_button.bind(on_release=self.start_game)

        # ======== КНОПКА «Вернуться в главное меню» (сразу видна) ========
        self.back_btn = RoundedButton(
            text="Вернуться в главное меню",
            size_hint=(0.34, 0.08),
            pos_hint={'x': 0.005, 'y': 0.05},
            color=(1, 1, 1, 1),
            font_size='16sp',
            background_color=(0.8, 0.2, 0.2, 1),
            opacity=1
        )
        self.back_btn.bind(on_release=self.back_to_menu)
        self.buttons_container.add_widget(self.kingdom_buttons)
        self.buttons_container.add_widget(self.start_game_button)
        self.buttons_container.add_widget(self.back_btn)

        # ======== Запускаем анимацию появления кнопок-фракций ========
        Clock.schedule_once(lambda dt: self.animate_in(), 0.3)

    def animate_in(self):
        """
        1) Ставим панель в финальную позицию (выше),
        2) Поочерёдно проявляем opacity каждой кнопки-фракции,
        3) Кнопки «Начать игру» и «Вернуться» уже видны.
        """
        # Смещаем финальную позицию панели по Y (тоже выше):
        final_x_panel = Window.width * 0.1
        final_y_panel = Window.height * 0.6 - self.kingdom_buttons.height / 2  # было 0.5, заменили на 0.6
        self.kingdom_buttons.pos = (final_x_panel, final_y_panel)

        # Список всех кнопок-фракций внутри BoxLayout, сверху вниз:
        faction_buttons = list(self.kingdom_buttons.children)[::-1]
        delay_between = 0.15

        for idx, btn in enumerate(faction_buttons):
            Clock.schedule_once(
                lambda dt, widget=btn: Animation(opacity=1, duration=0.4).start(widget),
                idx * delay_between
            )

        total_delay = (len(faction_buttons) - 1) * delay_between + 0.4
        self.buttons_locked = True
        Clock.schedule_once(lambda dt: setattr(self, 'buttons_locked', False), total_delay)
        Clock.schedule_once(self.store_coords, 0)

    def store_coords(self, dt):
        cur = self.conn.cursor()
        now = datetime.now().isoformat()
        screen_section = 'kingdom_selection'
        for btn in self.kingdom_buttons.children:
            # Получаем абсолютные координаты кнопки
            abs_pos = btn.to_window(*btn.pos)
            abs_x, abs_y = abs_pos[0], abs_pos[1]
            width = btn.width
            height = btn.height
            element_name = btn.text
            cur.execute("""
                INSERT INTO interface_coord 
                    (element_name, screen_section, x, y, width, height, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (element_name, screen_section, abs_x, abs_y, width, height, now, now))
        self.conn.commit()

    def loop_video(self, instance):
        instance.state = 'stop'
        instance.state = 'play'

    def calculate_panel_height(self, btn_height, spacing, padding):
        num_buttons = len(self.faction_data)
        return (btn_height * num_buttons) + (spacing * (num_buttons - 1)) + (padding[1] + padding[3])

    def back_to_menu(self, instance):
        if getattr(self, 'buttons_locked', False):
            return

        # --- Добавляем строку для остановки фонового видео ---
        if hasattr(self, 'bg_video'):
            self.bg_video.state = 'stop'
            print("Фоновое видео choice.mp4 остановлено при возврате в меню.")

        app = App.get_running_app()
        app.root.clear_widgets()
        app.root.add_widget(MenuWidget(self.conn))

    def load_factions_from_db(self):
        """
        Загружает список уникальных фракций из таблицы diplomacies_default.
        Исключает фракцию "Мятежники".
        :return: Список словарей с информацией о фракциях.
        """
        factions = []
        try:
            cursor = self.conn.cursor()
            # Выполняем запрос к таблице diplomacies_default, исключая "Мятежники"
            cursor.execute("""
                SELECT DISTINCT faction1 
                FROM diplomacies_default
                WHERE faction1 != 'Мятежники'
            """)
            rows = cursor.fetchall()

            # Обрабатываем результаты запроса
            for row in rows:
                faction_name = row[0]
                if faction_name:
                    factions.append({"name": faction_name})

        except sqlite3.Error as e:
            print(f"Ошибка при загрузке данных из базы данных: {e}")

        return factions

    def select_kingdom(self, instance):
        """
        При клике на кнопку-фракцию: показываем PNG-рамку
        ровно по координатам из interface_coord.
        """
        cur = self.conn.cursor()
        self.stop_border_animation()  # останавливает предыдущую анимацию
        if getattr(self, 'buttons_locked', False):
            return

        self.selected_button = instance
        kingdom_name = instance.text

        # === Обновление изображения советника ===
        kingdom_rename = {
            "Север": "people",
            "Эльфы": "elfs",
            "Адепты": "adept",
            "Вампиры": "vampire",
            "Элины": "poly"
        }
        app = App.get_running_app()
        app.selected_kingdom = kingdom_name
        eng = kingdom_rename.get(kingdom_name, kingdom_name).lower()
        adv_path = f'files/sov/{eng}.jpg'
        if os.path.exists(adv_path):
            self.advisor_image.source = adv_path
            self.advisor_image.reload()

        # === ПОЗИЦИОНИРОВАНИЕ PNG-РАМКИ НА ОСНОВЕ ДАННЫХ ИЗ БД ===
        padding = dp(30)

        cur.execute("""
            SELECT x, y, width, height 
            FROM interface_coord 
            WHERE element_name=? AND screen_section=?
            ORDER BY id DESC LIMIT 1
        """, (kingdom_name, 'kingdom_selection'))

        row = cur.fetchone()
        if not row:
            return

        btn_x, btn_y, btn_width, btn_height = map(float, row)

        # Растягиваем рамку чуть больше кнопки
        self.border_image.size_hint = (None, None)
        self.border_image.size = (btn_width + padding * 2, btn_height + padding * 2)
        self.border_image.pos = (btn_x - padding, btn_y - padding)
        self.border_image.opacity = 0
        self.border_image.allow_stretch = True
        self.border_image.keep_ratio = False

        def pulse_loop(*args):
            anim = Animation(opacity=1, duration=0.5) + Animation(opacity=0.4, duration=0.5)
            anim.repeat = True
            anim.start(self.border_image)

        Clock.schedule_once(pulse_loop, 0)

        # === Обновление инфо-панели справа ===
        self.get_kingdom_info(kingdom_name)


    def stop_border_animation(self):
        Animation.stop_all(self.border_image)
        self.border_image.opacity = 0

    def hex_to_rgba(self, hex_color):
        # Вставьте здесь свою логику конвертации
        return (0, 0.3, 0.4, 1)

    def generate_icons_layout(self, value, max_value=3):
        layout = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(20))
        for i in range(max_value):
            img_path = 'files/pict/menu/full.png' if i < value else 'files/pict/menu/grey.png'
            img = Image(source=img_path, size_hint=(None, None), size=('16dp', '16dp'))
            layout.add_widget(img)
        return layout

    def get_kingdom_info(self, kingdom):
        full_img = 'files/pict/menu/full.png'
        empty_img = 'files/pict/menu/grey.png'
        if not os.path.exists(full_img) or not os.path.exists(empty_img):
            return

        stats = {
            "Север": {"Доход Крон": 3, "Доход Кристаллов": 1, "Армия": 2},
            "Эльфы": {"Доход Крон": 2, "Доход Кристаллов": 2, "Армия": 2},
            "Вампиры": {"Доход Крон": 2, "Доход Кристаллов": 2, "Армия": 3},
            "Элины": {"Доход Крон": 1, "Доход Кристаллов": 3, "Армия": 1},
            "Адепты": {"Доход Крон": 1, "Доход Кристаллов": 2, "Армия": 2}
        }
        data = stats.get(kingdom)
        if not data:
            return

        self.faction_info_container.clear_widgets()

        spacing = dp(20)  # Расстояние между надписью и иконками

        crown_row = BoxLayout(size_hint_y=None, height=dp(20))
        crown_row.add_widget(Label(text="Доход Крон:", size_hint_x=None, width=dp(100)))
        crown_row.add_widget(Widget(size_hint_x=None, width=spacing))  # Пробел
        crown_row.add_widget(self.generate_icons_layout(data["Доход Крон"]))
        self.faction_info_container.add_widget(crown_row)

        resource_row = BoxLayout(size_hint_y=None, height=dp(20))
        resource_row.add_widget(Label(text="Доход Кристаллов:", size_hint_x=None, width=dp(100)))
        resource_row.add_widget(Widget(size_hint_x=None, width=spacing))  # Пробел
        resource_row.add_widget(self.generate_icons_layout(data["Доход Кристаллов"]))
        self.faction_info_container.add_widget(resource_row)

        army_row = BoxLayout(size_hint_y=None, height=dp(20))
        army_row.add_widget(Label(text="Армия:", size_hint_x=None, width=dp(100)))
        army_row.add_widget(Widget(size_hint_x=None, width=spacing))  # Пробел
        army_row.add_widget(self.generate_icons_layout(data["Армия"]))
        self.faction_info_container.add_widget(army_row)

    # Найди функцию start_game внутри класса KingdomSelectionWidget
    def start_game(self, instance):
        if getattr(self, 'buttons_locked', False):
            return

        if not getattr(self, 'selected_button', None):
            print("Фракция не выбрана.")
            return

        # === Блокируем все кнопки ===
        self.disable_all_buttons(True)

        # --- Добавляем строку для остановки фонового видео ---
        if hasattr(self, 'bg_video'):
            self.bg_video.state = 'stop'
            print("Фоновое видео choice.mp4 остановлено перед запуском start_game.mp4.")

        # === Создаём Overlay и запускаем видео ===
        overlay = FloatLayout(size=Window.size)
        self.overlay = overlay
        self.add_widget(overlay)

        self.start_video = Video(
            source='files/menu/start_game.mp4',
            state='play',
            options={'eos': 'stop'},
            allow_stretch=True,
            keep_ratio=False,
            size=Window.size,
            pos=(0, 0)
        )
        overlay.add_widget(self.start_video)

        # Привязываем on_eos, чтобы при окончании видео сразу запустить игру:
        self.start_video.bind(on_eos=self.on_start_video_end)

        # Резервный таймер на 3 секунды, если on_eos по какой-то причине не сработает:
        Clock.schedule_once(self.force_start_game, 3)

    def on_start_video_end(self, instance, value):
        # Когда видео завершено (или state == 'stop'), начинаем игру
        if value or (self.start_video and self.start_video.state == 'stop'):
            print("Видео завершено (on_eos), начинаем игру...")
            self.cleanup_and_start_game()

    def force_start_game(self, dt):
        # Если on_eos не сработал за 3, сек, форсируем запуск игры
        print("Резервный таймер сработал — завершаем видео и запускаем игру")
        if self.start_video:
            self.start_video.state = 'stop'
        self.cleanup_and_start_game()

    def cleanup_and_start_game(self):
        # --- Добавляем эту строку для остановки фонового видео ---
        if hasattr(self, 'bg_video'):
            self.bg_video.state = 'stop'
            print("Фоновое видео choice.mp4 остановлено.")

        # Убираем оверлей с начального видео (если он есть)
        if hasattr(self, 'overlay') and self.overlay in self.children:
            self.remove_widget(self.overlay)
        self.disable_all_buttons(False)

        try:
            app = App.get_running_app()
            restore_from_backup(self.conn)
            selected_kingdom = app.selected_kingdom
            map_widget = MapWidget(selected_kingdom=selected_kingdom, player_kingdom=selected_kingdom, conn=self.conn)
            cities = load_cities_from_db(self.conn, selected_kingdom)
            if not cities:
                print("Города не найдены.")
                return

            game_screen = GameScreen(selected_kingdom, cities, conn=self.conn)
            app.root.clear_widgets()
            app.root.add_widget(map_widget)
            app.root.add_widget(game_screen)
            Clock.schedule_once(lambda dt: map_widget.blink_player_city_icon(), 1.0)
        except Exception as e:
            print(f"Ошибка при запуске игры: {e}")

    def disable_all_buttons(self, disabled=True):
        for child in self.buttons_container.walk():
            if isinstance(child, RoundedButton):
                child.disabled = disabled


class RoundedButton(Button):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.background_normal = ''
        self.background_color = (0, 0, 0, 0)
        self.color = (1, 1, 1, 1)  # Белый текст по умолчанию
        self.bind(pos=self.update_canvas, size=self.update_canvas)

    def update_canvas(self, *args):
        self.canvas.before.clear()
        with self.canvas.before:
            # Основной цвет кнопки
            Color(0.1, 0.1, 0.3, 0.85)
            RoundedRectangle(
                pos=self.pos,
                size=self.size,
                radius=[25]
            )
            # Рамка с эффектом свечения
            Color(0.3, 0.3, 0.8, 0.7)
            Line(
                rounded_rectangle=(self.x, self.y, self.width, self.height, 25),
                width=1.2
            )


class AnimatedLabel(Label):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.animation = None

    def start_glow_animation(self):
        if self.animation:
            self.animation.cancel(self)

        anim = Animation(
            outline_color=(0.8, 0.8, 1, 1),
            duration=2.0
        ) + Animation(
            outline_color=(0.2, 0.2, 0.4, 1),
            duration=2.0
        )
        anim.repeat = True
        anim.start(self)


class MenuWidget(FloatLayout):
    def __init__(self, conn, selected_map=None, **kwargs):
        super(MenuWidget, self).__init__(**kwargs)
        self.conn = conn
        self.buttons_locked = True  # Инициализируем сразу

        # Хранение идентификаторов запланированных задач
        self.background_anim_event = None
        self.float_anim_event = None
        # Счетчик для анимации фона (чтобы не запускать лишние задачи)
        self._anim_scheduled = False

        # ======== Фоновые изображения ========
        self.bg_image_1 = Image(
            source='files/menu/vampire.jpg',
            allow_stretch=True,
            keep_ratio=False,
            size_hint=(1, 1),
            pos_hint={'x': 0, 'y': 0}
        )
        self.bg_image_2 = Image(
            source='files/menu/people.jpg',
            allow_stretch=True,
            keep_ratio=False,
            opacity=0,
            size_hint=(1, 1),
            pos_hint={'x': 0, 'y': 0}
        )
        self.add_widget(self.bg_image_1)
        self.add_widget(self.bg_image_2)

        # ======== Инициализация переменных для анимации фона ========
        self.current_image = self.bg_image_1
        self.next_image = self.bg_image_2

        # ======== Логотип / Заголовок с анимацией ========
        self.title_label = AnimatedLabel(
            text="Легенды Лэрдона",
            font_size='48sp',
            bold=True,
            color=(1, 1, 1, 1),
            outline_color=(0.2, 0.2, 0.4, 1),
            outline_width=3,
            halign='center',
            valign='middle',
            size_hint=(0.8, 0.15),
            pos_hint={'center_x': 0.5, 'top': 0.92},
            markup=True
        )
        self.add_widget(self.title_label)

        # ======== Контейнер для кнопок ========
        self.button_container = FloatLayout(size_hint=(1, 0.7), pos_hint={'center_x': 0.5, 'y': 0.15})
        self.add_widget(self.button_container)

        # ======== Создаём стилизованные кнопки ========
        button_configs = [
            {"text": "В Лэрдон", "y_pos": 0.75, "color": (0.2, 0.6, 0.9, 1), "action": self.start_game},
            {"text": "Рейтинг", "y_pos": 0.58, "color": (0.3, 0.8, 0.5, 1), "action": self.open_dossier},
            {"text": "Как играть", "y_pos": 0.41, "color": (0.9, 0.7, 0.2, 1), "action": self.open_how_to_play},
            {"text": "Автор", "y_pos": 0.24, "color": (0.8, 0.4, 0.8, 1), "action": self.open_author},
            {"text": "Выход", "y_pos": 0.07, "color": (0.9, 0.3, 0.3, 1), "action": self.exit_game}
        ]
        self.buttons = []
        for config in button_configs:
            btn = RoundedButton(
                text=config["text"],
                size_hint=(0.5, 0.12),
                pos_hint={'center_x': 0.5, 'y': config["y_pos"]},
                color=(1, 1, 1, 1),
                font_size='18sp',
                bold=True,
                opacity=0
            )
            # Сохраняем цвет для использования в анимациях
            btn.base_color = config["color"]
            btn.bind(on_release=config["action"])
            self.buttons.append(btn)
            self.button_container.add_widget(btn)

        # ======== Декоративные элементы ========
        self.particles = []
        self.add_decoration()

        # ======== Анимации ========
        Clock.schedule_once(self.animate_title, 0.2)
        Clock.schedule_once(self.animate_buttons_in, 0.4)
        # Запланируем анимацию фона *только один раз* и сохраним событие
        if not self._anim_scheduled:
            self.background_anim_event = Clock.schedule_interval(self.animate_background, 5)
            self._anim_scheduled = True
        # Запланируем анимацию плавания кнопок и сохраним событие
        self.float_anim_event = Clock.schedule_interval(self.float_animation, 0.05) # ~60 FPS для плавности

    def on_parent(self, widget, parent):
        """
        Вызывается Kivy при изменении родительского элемента виджета.
        Используется для отмены задач Clock при удалении виджета.
        """
        # Если виджет удаляется (parent становится None)
        if parent is None:
            # Отменяем задачи, связанные с этим виджетом
            if self.background_anim_event:
                Clock.unschedule(self.background_anim_event)
                print(f"[MenuWidget] Задача animate_background отменена при удалении виджета.")
            if self.float_anim_event:
                Clock.unschedule(self.float_anim_event)
                print(f"[MenuWidget] Задача float_animation отменена при удалении виджета.")
            # Сброс флага, чтобы при следующем создании можно было снова запланировать
            self._anim_scheduled = False

    def add_decoration(self):
        """Добавляем декоративные элементы"""
        for i in range(6):
            particle = Label(
                text="✦",
                font_size='20sp',
                color=(1, 1, 1, 0),
                opacity=0
            )
            self.particles.append(particle)
            self.add_widget(particle)

    def animate_title(self, dt):
        """Анимация заголовка"""
        self.title_label.start_glow_animation()

    def animate_particles(self):
        """Анимация декоративных частиц"""
        positions = [
            {'x': 0.1, 'y': 0.85}, {'x': 0.9, 'y': 0.8},
            {'x': 0.15, 'y': 0.65}, {'x': 0.85, 'y': 0.6},
            {'x': 0.2, 'y': 0.45}, {'x': 0.8, 'y': 0.4}
        ]
        for i, particle in enumerate(self.particles):
            if i < len(positions):
                particle.pos_hint = positions[i]
                anim = Animation(opacity=0.6, duration=2.0) + Animation(opacity=0.2, duration=2.0)
                anim.repeat = True
                # Важно: не сохраняем ссылку на эту анимацию, так как она привязана к Label
                # и отменяется при его удалении. Но если бы мы сохраняли, нужно было бы отменять.
                Clock.schedule_once(lambda dt, p=particle, a=anim: a.start(p), i * 0.3)

    def animate_buttons_in(self, dt):
        """Анимированное появление кнопок с эффектом волны"""
        # Сначала показываем декоративные элементы
        self.animate_particles()
        # Анимация кнопок с эффектом "волны"
        for i, btn in enumerate(self.buttons):
            # Начальная позиция - смещены вправо
            original_y = btn.pos_hint['y']
            btn.pos_hint = {'center_x': 1.5, 'y': original_y}
            # Анимация движения и появления
            anim = Animation(
                pos_hint={'center_x': 0.5, 'y': original_y},
                duration=0.7,
                transition='out_back'
            ) & Animation(
                opacity=1,
                duration=0.5
            )
            Clock.schedule_once(
                lambda dt, widget=btn, animation=anim: animation.start(widget),
                i * 0.12
            )
        # Разблокировка кнопок после анимации
        total_delay = len(self.buttons) * 0.12 + 0.8
        Clock.schedule_once(lambda dt: setattr(self, 'buttons_locked', False), total_delay)

    def float_animation(self, dt):
        """Плавное плавающее движение кнопок"""
        if hasattr(self, 'buttons_locked') and self.buttons_locked:
            return
        current_time = Clock.get_time()
        for i, btn in enumerate(self.buttons):
            if not hasattr(btn, 'original_y'):
                btn.original_y = btn.pos_hint['y']
            # Плавное движение вверх-вниз
            float_offset = math.sin(current_time * 2 + i * 0.5) * 0.003
            new_y = btn.original_y + float_offset
            btn.pos_hint = {'center_x': 0.5, 'y': new_y}

    def create_button_animation(self, instance):
        """Анимация при нажатии на кнопку"""
        if getattr(self, 'buttons_locked', True):
            return
        # Анимация нажатия
        anim = Animation(
            size_hint=(0.48, 0.115),
            duration=0.08
        ) + Animation(
            size_hint=(0.5, 0.12),
            duration=0.08
        )
        anim.start(instance)

    def animate_background(self, dt):
        """Фоновая подмена изображений с плавным переходом"""
        new_source = random.choice([
            'files/menu/people.jpg',
            'files/menu/elfs.jpg',
            'files/menu/vampire.jpg',
            'files/menu/poly.jpg',
            'files/menu/adept.jpg'
        ])
        # Гарантируем, что источник изменится
        while new_source == self.next_image.source:
            new_source = random.choice([
                'files/menu/people.jpg',
                'files/menu/elfs.jpg',
                'files/menu/vampire.jpg',
                'files/menu/poly.jpg',
                'files/menu/adept.jpg'
            ])
        self.next_image.source = new_source
        fade_out = Animation(opacity=0, duration=2.0)
        fade_in = Animation(opacity=1, duration=2.0)
        fade_out.start(self.current_image)
        fade_in.start(self.next_image)
        # Меняем указатели для следующей анимации
        self.current_image, self.next_image = self.next_image, self.current_image
    # === Обёртки для обработчиков кнопок с анимацией ===
    def open_dossier(self, instance):
        self.button_action_wrapper(self._open_dossier, instance)

    def open_how_to_play(self, instance):
        self.button_action_wrapper(self._open_how_to_play, instance)

    def open_author(self, instance):
        self.button_action_wrapper(self._open_author, instance)

    def start_game(self, instance):
        self.button_action_wrapper(self._start_game, instance)

    def exit_game(self, instance):
        self.button_action_wrapper(self._exit_game, instance)

    def button_action_wrapper(self, action_func, instance):
        """Обёртка для добавления анимации к действиям кнопок"""
        self.create_button_animation(instance)
        Clock.schedule_once(lambda dt: action_func(instance), 0.16)

    def _open_dossier(self, instance):
        if getattr(self, 'buttons_locked', True):
            return
        app = App.get_running_app()
        app.root.clear_widgets()
        app.root.add_widget(DossierScreen(self.conn))

    def _open_how_to_play(self, instance):
        if getattr(self, 'buttons_locked', True):
            return
        app = App.get_running_app()
        app.root.clear_widgets()
        app.root.add_widget(HowToPlayScreen(self.conn))

    def _open_author(self, instance):
        if getattr(self, 'buttons_locked', True):
            return
        app = App.get_running_app()
        app.root.clear_widgets()
        app.root.add_widget(AuthorScreen(self.conn))

    def _start_game(self, instance):
        if getattr(self, 'buttons_locked', True):
            return
        app = App.get_running_app()
        app.root.clear_widgets()
        app.root.add_widget(KingdomSelectionWidget(self.conn))

    def _exit_game(self, instance):
        app = App.get_running_app()
        app.on_stop()
        app.stop()


class CustomTab(TabbedPanelItem):
    def __init__(self, **kwargs):
        super(CustomTab, self).__init__(**kwargs)
        self.active_color = get_color_from_hex('#FF5733')  # например, оранжевый
        self.inactive_color = get_color_from_hex('#DDDDDD')  # светло-серый
        self.background_color = self.inactive_color
        self.bind(state=self.update_background)

    def update_background(self, *args):
        if self.state == 'down':
            self.background_color = self.active_color
        else:
            self.background_color = self.inactive_color


class DossierScreen(Screen):
    def __init__(self, conn, **kwargs):
        super().__init__(**kwargs)
        self.conn = conn
        self.auto_clear_event = None
        self.auto_clear_toggle = None
        self.tabs = None
        self.build_ui()

    def build_ui(self):
        """
        Основной метод, собирающий весь интерфейс:
        - Заголовок
        - TabbedPanel, растягивающийся по оставшемуся пространству
        - Нижняя панель кнопок
        """
        root_layout = BoxLayout(orientation='vertical')

        # === Заголовок "Рейтинг" ===
        title_widget = self._create_title_bar()
        root_layout.add_widget(title_widget)

        # === TabbedPanel ===
        self.tabs = TabbedPanel(do_default_tab=False, size_hint=(1, 1))
        self.load_dossier_data()
        root_layout.add_widget(self.tabs)

        # === Нижняя панель кнопок ===
        bottom_panel = self._create_bottom_panel()
        root_layout.add_widget(bottom_panel)

        self.add_widget(root_layout)

    def _create_title_bar(self):
        """
        Создаёт BoxLayout с заливкой фона и границами, а внутри Label.
        Возвращает готовый виджет.
        """
        title_box = BoxLayout(size_hint_y=None, height=dp(60))
        with title_box.canvas.before:
            Color(0.1, 0.1, 0.1, 0.95)
            bg_rect = Rectangle(size=title_box.size, pos=title_box.pos)
            Color(0, 0.7, 1, 1) # Цвет рамки
            border_line = Line(
                rectangle=(title_box.x, title_box.y, title_box.width, title_box.height),
                width=2
            )

        def _update_title_canvas(instance, _):
            bg_rect.size = instance.size
            bg_rect.pos = instance.pos
            border_line.rectangle = (instance.x, instance.y, instance.width, instance.height)

        title_box.bind(pos=_update_title_canvas, size=_update_title_canvas)

        title_label = Label(
            text="[b]Рейтинг[/b]",
            markup=True,
            font_size=sp(24),
            color=get_color_from_hex('#FFD700'),
            halign='center',
            valign='middle'
        )
        title_box.add_widget(title_label)
        return title_box

    def _create_bottom_panel(self):
        """
        Создаёт нижнюю панель с кнопками.
        Добавлены рамки для кнопок.
        """
        bottom = BoxLayout(size_hint_y=None, height=dp(70), spacing=dp(10), padding=dp(10))

        # --- Кнопка «Назад» ---
        back_btn_wrapper = BoxLayout(size_hint_x=0.5, size_hint_y=1)
        with back_btn_wrapper.canvas.before:
            Color(0, 0, 0, 1) # Цвет фона кнопки
            back_bg_rect = Rectangle(size=back_btn_wrapper.size, pos=back_btn_wrapper.pos)
            Color(0, 0.7, 1, 1) # Цвет рамки кнопки
            back_border_line = Line(
                rectangle=(back_btn_wrapper.x, back_btn_wrapper.y, back_btn_wrapper.width, back_btn_wrapper.height),
                width=2
            )

        def _update_back_btn_canvas(instance, _):
            back_bg_rect.size = instance.size
            back_bg_rect.pos = instance.pos
            back_border_line.rectangle = (instance.x, instance.y, instance.width, instance.height)

        back_btn_wrapper.bind(pos=_update_back_btn_canvas, size=_update_back_btn_canvas)

        back_btn = Button(
            text="Назад",
            background_color=(0, 0.7, 1, 0.1), # Прозрачный фон, чтобы видно было обводку
            font_size=sp(16),
            border=(2, 2, 2, 2) # Параметры border не влияют на Button напрямую в Kivy
        )
        back_btn.bind(on_release=self.go_back)
        back_btn_wrapper.add_widget(back_btn)

        # --- Кнопка «Очистить данные» ---
        clear_btn_wrapper = BoxLayout(size_hint_x=0.5, size_hint_y=1)
        with clear_btn_wrapper.canvas.before:
            Color(0.2, 0.2, 0.2, 1) # Цвет фона кнопки
            clear_bg_rect = Rectangle(size=clear_btn_wrapper.size, pos=clear_btn_wrapper.pos)
            Color(0.9, 0.2, 0.2, 1) # Цвет рамки кнопки
            clear_border_line = Line(
                rectangle=(clear_btn_wrapper.x, clear_btn_wrapper.y, clear_btn_wrapper.width, clear_btn_wrapper.height),
                width=2
            )

        def _update_clear_btn_canvas(instance, _):
            clear_bg_rect.size = instance.size
            clear_bg_rect.pos = instance.pos
            clear_border_line.rectangle = (instance.x, instance.y, instance.width, instance.height)

        clear_btn_wrapper.bind(pos=_update_clear_btn_canvas, size=_update_clear_btn_canvas)

        clear_btn = Button(
            text="Очистить",
            background_color=(0.9, 0.2, 0.2, 0.1), # Прозрачный фон
            font_size=sp(16)
        )
        clear_btn.bind(on_release=self.clear_dossier)
        clear_btn_wrapper.add_widget(clear_btn)

        bottom.add_widget(back_btn_wrapper)
        bottom.add_widget(clear_btn_wrapper)

        return bottom



    def _create_character_card(self, data: dict) -> BoxLayout:
        """
        Создаёт одну карточку «персонажа».
        Теперь адаптирована под мобильные устройства.
        """
        card = BoxLayout(
            orientation='vertical',
            size_hint_y=None,
            spacing=dp(5),
            padding=dp(10)
        )

        # Фон и рамка у карточки
        with card.canvas.before:
            Color(0.15, 0.15, 0.15, 1)
            bg_rect = Rectangle(size=card.size, pos=card.pos)
            Color(0.5, 0.5, 0.5, 1) # Цвет рамки
            border_line = Line(
                rectangle=(card.x, card.y, card.width, card.height),
                width=2
            )

        def _update_card_canvas(instance, _):
            bg_rect.size = instance.size
            bg_rect.pos = instance.pos
            border_line.rectangle = (instance.x, instance.y, instance.width, instance.height)

        card.bind(pos=_update_card_canvas, size=_update_card_canvas)

        # --- Обработка звания ---
        raw_rank = data.get('military_rank') or "Еще не признан своим..."
        rank = raw_rank.strip()
        rank = unicodedata.normalize("NFC", rank)
        rank = (
            rank
            .replace("\u2010", "-")
            .replace("\u2011", "-")
            .replace("\u2012", "-")
            .replace("\u2013", "-")
            .replace("\u2014", "-")
            .replace("\u2015", "-")
        )
        filename = RANK_TO_FILENAME.get(rank, "0.png")
        asset_path = f"files/menu/dossier/{filename}"
        real_path = resource_find(asset_path)

        # --- Иконка ---
        image_container = BoxLayout(size_hint_y=None, height=dp(100), padding=dp(5))
        if real_path:
            rank_img = Image(
                source=real_path,
                size_hint=(None, None),
                size=(dp(80), dp(80)),
                allow_stretch=True,
                keep_ratio=True
            )
        else:
            rank_img = Label(text="?", font_size=sp(40), color=(1, 1, 1, 0.5))

        img_anchor = AnchorLayout(anchor_x='center', anchor_y='center')
        img_anchor.add_widget(rank_img)
        image_container.add_widget(img_anchor)
        card.add_widget(image_container)

        # --- Текст звания ---
        rank_label = Label(
            text=f"[b]{raw_rank}[/b]",
            markup=True,
            font_size=sp(20),
            color=(1, 1, 1, 1),
            halign='center',
            valign='middle',
            size_hint_y=None,
            height=dp(30)
        )
        card.add_widget(rank_label)

        # --- Статистика в Grid ---
        stats_grid = GridLayout(cols=2, spacing=dp(5), size_hint_y=None, height=dp(120))
        # Левый блок
        left_text = (
            f"[b]Боевой рейтинг(ср.):[/b]\n{data.get('avg_military_rating', 0)}\n"
            f"[b]Голод(ср.):[/b]\n{data.get('avg_soldiers_starving', 0)}"
        )
        left_label = Label(
            text=left_text,
            markup=True,
            font_size=sp(14),
            color=(1, 1, 1, 1),
            halign='center',
            valign='top',
            text_size=(None, None)
        )
        stats_grid.add_widget(left_label)

        # Правый блок
        right_text = (
            f"[b]Сражения (В/П):[/b]\n"
            f"[color=#00FF00]{data.get('victories', 0)}[/color]/"
            f"[color=#FF0000]{data.get('defeats', 0)}[/color]\n"
            f"[b]Матчи (В/П):[/b]\n"
            f"[color=#00FF00]{data.get('matches_won', 0)}[/color]/"
            f"[color=#FF0000]{data.get('matches_lost', 0)}[/color]"
        )
        right_label = Label(
            text=right_text,
            markup=True,
            font_size=sp(14),
            color=(1, 1, 1, 1),
            halign='center',
            valign='top',
            text_size=(None, None)
        )
        stats_grid.add_widget(right_label)

        card.add_widget(stats_grid)

        # --- Дата ---
        date_label = Label(
            text=f"Последняя игра: {data.get('last_data', '-')}",
            font_size=sp(12),
            color=get_color_from_hex('#AAAAAA'),
            halign='center',
            valign='middle',
            size_hint_y=None,
            height=dp(20)
        )
        card.add_widget(date_label)

        card.height = dp(270) # Примерная высота, можно рассчитать динамически
        return card

    def clear_dossier(self, instance):
        """Очистка данных и обновление интерфейса."""
        try:
            conn = self.conn
            cursor = conn.cursor()
            cursor.execute("DELETE FROM dossier")
            conn.commit()
            print("✅ Все записи успешно удалены.")
        except sqlite3.Error as e:
            print(f"❌ Ошибка удаления: {e}")

        # Пересоздаём TabbedPanel и заменяем его в родительском макете
        self._recreate_tabs()

    def _recreate_tabs(self):
        """Пересоздаёт TabbedPanel и заменяет старый."""
        # Удаляем старый TabbedPanel из макета
        root_layout = self.children[0]  # BoxLayout(orientation='vertical')
        # Найдём старый TabbedPanel по индексу (предполагаем, что он второй с конца, после bottom_panel и перед title)
        # Лучше получить его индекс надёжно.
        # self.children - это [BoxLayout], root_layout.children = [bottom_panel, old_tabs, title_widget]
        # Индекс старого tabs: 1
        old_tabs_index = 1
        old_tabs = root_layout.children[old_tabs_index]
        root_layout.remove_widget(old_tabs)

        # Создаём новый TabbedPanel
        new_tabs = TabbedPanel(do_default_tab=False, size_hint=(1, 1))
        # Загружаем данные в новый TabbedPanel
        self._load_dossier_data_to_tabs(new_tabs)

        # Вставляем новый TabbedPanel обратно на старое место (индекс 1)
        root_layout.add_widget(new_tabs, index=old_tabs_index)

        # Сохраняем ссылку на новый TabbedPanel
        self.tabs = new_tabs

    def _load_dossier_data_to_tabs(self, tabs_widget):
        """
        Читает данные из SQLite и наполняет переданный TabbedPanel.
        """
        # Убедимся, что старые вкладки удалены
        if tabs_widget.get_tab_list():
            for tab in list(tabs_widget.get_tab_list()):
                tabs_widget.remove_widget(tab)

        try:
            conn = self.conn
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM dossier")
            rows = cursor.fetchall()
        except sqlite3.Error as e:
            print(f"Ошибка базы данных: {e}")
            rows = []

        if not rows:
            info_label = Label(
                text="Вы еще не воевали ни за одну расу...",
                font_size=sp(18),
                color=get_color_from_hex('#FFFFFF'),
                halign='center',
                valign='middle'
            )
            tab = TabbedPanelItem(text="Информация")
            tab.add_widget(info_label)
            tabs_widget.add_widget(tab)
            return

        factions = {}
        for row in rows:
            faction = row[1]
            data = {
                'military_rank': row[2],
                'avg_military_rating': row[3],
                'avg_soldiers_starving': row[4],
                'victories': row[5],
                'defeats': row[6],
                'matches_won': row[7],
                'matches_lost': row[8],
                'last_data': row[9]
            }
            factions.setdefault(faction, []).append(data)

        for faction, data_list in factions.items():
            tab = CustomTab(text=faction)
            scroll = ScrollView()
            grid = GridLayout(
                cols=1,
                spacing=dp(10),
                padding=dp(10),
                size_hint_y=None
            )
            grid.bind(minimum_height=grid.setter('height'))

            for data in data_list:
                card = self._create_character_card(data)
                grid.add_widget(card)

            scroll.add_widget(grid)
            tab.add_widget(scroll)
            tabs_widget.add_widget(tab)

    # Модифицируем load_dossier_data, чтобы он использовал текущий self.tabs
    def load_dossier_data(self):
        """
        Читает данные из SQLite и наполняет текущий TabbedPanel (self.tabs).
        """
        self._load_dossier_data_to_tabs(self.tabs)

    def go_back(self, instance):
        """Переход в главное меню."""
        app = App.get_running_app()
        root = app.root
        root.clear_widgets()
        root.add_widget(MenuWidget(self.conn)) # MenuWidget находится в этом же файле не надо ничего импортировать

    def _recreate_dossier_tab(self):
        """Пересоздание вкладки."""
        for tab in list(self.tabs.get_tab_list()):
            self.tabs.remove_widget(tab)
        self.load_dossier_data()


class HowToPlayScreen(Screen):
    def __init__(self, conn, **kwargs):
        super().__init__(**kwargs)
        self.conn = conn
        with self.canvas.before:
            self.bg_rect = Rectangle(
                source='files/menu/how_to_play_bg.jpg',  # путь к фону экрана обучения
                pos=self.pos,
                size=self.size
            )
        self.bind(pos=self._update_bg, size=self._update_bg)
        self.build_ui()

    def build_ui(self):
        layout = BoxLayout(orientation='vertical', padding=dp(20), spacing=dp(20))

        title = Label(
            text="[b]Как играть[/b]",
            markup=True,
            font_size='32sp',
            size_hint=(1, None),
            height=dp(60),
            halign='center',
            valign='middle',
            color=(1, 1, 1, 1)
        )
        layout.add_widget(title)

        scroll = ScrollView(size_hint=(1, 1), bar_width=dp(12), scroll_type=['bars', 'content'], bar_color=(1, 1, 0, 1),
                            bar_inactive_color=(1, 1, 0, 0.4))
        content = BoxLayout(orientation='vertical', size_hint_y=None, spacing=dp(10), padding=dp(10))
        content.bind(minimum_height=content.setter('height'))

        how_to_text = (
            "[b]Экономика[/b]\n"
            "В игре есть три основных ресурса, которые можно заработать:\n"
            "- [color=#ffcc00]Крона[/color] — деньги, добываются продажей Кристаллов, налогами или выпрашиванием у "
            "союзника.\n"
            "- [color=#99ccff]Кристаллы[/color] — ресурс, растет от количества фабрик. При отрицательном значении "
            "население сокращается (если население достигнет 0, то засчитается поражение).\n"
            "- [color=#00ccff]Рабочие[/color] — требуются для найма юнитов и увеличивают население (которое дает "
            "кроны). Растут от количества больниц.\n\n"
            "[b]Боевые единицы[/b]\n"
            "В игре используется новая структура армии в отличие от 'Лэрдона':\n\n"
            "- [b]1 класс[/b] — основные юниты. Без героя крайне слабы.\n"
            "- [b]2 и 3 классы[/b] — герои, усиливают 1 класс своими характеристиками.\n"
            "- [b]4 класс[/b] — элита. Не усиливают других, но сильны сами по себе.\n\n"
            "[b]Порядок атаки[/b]\n"
            "1 класс — вступают в бой первыми, затем 2 класс, после него 3, и в конце 4.\n"
            "Если в армии несколько типов 1 класса, первыми в бой вступают те, у кого [color=#FFD700]наибольший урон[/color].\n\n"
            "[b]Поддержка героев[/b]\n"
            "Отсутствие героя делает юниты 1 класса почти бесполезными против сильного врага.\n"
            "Сами герои могут делиться на тех, кто больше полезен в защите, и тех, кто больше полезен в атаке "
            "(здесь важно обратить внимание на то, какая характеристика у героя больше).\n\n"
            "[b]Ресурсы и идеологии[/b]\n"
            "Каждая фракция при старте игры обладает своей идеологией:\n"
            "- [b]Смирение[/b] — увеличивает доход [color=#ffcc00]крон[/color].\n"
            "- [b]Борьба[/b] — увеличивает поступление [color=#99ccff]Кристаллов[/color].\n"
            "Обе идеологии ненавидят друг друга и рано или поздно начнут войну, если у одного из них окажется слабая армия.\n\n"

            "[b]Совет и дворцовые интриги[/b]\n"
            "В игре присутствует система Совета, где заседают влиятельные члены совета фракции. У каждого из них — свои "
            "политические взгляды, интересы и амбиции.\n\n"
            "[b]Разные типы членов совета:[/b]\n"
            "- Кто-то придерживается определённой идеологии.\n"
            "- Кто-то выступает за хорошие отношения с конкретной фракцией.\n"
            "- А есть и те, кто не прочь изменить своим принципам — за соответствующее вознаграждение. У таких персонажей "
            "доступна кнопка [b]'Договориться'[/b].\n\n"
            "[b]Управление лояльностью:[/b]\n"
            "Они озвучат свою цену, и если вы её заплатите — станут более лояльными. Однако за их лояльностью нужно следить: "
            "со временем она может снижаться. Чтобы этого не произошло — периодически проводите мероприятия, направленные "
            "на укрепление их симпатий.\n\n"
            "[b]Что будет, если игнорировать совет?[/b]\n"
            "Если вы не будете пытаться угодить членам совета, возможны следующие сценарии:\n\n"
            "- [b]Открытая оппозиция:[/b] придётся прибегнуть к устранению неугодных членов совета. Но будьте осторожны: "
            "тайные службы не всегда справляются со своей задачей. Провал может стать достоянием общественности и серьёзно "
            "подорвать ваш авторитет.\n"
            "- [b]Переворот:[/b] если вы полностью проигнорируете политическую игру, члены совета могут потребовать "
            "освободить трон. Это сулит [b]мгновенное поражение[/b], даже если вы завоевали половину мира — потеря власти "
            "в собственных стенах делает все ваши победы бессмысленными."
        )

        label = Label(
            text=how_to_text,
            markup=True,
            font_size='18sp',
            halign='left',
            valign='top',
            size_hint_y=None,
            text_size=(Window.width * 0.9, None)
        )
        label.bind(texture_size=lambda instance, value: setattr(label, 'height', value[1]))

        content.add_widget(label)
        scroll.add_widget(content)

        # Пульсация полосы прокрутки
        from kivy.animation import Animation
        def animate_bar():
            anim = Animation(bar_color=(1, 0.6, 0, 1), duration=0.5) + Animation(bar_color=(1, 1, 0, 1), duration=0.5)
            anim.repeat = True
            anim.start(scroll)

        animate_bar()
        layout.add_widget(scroll)

        back_button = Button(
            text="Назад",
            size_hint=(0.3, None),
            height=dp(50),
            pos_hint={'center_x': 0.5},
            background_color=(0.2, 0.6, 1, 1),
            color=(1, 1, 1, 1),
            font_size='16sp'
        )
        back_button.bind(on_release=self.go_back)
        layout.add_widget(back_button)

        self.add_widget(layout)

    def _update_bg(self, *args):
        self.bg_rect.pos = self.pos
        self.bg_rect.size = self.size

    def go_back(self, instance):
        app = App.get_running_app()
        app.root.clear_widgets()
        app.root.add_widget(MenuWidget(self.conn))


class Lerdon(App):
    def __init__(self, **kwargs):
        super(Lerdon, self).__init__(**kwargs)
        print("app starting...")
        # Флаг, что мы на мобильной платформе Android
        self.is_mobile = (platform == 'android')
        # Можно завести другие глобальные настройки здесь
        self.selected_kingdom = None  # Атрибут для хранения выбранного королевства

        # Инициализация соединения с базой данных
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA journal_mode=WAL;")
        self.conn.execute("PRAGMA synchronous=NORMAL;")
        self.conn.execute("PRAGMA busy_timeout=5000;")

    def build(self):
        """Создает начальный интерфейс приложения."""

        return LoadingScreen(self.conn)

    def restart_app(self):
        """Перезапуск игры — очистка БД, восстановление бэкапа, пересоздание интерфейса."""
        try:
            # Очистка таблиц
            clear_tables(self.conn)
            self.conn.commit()
            print("Таблицы успешно очищены.")
        except sqlite3.Error as e:
            print(f"Ошибка при очистке таблиц: {e}")
            self.conn.rollback()

        # Восстановление из бэкапа
        restore_from_backup(self.conn)

        # Сброс состояния приложения
        self.selected_kingdom = None

        # Полная очистка корневого виджета
        if self.root:
            self.root.clear_widgets()

        # Пересоздание главного меню
        Clock.schedule_once(self.recreate_main_menu, 0.2)

    def recreate_main_menu(self, dt):
        """Пересоздание главного меню после очистки."""
        self.root.add_widget(MenuWidget(self.conn))
        print("Главное меню полностью пересоздано")

    def on_stop(self):
        print("Завершение работы приложения...")

        # 1) Делаем checkpoint и сразу закрываем — без переключения journal_mode
        try:
            self.conn.execute("PRAGMA wal_checkpoint(TRUNCATE);")
        except sqlite3.Error as e:
            print(f"[WARNING] Не удалось сделать WAL checkpoint: {e}")

        try:
            self.conn.close()
            print("Соединение с БД закрыто корректно.")
        except sqlite3.Error as e:
            print(f"Ошибка при закрытии соединения с БД: {e}")

        # 2) Удаляем файлы WAL/SHM (опционально)
        for ext in (".db-wal", ".db-shm"):
            path = db_path + ext
            if os.path.exists(path):
                try:
                    os.remove(path)
                    print(f"Удалён файл {path}")
                except OSError as e:
                    print(f"Не удалось удалить {path}: {e}")

        print("Приложение завершило работу.")

    def get_connection(self):
        """Возвращает текущее соединение с БД."""
        return self.conn

if __name__ == '__main__':
    Lerdon().run()

