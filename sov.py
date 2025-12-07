from kivy.uix.checkbox import CheckBox

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
        self._attack_progress = 0
        self._defense_progress = 0
        self.game_screen = game_screen_instance

        # Инициализация таблицы политических систем
        self.initialize_political_systems()

        # Цветовая тема интерфейса
        self.colors = {
            'background': (0.95, 0.95, 0.95, 1),
            'primary': (0.118, 0.255, 0.455, 1),
            'accent': (0.227, 0.525, 0.835, 1),
            'text': (1, 1, 1, 1),
            'card': (1, 1, 1, 1)
        }

        # Главное окно интерфейса (создается ПЕРВЫМ!)
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
            height=Window.height * 0.3,  # адаптивная высота
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
        bottom_panel = BoxLayout(
            size_hint=(1, None),
            height=Window.height * 0.09,  # уменьшено на ~1.5 раза
            padding=dp(6),
            spacing=dp(6),
            pos_hint={'x': 0, 'y': 0}
        )

        button_style = {
            "size_hint": (1, 1),
            "background_normal": '',
            "color": (1, 1, 1, 1),
            "font_size": calculate_font_size() * 0.9,  # немного компактнее текст
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

        # === Финальная сборка основного интерфейса ===
        self.interface_window.add_widget(main_layout)
        self.interface_window.add_widget(bottom_panel)

        # === КНОПКА ЧАТА С ИИ (в правом верхнем углу) ===
        # Теперь interface_window уже создан, можно добавлять кнопку
        self.ai_chat_button = ClickableImage(
            source="files/pict/sov/letter.png",
            size_hint=(None, None),
            size=(dp(50), dp(50)),
            pos_hint={'right': 0.98, 'top': 0.98},
            allow_stretch=True
        )

        # Добавляем круглый фон
        with self.ai_chat_button.canvas.before:
            Color(0.2, 0.6, 0.9, 0.9)
            self.ai_chat_bg = Ellipse(
                pos=self.ai_chat_button.pos,
                size=self.ai_chat_button.size
            )

            # Обводка
            Color(1, 1, 1, 0.8)
            self.ai_chat_border = Line(
                circle=(
                    self.ai_chat_button.center_x,
                    self.ai_chat_button.center_y,
                    min(self.ai_chat_button.width, self.ai_chat_button.height) / 2 - dp(1)
                ),
                width=dp(2)
            )

        # Обновляем фон при изменении позиции/размера
        def update_ai_chat_bg(instance, value):
            instance.canvas.before.clear()
            with instance.canvas.before:
                Color(0.2, 0.6, 0.9, 0.9)
                Ellipse(pos=instance.pos, size=instance.size)

                Color(1, 1, 1, 0.8)
                Line(circle=(
                    instance.center_x,
                    instance.center_y,
                    min(instance.width, instance.height) / 2 - dp(1)
                ), width=dp(2))

        self.ai_chat_button.bind(pos=update_ai_chat_bg, size=update_ai_chat_bg)
        self.ai_chat_button.bind(on_press=self.open_ai_chat)

        # Добавляем кнопку в интерфейс (ПОСЛЕ создания interface_window!)
        self.interface_window.add_widget(self.ai_chat_button)

        # === Popup ===
        self.popup = Popup(
            title="",
            title_size=Window.height * 0.03,
            title_align="center",
            content=self.interface_window,
            size_hint=(0.7, 0.7),
            separator_height=dp(0),
            background=f'files/sov/parlament/{translation_dict.get(self.faction)}_palace.jpg'
            if os.path.exists(f'files/sov/parlament/{translation_dict.get(self.faction)}_palace.jpg') else ''
        )
        self.popup.open()

    def _update_border(self, *args):
        self.border_rect.rectangle = (
            dp(2),
            dp(2),
            self.interface_window.width - dp(4),
            self.interface_window.height - dp(4)
        )

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

    def open_ai_chat(self, instance):
        """Открывает окно дипломатических переговоров с другими фракциями"""

        # === Создаем окно дипломатии ===
        diplomacy_window = FloatLayout(size_hint=(1, 1))

        # Фон - кабинет правителя
        with diplomacy_window.canvas.before:
            Color(0.08, 0.08, 0.12, 0.95)
            Rectangle(pos=diplomacy_window.pos, size=diplomacy_window.size)

        # === Шапка с информацией о фракции игрока ===
        header = BoxLayout(
            orientation='horizontal',
            size_hint=(1, None),
            height=dp(60),
            padding=[dp(15), dp(10)],
            pos_hint={'top': 1}
        )

        # Кнопка назад
        back_button = Button(
            text="← Назад",
            size_hint=(None, None),
            size=(dp(100), dp(40)),
            background_color=(0.3, 0.3, 0.5, 1),
            background_normal='',
            font_size='16sp',
            on_press=lambda x: self.return_to_main_tab()
        )

        # Информация о текущей фракции
        faction_info = BoxLayout(
            orientation='vertical',
            size_hint=(0.4, 1),
            spacing=dp(2)
        )

        title_label = Label(
            text=f"Дипломатическая переписка",
            font_size='18sp',
            bold=True,
            color=(1, 1, 1, 1),
            halign='center'
        )

        faction_info.add_widget(title_label)

        # === ВЫПАДАЮЩИЙ СПИСОК ФРАКЦИЙ ===
        faction_selector_box = BoxLayout(
            orientation='horizontal',
            size_hint=(0.4, 1),
            spacing=dp(10)
        )

        # Метка перед списком
        selector_label = Label(
            text="Фракция:",
            font_size='16sp',
            color=(0.8, 0.8, 0.9, 1),
            size_hint=(0.4, 1)
        )

        # Создаем выпадающий список
        self.faction_spinner = Spinner(
            text='Выберите фракцию',
            values=[],
            size_hint=(0.6, None),
            size=(dp(150), dp(40)),
            background_color=(0.2, 0.3, 0.5, 1),
            font_size='14sp'
        )

        # Заполняем список фракциями
        all_factions = ["Север", "Эльфы", "Адепты", "Вампиры", "Элины"]
        for faction in all_factions:
            if faction != self.faction:
                self.faction_spinner.values.append(faction)

        self.faction_spinner.bind(text=self.on_faction_selected)

        faction_selector_box.add_widget(selector_label)
        faction_selector_box.add_widget(self.faction_spinner)

        # Кнопка обновления чата
        refresh_button = Button(
            text="🔄",
            size_hint=(None, None),
            size=(dp(40), dp(40)),
            background_color=(0.4, 0.4, 0.6, 1),
            background_normal='',
            font_size='18sp',
            on_press=lambda x: self.load_chat_history()
        )

        header.add_widget(back_button)
        header.add_widget(faction_info)
        header.add_widget(faction_selector_box)
        header.add_widget(refresh_button)

        # === Основная область чата ===
        main_area = BoxLayout(
            orientation='vertical',
            size_hint=(1, 0.85),
            spacing=dp(10),
            padding=[dp(15), dp(10)],
            pos_hint={'top': 0.88}
        )

        # === Заголовок текущей переписки ===
        chat_header = BoxLayout(
            orientation='horizontal',
            size_hint=(1, None),
            height=dp(50),
            padding=[dp(10), 0]
        )

        # Иконка текущей фракции
        self.current_faction_icon = Image(
            source='files/pict/question.png',
            size_hint=(None, None),
            size=(dp(40), dp(40)),
            allow_stretch=True
        )

        # Информация о текущих переговорах
        self.chat_info_box = BoxLayout(
            orientation='vertical',
            size_hint=(0.8, 1),
            spacing=dp(2)
        )

        self.chat_title = Label(
            text="Выберите фракцию для просмотра переписки",
            font_size='16sp',
            bold=True,
            color=(1, 1, 1, 1),
            halign='left'
        )

        self.relation_status = Label(
            text="Отношения: ---",
            font_size='12sp',
            color=(0.7, 0.7, 0.7, 1),
            halign='left'
        )

        self.chat_info_box.add_widget(self.chat_title)
        self.chat_info_box.add_widget(self.relation_status)

        chat_header.add_widget(self.current_faction_icon)
        chat_header.add_widget(self.chat_info_box)

        # === Область чата (история переписки) ===
        chat_area = BoxLayout(
            orientation='vertical',
            size_hint=(1, 0.7)
        )

        # Скроллируемая область сообщений
        self.chat_scroll = ScrollView(
            size_hint=(1, 1),
            bar_width=dp(8),
            bar_color=(0.5, 0.5, 0.5, 0.5)
        )

        self.chat_container = BoxLayout(
            orientation='vertical',
            size_hint_y=None,
            spacing=dp(10),
            padding=[dp(15), dp(10)]
        )
        self.chat_container.bind(minimum_height=self.chat_container.setter('height'))
        self.chat_scroll.add_widget(self.chat_container)

        chat_area.add_widget(chat_header)
        chat_area.add_widget(self.chat_scroll)

        # === Панель ввода нового сообщения ===
        input_panel = BoxLayout(
            orientation='horizontal',
            size_hint=(1, None),
            height=dp(60),
            spacing=dp(10),
            padding=[dp(5), dp(5)]
        )

        self.message_input = TextInput(
            hint_text="Введите ваше сообщение...",
            multiline=False,
            size_hint=(0.7, 1),
            background_color=(0.15, 0.15, 0.2, 1),
            foreground_color=(1, 1, 1, 1),
            padding=[dp(10), dp(10)]
        )

        send_button = Button(
            text="Отправить",
            size_hint=(0.3, 1),
            background_color=(0.2, 0.5, 0.8, 1),
            background_normal='',
            font_size='16sp',
            bold=True,
            on_press=self.send_diplomatic_message
        )

        input_panel.add_widget(self.message_input)
        input_panel.add_widget(send_button)

        # === Панель быстрых действий ===
        actions_panel = BoxLayout(
            orientation='horizontal',
            size_hint=(1, None),
            height=dp(50),
            spacing=dp(5),
            padding=[dp(10), dp(5)]
        )

        quick_actions = [
            ("📋 Отчет", self.request_report),
            ("💰 Торговля", self.propose_trade_quick),
            ("🤝 Мир", self.propose_peace),
            ("⚔️ Угроза", self.send_threat)
        ]

        for text, callback in quick_actions:
            btn = Button(
                text=text,
                size_hint=(1, 1),
                background_color=(0.3, 0.3, 0.5, 1),
                background_normal='',
                font_size='12sp',
                on_press=callback
            )
            actions_panel.add_widget(btn)

        # Собираем основную область
        main_area.add_widget(chat_area)
        main_area.add_widget(input_panel)
        main_area.add_widget(actions_panel)

        # === Панель статуса ===
        status_panel = BoxLayout(
            orientation='horizontal',
            size_hint=(1, None),
            height=dp(30),
            padding=[dp(15), 0],
            pos_hint={'bottom': 1}
        )

        self.chat_status = Label(
            text="Готов к дипломатической переписке",
            font_size='12sp',
            color=(0.7, 0.7, 0.7, 1)
        )

        status_panel.add_widget(self.chat_status)

        # Финальная сборка окна
        diplomacy_window.add_widget(header)
        diplomacy_window.add_widget(main_area)
        diplomacy_window.add_widget(status_panel)

        # Устанавливаем содержимое popup
        self.popup.content = diplomacy_window

        # Инициализируем выбранную фракцию
        self.selected_faction = None

        # Фокусируемся на поле ввода
        Clock.schedule_once(lambda dt: setattr(self.message_input, 'focus', True), 0.3)

    def on_faction_selected(self, spinner, text):
        """Обработчик выбора фракции из выпадающего списка"""
        if text and text != 'Выберите фракцию':
            self.selected_faction = text
            self.load_chat_history()
            self.update_chat_header(text)

    def update_chat_header(self, faction):
        """Обновляет заголовок чата при выборе фракции"""
        # Обновляем иконку
        icon_path = f"files/pict/factions/{translation_dict.get(faction, faction.lower())}.png"
        if os.path.exists(icon_path):
            self.current_faction_icon.source = icon_path
        else:
            self.current_faction_icon.source = 'files/pict/question.png'

        # Обновляем заголовок
        self.chat_title.text = f"Переписка с {faction}"

        # Обновляем статус отношений
        relations = self.load_combined_relations()
        relation_data = relations.get(faction, {"relation_level": 0, "status": "нейтралитет"})

        try:
            relation_level = int(relation_data["relation_level"])
        except (ValueError, TypeError, KeyError):
            relation_level = 0

        rel_color = self.get_relation_color(relation_level)
        self.relation_status.text = f"Отношения: {relation_level}/100 ({relation_data.get('status', 'нейтралитет')})"
        self.relation_status.color = rel_color

    def load_chat_history(self):
        """Загружает историю переписки с выбранной фракцией"""
        if not hasattr(self, 'selected_faction') or not self.selected_faction:
            self.chat_status.text = "Выберите фракцию для загрузки переписки"
            return

        # Очищаем текущие сообщения
        self.chat_container.clear_widgets()

        # Добавляем системное сообщение о начале переписки
        self.add_chat_message_system(f"Начало переписки с {self.selected_faction}. Загрузка истории...")

        try:
            cursor = self.db_connection.cursor()

            # Загружаем историю переговоров из БД
            cursor.execute('''
                SELECT message, is_player, timestamp 
                FROM negotiation_history 
                WHERE (faction1 = ? AND faction2 = ?) 
                   OR (faction1 = ? AND faction2 = ?)
                ORDER BY timestamp ASC
                LIMIT 50
            ''', (self.faction, self.selected_faction, self.selected_faction, self.faction))

            history = cursor.fetchall()

            if history:
                for message, is_player, timestamp in history:
                    # Форматируем дату
                    try:
                        dt = datetime.strptime(timestamp, '%Y-%m-%d %H:%M:%S')
                        formatted_time = dt.strftime("%d.%m %H:%M")
                    except:
                        formatted_time = timestamp

                    # Определяем отправителя
                    if bool(is_player):
                        sender = self.faction
                        is_player_msg = True
                    else:
                        sender = self.selected_faction
                        is_player_msg = False

                    # Добавляем сообщение в чат
                    self.add_chat_message(
                        message=message,
                        sender=sender,
                        timestamp=formatted_time,
                        is_player=is_player_msg
                    )

                self.chat_status.text = f"Загружено {len(history)} сообщений"
            else:
                self.add_chat_message_system("История переписки пуста. Отправьте первое сообщение!")
                self.chat_status.text = "Нет истории переписки"

        except Exception as e:
            print(f"Ошибка при загрузке истории чата: {e}")
            self.add_chat_message_system(f"Ошибка загрузки истории: {str(e)}")
            self.chat_status.text = "Ошибка загрузки"

    def add_chat_message(self, message, sender, timestamp, is_player=False):
        """Добавляет сообщение в чат"""
        message_box = BoxLayout(
            orientation='vertical',
            size_hint=(0.8 if is_player else 0.7, None),
            spacing=dp(2)
        )

        # Выравнивание сообщений
        if is_player:
            message_box.pos_hint = {'right': 1}
        else:
            message_box.pos_hint = {'x': 0}

        # Заголовок сообщения
        header = BoxLayout(
            orientation='horizontal',
            size_hint=(1, None),
            height=dp(20)
        )

        sender_label = Label(
            text=f"{'👑' if is_player else '🏛️'} {sender}",
            font_size='11sp',
            color=(0.8, 0.8, 0.8, 1) if is_player else (0.7, 0.8, 1, 1),
            size_hint=(0.7, 1),
            halign='left'
        )

        time_label = Label(
            text=timestamp,
            font_size='10sp',
            color=(0.6, 0.6, 0.6, 1),
            size_hint=(0.3, 1),
            halign='right'
        )

        header.add_widget(sender_label)
        header.add_widget(time_label)

        # Текст сообщения
        message_label = Label(
            text=message,
            font_size='13sp',
            color=(1, 1, 1, 1) if is_player else (0.9, 0.9, 0.9, 1),
            size_hint=(1, None),
            halign='left',
            valign='top'
        )
        message_label.bind(
            width=lambda *x: message_label.setter('text_size')(message_label, (message_label.width - dp(20), None)),
            texture_size=lambda *x: message_label.setter('height')(message_label,
                                                                   message_label.texture_size[1] + dp(10))
        )

        # Фон сообщения
        message_container = BoxLayout(
            orientation='vertical',
            padding=[dp(10), dp(8)]
        )

        with message_container.canvas.before:
            if is_player:
                Color(0.2, 0.4, 0.6, 0.8)  # Синий для игрока
            else:
                Color(0.3, 0.3, 0.4, 0.8)  # Серый для другой фракции
            RoundedRectangle(
                pos=message_container.pos,
                size=message_container.size,
                radius=[dp(10), ]
            )

        message_box.add_widget(header)
        message_box.add_widget(message_label)
        message_container.add_widget(message_box)

        # Добавляем в контейнер чата
        self.chat_container.add_widget(message_container)

        # Прокручиваем вниз
        Clock.schedule_once(lambda dt: self.scroll_chat_to_bottom(), 0.1)

    def add_chat_message_system(self, message):
        """Добавляет системное сообщение в чат"""
        message_box = BoxLayout(
            orientation='vertical',
            size_hint=(0.9, None),
            spacing=dp(2)
        )

        # Системное сообщение по центру
        message_box.pos_hint = {'center_x': 0.5}

        # Текст системного сообщения
        message_label = Label(
            text=f"📢 {message}",
            font_size='12sp',
            color=(0.8, 0.8, 0.4, 1),
            size_hint=(1, None),
            halign='center',
            valign='middle'
        )
        message_label.bind(
            texture_size=lambda *x: message_label.setter('height')(message_label, message_label.texture_size[1] + dp(5))
        )

        message_box.add_widget(message_label)

        # Добавляем в контейнер чата
        self.chat_container.add_widget(message_box)

    def send_diplomatic_message(self, instance):
        """Отправляет дипломатическое сообщение"""
        message = self.message_input.text.strip()
        if not message:
            return

        if not hasattr(self, 'selected_faction') or not self.selected_faction:
            self.add_chat_message_system("Сначала выберите фракцию для переписки!")
            return

        # Добавляем сообщение игрока
        current_time = datetime.now().strftime("%d.%m %H:%M")
        self.add_chat_message(
            message=message,
            sender=self.faction,
            timestamp=current_time,
            is_player=True
        )

        # Сохраняем в базу данных
        self.save_negotiation_message(self.selected_faction, message, is_player=True)

        # Очищаем поле ввода
        self.message_input.text = ""

        # Генерируем ответ ИИ (имитация)
        Clock.schedule_once(
            lambda dt: self.generate_ai_response_to_message(message, self.selected_faction),
            1.5
        )

        self.chat_status.text = "Сообщение отправлено"

    def generate_ai_response_to_message(self, player_message, target_faction):
        """Генерирует ответ от ИИ фракции"""
        # Получаем текущие отношения
        relations = self.load_combined_relations()
        relation_data = relations.get(target_faction, {"relation_level": 50, "status": "нейтралитет"})

        # Простой ИИ для ответа
        response = self.generate_diplomatic_response(player_message, target_faction, relation_data)

        # Добавляем ответ ИИ
        current_time = datetime.now().strftime("%d.%m %H:%M")
        self.add_chat_message(
            message=response,
            sender=target_faction,
            timestamp=current_time,
            is_player=False
        )

        # Сохраняем в базу данных
        self.save_negotiation_message(target_faction, response, is_player=False)

        self.chat_status.text = "Получен ответ"

    def generate_diplomatic_response(self, player_message, target_faction, relation_data):
        """Генерирует дипломатический ответ на основе сообщения и отношений"""
        player_message_lower = player_message.lower()

        # Преобразуем relation_level в int
        try:
            relation_level = int(relation_data["relation_level"])
        except (ValueError, TypeError, KeyError):
            relation_level = 50  # значение по умолчанию

        status = relation_data.get("status", "нейтралитет")

        # Получаем контекст для более умного ответа
        game_context = self.get_game_context_for_faction(target_faction)

        # === Анализ настроения сообщения ===
        mood = self.analyze_message_mood(player_message_lower)

        # === Анализ типа сообщения ===
        message_type = self.analyze_message_type(player_message_lower)

        # === Генерация ответа на основе контекста ===
        response = self.generate_contextual_response(
            player_message_lower, target_faction, relation_level,
            status, mood, message_type, game_context
        )

        return response

    def get_game_context_for_faction(self, target_faction):
        """Получает игровой контекст для указанной фракции"""
        try:
            cursor = self.db_connection.cursor()

            # Получаем ресурсы фракции
            cursor.execute("SELECT gold, crystals, food FROM resources WHERE faction = ?", (target_faction,))
            resources = cursor.fetchone()

            # Получаем количество городов
            cursor.execute("SELECT COUNT(*) FROM cities WHERE faction = ?", (target_faction,))
            city_count = cursor.fetchone()[0]

            # Получаем армию
            cursor.execute("""
                SELECT SUM(unit_count) 
                FROM garrisons g 
                JOIN units u ON g.unit_name = u.unit_name 
                WHERE u.faction = ?
            """, (target_faction,))
            army_count = cursor.fetchone()[0] or 0

            # Получаем политическую систему
            cursor.execute("SELECT system FROM political_systems WHERE faction = ?", (target_faction,))
            political_system = cursor.fetchone()
            political_system = political_system[0] if political_system else "Неизвестно"

            return {
                'resources': resources or (0, 0, 0),
                'city_count': city_count or 0,
                'army_count': army_count or 0,
                'political_system': political_system,
                'strength': self.calculate_faction_strength(target_faction)
            }

        except Exception as e:
            print(f"Ошибка при получении контекста для фракции {target_faction}: {e}")
            return {}

    def calculate_faction_strength(self, faction):
        """Рассчитывает силу фракции"""
        try:
            cursor = self.db_connection.cursor()

            # Армия
            cursor.execute("""
                SELECT SUM(unit_count * u.attack + unit_count * u.defense) 
                FROM garrisons g 
                JOIN units u ON g.unit_name = u.unit_name 
                WHERE u.faction = ?
            """, (faction,))
            army_power = cursor.fetchone()[0] or 0

            # Города
            cursor.execute("SELECT COUNT(*) FROM cities WHERE faction = ?", (faction,))
            city_count = cursor.fetchone()[0] or 0

            # Ресурсы
            cursor.execute("SELECT gold, crystals, food FROM resources WHERE faction = ?", (faction,))
            resources = cursor.fetchone()
            resource_score = sum(resources) if resources else 0

            return army_power + (city_count * 100) + (resource_score * 0.1)

        except Exception as e:
            print(f"Ошибка при расчете силы фракции {faction}: {e}")
            return 0

    def analyze_message_mood(self, message):
        """Анализирует настроение сообщения"""
        positive_words = ['спасибо', 'благодарю', 'прошу', 'пожалуйста', 'уважаем', 'ценю',
                          'рад', 'рады', 'отличн', 'прекрасн', 'замечательн', 'согласн', 'дружб']

        negative_words = ['угроз', 'уничтож', 'нападу', 'атакую', 'война', 'ненавижу',
                          'против', 'враг', 'смерть', 'уничтожу', 'раздавлю', 'сокрушу']

        neutral_words = ['предлагаю', 'обсуж', 'договор', 'соглашен', 'торгов', 'ресурс',
                         'город', 'помощь', 'поддержк', 'информац', 'вопрос']

        question_words = ['?', 'почему', 'зачем', 'когда', 'сколько', 'где', 'кто', 'что', 'как']

        positive_score = sum(1 for word in positive_words if word in message)
        negative_score = sum(1 for word in negative_words if word in message)
        neutral_score = sum(1 for word in neutral_words if word in message)
        is_question = any(word in message for word in question_words)

        if negative_score > positive_score and negative_score > neutral_score:
            return "negative"
        elif positive_score > negative_score and positive_score > neutral_score:
            return "positive"
        elif is_question:
            return "question"
        else:
            return "neutral"

    def analyze_message_type(self, message):
        """Анализирует тип сообщения"""
        categories = {
            'greeting': ['привет', 'здравствуй', 'добрый', 'hello', 'hi', 'день'],
            'farewell': ['пока', 'до свидан', 'прощай', 'удачи', 'bye'],
            'alliance': ['союз', 'альянс', 'объедин', 'вместе', 'совмест', 'помощь военн'],
            'war': ['война', 'атака', 'напасть', 'уничтож', 'сражен', 'битв', 'конфликт'],
            'trade': ['торгов', 'обмен', 'ресурс', 'товар', 'куплю', 'продам', 'цен', 'деньг', 'крон'],
            'peace': ['мир', 'перемир', 'прекрат', 'законч', 'договор мирн'],
            'threat': ['угроз', 'опас', 'предупрежд', 'осторожн', 'последств'],
            'information': ['информац', 'данн', 'сведен', 'отчет', 'состоян', 'ситуац', 'новост'],
            'request': ['прошу', 'запрос', 'требу', 'нужн', 'хочу', 'желаю'],
            'offer': ['предлагаю', 'предложен', 'могу', 'готов', 'соглас']
        }

        scores = {category: 0 for category in categories}

        for category, words in categories.items():
            for word in words:
                if word in message:
                    scores[category] += 1

        # Возвращаем категорию с наибольшим количеством совпадений
        max_score = max(scores.values())
        if max_score > 0:
            for category, score in scores.items():
                if score == max_score:
                    return category

        return "general"

    def generate_contextual_response(self, message, faction, relation_level, status, mood, message_type, context):
        """Генерирует контекстный ответ"""

        # Словарь персонажей для разных фракций
        faction_personalities = {
            "Север": {"formal": 8, "aggressive": 6, "pragmatic": 7, "honorable": 9},
            "Эльфы": {"formal": 9, "aggressive": 3, "pragmatic": 6, "honorable": 8, "wise": 9},
            "Адепты": {"formal": 7, "aggressive": 5, "pragmatic": 8, "honorable": 6, "mysterious": 8},
            "Вампиры": {"formal": 9, "aggressive": 8, "pragmatic": 7, "honorable": 4, "arrogant": 9},
            "Элины": {"formal": 6, "aggressive": 4, "pragmatic": 9, "honorable": 7, "diplomatic": 8}
        }

        personality = faction_personalities.get(faction, {"formal": 7, "pragmatic": 6, "honorable": 6})

        # === Формирование ответа на основе типа сообщения ===

        if message_type == "greeting":
            if mood == "positive":
                greetings = [
                    f"{faction} приветствует вас, правитель. Надеюсь, дела идут хорошо.",
                    f"Добро пожаловать, ваше величество. Рады слышать от вас.",
                    f"Приветствую вас от имени {faction}. Чем можем быть полезны?"
                ]
            else:
                greetings = [
                    f"{faction} вас слушает.",
                    f"Мы получили ваше сообщение. Говорите.",
                    f"{faction} на связи. Что вам нужно?"
                ]
            return self.select_response_by_personality(greetings, personality)

        elif message_type == "farewell":
            farewells = [
                f"До новых встреч, правитель. Пусть удача сопутствует вам.",
                f"Прощайте. Надеюсь, наши пути пересекутся вновь.",
                f"{faction} прощается с вами. Будьте осторожны."
            ]
            return self.select_response_by_personality(farewells, personality)

        elif message_type == "alliance":
            return self.generate_alliance_response(faction, relation_level, status, mood, personality, context)

        elif message_type == "war":
            return self.generate_war_response(faction, relation_level, status, mood, personality, context)

        elif message_type == "trade":
            return self.generate_trade_response(faction, relation_level, status, mood, personality, context)

        elif message_type == "peace":
            return self.generate_peace_response(faction, relation_level, status, mood, personality, context)

        elif message_type == "threat":
            return self.generate_threat_response(faction, relation_level, status, mood, personality, context)

        elif message_type == "information":
            return self.generate_information_response(faction, relation_level, status, mood, personality, context,
                                                      message)

        elif message_type == "request":
            return self.generate_request_response(faction, relation_level, status, mood, personality, context, message)

        elif message_type == "offer":
            return self.generate_offer_response(faction, relation_level, status, mood, personality, context, message)

        else:
            # Общий ответ для неопределенных сообщений
            if mood == "question":
                responses = [
                    f"Интересный вопрос. {faction} должна обдумать это.",
                    f"Нам нужно больше информации чтобы ответить на ваш вопрос.",
                    f"Это требует размышлений. Дайте нам время."
                ]
            elif mood == "positive":
                responses = [
                    f"Благодарим за ваше сообщение. {faction} ценит ваше обращение.",
                    f"Мы рады услышать от вас. Спасибо за сообщение.",
                    f"Ваши слова не останутся без внимания."
                ]
            elif mood == "negative":
                responses = [
                    f"{faction} отмечает ваш тон. Будем надеяться на лучшее.",
                    f"Мы слышим вас. Давайте сохраним спокойствие.",
                    f"Ваше сообщение получено. Просим сохранять дипломатический тон."
                ]
            else:
                responses = [
                    f"{faction} получила ваше сообщение. Мы рассмотрим его.",
                    f"Сообщение принято к сведению.",
                    f"Ваше обращение зарегистрировано."
                ]

            return self.select_response_by_personality(responses, personality)

    def select_response_by_personality(self, responses, personality):
        """Выбирает ответ в соответствии с личностью фракции"""
        import random

        # Взвешенный выбор в зависимости от личности
        if personality.get("arrogant", 0) > 7:
            # Более высокомерные ответы
            arrogant_responses = [
                "Мы выслушали ваши слова. Надеемся, они стоили нашего времени.",
                "Ваше сообщение... интересно. Для кого-то вашего уровня.",
                f"Мы приняли к сведению. Не ожидайте слишком многого."
            ]
            responses = arrogant_responses + responses

        if personality.get("wise", 0) > 7:
            # Более мудрые/загадочные ответы
            wise_responses = [
                "Ветры перемен приносят ваши слова. Мы прислушаемся к ним.",
                "Как листья на дереве времени, ваше сообщение найдет свой ответ.",
                "Мудрость требует размышлений. Мы дадим ответ в должное время."
            ]
            responses = wise_responses + responses

        if personality.get("aggressive", 0) > 7:
            # Более агрессивные ответы
            aggressive_responses = [
                "Говорите яснее, у нас нет времени на пустые слова.",
                "Ваше сообщение получено. Будьте кратки в следующий раз.",
                "Мы слушаем. Но наше терпение не безгранично."
            ]
            responses = aggressive_responses + responses

        return random.choice(responses)

    def generate_alliance_response(self, faction, relation_level, status, mood, personality, context):
        """Генерирует ответ на предложение союза"""

        if status == "союз":
            responses = [
                f"Мы уже союзники, правитель. Нужно ли что-то еще?",
                f"Наш союз крепок. Что вас беспокоит?",
                f"Как союзники, мы готовы слушать ваши предложения."
            ]
        elif relation_level > 75:
            if mood == "positive":
                responses = [
                    f"{faction} рассматривает ваше предложение о союзе благосклонно.",
                    f"Наши отношения достаточно крепки для союза. Обсудим детали?",
                    f"Мы заинтересованы в союзе. Какие условия вы предлагаете?"
                ]
            else:
                responses = [
                    f"Союз возможен, но нужны гарантии с вашей стороны.",
                    f"{faction} готова обсуждать союз, но у нас есть условия.",
                    f"Мы рассматриваем ваше предложение. Что вы можете предложить взамен?"
                ]
        elif relation_level > 50:
            responses = [
                f"Наши отношения еще развиваются. Давайте укрепим их прежде чем говорить о союзе.",
                f"Союз требует больше доверия. Предлагаю сначала наладить торговлю.",
                f"{faction} видит потенциал, но пока рано говорить о полноценном союзе."
            ]
        else:
            responses = [
                f"Наши отношения слишком натянуты для союза. Предлагаю начать с малого.",
                f"{faction} не видит оснований для союза при текущих отношениях.",
                f"Прежде чем говорить о союзе, нам нужно улучшить взаимопонимание."
            ]

        return self.select_response_by_personality(responses, personality)

    def generate_war_response(self, faction, relation_level, status, mood, personality, context):
        """Генерирует ответ на угрозы войны"""

        faction_strength = context.get('strength', 0)

        if status == "война":
            if mood == "negative":
                responses = [
                    f"Мы уже воюем! Ваши угрозы бессмысленны!",
                    f"Война идет. Говорите о мире или готовьтесь к бою!",
                    f"На поле боя слова ничего не стоят!"
                ]
            else:
                responses = [
                    f"Конфликт между нами продолжается. Что вы предлагаете?",
                    f"Мы в состоянии войны. Ищем пути к разрешению.",
                    f"Война - это реальность. Давайте искать выход."
                ]
        else:
            if relation_level < 30:
                if faction_strength > self.calculate_faction_strength(self.faction):
                    responses = [
                        f"{faction} не боится ваших угроз! Мы готовы к войне!",
                        f"Вы бросаете вызов не той фракции! Наши армии ждут!",
                        f"Угрозы? {faction} ответит сталью и кровью!"
                    ]
                else:
                    responses = [
                        f"Ваши угрозы не пугают нас. Но мы надеемся на мирное решение.",
                        f"{faction} предпочитает дипломатию, но готова защищаться.",
                        f"Мы слышим ваши угрозы. Предлагаем обсудить это цивилизованно."
                    ]
            else:
                responses = [
                    f"Это серьезное заявление, правитель. Вы уверены в своих словах?",
                    f"Война принесет разрушение нам обоим. Есть ли альтернатива?",
                    f"{faction} надеется, что это лишь слова, а не намерения."
                ]

        return self.select_response_by_personality(responses, personality)

    def generate_trade_response(self, faction, relation_level, status, mood, personality, context):
        """Генерирует ответ на торговые предложения"""

        resources = context.get('resources', (0, 0, 0))

        if relation_level > 40:
            if mood == "positive":
                responses = [
                    f"{faction} заинтересована в торговле. Что конкретно вы предлагаете?",
                    f"Торговля может быть взаимовыгодной. Обсудим условия?",
                    f"Мы всегда открыты для разумных торговых предложений."
                ]
            else:
                responses = [
                    f"Торговля возможна, но условия должны быть справедливыми.",
                    f"{faction} рассмотрит ваше предложение. Какие у вас ресурсы?",
                    f"Что вы предлагаете и что хотите получить взамен?"
                ]

            # Добавляем информацию о ресурсах, если их мало
            if resources[0] < 1000 or resources[1] < 500:  # мало золота или кристаллов
                responses.append(f"Наши ресурсы ограничены, но мы готовы обсуждать.")
        else:
            responses = [
                f"Сначала нужно улучшить отношения для серьезной торговли.",
                f"Торговля требует доверия. Давайте наладим отношения сначала.",
                f"{faction} предпочитает знать партнеров лучше перед торговлей."
            ]

        return self.select_response_by_personality(responses, personality)

    def generate_peace_response(self, faction, relation_level, status, mood, personality, context):
        """Генерирует ответ на предложения мира"""

        if status == "война":
            if mood == "positive":
                responses = [
                    f"Мы устали от войны. Готовы обсудить условия мира.",
                    f"Мир возможен. Какие условия вы предлагаете?",
                    f"{faction} готова сложить оружие при разумных условиях."
                ]
            else:
                responses = [
                    f"Мир? После всего, что было? Нужны серьезные гарантии.",
                    f"Мы слышим ваше предложение. Что вы предлагаете взамен?",
                    f"Мир требует компенсаций за причиненные потери."
                ]
        else:
            responses = [
                f"Мы и так не воюем. О каком мире речь?",
                f"Мир уже есть между нами. Что вас беспокоит?",
                f"Нет конфликта - нет нужды в мире. Есть конкретные предложения?"
            ]

        return self.select_response_by_personality(responses, personality)

    def generate_threat_response(self, faction, relation_level, status, mood, personality, context):
        """Генерирует ответ на угрозы"""

        if relation_level > 60:
            responses = [
                f"Это недружественный тон, правитель. Давайте сохраним уважение.",
                f"Угрозы не помогут нашим отношениям. Предлагаю диалог.",
                f"{faction} ценит прямоту, но просит соблюдать дипломатический этикет."
            ]
        else:
            responses = [
                f"Ваши угрозы приняты к сведению. {faction} готова к любому развитию.",
                f"Мы не боимся угроз. Наши армии наготове.",
                f"Угрожать - легко. Действовать - сложно. Что вы выберете?"
            ]

        return self.select_response_by_personality(responses, personality)

    def generate_information_response(self, faction, relation_level, status, mood, personality, context, message):
        """Генерирует ответ на запрос информации"""

        # Извлекаем тип запрашиваемой информации
        if any(word in message for word in ['ресурс', 'золот', 'кристал', 'еда', 'пищ']):
            resources = context.get('resources', (0, 0, 0))
            if relation_level > 50:
                response = f"Наши ресурсы: золото - {resources[0]}, кристаллы - {resources[1]}, продовольствие - {resources[2]}."
            else:
                response = f"{faction} не разглашает информацию о ресурсах так открыто."

        elif any(word in message for word in ['арми', 'войск', 'солдат', 'защит']):
            army = context.get('army_count', 0)
            if relation_level > 60:
                response = f"Наша армия насчитывает примерно {army} воинов."
            else:
                response = f"Информация о нашей армии - военная тайна."

        elif any(word in message for word in ['город', 'поселен', 'территор']):
            cities = context.get('city_count', 0)
            if relation_level > 40:
                response = f"Под нашим контролем {cities} городов."
            else:
                response = f"Количество городов не разглашается."

        elif any(word in message for word in ['систем', 'идеолог', 'полит']):
            system = context.get('political_system', 'Неизвестно')
            response = f"{faction} следует пути {system}."

        else:
            if mood == "question":
                response = f"{faction} нуждается в уточнении. О какой именно информации идет речь?"
            else:
                response = f"Мы готовы предоставить информацию в рамках наших возможностей."

        return response

    def generate_request_response(self, faction, relation_level, status, mood, personality, context, message):
        """Генерирует ответ на просьбы"""

        if relation_level > 50:
            if "помощь" in message or "поддержк" in message:
                if mood == "positive":
                    responses = [
                        f"Мы рассмотрим возможность помощи. Опишите ситуацию подробнее.",
                        f"{faction} готова помочь союзнику. Что конкретно нужно?",
                        f"Как дружественной фракции, мы готовы оказать поддержку."
                    ]
                else:
                    responses = [
                        f"Помощь требует взаимности. Что вы предлагаете взамен?",
                        f"Мы поможем, но нужны гарантии.",
                        f"Помощь возможна при определенных условиях."
                    ]
            else:
                responses = [
                    f"Мы рассмотрим вашу просьбу. Дайте нам время.",
                    f"Ваше обращение принято. Ответим после обсуждения.",
                    f"{faction} обдумает вашу просьбу."
                ]
        else:
            responses = [
                f"Наши отношения не позволяют выполнять просьбы так легко.",
                f"Сначала нужно укрепить доверие между нами.",
                f"Просьбы требуют определенного уровня отношений."
            ]

        return self.select_response_by_personality(responses, personality)

    def generate_offer_response(self, faction, relation_level, status, mood, personality, context, message):
        """Генерирует ответ на предложения"""

        if relation_level > 40:
            if mood == "positive":
                responses = [
                    f"Интересное предложение. Расскажите подробнее.",
                    f"{faction} заинтересована. Какие детали?",
                    f"Мы готовы слушать. Что конкретно вы предлагаете?"
                ]
            else:
                responses = [
                    f"Предложение получено. Что вы ожидаете взамен?",
                    f"Мы рассмотрим ваше предложение, но нужны уточнения.",
                    f"Интересно. Каковы условия?"
                ]
        else:
            responses = [
                f"Предложение требует доверия, которого пока нет.",
                f"Давайте сначала улучшим отношения, а потом обсудим предложения.",
                f"Слишком рано для серьезных предложений."
            ]

        return self.select_response_by_personality(responses, personality)

    # Быстрые действия
    def request_report(self, instance):
        """Запрос отчета"""
        if hasattr(self, 'selected_faction') and self.selected_faction:
            self.message_input.text = "Прошу предоставить отчет о текущей ситуации в ваших землях."
            self.send_diplomatic_message(None)

    def propose_trade_quick(self, instance):
        """Быстрое предложение торговли"""
        if hasattr(self, 'selected_faction') and self.selected_faction:
            self.message_input.text = "Предлагаю обсудить условия торгового соглашения."
            self.send_diplomatic_message(None)

    def propose_peace(self, instance):
        """Быстрое предложение мира"""
        if hasattr(self, 'selected_faction') and self.selected_faction:
            self.message_input.text = "Предлагаю прекратить конфликт и заключить мирный договор."
            self.send_diplomatic_message(None)

    def send_threat(self, instance):
        """Быстрая угроза"""
        if hasattr(self, 'selected_faction') and self.selected_faction:
            self.message_input.text = "Если вы не прекратите свои действия, мы будем вынуждены объявить войну!"
            self.send_diplomatic_message(None)


    def load_diplomatic_factions(self):
        """Загружает список фракций для дипломатии"""
        self.factions_container.clear_widgets()

        # Все фракции кроме текущей и мятежников
        all_factions = ["Север", "Эльфы", "Адепты", "Вампиры", "Элины"]
        current_faction_en = translation_dict.get(self.faction, self.faction)

        for faction in all_factions:
            if faction != self.faction:
                # Получаем текущие отношения
                relations = self.load_combined_relations()
                relation_data = relations.get(faction, {"relation_level": 0, "status": "нейтралитет"})
                relation_level = relation_data["relation_level"]
                status = relation_data["status"]

                # Создаем кнопку фракции
                btn_color = self.get_relation_color(relation_level)
                btn = Button(
                    text=f"{faction}\n[{status}]",
                    size_hint=(1, None),
                    height=dp(70),
                    background_color=btn_color,
                    background_normal='',
                    color=(1, 1, 1, 1),
                    font_size='14sp',
                    bold=True,
                    halign='center'
                )

                # Привязываем выбор фракции
                btn.bind(on_press=lambda instance, f=faction: self.select_faction_for_negotiation(f))

                # Добавляем иконку (если есть)
                try:
                    icon_path = f"files/pict/factions/{translation_dict.get(faction, faction.lower())}.png"
                    if os.path.exists(icon_path):
                        btn_layout = BoxLayout(orientation='horizontal', spacing=dp(5))
                        icon = Image(
                            source=icon_path,
                            size_hint=(None, None),
                            size=(dp(30), dp(30)),
                            allow_stretch=True
                        )
                        btn_layout.add_widget(icon)
                        btn_layout.add_widget(btn)
                        self.factions_container.add_widget(btn_layout)
                    else:
                        self.factions_container.add_widget(btn)
                except:
                    self.factions_container.add_widget(btn)

    def select_faction_for_negotiation(self, faction):
        """Выбирает фракцию для переговоров"""
        self.selected_faction = faction

        # Обновляем заголовок
        self.negotiation_title.text = f"Переговоры с {faction}"

        # Обновляем иконку
        icon_path = f"files/pict/factions/{translation_dict.get(faction, faction.lower())}.png"
        if os.path.exists(icon_path):
            self.negotiation_faction_icon.source = icon_path

        # Получаем текущие отношения
        relations = self.load_combined_relations()
        relation_data = relations.get(faction, {"relation_level": 0, "status": "нейтралитет"})

        # Обновляем статус отношений
        rel_color = self.get_relation_color(relation_data["relation_level"])
        self.relation_status_label.text = f"Отношения: {relation_data['relation_level']}/100"
        self.relation_status_label.color = rel_color

        # Очищаем предыдущие переговоры
        self.diplo_container.clear_widgets()

        # Добавляем историю переговоров (здесь можно загрузить из БД)
        self.add_diplomatic_message(
            f"Начало переговоров с фракцией {faction}. "
            f"Текущий статус: {relation_data['status']}. "
            f"Уровень отношений: {relation_data['relation_level']}/100.",
            is_system=True
        )

        # Активируем кнопки дипломатических действий
        self.update_diplomatic_actions(faction, relation_data)

        # Загружаем историю переговоров из БД
        self.load_negotiation_history(faction)

    def init_diplomatic_actions(self):
        """Инициализирует кнопки дипломатических действий"""
        self.actions_grid.clear_widgets()

        # Кнопки изначально неактивны
        actions = [
            ("🤝", "Предложить союз", (0.2, 0.6, 0.3, 0.5), self.propose_alliance),
            ("⚔️", "Объявить войну", (0.8, 0.2, 0.2, 0.5), self.declare_war),
            ("📜", "Торговый договор", (0.3, 0.5, 0.7, 0.5), self.propose_trade),
            ("🕊️", "Перемирие", (0.5, 0.5, 0.5, 0.5), self.propose_ceasefire),
            ("💰", "Дать дань", (0.8, 0.6, 0.2, 0.5), self.offer_tribute),
            ("🔍", "Разведка", (0.4, 0.3, 0.6, 0.5), self.request_intel)
        ]

        for icon, text, color, callback in actions:
            btn = Button(
                text=f"{icon}\n{text}",
                size_hint=(1, 1),
                background_color=color,
                background_normal='',
                color=(1, 1, 1, 1),
                font_size='12sp',
                disabled=True
            )
            btn.bind(on_press=lambda instance, cb=callback: cb())
            self.actions_grid.add_widget(btn)

    def update_diplomatic_actions(self, faction, relation_data):
        """Обновляет доступность дипломатических действий в зависимости от отношений"""
        try:
            relation_level = int(relation_data["relation_level"])
        except (ValueError, TypeError, KeyError):
            relation_level = 50

        status = relation_data.get("status", "нейтралитет")

        for i, btn in enumerate(self.actions_grid.children):
            # Включаем/выключаем кнопки в зависимости от ситуации
            if status == "война":
                # Во время войны доступны только перемирие
                btn.disabled = (i != 3)  # только "Перемирие" активно
                btn.background_color = btn.background_color[:3] + (1.0 if not btn.disabled else 0.3)
            elif status == "союз":
                # В союзе нельзя объявлять войну
                btn.disabled = (i == 1)  # "Объявить войну" неактивна
                btn.background_color = btn.background_color[:3] + (1.0 if not btn.disabled else 0.3)
            elif relation_level < 30:
                # Плохие отношения - ограниченные возможности
                btn.disabled = (i in [0, 2])  # союз и торговля неактивны
                btn.background_color = btn.background_color[:3] + (1.0 if not btn.disabled else 0.3)
            else:
                # Нормальные отношения - все доступно
                btn.disabled = False
                btn.background_color = btn.background_color[:3] + (1.0,)

    def add_diplomatic_message(self, text, is_player=False, is_system=False, faction=None):
        """Добавляет сообщение в дипломатический чат"""
        message_box = BoxLayout(
            orientation='vertical',
            size_hint=(1, None),
            spacing=dp(2)
        )

        # Заголовок сообщения
        if is_system:
            sender = "📢 Система"
            color = (0.7, 0.7, 0.3, 1)
        elif is_player:
            sender = f"👑 {self.faction}"
            color = (0.3, 0.7, 0.3, 1)
        else:
            sender = f"🏛️ {faction or 'Другая фракция'}"
            color = (0.3, 0.5, 0.8, 1)

        timestamp = datetime.now().strftime("%H:%M")
        header = Label(
            text=f"{sender} • {timestamp}",
            font_size='11sp',
            color=(0.7, 0.7, 0.7, 1),
            size_hint=(1, None),
            height=dp(18),
            halign='left'
        )

        # Текст сообщения
        message = Label(
            text=text,
            font_size='14sp',
            color=color,
            size_hint=(1, None),
            halign='left',
            valign='top'
        )
        message.bind(
            width=lambda *x: message.setter('text_size')(message, (message.width - dp(20), None)),
            texture_size=lambda *x: message.setter('height')(message, message.texture_size[1] + dp(10))
        )

        # Контейнер с фоном
        message_container = BoxLayout(
            orientation='vertical',
            size_hint=(0.8 if is_player else 0.7, None),
            size_hint_x=None,
            padding=[dp(12), dp(8)],
            pos_hint={'right': 1} if is_player else {'x': 0}
        )

        # Фон сообщения
        with message_container.canvas.before:
            if is_system:
                Color(0.2, 0.2, 0.3, 0.9)
            elif is_player:
                Color(0.2, 0.4, 0.2, 0.8)
            else:
                Color(0.2, 0.3, 0.5, 0.8)
            RoundedRectangle(
                pos=message_container.pos,
                size=message_container.size,
                radius=[dp(10), dp(10), dp(10), dp(10)]
            )

        message_box.add_widget(header)
        message_box.add_widget(message)
        message_container.add_widget(message_box)

        # Добавляем в контейнер чата
        self.diplo_container.add_widget(message_container)

        # Прокручиваем вниз
        Clock.schedule_once(lambda dt: self.scroll_diplo_to_bottom(), 0.1)

    def send_diplomatic_proposal(self, instance):
        """Отправляет дипломатическое предложение"""
        message = self.diplo_input.text.strip()
        if not message or not hasattr(self, 'selected_faction'):
            return

        # Добавляем сообщение игрока
        self.add_diplomatic_message(message, is_player=True)
        self.diplo_input.text = ""

        # Сохраняем в историю переговоров
        self.save_negotiation_message(self.selected_faction, message, is_player=True)

        # Генерируем ответ ИИ (имитация)
        Clock.schedule_once(
            lambda dt: self.generate_ai_diplomatic_response(message, self.selected_faction),
            2.0
        )

    def generate_ai_diplomatic_response(self, player_message, target_faction):
        """Генерирует дипломатический ответ от ИИ фракции"""
        # Получаем текущие отношения
        relations = self.load_combined_relations()
        relation_data = relations.get(target_faction, {"relation_level": 50, "status": "нейтралитет"})

        # Простой ИИ для ответа (можно значительно расширить)
        if "союз" in player_message.lower():
            response = f"{target_faction} рассматривает ваше предложение о союзе. Это может занять время."
        elif "война" in player_message.lower():
            response = f"{target_faction} отвергает ваши угрозы! Мы готовы к бою!"
        elif "торгов" in player_message.lower():
            response = f"{target_faction} заинтересована в торговых отношениях. Какие условия вы предлагаете?"
        else:
            response = f"{target_faction} получила ваше сообщение. Мы дадим ответ в ближайшее время."

        # Добавляем ответ ИИ
        self.add_diplomatic_message(response, is_player=False, faction=target_faction)

        # Сохраняем в историю
        self.save_negotiation_message(target_faction, response, is_player=False)

    def propose_alliance(self):
        """Предложить союз"""
        if hasattr(self, 'selected_faction'):
            self.add_diplomatic_message(
                f"Вы предлагаете военный союз фракции {self.selected_faction}.",
                is_player=True
            )
            self.save_negotiation_message(
                self.selected_faction,
                "Предложение военного союза",
                is_player=True
            )

    def declare_war(self):
        """Объявить войну"""
        if hasattr(self, 'selected_faction'):
            self.add_diplomatic_message(
                f"Вы объявляете войну фракции {self.selected_faction}!",
                is_player=True
            )
            self.save_negotiation_message(
                self.selected_faction,
                "Объявление войны",
                is_player=True
            )
            # Здесь можно добавить логику изменения статуса в БД

    def propose_trade(self):
        """Предложить торговый договор"""
        if hasattr(self, 'selected_faction'):
            self.add_diplomatic_message(
                f"Вы предлагаете торговый договор фракции {self.selected_faction}.",
                is_player=True
            )
            self.save_negotiation_message(
                self.selected_faction,
                "Предложение торгового договора",
                is_player=True
            )

    def propose_ceasefire(self):
        """Предложить перемирие"""
        if hasattr(self, 'selected_faction'):
            self.add_diplomatic_message(
                f"Вы предлагаете перемирие фракции {self.selected_faction}.",
                is_player=True
            )
            self.save_negotiation_message(
                self.selected_faction,
                "Предложение перемирия",
                is_player=True
            )

    def offer_tribute(self):
        """Предложить дань"""
        if hasattr(self, 'selected_faction'):
            self.add_diplomatic_message(
                f"Вы предлагаете дань фракции {self.selected_faction} в обмен на мир.",
                is_player=True
            )
            self.save_negotiation_message(
                self.selected_faction,
                "Предложение дани",
                is_player=True
            )

    def request_intel(self):
        """Запросить разведданные"""
        if hasattr(self, 'selected_faction'):
            self.add_diplomatic_message(
                f"Вы запрашиваете разведданные у фракции {self.selected_faction}.",
                is_player=True
            )
            self.save_negotiation_message(
                self.selected_faction,
                "Запрос разведданных",
                is_player=True
            )

    def create_quick_treaties_panel(self):
        """Создает панель быстрых договоров"""
        panel = BoxLayout(
            orientation='horizontal',
            size_hint=(1, None),
            height=dp(50),
            spacing=dp(5),
            padding=[dp(10), dp(5)],
            pos_hint={'bottom': 1}
        )

        treaties = [
            ("Ненападение", (0.4, 0.4, 0.6, 1)),
            ("Открытые границы", (0.3, 0.5, 0.4, 1)),
            ("Военная помощь", (0.6, 0.3, 0.3, 1)),
            ("Научный обмен", (0.3, 0.4, 0.6, 1))
        ]

        for text, color in treaties:
            btn = Button(
                text=text,
                size_hint=(1, 1),
                background_color=color,
                background_normal='',
                font_size='12sp',
                on_press=lambda instance, t=text: self.propose_quick_treaty(t)
            )
            panel.add_widget(btn)

        return panel

    def propose_quick_treaty(self, treaty_type):
        """Предлагает быстрый договор"""
        if hasattr(self, 'selected_faction'):
            self.add_diplomatic_message(
                f"Вы предлагаете договор '{treaty_type}' фракции {self.selected_faction}.",
                is_player=True
            )
            self.save_negotiation_message(
                self.selected_faction,
                f"Предложение договора: {treaty_type}",
                is_player=True
            )

    def load_negotiation_history(self, faction):
        """Загружает историю переговоров с фракцией из БД"""
        try:
            cursor = self.db_connection.cursor()
            cursor.execute('''
                SELECT message, is_player, timestamp 
                FROM negotiation_history 
                WHERE faction1 = ? AND faction2 = ? 
                ORDER BY timestamp DESC 
                LIMIT 10
            ''', (self.faction, faction))

            history = cursor.fetchall()

            # Добавляем исторические сообщения (в обратном порядке)
            for message, is_player, timestamp in reversed(history):
                self.add_diplomatic_message(
                    message,
                    is_player=bool(is_player),
                    is_system=False,
                    faction=faction if not bool(is_player) else None
                )

        except Exception as e:
            print(f"Ошибка при загрузке истории переговоров: {e}")

    def save_negotiation_message(self, target_faction, message, is_player=True):
        """Сохраняет сообщение переговоров в БД"""
        try:
            cursor = self.db_connection.cursor()
            cursor.execute('''
                INSERT INTO negotiation_history 
                (faction1, faction2, message, is_player, timestamp) 
                VALUES (?, ?, ?, ?, datetime('now'))
            ''', (self.faction, target_faction, message, 1 if is_player else 0))

            self.db_connection.commit()
        except Exception as e:
            print(f"Ошибка при сохранении сообщения переговоров: {e}")

    def scroll_diplo_to_bottom(self):
        """Прокручивает дипломатический чат вниз"""
        if hasattr(self, 'diplo_scroll') and self.diplo_scroll:
            self.diplo_scroll.scroll_y = 0

    def show_diplomacy_settings(self, instance):
        """Показывает настройки дипломатии"""
        content = BoxLayout(orientation='vertical', spacing=dp(10), padding=dp(20))

        title = Label(
            text="Настройки дипломатии",
            font_size='20sp',
            bold=True,
            color=(1, 1, 1, 1)
        )

        # Настройки можно добавить по необходимости
        auto_response = CheckBox(
            active=True,
            size_hint=(None, None),
            size=(dp(30), dp(30))
        )

        auto_response_label = Label(
            text="Автоответ на предложения",
            color=(1, 1, 1, 1),
            size_hint=(1, None),
            height=dp(30)
        )

        close_button = Button(
            text="Закрыть",
            size_hint=(1, None),
            height=dp(40),
            background_color=(0.3, 0.5, 0.8, 1),
            on_press=lambda x: self.return_to_main_tab()
        )

        content.add_widget(title)
        content.add_widget(auto_response_label)
        content.add_widget(auto_response)
        content.add_widget(close_button)

        settings_popup = Popup(
            title="",
            content=content,
            size_hint=(0.5, 0.4),
            background=''
        )
        settings_popup.open()

    def create_quick_questions_panel(self):
        """Создает панель быстрых вопросов"""
        panel = BoxLayout(
            orientation='horizontal',
            size_hint=(1, None),
            height=dp(50),
            spacing=dp(5),
            padding=[dp(10), 0],
            pos_hint={'top': 0.15}
        )

        questions = [
            "Совет по экономике",
            "Военная стратегия",
            "Дипломатия",
            "Угрозы"
        ]

        for question in questions:
            btn = Button(
                text=question,
                size_hint=(1, 1),
                background_color=(0.3, 0.3, 0.5, 1),
                background_normal='',
                font_size='12sp',
                on_press=lambda instance, q=question: self.ask_quick_question(q)
            )
            panel.add_widget(btn)

        return panel


    def scroll_chat_to_bottom(self):
        """Прокручивает чат вниз"""
        if self.chat_scroll:
            self.chat_scroll.scroll_y = 0


    def ask_quick_question(self, question):
        """Задает быстрый вопрос из панели"""
        self.chat_input.text = question
        self.send_ai_message(None)


    def get_game_context(self):
        """Получает контекст игры для ИИ"""
        try:
            cursor = self.db_connection.cursor()

            # Получаем ресурсы
            cursor.execute("SELECT * FROM resources WHERE faction = ?", (self.faction,))
            resources = cursor.fetchone()

            # Получаем города
            cursor.execute("SELECT COUNT(*) FROM cities WHERE faction = ?", (self.faction,))
            city_count = cursor.fetchone()[0]

            # Получаем армию
            cursor.execute("""
                SELECT SUM(unit_count) 
                FROM garrisons g 
                JOIN units u ON g.unit_name = u.unit_name 
                WHERE u.faction = ?
            """, (self.faction,))
            army_count = cursor.fetchone()[0] or 0

            # Получаем отношения
            cursor.execute("SELECT relationship FROM relations WHERE faction1 = ?", (self.faction,))
            relations = cursor.fetchall()

            return {
                'faction': self.faction,
                'resources': resources,
                'city_count': city_count,
                'army_count': army_count,
                'relations': relations
            }

        except Exception as e:
            print(f"Ошибка при получении контекста игры: {e}")
            return {'faction': self.faction}

    def generate_ai_response_based_on_context(self, user_message, context):
        """Генерирует ответ ИИ на основе контекста"""
        user_message_lower = user_message.lower()

        # Анализ ключевых слов в сообщении
        if any(word in user_message_lower for word in ['эконом', 'доход', 'деньги', 'ресурс', 'кроны']):
            return self.generate_economy_advice(context)

        elif any(word in user_message_lower for word in ['войн', 'арми', 'солдат', 'защит', 'атака']):
            return self.generate_military_advice(context)

        elif any(word in user_message_lower for word in ['дипломат', 'союз', 'враг', 'отношен']):
            return self.generate_diplomacy_advice(context)

        elif any(word in user_message_lower for word in ['город', 'строит', 'развит']):
            return self.generate_development_advice(context)

        else:
            return self.generate_general_advice(context)

    def generate_economy_advice(self, context):
        """Генерирует экономический совет"""
        advice = "🏦 **Экономические рекомендации:**\n\n"

        if context.get('resources'):
            advice += "1. Увеличивайте производство кристаллов\n"
            advice += "2. Стройте новые фабрики\n"
            advice += "3. Управляйте налогами разумно\n"
            advice += "4. Инвестируйте в развитие городов\n"

        advice += f"\nДля фракции {self.faction} особенно важно балансировать между производством и потреблением."
        return advice

    def generate_military_advice(self, context):
        """Генерирует военный совет"""
        army_count = context.get('army_count', 0)
        advice = f"⚔️ **Военные рекомендации:**\n\n"
        advice += f"Текущая численность армии: {army_count}\n\n"

        if army_count < 100:
            advice += "1. Срочно наращивайте армию\n"
            advice += "2. Нанимайте юнитов 1-2 классов\n"
            advice += "3. Укрепляйте оборону городов\n"
        elif army_count < 500:
            advice += "1. Улучшайте существующие войска\n"
            advice += "2. Нанимайте героев (3-4 класс)\n"
            advice += "3. Исследуйте новые технологии\n"
        else:
            advice += "1. Планируйте стратегические кампании\n"
            advice += "2. Используйте комбинированные отряды\n"
            advice += "3. Создавайте резервные армии\n"

        return advice

    def generate_diplomacy_advice(self, context):
        """Генерирует дипломатический совет"""
        advice = "🤝 **Дипломатические рекомендации:**\n\n"

        relations = context.get('relations', [])
        if relations:
            advice += "Текущие отношения:\n"
            for rel in relations[:3]:  # Показываем только первые 3
                advice += f"• Уровень: {rel[0]}/100\n"

        advice += "\n1. Заключайте торговые договоры\n"
        advice += "2. Обменивайтесь культурными бонусами\n"
        advice += "3. Избегайте войн на два фронта\n"
        advice += "4. Используйте шпионаж для разведки\n"

        return advice

    def generate_development_advice(self, context):
        """Генерирует совет по развитию"""
        city_count = context.get('city_count', 0)
        advice = f"🏙️ **Развитие городов ({city_count} шт.):**\n\n"

        if city_count < 3:
            advice += "1. Сосредоточьтесь на захвате новых городов\n"
            advice += "2. Укрепляйте столицу\n"
            advice += "3. Развивайте инфраструктуру\n"
        elif city_count < 7:
            advice += "1. Улучшайте существующие города\n"
            advice += "2. Создавайте специализированные города\n"
            advice += "3. Инвестируйте в науку и культуру\n"
        else:
            advice += "1. Создавайте мегаполисы\n"
            advice += "2. Оптимизируйте логистику\n"
            advice += "3. Развивайте уникальные особенности городов\n"

        return advice

    def generate_general_advice(self, context):
        """Генерирует общий совет"""
        advice = "🎯 **Общие рекомендации:**\n\n"
        advice += "1. Балансируйте между развитием и экспансией\n"
        advice += "2. Следите за сезонными эффектами\n"
        advice += "3. Управляйте дворянами (советниками)\n"
        advice += "4. Планируйте долгосрочную стратегию\n"
        advice += f"\nКак правитель {self.faction}, вы должны быть гибкими и адаптироваться к изменяющимся условиям."

        return advice

    def clear_chat_history(self):
        """Очищает историю чата"""
        if hasattr(self, 'chat_container'):
            self.chat_container.clear_widgets()
            self.add_welcome_message()

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
            query = "SELECT faction, system FROM political_systems WHERE faction != 'Мятежники'"
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
                WHERE faction1 = ? AND faction2 != 'Мятежники'
            ''', (self.faction,))
            rows = self.cursor.fetchall()

            # Преобразуем результат в словарь
            relations = {faction2: relationship for faction2, relationship in rows}
            return relations

        except sqlite3.Error as e:
            print(f"Ошибка при загрузке отношений из таблицы relations: {e}")
            return {}

    def load_diplomacies(self):
        """
        Загружает дипломатические соглашения из базы данных для текущей фракции (self.faction).
        Возвращает словарь, где ключи — названия фракций, а значения — статусы отношений.
        """
        diplomacies_data = {}
        try:
            cursor = self.db_connection.cursor()
            # Добавляем условие WHERE faction1 = ? и исключаем Мятежников
            query = "SELECT faction2, relationship FROM diplomacies WHERE faction1 = ? AND faction2 != 'Мятежники'"
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

    def load_relations_for_target(self, target_faction):
        """
        Загружает отношения для указанной целевой фракции.
        Возвращает словарь, где ключи — названия фракций, а значения — уровни отношений.
        """
        try:
            self.cursor.execute('''
                SELECT faction2, relationship
                FROM relations
                WHERE faction1 = ? AND faction2 != 'Мятежники'
            ''', (target_faction,))
            rows = self.cursor.fetchall()
            return {faction2: relationship for faction2, relationship in rows}
        except sqlite3.Error as e:
            print(f"Ошибка при загрузке отношений для фракции {target_faction}: {e}")
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

            if self.game_screen:
                print("Уведомление GameScreen об изменении идеологии...")
                # Вызываем метод обновления в GameScreen
                self.game_screen.refresh_player_ideology()  # <-- Вызов метода из GameScreen
            else:
                print("Предупреждение: Ссылка на GameScreen не передана, обновление иконок невозможно.")
            self.show_political_systems()

        except sqlite3.Error as e:
            print(f"Ошибка при обновлении политической системы: {e}")

    def close_window(self, instance):
        """Закрытие окна"""
        print("Метод close_window вызван.")  # Отладочный вывод
        if hasattr(self, 'popup') and self.popup:
            self.popup.dismiss()
        else:
            print("Ошибка: Попап не найден.")

    def calculate_coefficient(self, relation_level):
        """Рассчитывает коэффициент на основе уровня отношений"""
        try:
            rel = int(relation_level)  # Преобразуем в int
        except (ValueError, TypeError):
            rel = 50  # значение по умолчанию

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

        # --- Кнопки выбор идеологии ---
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

        # --- Определяем функции-обработчики для задержки возврата ---
        def schedule_return_to_main(dt):
            """Функция, которая вызывает возврат на главное меню после задержки"""
            self.return_to_main_tab()

        # Привязываем кнопки к выполнению двух действий:
        # 1. Обновление идеологии (сразу)
        # 2. Планирование возврата (через 2 секунды)
        capitalism_button.bind(
            on_release=lambda x: [
                self.update_political_system("Смирение"), # Выполняется сразу
                Clock.schedule_once(schedule_return_to_main, 2.0) # Планируется на 2 сек
            ]
        )
        communism_button.bind(
            on_release=lambda x: [
                self.update_political_system("Борьба"), # Выполняется сразу
                Clock.schedule_once(schedule_return_to_main, 2.0) # Планируется на 2 сек
            ]
        )

        # Добавляем рамки вокруг кнопок
        for btn in (capitalism_button, communism_button):
            with btn.canvas.after:
                Color(0.1, 0.1, 0.1, 1)
                btn.border_line = Line(
                    rectangle=(btn.x, btn.y, btn.width, btn.height), width=1.5)
            btn.bind(
                size=lambda inst, val: setattr(inst.border_line, "rectangle", (inst.x, inst.y, inst.width, inst.height))
            )
            btn.bind(
                pos=lambda inst, val: setattr(inst.border_line, "rectangle", (inst.x, inst.y, inst.width, inst.height))
            )

        system_layout.add_widget(capitalism_button)
        system_layout.add_widget(communism_button)
        # --- Изменения заканчиваются здесь ---

        content.add_widget(system_layout)

        # Обновляем содержимое popup
        self.popup.content = content

    def show_relations(self, instance=None):
        """Отображает окно с таблицей отношений."""
        self.manage_relations()
        combined_relations = self.load_combined_relations()

        if not combined_relations:
            print(f"Нет данных об отношениях для фракции {self.faction}.")
            return

        # === Основное содержимое ===
        content = BoxLayout(orientation='vertical', spacing=dp(8), padding=dp(10))

        # Таблица
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

        # === Кнопка Назад ===
        back_button = Button(
            text="Назад",
            background_color=(0.227, 0.525, 0.835, 1),
            font_size='16sp',
            size_hint=(1, None),
            height=calculate_font_size() * 0.9,
            color=(1, 1, 1, 1),
            background_normal='',
            background_down='',
            bold=True
        )

        # Добавляем рамку вокруг кнопки Назад
        with back_button.canvas.after:
            Color(0.1, 0.1, 0.1, 1)
            back_button.border_line = Line(
                rectangle=(back_button.x, back_button.y, back_button.width, back_button.height), width=1.5)
        back_button.bind(
            size=lambda inst, val: setattr(inst.border_line, "rectangle", (inst.x, inst.y, inst.width, inst.height))
        )
        back_button.bind(
            pos=lambda inst, val: setattr(inst.border_line, "rectangle", (inst.x, inst.y, inst.width, inst.height))
        )

        # При нажатии — возвращаем исходный интерфейс
        back_button.bind(on_release=lambda x: self.return_to_main_tab())

        content.add_widget(back_button)
        self.popup.content = content

    def return_to_main_tab(self, *args):
        """Возвращает к главному интерфейсу (главная вкладка)."""
        self.popup.content = self.interface_window

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
        if value <= 0.1:
            return (0.8, 0.1, 0.1, 1)  # Красный
        elif 0.1 < value <= 0.4:
            return (1.0, 0.5, 0.0, 1)  # Оранжевый
        elif 0.4 < value <= 0.9:
            return (1.0, 0.8, 0.0, 1)  # Желтый
        elif 0.9 < value <= 1.5:
            return (0.2, 0.7, 0.3, 1)  # Зеленый
        elif 1.5 < value <= 2:
            return (0.0, 0.8, 0.8, 1)  # Голубой
        elif 2 < value <= 3.1:
            return (0.0, 0.6, 1.0, 1)  # Синий
        elif 3.1 < value <= 4:
            return (0.1, 0.3, 0.9, 1)  # Темно-синий
        else:
            return (1, 1, 1, 1)  # Белый

    def get_relation_color(self, value):
        """Возвращает цвет в зависимости от значения"""
        try:
            value = int(value)  # Преобразуем в int
        except (ValueError, TypeError):
            value = 50  # значение по умолчанию

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
