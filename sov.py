from db_lerdon_connect import *


def calculate_font_size():
    base_height = 360
    default_font_size = 14
    scale_factor = Window.height / base_height

    # Увеличиваем шрифт на Android
    if platform == 'android':
        scale_factor *= 1.5  # или 2 для более крупного текста

    return max(14, int(default_font_size * scale_factor))


# Словарь для перевода названий
translation_dict = {
    "Люди": "people",
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


class AdvisorView(FloatLayout):
    def __init__(self, faction, conn, **kwargs):
        super(AdvisorView, self).__init__(**(kwargs))
        self.faction = faction
        self.db_connection = conn  # Единое подключение к базе
        self.cursor = self.db_connection.cursor()
        self._attack_progress = 0
        self._defense_progress = 0
        # Инициализация таблицы political_systems
        self.initialize_political_systems()
        # Настройки темы
        self.colors = {
            'background': (0.95, 0.95, 0.95, 1),
            'primary': (0.118, 0.255, 0.455, 1),  # Темно-синий
            'accent': (0.227, 0.525, 0.835, 1),  # Голубой
            'text': (1, 1, 1, 1),
            'card': (1, 1, 1, 1)
        }

        # Создаем главное окно
        self.interface_window = FloatLayout(size_hint=(1, 1))

        # Основной контейнер
        main_layout = BoxLayout(
            orientation='horizontal',
            spacing=dp(20),
            padding=dp(20),
            size_hint=(1, 1)
        )

        # Левая панель с изображением
        left_panel = FloatLayout(size_hint=(0.45, 1))

        # Правая панель
        right_panel = BoxLayout(
            orientation='vertical',
            size_hint=(0.55, 1),
            spacing=0,
            padding=0
        )

        # Панель вкладок
        tabs_panel = ScrollView(
            size_hint=(1, None),
            height=Window.height * 0.3,  # Адаптивная высота
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

        # Сборка интерфейса
        main_layout.add_widget(left_panel)
        main_layout.add_widget(right_panel)

        # Нижняя панель с кнопками
        bottom_panel = BoxLayout(
            size_hint=(1, None),
            height=Window.height * 0.1,  # Адаптивная высота
            padding=dp(10),
            pos_hint={'x': 0, 'y': 0},
            spacing=dp(10)
        )

        political_system_button = Button(
            text="Идеология",
            size_hint=(1, 1),  # Растягиваем кнопку по ширине и высоте
            background_normal='',
            background_color=(0.227, 0.525, 0.835, 1),
            color=(1, 1, 1, 1),
            font_size=calculate_font_size(),  # Размер шрифта зависит от высоты окна
            bold=True,
            border=(0, 0, 0, 0)
        )
        political_system_button.bind(on_release=lambda x: self.show_political_systems())

        relations_button = Button(
            text="Отношения",
            size_hint=(1, 1),  # Растягиваем кнопку по ширине и высоте
            background_normal='',
            background_color=(0.118, 0.255, 0.455, 1),
            color=(1, 1, 1, 1),
            font_size=calculate_font_size(),  # Размер шрифта зависит от высоты окна
            bold=True,
            border=(0, 0, 0, 0)
        )
        relations_button.bind(on_release=lambda x: self.show_relations("Состояние отношений"))

        bottom_panel.add_widget(political_system_button)
        bottom_panel.add_widget(relations_button)

        self.interface_window.add_widget(main_layout)
        self.interface_window.add_widget(bottom_panel)

        # Создаем Popup
        self.popup = Popup(
            title=f"",  # Жирный шрифт с помощью [b][/b]
            title_size=Window.height * 0.03,  # Размер заголовка зависит от высоты окна
            title_align="center",  # Центрирование текста (по умолчанию уже centered, но явно указываем)
            content=self.interface_window,
            size_hint=(0.7, 0.7),
            separator_height=dp(0),
            background=f'files/sov/parlament/{translation_dict.get(self.faction)}_palace.jpg' if os.path.exists(
                f'files/sov/parlament/{translation_dict.get(self.faction)}_palace.jpg') else ''
        )
        self.popup.open()


    def create_arrow_icon(self, direction):
        if direction == "up":
            source = 'files/pict/up.png'
        else:
            source = 'files/pict/down.png'

        return Image(
            source=source,
            size_hint=(None, None),
            size=(dp(24), dp(24)),
            allow_stretch=True,
            keep_ratio=True
        )

    def load_political_system(self):
        """
        Загружает текущую политическую систему фракции из базы данных.
        """
        try:
            query = "SELECT system FROM political_systems WHERE faction = ?"
            self.cursor.execute(query, (self.faction,))
            result = self.cursor.fetchone()
            return result[0] if result else "Смирение"  # По умолчанию "Смирение"
        except sqlite3.Error as e:
            print(f"Ошибка при загрузке политической системы: {e}")
            return "Смирение"

    def load_political_systems(self):
        """
        Загружает данные о политических системах всех фракций из базы данных.
        Возвращает словарь, где ключи — названия фракций, а значения — информация о системе и её влиянии.
        """
        try:
            query = "SELECT faction, system FROM political_systems"
            self.cursor.execute(query)
            rows = self.cursor.fetchall()

            # Преобразуем результат в словарь
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
        """
        Возвращает текстовое описание влияния политической системы.
        """
        if system == "Смирение":
            return 15
        elif system == "Борьба":
            return 15
        else:
            return "Неизвестное влияние"

    def initialize_political_systems(self):
        """
        Инициализирует таблицу political_systems значениями по умолчанию,
        если она пуста. Политическая система для каждой фракции выбирается случайным образом.
        Условие: не может быть меньше 2 и больше 3 стран с одним политическим строем.
        """
        try:
            # Проверяем, есть ли записи в таблице
            self.cursor.execute("SELECT COUNT(*) FROM political_systems")
            count = self.cursor.fetchone()[0]
            if count == 0:
                # Список всех фракций
                factions = ["Люди", "Эльфы", "Вампиры", "Адепты", "Элины"]

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
        """
        Обновляет политическую систему фракции в базе данных и пересоздает окно.
        """
        try:
            # Обновляем политическую систему в базе данных
            query = """
                INSERT INTO political_systems (faction, system)
                VALUES (?, ?)
                ON CONFLICT(faction) DO UPDATE SET system = excluded.system
            """
            self.cursor.execute(query, (self.faction, new_system))
            self.db_connection.commit()
            print(f"Политическая система обновлена: {new_system}")

            # Пересоздаем окно с обновленными данными
            if hasattr(self, 'popup') and self.popup:
                self.popup.dismiss()  # Закрываем текущее окно
            self.show_political_systems()  # Показываем обновленное окно

        except sqlite3.Error as e:
            print(f"Ошибка при обновлении политической системы: {e}")

    def close_window(self, instance):
        """Закрытие окна"""
        print("Метод close_window вызван.")  # Отладочный вывод
        if hasattr(self, 'popup') and self.popup:
            self.popup.dismiss()
        else:
            print("Ошибка: Попап не найден.")

    def load_relations(self):
        """
        Загружает текущие отношения из таблицы relations в базе данных.
        Возвращает словарь, где ключи — названия фракций, а значения — уровни отношений.
        """
        try:
            # Выполняем запрос к таблице relations
            self.cursor.execute('''
                SELECT faction2, relationship
                FROM relations
                WHERE faction1 = ?
            ''', (self.faction,))
            rows = self.cursor.fetchall()

            # Преобразуем результат в словарь
            relations = {faction2: relationship for faction2, relationship in rows}
            return relations

        except sqlite3.Error as e:
            print(f"Ошибка при загрузке отношений из таблицы relations: {e}")
            return {}

    def calculate_coefficient(self, relation_level):
        """Рассчитывает коэффициент на основе уровня отношений"""
        relation_level = int(relation_level)
        if relation_level < 15:
            return 0
        elif 15 <= relation_level < 25:
            return 0.08
        elif 25 <= relation_level < 35:
            return 0.3
        elif 35 <= relation_level < 50:
            return 0.8
        elif 50 <= relation_level < 60:
            return 1.0
        elif 60 <= relation_level < 75:
            return 1.4
        elif 75 <= relation_level < 90:
            return 2.0
        elif 90 <= relation_level <= 100:
            return 2.9
        else:
            return 0

    def load_combined_relations(self):
        """
        Загружает и комбинирует отношения из таблицы relations и файла diplomaties
        Возвращает словарь, где ключи — названия фракций, а значения — словари с уровнем отношений и статусом.
        """
        # Загрузка данных из таблицы relations
        relations_data = self.load_relations()
        print("Загруженные данные из таблицы relations:", relations_data)  # Отладочный вывод

        # Загрузка данных из таблицы diplomaties
        diplomacies_data = self.load_diplomacies()
        print("Загруженные данные из таблицы diplomaties:", diplomacies_data)  # Отладочный вывод

        # Создаем комбинированный словарь отношений
        combined_relations = {}

        # Обрабатываем данные из таблицы relations
        for target_faction, relation_level in relations_data.items():
            combined_relations[target_faction] = {
                "relation_level": relation_level,
                "status": "неизвестно"  # значение по умолчанию
            }

        # Добавляем/обновляем статусы из таблицы diplomaties
        for target_faction, status in diplomacies_data.items():
            if target_faction in combined_relations:
                combined_relations[target_faction]["status"] = status
            else:
                combined_relations[target_faction] = {
                    "relation_level": 0,  # значение по умолчанию
                    "status": status
                }

        print("Комбинированные отношения:", combined_relations)  # Отладочный вывод
        return combined_relations


    def reset_popup_to_main(self, *args):
        """Возвращает к главному интерфейсу вкладки"""
        # Очищаем и восстанавливаем основной интерфейс
        self.interface_window.clear_widgets()
        main_layout = BoxLayout(
            orientation='horizontal',
            spacing=dp(20),
            padding=dp(20),
            size_hint=(1, 1)
        )

        # Левая панель с изображением
        left_panel = FloatLayout(size_hint=(0.45, 1))
        # Правая панель
        right_panel = BoxLayout(
            orientation='vertical',
            size_hint=(0.55, 1),
            spacing=0,
            padding=0
        )

        # Панель вкладок
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

        # Сборка интерфейса
        main_layout.add_widget(left_panel)
        main_layout.add_widget(right_panel)

        # Нижняя панель с кнопками
        bottom_panel = BoxLayout(
            size_hint=(1, None),
            height=Window.height * 0.1,
            padding=dp(10),
            pos_hint={'x': 0, 'y': 0},
            spacing=dp(10)
        )
        political_system_button = Button(
            text="Идеология",
            size_hint=(1, 1),
            background_normal='',
            background_color=(0.227, 0.525, 0.835, 1),
            color=(1, 1, 1, 1),
            font_size=calculate_font_size(),
            bold=True,
            border=(0, 0, 0, 0)
        )
        political_system_button.bind(on_release=lambda x: self.show_political_systems())

        relations_button = Button(
            text="Отношения",
            size_hint=(1, 1),
            background_normal='',
            background_color=(0.118, 0.255, 0.455, 1),
            color=(1, 1, 1, 1),
            font_size=calculate_font_size(),
            bold=True,
            border=(0, 0, 0, 0)
        )
        relations_button.bind(on_release=lambda x: self.show_relations("Состояние отношений"))

        bottom_panel.add_widget(political_system_button)
        bottom_panel.add_widget(relations_button)

        self.interface_window.add_widget(main_layout)
        self.interface_window.add_widget(bottom_panel)

        self.popup.content = self.interface_window

    def load_diplomacies(self):
        """
        Загружает дипломатические соглашения из базы данных для текущей фракции (self.faction).
        Возвращает словарь, где ключи — названия фракций, а значения — статусы отношений.
        """
        diplomacies_data = {}
        try:
            cursor = self.db_connection.cursor()
            # Добавляем условие WHERE faction1 = ?
            query = "SELECT faction2, relationship FROM diplomacies WHERE faction1 = ?"
            cursor.execute(query, (self.faction,))
            rows = cursor.fetchall()

            print("Загруженные данные из таблицы diplomacies:", rows)  # Отладочный вывод

            # Преобразуем результат в словарь
            for faction2, relationship in rows:
                diplomacies_data[faction2] = relationship

        except sqlite3.Error as e:
            print(f"Ошибка при работе с базой данных: {e}")
        finally:
            print("Результат загрузки diplomacies_data:", diplomacies_data)  # Отладочный вывод
            return diplomacies_data

    def manage_relations(self):
        """
        Управление отношениями только для фракций, заключивших дипломатическое соглашение.
        Использует данные из таблиц БД `relations` и `diplomacies`.
        """
        # Загружаем текущие отношения из базы данных
        relations_data = self.load_relations()

        if not relations_data:
            print(f"Отношения для фракции {self.faction} не найдены.")
            return

        # Загружаем дипломатические соглашения из базы данных
        diplomacies_data = self.load_diplomacies()

        # Проверяем, есть ли дипломатические соглашения для текущей фракции
        if self.faction not in diplomacies_data:
            print(f"Дипломатические соглашения для фракции {self.faction} не найдены.")
            return

        # Получаем список фракций, с которыми заключены соглашения
        agreements = diplomacies_data[self.faction].get("отношения", {})

        for target_faction, status in agreements.items():
            if status == "союз":  # Рассматриваем только фракции с дипломатическим союзом
                # Проверяем, есть ли отношения с этой фракцией
                if target_faction in relations_data:
                    current_value_self = relations_data[target_faction]
                    current_value_other = self.load_relations_for_target(target_faction).get(self.faction, 0)

                    # Увеличиваем уровень отношений (не более 100)
                    relations_data[target_faction] = min(current_value_self + 7, 100)
                    self.update_relations_in_db(target_faction, min(current_value_other + 7, 100))

        # Сохраняем обновленные данные в базу данных
        self.save_relations_to_db(relations_data)

    def load_relations_for_target(self, target_faction):
        """
        Загружает отношения для указанной целевой фракции.
        Возвращает словарь, где ключи — названия фракций, а значения — уровни отношений.
        """
        try:
            self.cursor.execute('''
                SELECT faction2, relationship
                FROM relations
                WHERE faction1 = ?
            ''', (target_faction,))
            rows = self.cursor.fetchall()
            return {faction2: relationship for faction2, relationship in rows}
        except sqlite3.Error as e:
            print(f"Ошибка при загрузке отношений для фракции {target_faction}: {e}")
            return {}

    def update_relations_in_db(self, target_faction, new_value):
        """
        Обновляет уровень отношений в базе данных для указанной целевой фракции.
        """
        try:
            self.cursor.execute('''
                UPDATE relations
                SET relationship = ?
                WHERE faction1 = ? AND faction2 = ?
            ''', (new_value, target_faction, self.faction))
            self.db_connection.commit()
        except sqlite3.Error as e:
            print(f"Ошибка при обновлении отношений для фракции {target_faction}: {e}")

    def save_relations_to_db(self, relations_data):
        """
        Сохраняет обновленные отношения в базу данных.
        """
        try:
            for target_faction, relationship in relations_data.items():
                self.cursor.execute('''
                    UPDATE relations
                    SET relationship = ?
                    WHERE faction1 = ? AND faction2 = ?
                ''', (relationship, self.faction, target_faction))
            self.db_connection.commit()
            print("Отношения успешно сохранены в базе данных.")
        except sqlite3.Error as e:
            print(f"Ошибка при сохранении отношений в базе данных: {e}")

    def show_political_systems(self):
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

        system_layout = BoxLayout(
            orientation='horizontal',
            size_hint=(1, None),
            height=dp(60),
            spacing=dp(10)
        )

        capitalism_button = Button(
            text="Смирение",
            background_color=(0.2, 0.7, 0.3, 1),
            font_size='18sp',
            size_hint=(0.5, None),
            height=dp(50),
            color=(1, 1, 1, 1),
            background_normal='',
            background_down=''
        )
        communism_button = Button(
            text="Борьба",
            background_color=(0.8, 0.2, 0.2, 1),
            font_size='18sp',
            size_hint=(0.5, None),
            height=dp(50),
            color=(1, 1, 1, 1),
            background_normal='',
            background_down=''
        )

        capitalism_button.bind(on_release=lambda x: self.update_political_system("Смирение"))
        communism_button.bind(on_release=lambda x: self.update_political_system("Борьба"))

        system_layout.add_widget(capitalism_button)
        system_layout.add_widget(communism_button)

        content.add_widget(system_layout)

        # Обновляем содержимое popup вместо создания нового
        self.popup.content = content

    def show_relations(self, instance):
        """Отображает окно с таблицей отношений."""
        self.manage_relations()

        # Загружаем комбинированные отношения
        combined_relations = self.load_combined_relations()
        print("Комбинированные отношения для отображения:", combined_relations)

        if not combined_relations:
            print(f"Нет данных об отношениях для фракции {self.faction}.")
            return

        # Очищаем текущее содержимое popup
        content = BoxLayout(orientation='vertical', spacing=dp(8), padding=dp(10))

        table = GridLayout(
            cols=4,
            size_hint_y=None,
            spacing=dp(4),
            row_default_height=dp(40)
        )
        table.bind(minimum_height=table.setter('height'))

        for title in ["Фракция", "Отношения", "Торговля", "Статус"]:
            table.add_widget(self.create_header(title))

        for country, data in combined_relations.items():
            relation_level = data["relation_level"]
            status = data["status"]

            table.add_widget(self.create_cell(country))
            table.add_widget(self.create_value_cell(relation_level))
            table.add_widget(self.create_value_trade_cell(self.calculate_coefficient(relation_level)))
            table.add_widget(self.create_status_cell(status))

        scroll = ScrollView(
            size_hint=(1, 0.7),
            bar_width=dp(6),
            bar_color=(0.5, 0.5, 0.5, 0.6),
            scroll_type=['bars', 'content']
        )
        scroll.add_widget(table)
        content.add_widget(scroll)

        back_button = Button(
            text="Назад",
            background_color=(0.227, 0.525, 0.835, 1),
            font_size='16sp',
            size_hint=(1, None),
            height=dp(48),
            color=(1, 1, 1, 1),
            background_normal='',
            background_down=''
        )
        back_button.bind(on_release=lambda x: self.reset_popup_to_main())
        content.add_widget(back_button)

        # Обновляем содержимое popup вместо создания нового
        self.popup.content = content

    def create_value_cell(self, value):
        color = self.get_relation_color(value)
        return Label(
            text=str(value),
            font_size='14sp',
            bold=True,
            color=color,
            halign='center',
            valign='middle',
            size_hint_y=None,
            height=dp(40),
            outline_color=(0, 0, 0, 1),
            outline_width=2
        )

    def create_value_trade_cell(self, coefficient):
        color = self.get_relation_trade_color(coefficient)
        return Label(
            text=f"{coefficient:.1f}x",
            font_size='14sp',
            bold=True,
            color=color,
            halign='center',
            valign='middle',
            size_hint_y=None,
            height=dp(40),
            outline_color=(0, 0, 0, 1),  # Чёрная обводка
            outline_width=2  # Толщина обводки
        )

    def create_status_cell(self, status):
        color = self.get_status_color(status)
        return Label(
            text=status,
            font_size='14sp',
            bold=True,
            color=color,
            halign='center',
            valign='middle',
            size_hint_y=None,
            height=dp(40),
            outline_color=(0, 0, 0, 1),  # Чёрная обводка
            outline_width=2  # Толщина обводки
        )

    def create_cell(self, text, status="нейтралитет"):
        color = self.get_status_color(status)  # Цвет зависит от статуса
        label = Label(
            text=str(text),
            size_hint_y=None,
            height=dp(40),
            color=color,
            halign='center',
            valign='middle',
            outline_color=(0, 0, 0, 1),  # Чёрная обводка
            outline_width=2  # Толщина обводки
        )
        label.bind(size=label.setter('text_size'))
        return label

    def _create_cell(self, text, highlight=False):
        text_color = self.colors['accent'] if highlight else (1, 1, 1, 1)
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

    def create_header(self, text):
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
            outline_color=(0, 0, 0, 1),   # Чёрная обводка
            outline_width=2
        )
        label.bind(size=label.setter('text_size'))
        return label

    def get_status_color(self, status):
        """Определяет цвет на основе статуса отношений."""
        if status == "война":
            return (1, 0, 0, 1)  # Красный
        elif status == "нейтралитет":
            return (1, 1, 1, 1)  # Белый
        elif status == "союз":
            return (0, 0.75, 0.8, 1)  # Синий
        else:
            return (0.5, 0.5, 0.5, 1)  # Серый (для неизвестного статуса)


    def get_relation_trade_color(self, value):
        """Возвращает цвет в зависимости от значения коэффициента"""
        if value <= 0.09:
            return (0.8, 0.1, 0.1, 1)  # Красный
        elif 0.09 < value <= 0.2:
            return (1.0, 0.5, 0.0, 1)  # Оранжевый
        elif 0.2 < value <= 0.8:
            return (1.0, 0.8, 0.0, 1)  # Желтый
        elif 0.8 < value <= 1.0:
            return (0.2, 0.7, 0.3, 1)  # Зеленый
        elif 1.0 < value <= 1.4:
            return (0.0, 0.8, 0.8, 1)  # Голубой
        elif 1.4 < value <= 2.0:
            return (0.0, 0.6, 1.0, 1)  # Синий
        elif 2.0 < value <= 3.1:
            return (0.1, 0.3, 0.9, 1)  # Темно-синий
        else:
            return (1, 1, 1, 1)  # Белый


    def get_relation_color(self, value):
        """Возвращает цвет в зависимости от значения"""
        value = int(value)
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

    def update_rect(self, instance, value):
        """Обновляет позицию и размер прямоугольника фона"""
        self.rect.pos = instance.pos
        self.rect.size = instance.size