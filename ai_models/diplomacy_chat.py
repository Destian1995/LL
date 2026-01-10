# ai_models/diplomacy_chat.py
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.image import Image
from kivy.uix.textinput import TextInput
from kivy.uix.spinner import Spinner
from kivy.graphics import Color, Rectangle, RoundedRectangle
from kivy.core.window import Window
from kivy.metrics import dp
from kivy.clock import Clock
from datetime import datetime
import os
from .nlp_processor import NaturalLanguageProcessor
from .manipulation_strategy import ManipulationStrategy
from .translation import translation_dict

class EnhancedDiplomacyChat():
    """Улучшенная версия дипломатического чата с обработкой запросов"""

    def __init__(self, advisor_view, db_connection):
        self.advisor = advisor_view
        self.db_connection = db_connection
        self.faction = advisor_view.faction
        # Инициализируем NLP процессор
        self.nlp_processor = NaturalLanguageProcessor()

        # Инициализируем стратегию манипуляций
        self.manipulation_strategy = ManipulationStrategy()

        # Контекст переговоров
        self.negotiation_context = {}

        # Активные переговоры (resource_request, alliance_request, trade_request)
        self.active_negotiations = {}

        # История предложений в текущей сессии
        self.current_offers = {}

        # Ожидаемые ответы от ИИ

        # Ссылки на UI элементы
        self.chat_scroll = None
        self.chat_container = None
        self.message_input = None
        self.chat_status = None
        self.faction_spinner = None

    def open_diplomacy_window(self):
        """Открывает окно дипломатических переговоров"""
        diplomacy_window = BoxLayout(
            orientation='horizontal',
            size_hint=(1, 1),
            spacing=dp(10),
            padding=dp(10)
        )

        # Фон
        with diplomacy_window.canvas.before:
            Color(0.08, 0.08, 0.12, 0.95)
            Rectangle(pos=diplomacy_window.pos, size=diplomacy_window.size)

        # Левая часть - чат (75% ширины)
        chat_section = BoxLayout(
            orientation='vertical',
            size_hint=(0.75, 1),
            spacing=dp(10)
        )

        # Шапка
        header = self.create_chat_header()
        chat_section.add_widget(header)

        # Основная область чата
        main_area = self.create_chat_main_area()
        chat_section.add_widget(main_area)

        # Панель статуса
        status_panel = self.create_status_panel()
        chat_section.add_widget(status_panel)

        # Правая часть - информация об отношениях (25% ширины)
        info_section = self.create_relation_sidebar()

        # Добавляем обе секции
        diplomacy_window.add_widget(chat_section)
        diplomacy_window.add_widget(info_section)

        # Устанавливаем содержимое popup
        self.advisor.popup.content = diplomacy_window

        # Фокусируемся на поле ввода
        Clock.schedule_once(lambda dt: setattr(self.message_input, 'focus', True), 0.3)

    def create_chat_main_area(self):
        """Создает основную область чата"""
        main_area = BoxLayout(
            orientation='vertical',
            size_hint=(1, 0.85),
            spacing=dp(10),
            padding=[dp(15), dp(10)]
        )

        # Заголовок текущей переписки
        chat_header = BoxLayout(
            orientation='horizontal',
            size_hint=(1, None),
            height=dp(50),
            padding=[dp(10), 0]
        )

        self.current_faction_icon = Image(
            source='files/pict/question.png',
            size_hint=(None, None),
            size=(dp(40), dp(40)),
            allow_stretch=True
        )

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

        # Область чата (история переписки)
        chat_area = BoxLayout(
            orientation='vertical',
            size_hint=(1, 0.7)
        )

        self.chat_scroll = ScrollView(
            size_hint=(1, 1),
            bar_width=dp(8),
            bar_color=(0.5, 0.5, 0.5, 0.5),
            do_scroll_x=False,
            scroll_type=['bars', 'content']
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

        # Панель ввода
        input_panel = self.create_input_panel()
        chat_area.add_widget(input_panel)

        main_area.add_widget(chat_area)
        return main_area

    def create_input_panel(self):
        """Создает панель ввода сообщения"""
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
            padding=[dp(10), dp(10)],
            font_size='14sp'
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

        return input_panel

    def create_status_panel(self):
        """Создает панель статуса"""
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
        return status_panel

    def on_faction_selected(self, spinner, text):
        """Обработчик выбора фракции"""
        if text and text != 'Выберите фракцию':
            self.selected_faction = text
            self.load_chat_history()
            self.update_chat_header(text)
            self.update_relation_display(text)  # Добавляем обновление отображения
            self.load_trade_history(text)  # Загружаем историю сделок

    def load_trade_history(self, faction):
        """Загружает историю сделок с фракцией"""
        if not hasattr(self, 'trade_history_label'):
            return

        try:
            cursor = self.db_connection.cursor()
            cursor.execute('''
                SELECT initiator, initiator_type_resource, initiator_summ_resource,
                       target_type_resource, target_summ_resource, timestamp
                FROM trade_agreements
                WHERE (initiator = ? AND target_faction = ?)
                   OR (initiator = ? AND target_faction = ?)
                ORDER BY timestamp DESC
                LIMIT 10
            ''', (self.faction, faction, faction, self.faction))

            trades = cursor.fetchall()

            if trades:
                history_text = "Последние сделки:\n\n"
                for trade in trades:
                    initiator, give_type, give_amount, get_type, get_amount, timestamp = trade

                    if initiator == self.faction:
                        direction = "Вы → "
                    else:
                        direction = "← " + faction

                    history_text += (
                            f"{direction}\n"
                            f"Отдали: {give_amount} {give_type}\n"
                            f"Получили: {get_amount} {get_type}\n"
                            f"[size=10]{timestamp}[/size]\n"
                            + "-" * 30 + "\n"
                    )
            else:
                history_text = "Нет истории сделок"

            self.trade_history_label.text = history_text
            self.trade_history_label.markup = True

        except Exception as e:
            print(f"Ошибка загрузки истории сделок: {e}")
            self.trade_history_label.text = "Ошибка загрузки истории"

    def update_chat_header(self, faction):
        """Обновляет заголовок чата"""
        # Обновляем иконку
        icon_path = f"files/buildings/{translation_dict.get(faction, faction.lower())}.png"
        if os.path.exists(icon_path):
            self.current_faction_icon.source = icon_path
        else:
            self.current_faction_icon.source = 'files/pict/question.png'

        # Обновляем заголовок
        self.chat_title.text = f"Переписка с {faction}"

        # Обновляем статус отношений
        relations = self.advisor.relations_manager.load_combined_relations()
        relation_data = relations.get(faction, {"relation_level": 0, "status": "нейтралитет"})

        try:
            relation_level = int(relation_data["relation_level"])
        except (ValueError, TypeError, KeyError):
            relation_level = 0

        rel_color = self.get_relation_color(relation_level)
        self.relation_status.text = f"Отношения: {relation_level}/100 ({relation_data.get('status', 'нейтралитет')})"
        self.relation_status.color = rel_color

    def load_chat_history(self):
        """Загружает историю переписки"""
        if not hasattr(self, 'selected_faction') or not self.selected_faction:
            self.chat_status.text = "Выберите фракцию для загрузки переписки"
            return

        # Очищаем текущие сообщения
        self.chat_container.clear_widgets()

        # Добавляем системное сообщение
        self.add_chat_message_system(f"Начало переписки с {self.selected_faction}. Загрузка истории...")

        try:
            cursor = self.db_connection.cursor()
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
        # Создаем контейнер для сообщения
        message_box = BoxLayout(
            orientation='vertical',
            size_hint_y=None,
            spacing=dp(2)
        )

        # Выравнивание сообщений: игрок справа, ИИ слева
        if is_player:
            message_box.pos_hint = {'right': 1}
            bg_color = (0.2, 0.4, 0.6, 0.8)  # Синий фон для игрока
        else:
            message_box.pos_hint = {'x': 0}
            bg_color = (0.3, 0.3, 0.4, 0.8)  # Серый фон для ИИ

        # Заголовок сообщения
        header = BoxLayout(
            orientation='horizontal',
            size_hint=(1, None),
            height=dp(20)
        )

        sender_label = Label(
            text=f"{'Справка' if is_player else '🏛️'} {sender}",
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
        max_width = Window.width * 0.6
        message_label = Label(
            text=message,
            font_size='13sp',
            color=(1, 1, 1, 1) if is_player else (0.9, 0.9, 0.9, 1),
            size_hint=(None, None),
            width=max_width,
            halign='left',
            valign='top',
            text_size=(max_width - dp(20), None)
        )

        # Привязываем высоту к тексту
        message_label.bind(texture_size=lambda *x: message_label.setter('height')(
            message_label, message_label.texture_size[1] + dp(10)))

        # Фон сообщения
        message_container = BoxLayout(
            orientation='vertical',
            padding=[dp(10), dp(8)],
            size_hint=(None, None)
        )

        total_height = dp(20) + message_label.height + dp(8)
        message_container.size = (max_width, total_height)

        with message_container.canvas.before:
            Color(*bg_color)
            RoundedRectangle(
                pos=message_container.pos,
                size=message_container.size,
                radius=[dp(10), ]
            )

        # Добавляем элементы
        message_box.add_widget(header)
        message_box.add_widget(message_label)
        message_container.add_widget(message_box)

        # Добавляем в контейнер чата
        self.chat_container.add_widget(message_container)

        # Прокручиваем вниз
        Clock.schedule_once(lambda dt: self.scroll_chat_to_bottom(), 0.1)

    def add_chat_message_system(self, message):
        """Добавляет системное сообщение"""
        message_box = BoxLayout(
            orientation='vertical',
            size_hint=(0.9, None),
            spacing=dp(2),
            pos_hint={'center_x': 0.5}
        )

        message_label = Label(
            text=f"📢 {message}",
            font_size='12sp',
            color=(0.8, 0.8, 0.4, 1),
            size_hint=(1, None),
            halign='center',
            valign='middle',
            text_size=(Window.width * 0.8, None)
        )

        message_label.bind(
            texture_size=lambda *x: message_label.setter('height')(
                message_label, message_label.texture_size[1] + dp(5))
        )

        message_box.add_widget(message_label)
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

        # Генерируем ответ ИИ
        response = self.generate_diplomatic_response(message, self.selected_faction)

        if response:
            ai_time = datetime.now().strftime("%d.%m %H:%M")

            # Добавляем сообщение ИИ в чат
            self.add_chat_message(
                message=response,
                sender=self.selected_faction,
                timestamp=ai_time,
                is_player=False
            )

            # Сохраняем ответ ИИ в БД
            self.save_negotiation_message(
                self.selected_faction,
                response,
                is_player=False
            )

    def generate_diplomatic_response(self, player_message, target_faction):
        """Генерирует ответ ИИ на сообщение игрока с учетом контекста переговоров"""

        print(f"DEBUG: Получено сообщение: '{player_message}' от игрока")  # Отладка

        # Загружаем данные об отношениях
        relations = self.advisor.relations_manager.load_combined_relations()
        relation_data = relations.get(target_faction, {"relation_level": 50, "status": "нейтралитет"})
        relation_level = int(relation_data.get("relation_level", 50))
        coefficient = self.calculate_coefficient(relation_level)

        # Если отношения слишком плохие для сделок
        if coefficient == 0 and self._is_resource_request(player_message):
            return (f"При нашем текущем уровне отношений ({relation_level}/100) "
                    f"я не готов обсуждать сделки.")
        # Получаем контекст переговоров для этой фракции
        context = self.negotiation_context.get(target_faction, {})
        print(f"DEBUG: Контекст для {target_faction}: {context}")  # Отладка

        # 1. ПЕРВОЕ - проверяем стадии торговли/ресурсов
        if context.get("stage") in (
                "ask_resource_type", "ask_resource_amount", "ask_player_offer", "counter_offer", "evaluate"):
            print(f"DEBUG: Обработка стадии диалога: {context.get('stage')}")  # Отладка
            forced = self._handle_forced_dialog(player_message, target_faction, context)
            if forced:
                return forced

        # 2. Проверяем на простые запросы ресурсов ПЕРЕД вызовом NLP
        is_resource_req = self._is_resource_request(player_message)
        print(f"DEBUG: _is_resource_request вернул: {is_resource_req}")  # Отладка

        if is_resource_req:
            # Инициируем диалог о ресурсах
            self.negotiation_context[target_faction] = {
                "stage": "ask_resource_type",
                "counter_offers": 0
            }
            return "Какой ресурс тебе нужен: Кроны, Кристаллы или Рабочие?"

        # 3. Определяем intent через NLP
        intent = self.nlp_processor.process_message(player_message, context)
        print(f"DEBUG: Определен intent: {intent.name} с уверенностью {intent.confidence}")  # Отладка

        # 4. Обрабатываем основные интенты
        # Обработка интентов для торговли
        if intent.name in ("demand_resources", "trade_propose"):
            print(f"DEBUG: Обработка intent торговли: {intent.name}")  # Отладка
            # Инициируем диалог о торговле
            self.negotiation_context[target_faction] = {
                "stage": "ask_resource_type",
                "counter_offers": 0
            }
            return "Какие ресурсы тебе нужны?"

        # Простые интенты для обычного диалога
        simple_responses = {
            "greeting": ["Привет! Рад тебя видеть.", "Здравствуйте! Как ваши дела?", "Приветствую!"],
            "farewell": ["До свидания!", "Пока! Будем ждать ваших предложений.", "Всего хорошего!"],
            "ask_status": [
                f"Наши отношения с тобой на уровне {relation_data.get('relation_level', 50)} ({relation_data.get('status', 'нейтралитет')}).",
                f"Я отношусь к тебе {relation_data.get('status', 'нейтралитет')}."
            ],
            "thanks": ["Пожалуйста!", "Рад помочь!", "Не за что!"],
            "insult": ["Я не буду отвечать на оскорбления.", "Давай вести переговоры конструктивно."],
            "threat": ["Угрозы не помогут в переговорах.", "Я не реагирую на угрозы."]
        }

        if intent.name in simple_responses:
            print(f"DEBUG: Обработка простого intent: {intent.name}")  # Отладка
            import random
            return random.choice(simple_responses[intent.name])

        # 5. ФОЛБЭК - если intent неизвестен или уверенность низкая
        print(f"DEBUG: Intent не распознан или уверенность низкая")  # Отладка

        # Проверяем вручную на ключевые слова БОЛЕЕ АГРЕССИВНО
        message_lower = player_message.lower()
        print(f"DEBUG: message_lower: '{message_lower}'")  # Отладка

        # РАСШИРЕННЫЙ список ключевых слов для запросов ресурсов
        request_patterns = [
            'нужн', 'дай', 'хочу', 'получит', 'можно', 'прошу',
            'треб', 'жела', 'хотел', 'хотела', 'хотелось',
            'необходим', 'требуется', 'требуются'
        ]

        # Проверяем, есть ли хоть одно слово запроса
        has_request_word = any(pattern in message_lower for pattern in request_patterns)
        print(f"DEBUG: has_request_word: {has_request_word}")  # Отладка

        # Проверяем наличие ресурсов
        resource_mentions = self._extract_resource_mentions(player_message)
        print(f"DEBUG: resource_mentions: {resource_mentions}")  # Отладка

        if has_request_word and resource_mentions:
            print(f"DEBUG: Найден запрос ресурсов вручную!")  # Отладка
            resource_type = resource_mentions[0]

            amount = self._extract_number(player_message)
            print(f"DEBUG: Извлеченное количество: {amount}")  # Отладка

            if amount:
                self.negotiation_context[target_faction] = {
                    "stage": "ask_player_offer",
                    "resource": resource_type,
                    "amount": amount,
                    "counter_offers": 0
                }
                return f"Хочешь {amount} {resource_type}? Что предлагаешь взамен?"
            else:
                self.negotiation_context[target_faction] = {
                    "stage": "ask_resource_amount",
                    "resource": resource_type,
                    "counter_offers": 0
                }
                return f"Сколько {resource_type} тебе нужно?"

        # 6. Проверяем на простые приветствия/прощания вручную
        greeting_words = ['привет', 'здравствуй', 'здравствуйте', 'добрый', 'хай', 'здаров', 'ку', 'hello', 'hi']
        farewell_words = ['пока', 'до свидания', 'прощай', 'удачи', 'всего', 'bye', 'goodbye']

        if any(word in message_lower for word in greeting_words):
            import random
            greetings = ["Привет! Рад тебя видеть.", "Здравствуйте! Как ваши дела?", "Приветствую!"]
            return random.choice(greetings)

        if any(word in message_lower for word in farewell_words):
            import random
            farewells = ["До свидания!", "Пока! Будем ждать ваших предложений.", "Всего хорошего!"]
            return random.choice(farewells)

        # Если ничего не распознано — нейтральный ответ
        fallback_messages = [
            "Я не совсем понял твой запрос. Можешь уточнить?",
            "Попробуй перефразировать....я не понял..",
            "Я не понимаю о чем речь..."
        ]

        import random
        response = random.choice(fallback_messages)
        print(f"DEBUG: Используется fallback response: '{response}'")  # Отладка
        return response

    def show_relation_tooltip(self, faction, pos=None):
        """Показывает всплывающую подсказку о влиянии отношений на сделки"""
        from kivy.uix.popup import Popup
        from kivy.uix.boxlayout import BoxLayout
        from kivy.uix.gridlayout import GridLayout
        from kivy.uix.label import Label
        from kivy.uix.button import Button
        from kivy.metrics import dp
        from kivy.graphics import Color, Rectangle, RoundedRectangle

        # Получаем данные об отношениях
        relations = self.advisor.relations_manager.load_combined_relations()
        relation_data = relations.get(faction, {"relation_level": 50, "status": "нейтралитет"})

        try:
            relation_level = int(relation_data.get("relation_level", 50))
        except (ValueError, TypeError):
            relation_level = 50

        coefficient = self.calculate_coefficient(relation_level)
        status = relation_data.get('status', 'нейтралитет')

        # Определяем цвет статуса
        if relation_level < 15:
            status_color = (0.8, 0.1, 0.1, 1)  # Красный
            status_desc = "Вражда"
        elif relation_level < 35:
            status_color = (1.0, 0.5, 0.0, 1)  # Оранжевый
            status_desc = "Напряженные"
        elif relation_level < 50:
            status_color = (1.0, 0.8, 0.0, 1)  # Желтый
            status_desc = "Прохладные"
        elif relation_level < 60:
            status_color = (0.2, 0.7, 0.3, 1)  # Зеленый
            status_desc = "Нейтральные"
        elif relation_level < 75:
            status_color = (0.0, 0.8, 0.8, 1)  # Бирюзовый
            status_desc = "Дружественные"
        elif relation_level < 90:
            status_color = (0.1, 0.3, 0.9, 1)  # Синий
            status_desc = "Очень дружественные"
        else:
            status_color = (1, 1, 1, 1)  # Белый
            status_desc = "Союзнические"

        # Создаем содержимое popup
        content = BoxLayout(
            orientation='vertical',
            spacing=dp(10),
            padding=dp(15)
        )

        # Фон
        with content.canvas.before:
            Color(0.1, 0.1, 0.15, 0.98)
            RoundedRectangle(
                pos=content.pos,
                size=content.size,
                radius=[dp(10), ]
            )

        # Заголовок
        header = Label(
            text=f"Отношения с {faction}",
            font_size='18sp',
            bold=True,
            color=(1, 1, 1, 1),
            size_hint=(1, None),
            height=dp(40)
        )
        content.add_widget(header)

        # Основная информация
        main_info = GridLayout(
            cols=2,
            spacing=dp(10),
            size_hint=(1, None),
            height=dp(80)
        )

        # Уровень отношений
        rel_label = Label(
            text="Уровень отношений:",
            font_size='14sp',
            color=(0.8, 0.8, 0.9, 1),
            halign='left'
        )

        rel_value = Label(
            text=f"{relation_level}/100",
            font_size='16sp',
            bold=True,
            color=status_color,
            halign='right'
        )

        # Коэффициент сделок
        coeff_label = Label(
            text="Коэффициент сделок:",
            font_size='14sp',
            color=(0.8, 0.8, 0.9, 1),
            halign='left'
        )

        coeff_value = Label(
            text=f"×{coefficient:.2f}",
            font_size='16sp',
            bold=True,
            color=status_color,
            halign='right'
        )

        main_info.add_widget(rel_label)
        main_info.add_widget(rel_value)
        main_info.add_widget(coeff_label)
        main_info.add_widget(coeff_value)

        content.add_widget(main_info)

        # Прогресс-бар отношений (визуализация)
        progress_container = BoxLayout(
            orientation='vertical',
            spacing=dp(5),
            size_hint=(1, None),
            height=dp(40)
        )

        progress_bg = BoxLayout(
            orientation='horizontal',
            size_hint=(1, None),
            height=dp(20)
        )

        # Визуализация прогресса отношений
        with progress_bg.canvas.before:
            Color(0.2, 0.2, 0.3, 1)
            Rectangle(pos=progress_bg.pos, size=progress_bg.size)

            # Заливка в зависимости от уровня
            fill_width = (relation_level / 100) * progress_bg.width
            Color(*status_color[:3], 0.7)
            Rectangle(
                pos=progress_bg.pos,
                size=(fill_width if fill_width > 0 else 0, progress_bg.height)
            )

        progress_label = Label(
            text=f"Статус: {status} ({status_desc})",
            font_size='12sp',
            color=status_color,
            size_hint=(1, None),
            height=dp(20)
        )

        progress_container.add_widget(progress_bg)
        progress_container.add_widget(progress_label)
        content.add_widget(progress_container)

        # Детали влияния на переговоры
        details = BoxLayout(
            orientation='vertical',
            spacing=dp(5),
            size_hint=(1, None),
            height=dp(150)
        )

        details_title = Label(
            text="Влияние на переговоры:",
            font_size='14sp',
            bold=True,
            color=(0.9, 0.9, 0.5, 1),
            size_hint=(1, None),
            height=dp(25)
        )
        details.add_widget(details_title)

        # Динамическое описание в зависимости от коэффициента
        descriptions = []

        if coefficient == 0:
            descriptions = [
                "• Сделки полностью невозможны",
                "• Любые предложения будут отклонены",
                "• Требуется улучшить отношения"
            ]
        elif coefficient < 0.5:
            descriptions = [
                "• Сделки крайне невыгодны для нас",
                "• Требуются предложения с премией 100%+",
                "• Могут обсуждаться только критически важные сделки"
            ]
        elif coefficient < 1.0:
            descriptions = [
                f"• Сделки требуют премии {int((1 / coefficient - 1) * 100)}%",
                "• Предложения оцениваются строго",
                "• Торг возможен, но сложен"
            ]
        elif coefficient < 1.5:
            descriptions = [
                "• Стандартные условия сделок",
                "• Рыночные цены и условия",
                "• Торг ведется на равных"
            ]
        elif coefficient < 2.0:
            descriptions = [
                "• Готовность идти на уступки",
                f"• Возможны скидки до {int((coefficient - 1) * 100)}%",
                "• Приоритет долгосрочным отношениям"
            ]
        else:
            descriptions = [
                "• Максимально выгодные условия",
                "• Готовы помочь в ущерб себе",
                "• Сделки укрепляют альянс"
            ]

        for desc in descriptions:
            desc_label = Label(
                text=desc,
                font_size='12sp',
                color=(0.8, 0.8, 0.9, 1),
                size_hint=(1, None),
                height=dp(20),
                halign='left'
            )
            details.add_widget(desc_label)

        content.add_widget(details)

        # Советы по улучшению отношений
        tips = BoxLayout(
            orientation='vertical',
            spacing=dp(5),
            size_hint=(1, None),
            height=dp(80)
        )

        tips_title = Label(
            text="Как улучшить отношения:",
            font_size='12sp',
            bold=True,
            color=(0.7, 0.9, 0.7, 1),
            size_hint=(1, None),
            height=dp(20)
        )
        tips.add_widget(tips_title)

        # Динамические советы
        improvement_tips = []

        if relation_level < 25:
            improvement_tips = [
                "✓ Заключите перемирие через посла",
                "✓ Предложите взаимовыгодную сделку",
                "✓ Избегайте конфликтных действий"
            ]
        elif relation_level < 50:
            improvement_tips = [
                "✓ Регулярно торгуйте с нами",
                "✓ Помогите в совместных задачах",
                "✓ Проявляйте дипломатичность"
            ]
        else:
            improvement_tips = [
                "✓ Заключайте долгосрочные соглашения",
                "✓ Оказывайте военную поддержку",
                "✓ Участвуйте в совместных проектах"
            ]

        for tip in improvement_tips:
            tip_label = Label(
                text=tip,
                font_size='11sp',
                color=(0.6, 0.8, 0.6, 1),
                size_hint=(1, None),
                height=dp(18),
                halign='left'
            )
            tips.add_widget(tip_label)

        content.add_widget(tips)

        # Кнопка закрытия
        close_btn = Button(
            text="Закрыть",
            size_hint=(1, None),
            height=dp(40),
            background_color=(0.3, 0.3, 0.5, 1),
            background_normal='',
            font_size='14sp'
        )
        content.add_widget(close_btn)

        # Создаем popup
        popup = Popup(
            title='',
            content=content,
            size_hint=(0.8, 0.7),
            auto_dismiss=True,
            separator_color=(0.3, 0.3, 0.5, 1),
            background=''
        )

        # Стилизуем фон popup
        popup.background_color = (0, 0, 0, 0.3)

        # Обработчик закрытия
        close_btn.bind(on_press=popup.dismiss)

        # Показываем popup
        popup.open()

        return popup

    def create_chat_header(self):
        """Создает шапку чата с иконками"""
        header = BoxLayout(
            orientation='horizontal',
            size_hint=(1, None),
            height=dp(60),
            padding=[dp(15), dp(10)],
            spacing=dp(10)
        )

        # Кнопка назад с иконкой
        back_button = Button(
            text="",
            size_hint=(None, None),
            size=(dp(40), dp(40)),
            background_normal='files/pict/sov/back.png',  # Путь к иконке "назад"
            background_color=(0.3, 0.3, 0.5, 1),
            border=(0, 0, 0, 0),
            on_press=lambda x: self.advisor.return_to_main_tab()
        )

        # Информация о текущей фракции
        faction_info = BoxLayout(
            orientation='vertical',
            size_hint=(0.4, 1),
            spacing=dp(2)
        )
        title_label = Label(
            text="Дипломатическая переписка",
            font_size='18sp',
            bold=True,
            color=(1, 1, 1, 1),
            halign='center'
        )
        faction_info.add_widget(title_label)

        # Выпадающий список фракций
        faction_selector_box = BoxLayout(
            orientation='horizontal',
            size_hint=(0.4, 1),
            spacing=dp(10)
        )
        selector_label = Label(
            text="Фракция:",
            font_size='16sp',
            color=(0.8, 0.8, 0.9, 1),
            size_hint=(0.4, 1)
        )

        self.faction_spinner = Spinner(
            text='Выберите фракцию',
            values=[],
            size_hint=(0.6, None),
            size=(dp(150), dp(40)),
            background_color=(0.2, 0.3, 0.5, 1),
            font_size='14sp',
            background_normal='',
            background_down=''
        )

        # Заполняем список фракций
        all_factions = ["Север", "Эльфы", "Адепты", "Вампиры", "Элины"]
        for faction in all_factions:
            if faction != self.faction:
                self.faction_spinner.values.append(faction)

        self.faction_spinner.bind(text=self.on_faction_selected)
        faction_selector_box.add_widget(selector_label)
        faction_selector_box.add_widget(self.faction_spinner)

        # Кнопка обновления с иконкой
        refresh_button = Button(
            text="",
            size_hint=(None, None),
            size=(dp(40), dp(40)),
            background_normal='files/pict/sov/switch.png',
            background_color=(0.4, 0.4, 0.6, 1),
            border=(0, 0, 0, 0),
            on_press=lambda x: self.load_chat_history()
        )

        # Кнопка информации об отношениях с иконкой
        info_button = Button(
            text="",
            size_hint=(None, None),
            size=(dp(40), dp(40)),
            background_normal='files/pict/sov/warning.png',
            background_color=(0.4, 0.4, 0.6, 1),
            border=(0, 0, 0, 0),
            on_press=self.show_relation_info
        )

        header.add_widget(back_button)
        header.add_widget(faction_info)
        header.add_widget(faction_selector_box)
        header.add_widget(info_button)
        header.add_widget(refresh_button)

        return header

    def create_relation_sidebar(self):
        """Создает боковую панель с информацией об отношениях (упрощенная версия)"""
        sidebar = BoxLayout(
            orientation='vertical',
            size_hint=(0.25, 1),
            spacing=dp(10),
            padding=dp(5)
        )

        # Заголовок панели
        sidebar_title = Label(
            text="Информация",
            font_size='16sp',
            bold=True,
            color=(1, 1, 1, 1),
            size_hint=(1, None),
            height=dp(30)
        )
        sidebar.add_widget(sidebar_title)

        # Область отображения отношений
        relations_box = BoxLayout(
            orientation='vertical',
            size_hint=(1, 0.6),
            spacing=dp(5),
            padding=dp(5)
        )

        self.relation_display = Label(
            text="Выберите фракцию",
            font_size='12sp',
            color=(0.9, 0.9, 0.9, 1),
            size_hint=(1, 1),
            valign='top',
            halign='center',
            text_size=(None, None)
        )
        relations_box.add_widget(self.relation_display)
        sidebar.add_widget(relations_box)

        # Кнопка подробной информации
        details_button = Button(
            text="Подробнее об отношениях",
            size_hint=(1, None),
            height=dp(40),
            background_color=(0.3, 0.3, 0.5, 1),
            background_normal='',
            font_size='12sp',
            on_press=self.show_relation_info
        )
        sidebar.add_widget(details_button)

        # История сделок
        history_box = BoxLayout(
            orientation='vertical',
            size_hint=(1, 0.4),
            spacing=dp(5),
            padding=dp(5)
        )

        history_title = Label(
            text="История сделок:",
            font_size='13sp',
            bold=True,
            color=(0.8, 0.8, 0.8, 1),
            size_hint=(1, None),
            height=dp(25)
        )
        history_box.add_widget(history_title)

        history_scroll = ScrollView(
            size_hint=(1, 1),
            bar_width=dp(5)
        )

        self.trade_history_label = Label(
            text="Нет истории сделок",
            font_size='11sp',
            color=(0.7, 0.7, 0.7, 1),
            size_hint_y=None,
            valign='top',
            halign='left'
        )
        self.trade_history_label.bind(
            texture_size=lambda *x: self.trade_history_label.setter('height')(
                self.trade_history_label, self.trade_history_label.texture_size[1])
        )

        history_scroll.add_widget(self.trade_history_label)
        history_box.add_widget(history_scroll)
        sidebar.add_widget(history_box)

        return sidebar

    def show_relation_info(self, instance):
        """Показывает информацию об отношениях с текущей выбранной фракцией"""
        if hasattr(self, 'selected_faction') and self.selected_faction:
            self.show_relation_tooltip(self.selected_faction)
        else:
            # Используем метод для добавления системного сообщения
            self.add_chat_message_system("Сначала выберите фракцию для просмотра информации об отношениях")

    def update_relation_display(self, faction=None):
        """Обновляет отображение информации об отношениях"""
        if not faction and hasattr(self, 'selected_faction'):
            faction = self.selected_faction

        if not faction:
            return

        # Получаем данные об отношениях
        relations = self.advisor.relations_manager.load_combined_relations()
        relation_data = relations.get(faction, {"relation_level": 50, "status": "нейтралитет"})

        try:
            relation_level = int(relation_data.get("relation_level", 50))
        except (ValueError, TypeError):
            relation_level = 50

        coefficient = self.calculate_coefficient(relation_level)
        status = relation_data.get('status', 'нейтралитет')

        # Форматируем текст для отображения
        display_text = f"""Отношения с {faction}

    Уровень: [b]{relation_level}/100[/b]
    Статус: {status}
    Коэффициент: ×{coefficient:.2f}

    [b]Влияние на сделки:[/b]
    """

        # Добавляем динамическое описание
        if coefficient == 0:
            display_text += "• Сделки невозможны\n"
        elif coefficient < 0.7:
            display_text += "• Требуется премия\n• Строгие условия\n"
        elif coefficient < 1.3:
            display_text += "• Стандартные условия\n• Равный торг\n"
        else:
            display_text += "• Выгодные условия\n• Готовы к уступкам\n"

        # Добавляем совет
        display_text += "\n[b]Совет:[/b]\n"
        if relation_level < 30:
            display_text += "Улучшите отношения\nперед сделками"
        elif relation_level < 60:
            display_text += "Торгуйтесь аккуратно"
        else:
            display_text += "Используйте преимущество"

        # Обновляем label
        if hasattr(self, 'relation_display'):
            self.relation_display.text = display_text
            self.relation_display.markup = True

    def _is_resource_request(self, message):
        """Определяет, является ли сообщение запросом ресурсов - УПРОЩЕННЫЙ ВАРИАНТ"""
        message_lower = message.lower().strip()

        print(f"DEBUG _is_resource_request: Анализируем '{message_lower}'")  # Отладка

        # Список ВСЕХ возможных слов для запросов
        request_words = [
            'нужен', 'нужны', 'нужно', 'нуждаюсь', 'нуждается',
            'дай', 'дайте', 'предоставь', 'предоставьте', 'отдай', 'отдайте',
            'хочу', 'хотел', 'хотела', 'хотелось', 'желаю', 'желаем',
            'получить', 'получать', 'достать', 'надо', 'надобно',
            'можно', 'мог бы', 'могла бы', 'могли бы',
            'прошу', 'просим', 'просят', 'просите',
            'требую', 'требуем', 'требуют', 'требуется', 'требуются',
            'необходим', 'необходимы', 'необходимо', 'необходима',
            'хотелось бы', 'хотеться', 'хотят'
        ]

        # Список ВСЕХ возможных ресурсов
        resource_words = [
            'крон', 'кронн', 'золот', 'золота', 'деньг', 'денег', 'монет', 'монеты',
            'кристалл', 'кристал', 'кристалы', 'руда', 'руды', 'минерал', 'минералы',
            'ресурс', 'ресурсы', 'ресурсов',
            'рабоч', 'рабочих', 'рабочего', 'люд', 'людей', 'крестьян', 'работник', 'работников',
            'арми', 'солдат', 'войск', 'воин', 'воинов'
        ]

        # Проверяем наличие хотя бы одного слова запроса
        has_request = any(req_word in message_lower for req_word in request_words)
        print(f"DEBUG _is_resource_request: has_request = {has_request}")  # Отладка

        # Проверяем наличие хотя бы одного слова ресурса
        has_resource = any(res_word in message_lower for res_word in resource_words)
        print(f"DEBUG _is_resource_request: has_resource = {has_resource}")  # Отладка

        # ДОПОЛНИТЕЛЬНО: проверяем на специальные фразы
        special_phrases = [
            'мне нужны', 'нужно мне', 'дайте мне', 'хочу получить',
            'можно получить', 'могли бы дать', 'хотел бы получить'
        ]

        has_special_phrase = any(phrase in message_lower for phrase in special_phrases)
        print(f"DEBUG _is_resource_request: has_special_phrase = {has_special_phrase}")  # Отладка

        # Возвращаем True если:
        # 1. Есть слово запроса И слово ресурса ИЛИ
        # 2. Есть специальная фраза
        result = (has_request and has_resource) or has_special_phrase
        print(f"DEBUG _is_resource_request: результат = {result}")  # Отладка

        return result

    def _extract_resource_mentions(self, message):
        """Извлекает все упоминания ресурсов из сообщения - РАСШИРЕННАЯ ВЕРСИЯ"""
        message_lower = message.lower()

        # Расширенное сопоставление
        resource_mapping = {
            'крон': 'Кроны', 'кронн': 'Кроны', 'золот': 'Кроны', 'деньг': 'Кроны',
            'денег': 'Кроны', 'монет': 'Кроны', 'монеты': 'Кроны', 'золота': 'Кроны',
            'кристалл': 'Кристаллы', 'кристал': 'Кристаллы', 'кристалы': 'Кристаллы',
            'руда': 'Кристаллы', 'руды': 'Кристаллы', 'минерал': 'Кристаллы',
            'минералы': 'Кристаллы', 'ресурс': 'Кристаллы', 'ресурсы': 'Кристаллы',
            'рабоч': 'Рабочие', 'рабочих': 'Рабочие', 'рабочего': 'Рабочие',
            'люд': 'Рабочие', 'людей': 'Рабочие', 'крестьян': 'Рабочие',
            'работник': 'Рабочие', 'работников': 'Рабочие', 'рабочей': 'Рабочие'
        }

        found_resources = []

        # Проверяем каждое слово в сообщении
        words = message_lower.split()
        for word in words:
            for keyword, resource_type in resource_mapping.items():
                # Проверяем вхождение ключевого слова в слово
                if keyword in word:
                    if resource_type not in found_resources:
                        found_resources.append(resource_type)
                    break  # переходим к следующему слову

        print(f"DEBUG _extract_resource_mentions: found {found_resources} in '{message}'")  # Отладка
        return found_resources

    def _extract_resource_request_info(self, message):
        """Извлекает информацию о запросе ресурсов из сообщения - УПРОЩЕННАЯ ВЕРСИЯ"""
        message_lower = message.lower()

        # Сначала пытаемся извлечь количество
        amount = self._extract_number(message)

        # Простое определение типа ресурса
        if any(word in message_lower for word in ['крон', 'золот', 'деньг', 'монет']):
            resource_type = 'Кроны'
        elif any(word in message_lower for word in ['кристалл', 'руда', 'минерал']):
            resource_type = 'Кристаллы'
        elif any(word in message_lower for word in ['рабоч', 'люд', 'крестьян', 'работник']):
            resource_type = 'Рабочие'
        else:
            resource_type = None

        if resource_type:
            return {
                'type': resource_type,
                'amount': amount if amount else 0  # 0 если количество не указано
            }

        return None

    def _extract_number(self, message):
        """Извлекает число из сообщения - улучшенная версия"""
        import re

        # Ищем цифры
        numbers = re.findall(r'\d+', message)
        if numbers:
            return int(numbers[0])

        # Ищем числительные (простая версия)
        numeral_map = {
            'один': 1, 'одну': 1, 'два': 2, 'две': 2, 'три': 3, 'четыре': 4,
            'пять': 5, 'шесть': 6, 'семь': 7, 'восемь': 8, 'девять': 9,
            'десять': 10, 'сотня': 100, 'сотню': 100, 'тысяча': 1000
        }

        message_lower = message.lower()
        for word, value in numeral_map.items():
            if word in message_lower:
                return value

        return None

    def _extract_trade_offer(self, message):
        """Извлекает торговое предложение из сообщения"""
        # Сначала пытаемся извлечь структурированное предложение
        info = self._extract_trade_info(message)
        if info:
            return {
                "type": info["get_type"],
                "amount": info["get_amount"]
            }

        # Если не получилось, ищем просто "ресурс + количество"
        import re

        # Словарь соответствий
        resource_map = {
            'крон': 'Кроны', 'золот': 'Кроны', 'деньг': 'Кроны',
            'кристалл': 'Кристаллы', 'кристал': 'Кристаллы', 'минерал': 'Кристаллы',
            'рабоч': 'Рабочие', 'люд': 'Рабочие', 'работник': 'Рабочие'
        }

        message_lower = message.lower()

        # Ищем число
        numbers = re.findall(r'\d+', message_lower)
        if not numbers:
            return None

        amount = int(numbers[0])

        # Ищем тип ресурса
        for key, resource_type in resource_map.items():
            if key in message_lower:
                return {
                    "type": resource_type,
                    "amount": amount
                }

        return None

    def _handle_forced_dialog(self, message, faction, context):
        message_lower = message.lower()

        if context.get("stage") == "ask_resource_type":
            resource = self._extract_resource_type(message)
            if not resource:
                # Ресурс не распознан → уточняем
                return "Какой ресурс тебе нужен: Кроны, Кристаллы или Рабочие?"
            context["resource"] = resource
            context["stage"] = "ask_resource_amount"
            return f"Сколько {resource} тебе нужно?"

        if context.get("stage") == "ask_resource_amount":
            amount = self._extract_number(message)
            if not amount:
                return "Назови конкретное количество."
            context["amount"] = amount
            context["stage"] = "ask_player_offer"
            return self._check_ai_stock_and_respond(faction, context)

        if context.get("stage") == "ask_player_offer":
            offer = self._extract_trade_offer(message)
            if not offer:
                # Проверяем, может быть игрок говорит "ничего" или отказывается
                if any(word in message_lower for word in
                       ['ничего', 'не хочу', 'отказываюсь', 'нет', 'хватит', 'прекратим']):
                    context["stage"] = "idle"
                    return "Хорошо, тогда не будем торговать."

                # Пробуем извлечь ресурс напрямую из сообщения
                resource = self._extract_resource_type(message)
                if resource:
                    # Если есть число, создаем предложение
                    amount = self._extract_number(message)
                    if amount:
                        offer = {
                            "type": resource,
                            "amount": amount
                        }
                        context["player_offer"] = offer
                        context["stage"] = "evaluate"
                        return self._evaluate_trade(faction, context)

                return "Что именно ты предлагаешь взамен? Назови ресурс и количество."

            # Сохраняем предложение и переходим к оценке
            context["player_offer"] = offer
            context["stage"] = "evaluate"
            return self._evaluate_trade(faction, context)

        # Обработка стадии counter_offer (предложение улучшения)
        if context.get("stage") == "counter_offer":
            # Проверяем, соглашается ли игрок на предложенное улучшение
            if any(word in message_lower for word in ['да', 'согласен', 'ок', 'хорошо', 'ладно', 'принимаю']):
                # Игрок согласился на улучшение - обновляем контекст и оцениваем
                context["stage"] = "evaluate"
                return self._evaluate_trade(faction, context)
            elif any(word in message_lower for word in ['нет', 'не согласен', 'отказываюсь']):
                context["stage"] = "idle"
                return "Хорошо, тогда сделку отменяем."
            else:
                # Игрок предлагает новый вариант
                offer = self._extract_trade_offer(message)
                if offer:
                    context["player_offer"] = offer
                    context["stage"] = "evaluate"
                    return self._evaluate_trade(faction, context)
                else:
                    return "Назови свое предложение или ответь на мое предложение."

        return None

    def _check_ai_stock_and_respond(self, faction, context):
        ai_resources = self._get_ai_resources(faction)
        have = ai_resources.get(context["resource"], 0)

        if have < context["amount"]:
            context["stage"] = "idle"
            return f"У меня нет столько {context['resource']}. Сделка невозможна."

        context["stage"] = "ask_player_offer"
        return (
            f"У меня есть {context['amount']} {context['resource']}. "
            "Что ты предлагаешь взамен?"
        )

    def _evaluate_trade(self, faction, context):
        """Оценивает торговое предложение с учетом отношений"""
        # Получаем данные о сделке из контекста
        resource = context.get("resource")
        amount = context.get("amount")
        player_offer = context.get("player_offer")

        if not all([resource, amount, player_offer]):
            return "Что-то пошло не так. Давайте начнем переговоры заново."

        # Создаем информацию о сделке
        deal_info = {
            'ai_gives_type': resource,
            'ai_gives_amount': amount,
            'player_gives_type': player_offer['type'],
            'player_gives_amount': player_offer['amount']
        }

        # Рассчитываем привлекательность
        attractiveness_data = self.calculate_deal_attractiveness(faction, deal_info, is_ai_giving=True)
        attractiveness = attractiveness_data['attractiveness']

        # Определяем порог принятия на основе отношений
        relations = self.advisor.relations_manager.load_combined_relations()
        relation_data = relations.get(faction, {"relation_level": 50})
        relation_level = int(relation_data.get("relation_level", 50))

        # Динамический порог: лучше отношения = более выгодные сделки для игрока
        if relation_level < 35:
            threshold = 1.5  # При плохих отношениях требуем очень выгодную сделку
        elif relation_level < 60:
            threshold = 1.2  # При нейтральных отношениях
        elif relation_level < 80:
            threshold = 1.0  # При дружественных
        else:
            threshold = 0.9  # При союзнических готовы на менее выгодные сделки

        # Отладочная информация
        print(f"DEBUG: Привлекательность сделки: {attractiveness:.2f}")
        print(f"DEBUG: Порог принятия: {threshold}")
        print(f"DEBUG: Коэффициент отношений: {attractiveness_data['relation_coefficient']}")

        # Принимаем решение
        if attractiveness >= threshold:
            # Сделка выгодна
            context["stage"] = "agreement"
            context["active_request"] = {
                "type": "resource_trade",
                "player_offers": player_offer,
                "ai_offers": {"type": resource, "amount": amount},
            }

            # Выполняем сделку
            if self.execute_agreed_trade(faction, context["active_request"]):
                # Улучшаем отношения при успешной сделке
                self.improve_relations_from_trade(faction, amount)
                return f"Согласен! Отношения позволяют нам заключить эту сделку."
            else:
                context["stage"] = "idle"
                return "Согласен, но возникла ошибка при обработке."

        else:
            # Сделка невыгодна - предлагаем улучшение
            context["stage"] = "counter_offer"

            # Рассчитываем, что нужно изменить
            needed_improvement = threshold - attractiveness

            # Предлагаем конкретные изменения
            if needed_improvement > 0.5:
                # Нужно значительно улучшить предложение
                suggested_multiplier = 1.0 + needed_improvement
                suggested_amount = int(player_offer['amount'] * suggested_multiplier)

                return (f"При наших отношениях ({relation_level}/100) это предложение недостаточно выгодно. "
                        f"Предложи хотя бы {suggested_amount} {player_offer['type'].lower()}.")

            elif needed_improvement > 0.2:
                # Небольшое улучшение
                suggested_amount = int(player_offer['amount'] * 1.3)

                return (f"Для текущего уровня отношений ({relation_level}/100) нужно немного улучшить предложение. "
                        f"Добавь еще {suggested_amount - player_offer['amount']} {player_offer['type'].lower()}.")

            else:
                # Почти достигли порога
                return (f"Мы почти договорились! При наших отношениях ({relation_level}/100) "
                        f"нужно совсем немного улучшить предложение. Можешь добавить еще "
                        f"{int(player_offer['amount'] * 0.1)} {player_offer['type'].lower()}?")

    def improve_relations_from_trade(self, faction, trade_amount):
        """Улучшает отношения после успешной сделки"""
        try:
            cursor = self.db_connection.cursor()

            # Рассчитываем улучшение отношений в зависимости от размера сделки
            if trade_amount < 100:
                improvement = 1
            elif trade_amount < 500:
                improvement = 2
            elif trade_amount < 1000:
                improvement = 3
            else:
                improvement = 5

            # Обновляем отношения
            cursor.execute('''
                UPDATE ai_relations 
                SET relation_level = relation_level + ? 
                WHERE ai_faction = ? AND target_faction = ?
            ''', (improvement, faction, self.faction))

            # Также обновляем в другую сторону
            cursor.execute('''
                UPDATE ai_relations 
                SET relation_level = relation_level + ? 
                WHERE ai_faction = ? AND target_faction = ?
            ''', (improvement, self.faction, faction))

            self.db_connection.commit()

            # Обновляем кэш отношений
            self.advisor.relations_manager.refresh_relations()

            print(f"Отношения с {faction} улучшены на {improvement} пунктов")

        except Exception as e:
            print(f"Ошибка при улучшении отношений: {e}")

    def update_chat_header(self, faction):
        """Обновляет заголовок чата"""
        # Существующий код...

        # Добавляем информацию о коэффициенте сделок
        relations = self.advisor.relations_manager.load_combined_relations()
        relation_data = relations.get(faction, {"relation_level": 0, "status": "нейтралитет"})

        try:
            relation_level = int(relation_data["relation_level"])
        except (ValueError, TypeError, KeyError):
            relation_level = 0

        # Рассчитываем коэффициент
        coefficient = self.calculate_coefficient(relation_level)

        # Добавляем информацию о коэффициенте в статус
        coefficient_text = f" (×{coefficient:.1f})" if coefficient > 0 else " (сделки невозможны)"

        self.relation_status.text = (
            f"Отношения: {relation_level}/100 "
            f"({relation_data.get('status', 'нейтралитет')}){coefficient_text}"
        )

        # Цвет в зависимости от коэффициента
        if coefficient == 0:
            rel_color = (0.8, 0.1, 0.1, 1)  # Красный
        elif coefficient < 0.7:
            rel_color = (1.0, 0.5, 0.0, 1)  # Оранжевый
        elif coefficient < 1.0:
            rel_color = (1.0, 0.8, 0.0, 1)  # Желтый
        elif coefficient < 1.5:
            rel_color = (0.2, 0.7, 0.3, 1)  # Зеленый
        else:
            rel_color = (0.1, 0.3, 0.9, 1)  # Синий

        self.relation_status.color = rel_color

    def _extract_trade_info(self, message):
        """Извлекает информацию о торговом предложении"""
        message_lower = message.lower()

        # Паттерны для поиска торговых предложений
        patterns = [
            r'(?P<give_amount>\d+)\s*(?P<give_type>крон|золот|кристалл|ресурс|рабоч|люд)[^\d]*(?P<get_amount>\d+)\s*(?P<get_type>крон|золот|кристалл|ресурс|рабоч|люд)',
            r'(?P<give_type>крон|золот|кристалл|ресурс|рабоч|люд)[^\d]*(?P<give_amount>\d+)[^\d]*(?P<get_type>крон|золот|кристалл|ресурс|рабоч|люд)[^\d]*(?P<get_amount>\d+)'
        ]

        import re
        for pattern in patterns:
            match = re.search(pattern, message_lower)
            if match:
                resource_map = {
                    'крон': 'Кроны', 'золот': 'Кроны',
                    'кристалл': 'Кристаллы', 'ресурс': 'Кристаллы',
                    'рабоч': 'Рабочие', 'люд': 'Рабочие'
                }

                return {
                    'give_type': resource_map.get(match.group('give_type'), 'Кроны'),
                    'give_amount': int(match.group('give_amount')),
                    'get_type': resource_map.get(match.group('get_type'), 'Кристаллы'),
                    'get_amount': int(match.group('get_amount'))
                }

        return None

    def _extract_resource_type(self, message):
        message_lower = message.lower()
        if any(word in message_lower for word in ['крон', 'золот', 'деньг']):
            return 'Кроны'
        elif any(word in message_lower for word in ['кристалл', 'ресурс', 'материал']):
            return 'Кристаллы'
        elif any(word in message_lower for word in ['рабоч', 'люд']):
            return 'Рабочие'
        return None

    def _get_ai_resources(self, faction):
        """Получает текущие ресурсы ИИ фракции"""
        # Используем соединение из AIController
        from ii import AIController

        # Создаем временный контроллер для проверки ресурсов
        ai = AIController(faction, self.db_connection)
        ai.load_resources_from_db()

        return {
            'Кроны': ai.resources.get('Кроны', 0),
            'Кристаллы': ai.resources.get('Кристаллы', 0),
            'Рабочие': ai.resources.get('Рабочие', 0)
        }

    def _calculate_trade_ratio(self, trade_info, faction, relation_data):
        """Рассчитывает соотношение торговой сделки"""

        # Получаем ресурсы ИИ
        ai_resources = self._get_ai_resources(faction)

        # Ценности ресурсов (более сбалансированные)
        resource_values = {
            'Кроны': 1.0,
            'Кристаллы': 1.0,
            'Рабочие': 1.0
        }

        # Что ИИ отдает
        ai_gives_value = trade_info['give_amount'] * resource_values.get(trade_info['give_type'], 1.0)

        # Что ИИ получает
        ai_gets_value = trade_info['get_amount'] * resource_values.get(trade_info['get_type'], 1.0)

        # Учитываем доступность ресурсов (но менее строго)
        ai_has_amount = ai_resources.get(trade_info['give_type'], 0)
        if ai_has_amount == 0:
            availability = 0  # Нет ресурсов вообще
        else:
            availability = min(1.0, ai_has_amount / max(1, trade_info['give_amount']))
            if availability < 0.5:
                availability = 0.5  # Минимальный доступный коэффициент

        # Учитываем отношения
        relation_level = int(relation_data.get("relation_level", 50))
        relation_factor = 0.8 + (relation_level - 50) / 100.0  # От 0.3 до 1.3

        # Рассчитываем выгодность
        if ai_gives_value > 0:
            base_ratio = ai_gets_value / ai_gives_value
            final_ratio = base_ratio * availability * relation_factor

            # Отладочная печать
            print(
                f"DEBUG: give={trade_info['give_amount']} {trade_info['give_type']}, get={trade_info['get_amount']} {trade_info['get_type']}")
            print(
                f"DEBUG: base_ratio={base_ratio}, availability={availability}, relation_factor={relation_factor}, final={final_ratio}")

            return final_ratio

        return 0

    def _suggest_trade_improvement(self, trade_info, current_ratio, threshold):
        """Предлагает улучшение торгового предложения"""

        # На сколько нужно улучшить предложение
        improvement_needed = threshold - current_ratio

        if improvement_needed > 0:
            # Предлагаем увеличить то, что игрок дает
            suggested_amount = int(trade_info['get_amount'] * (1 + improvement_needed * 1.5))

            # Проверяем разумность предложения (не более чем в 2 раза)
            if suggested_amount > trade_info['get_amount'] * 2:
                suggested_amount = trade_info['get_amount'] * 2

            return f"Это предложение недостаточно выгодно. Предложи {suggested_amount} {trade_info['get_type'].lower()} вместо {trade_info['get_amount']}?"

        return f"Предложи больше {trade_info['get_type'].lower()} или меньше {trade_info['give_type'].lower()}"

    def create_trade_agreement(self, initiator, target_faction, give_resource, give_amount, get_resource, get_amount):
        """Создает торговое соглашение"""
        try:
            cursor = self.db_connection.cursor()

            cursor.execute('''
                INSERT INTO trade_agreements 
                (initiator, target_faction, initiator_type_resource, initiator_summ_resource, 
                 target_type_resource, target_summ_resource, agree)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                initiator,
                target_faction,
                give_resource,
                give_amount,
                get_resource,
                get_amount,
                0  # 0 = ожидает подтверждения, 1 = принято, 2 = отклонено
            ))

            self.db_connection.commit()
            print(f"Создано торговое соглашение: {initiator} -> {target_faction}")
            return True

        except Exception as e:
            print(f"Ошибка при создании торгового соглашения: {e}")
            return False

    def _create_trade_query(self, faction, trade_info):
        """Создает торговое соглашение вместо записи в queries"""
        try:
            # trade_info содержит:
            # give_type: что ИИ отдает (ресурс игроку)
            # give_amount: сколько отдает
            # get_type: что ИИ получает (ресурс от игрока)
            # get_amount: сколько получает

            # С точки зрения ИИ:
            # initiator = игрок (self.faction)
            # target_faction = ИИ (faction)
            # Инициатор отдает get_type:get_amount, получает give_type:give_amount

            # Но в чате игрок - инициатор, поэтому:
            return self.create_trade_agreement(
                initiator=self.faction,  # Игрок инициирует сделку
                target_faction=faction,  # ИИ - цель
                give_resource=trade_info['get_type'],  # Что игрок отдает (то, что ИИ получает)
                give_amount=trade_info['get_amount'],
                get_resource=trade_info['give_type'],  # Что игрок получает (то, что ИИ отдает)
                get_amount=trade_info['give_amount']
            )

        except Exception as e:
            print(f"Ошибка при создании торгового соглашения: {e}")
            return False

    def execute_agreed_trade(self, faction, offer):
        """Выполняет согласованную сделку через trade_agreements"""
        try:
            if offer['type'] == 'resource_trade':
                player_offers = offer['player_offers']
                ai_offers = offer['ai_offers']

                # Создаем торговое соглашение
                success = self.create_trade_agreement(
                    initiator=self.faction,  # Игрок инициирует
                    target_faction=faction,  # ИИ принимает
                    give_resource=player_offers['type'],  # Игрок отдает
                    give_amount=player_offers['amount'],
                    get_resource=ai_offers['type'],  # Игрок получает
                    get_amount=ai_offers['amount']
                )

                if success:
                    # Очищаем контекст переговоров
                    if faction in self.negotiation_context:
                        self.negotiation_context[faction]['stage'] = 'completed'
                        self.negotiation_context[faction]['active_request'] = None

                    return True
                else:
                    return False

        except Exception as e:
            print(f"Ошибка при выполнении сделки: {e}")
            return False

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

    def scroll_chat_to_bottom(self):
        """Прокручивает чат вниз"""
        if self.chat_scroll:
            self.chat_scroll.scroll_y = 0

    def calculate_deal_attractiveness(self, faction, deal_info, is_ai_giving=True):
        """
        Рассчитывает привлекательность сделки с учетом отношений
        deal_info: словарь с информацией о сделке
        is_ai_giving: True если ИИ отдает ресурсы, False если получает
        """
        # Получаем уровень отношений
        relations = self.advisor.relations_manager.load_combined_relations()
        relation_data = relations.get(faction, {"relation_level": 50})
        relation_level = int(relation_data.get("relation_level", 50))

        # Базовый коэффициент отношений
        relation_coefficient = self.calculate_coefficient(relation_level)

        # Получаем ресурсы ИИ
        ai_resources = self._get_ai_resources(faction)

        # Определяем что ИИ отдает и получает
        if is_ai_giving:
            give_type = deal_info.get('ai_gives_type')
            give_amount = deal_info.get('ai_gives_amount', 0)
            get_type = deal_info.get('player_gives_type')
            get_amount = deal_info.get('player_gives_amount', 0)
        else:
            give_type = deal_info.get('player_gives_type')
            give_amount = deal_info.get('player_gives_amount', 0)
            get_type = deal_info.get('ai_gives_type')
            get_amount = deal_info.get('ai_gives_amount', 0)

        # Базовые ценности ресурсов (можно настроить)
        resource_values = {
            'Кроны': 1.0,
            'Кристаллы': 1.1,
            'Рабочие': 1.5
        }

        # Рассчитываем базовую стоимость
        give_value = give_amount * resource_values.get(give_type, 1.0)
        get_value = get_amount * resource_values.get(get_type, 1.0)

        # Учитываем доступность ресурсов у ИИ
        if give_type in ai_resources:
            ai_has = ai_resources[give_type]
            availability_factor = min(1.0, ai_has / max(1, give_amount))
        else:
            availability_factor = 0

        # Учитываем потребность в ресурсах
        need_factor = 1.0
        if get_type in ai_resources:
            # Если у ИИ мало этого ресурса, ценность выше
            current_amount = ai_resources[get_type]
            if current_amount < 100:  # Порог недостатка
                need_factor = 1.5

        # Итоговая формула привлекательности
        if give_value > 0:
            base_ratio = get_value / give_value
            attractiveness = base_ratio * relation_coefficient * availability_factor * need_factor
        else:
            attractiveness = 0

        return {
            'attractiveness': attractiveness,
            'base_ratio': get_value / give_value if give_value > 0 else 0,
            'relation_coefficient': relation_coefficient,
            'availability_factor': availability_factor,
            'need_factor': need_factor
        }

    def calculate_coefficient(self, relation_level):
        """Рассчитывает коэффициент на основе уровня отношений"""
        try:
            rel = int(relation_level)
        except (ValueError, TypeError):
            rel = 50

        # Уточненные диапазоны для более плавного перехода
        if rel < 15:
            return 0  # Вражда - сделки невозможны
        if 15 <= rel < 25:
            return 0.2  # Очень плохие отношения
        if 25 <= rel < 35:
            return 0.5  # Плохие отношения
        if 35 <= rel < 50:
            return 0.8  # Нейтральные
        if 50 <= rel < 60:
            return 1.0  # Нормальные (базовый коэффициент)
        if 60 <= rel < 75:
            return 1.3  # Дружественные
        if 75 <= rel < 90:
            return 1.7  # Очень дружественные
        if 90 <= rel <= 100:
            return 2.0  # Союзники
        return 0

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