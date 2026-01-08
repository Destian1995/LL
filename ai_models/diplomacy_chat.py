# ai_models/diplomacy_chat.py
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout
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

from .translation import translation_dict, reverse_translation_dict


class DiplomacyChat:
    def __init__(self, advisor_view):
        self.advisor = advisor_view
        self.faction = advisor_view.faction
        self.db_connection = advisor_view.db_connection
        self.selected_faction = None

        # Ссылки на UI элементы
        self.chat_scroll = None
        self.chat_container = None
        self.message_input = None
        self.chat_status = None
        self.faction_spinner = None

    def open_diplomacy_window(self):
        """Открывает окно дипломатических переговоров"""
        diplomacy_window = BoxLayout(
            orientation='vertical',
            size_hint=(1, 1),
            spacing=dp(10),
            padding=dp(10)
        )

        # Фон
        with diplomacy_window.canvas.before:
            Color(0.08, 0.08, 0.12, 0.95)
            Rectangle(pos=diplomacy_window.pos, size=diplomacy_window.size)

        # Шапка
        header = self.create_chat_header()
        diplomacy_window.add_widget(header)

        # Основная область чата
        main_area = self.create_chat_main_area()
        diplomacy_window.add_widget(main_area)

        # Панель статуса
        status_panel = self.create_status_panel()
        diplomacy_window.add_widget(status_panel)

        # Устанавливаем содержимое popup
        self.advisor.popup.content = diplomacy_window

        # Фокусируемся на поле ввода
        Clock.schedule_once(lambda dt: setattr(self.message_input, 'focus', True), 0.3)

    def create_chat_header(self):
        """Создает шапку чата"""
        header = BoxLayout(
            orientation='horizontal',
            size_hint=(1, None),
            height=dp(60),
            padding=[dp(15), dp(10)],
            spacing=dp(10)
        )

        # Кнопка назад
        back_button = Button(
            text="Назад",
            size_hint=(None, None),
            size=(dp(100), dp(40)),
            background_color=(0.3, 0.3, 0.5, 1),
            background_normal='',
            font_size='16sp',
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
            font_size='14sp'
        )

        # Заполняем список фракций
        all_factions = ["Север", "Эльфы", "Адепты", "Вампиры", "Элины"]
        for faction in all_factions:
            if faction != self.faction:
                self.faction_spinner.values.append(faction)

        self.faction_spinner.bind(text=self.on_faction_selected)
        faction_selector_box.add_widget(selector_label)
        faction_selector_box.add_widget(self.faction_spinner)

        # Кнопка обновления
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

        return header

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

    def update_chat_header(self, faction):
        """Обновляет заголовок чата"""
        # Обновляем иконку
        icon_path = f"files/pict/factions/{translation_dict.get(faction, faction.lower())}.png"
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
        Clock.schedule_once(
            lambda dt: self.generate_ai_response_to_message(message, self.selected_faction),
            1.5
        )

        self.chat_status.text = "Сообщение отправлено"

    def generate_ai_response_to_message(self, player_message, target_faction):
        """Генерирует ответ от ИИ фракции"""
        try:
            # Получаем текущие отношения
            relations = self.advisor.relations_manager.load_combined_relations()
            relation_data = relations.get(target_faction, {"relation_level": 50, "status": "нейтралитет"})

            # Генерируем ответ
            response = self.generate_diplomatic_response(player_message, target_faction, relation_data)

        except Exception as e:
            print(f"Ошибка при генерации ответа ИИ: {e}")
            response = f"{target_faction} получила ваше сообщение. Мы дадим ответ после обсуждения."

        # Добавляем ответ ИИ в чат
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

        # Обновляем отношения
        self.update_relations_based_on_message(player_message, response, target_faction)

        return response

    def generate_diplomatic_response(self, player_message, target_faction, relation_data):
        """Генерирует дипломатический ответ"""
        player_message_lower = player_message.lower()

        # Преобразуем relation_level в int
        try:
            relation_level = int(relation_data["relation_level"])
        except (ValueError, TypeError, KeyError):
            relation_level = 50

        status = relation_data.get("status", "нейтралитет")

        # Анализ настроения сообщения
        mood = self.analyze_message_mood(player_message_lower)

        # Анализ типа сообщения
        message_type = self.analyze_message_type(player_message_lower)

        # Генерация ответа
        response = self.generate_contextual_response(
            player_message_lower, target_faction, relation_level,
            status, mood, message_type, {}
        )

        return response

    def analyze_message_mood(self, message):
        """Анализирует настроение сообщения"""
        positive_words = ['спасибо', 'благодарю', 'прошу', 'пожалуйста', 'уважаем', 'ценю',
                          ' рад', 'рады', 'отличн', 'прекрасн', 'замечательн', 'согласн', 'дружб']
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
            'greeting': ['привет', 'здравствуй', 'добрый', 'hello', 'hi', 'день', 'здаров', 'хай'],
            'farewell': ['пока', 'до свидан', 'прощай', 'удачи', 'bye'],
            'alliance': ['союз', 'альянс', 'объедин', 'вместе', 'совмест', 'помощь военн'],
            'war': ['война', 'атака', 'напасть', 'уничтож', 'сражен', 'битв', 'конфликт'],
            'trade': ['торгов', 'обмен', 'ресурс', 'товар', 'куплю', 'продам', 'цен', 'деньг', 'крон', 'кристал'],
            'peace': ['мир', 'перемир', 'прекрат', 'законч', 'договор мирн'],
            'threat': ['угроз', 'опас', 'предупрежд', 'осторожн', 'последств'],
            'information': ['информац', 'данн', 'сведен', 'отчет', 'состоян', 'ситуац', 'новост'],
            'request': ['прошу', 'запрос', 'требу', 'нужн', 'хочу', 'желаю', 'надо', 'хочу', 'дай'],
            'offer': ['предлагаю', 'предложен', 'могу', 'готов', 'соглас']
        }

        scores = {category: 0 for category in categories}

        for category, words in categories.items():
            for word in words:
                if word in message:
                    scores[category] += 1

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

        # Генерация ответа по типу сообщения
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
            return self.generate_information_response(faction, relation_level, status, mood, personality, context, message)

        elif message_type == "request":
            return self.generate_request_response(faction, relation_level, status, mood, personality, context, message)

        elif message_type == "offer":
            return self.generate_offer_response(faction, relation_level, status, mood, personality, context, message)

        else:
            # Общий ответ
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

        if personality.get("arrogant", 0) > 7:
            arrogant_responses = [
                "Мы выслушали ваши слова. Надеемся, они стоили нашего времени.",
                "Ваше сообщение... интересно. Для кого-то вашего уровня.",
                f"Мы приняли к сведению. Не ожидайте слишком многого."
            ]
            responses = arrogant_responses + responses

        if personality.get("wise", 0) > 7:
            wise_responses = [
                "Ветры перемен приносят ваши слова. Мы прислушаемся к ним.",
                "Как листья на дереве времени, ваше сообщение найдет свой ответ.",
                "Мудрость требует размышлений. Мы дадим ответ в должное время."
            ]
            responses = wise_responses + responses

        if personality.get("aggressive", 0) > 7:
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
                responses = [
                    f"{faction} не боится ваших угроз! Мы готовы к войне!",
                    f"Вы бросаете вызов не той фракции! Наши армии ждут!",
                    f"Угрозы? {faction} ответит сталью и кровью!"
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
        if any(word in message for word in ['ресурс', 'золот', 'кристал', 'еда', 'пищ']):
            if relation_level > 50:
                response = f"Наши ресурсы стабильны, но точные цифры - государственная тайна."
            else:
                response = f"{faction} не разглашает информацию о ресурсах так открыто."
        elif any(word in message for word in ['арми', 'войск', 'солдат', 'защит']):
            if relation_level > 60:
                response = f"Наша армия готова защищать интересы {faction}."
            else:
                response = f"Информация о нашей армии - военная тайна."
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

    def update_relations_based_on_message(self, player_message, ai_response, target_faction):
        """Обновляет отношения на основе обмена сообщениями"""
        try:
            relations = self.advisor.relations_manager.load_combined_relations()
            if target_faction not in relations:
                return

            current_relation = relations[target_faction]["relation_level"]

            # Анализ тона сообщений
            player_tone = self.analyze_message_tone(player_message)
            ai_tone = self.analyze_message_tone(ai_response)

            # Определяем изменение отношений
            relation_change = 0

            if player_tone == "positive" and ai_tone == "positive":
                relation_change = 5
            elif player_tone == "negative" and ai_tone == "negative":
                relation_change = -10
            elif player_tone == "positive" and ai_tone == "negative":
                relation_change = -5
            elif player_tone == "negative" and ai_tone == "positive":
                relation_change = -2

            # Обновляем отношения
            new_relation = max(0, min(100, current_relation + relation_change))

            if new_relation != current_relation:
                self.advisor.relations_manager.update_relation_in_db(target_faction, new_relation)
                print(f"Отношения с {target_faction} изменились: {current_relation} -> {new_relation}")

        except Exception as e:
            print(f"Ошибка при обновлении отношений: {e}")

    def analyze_message_tone(self, message):
        """Анализирует тон сообщения"""
        message_lower = message.lower()

        positive_words = ['спасибо', 'благодарю', 'прошу', 'пожалуйста', 'уважаем',
                          'ценю', 'рад', 'рады', 'отличн', 'прекрасн', 'замечательн']
        negative_words = ['угроз', 'уничтож', 'нападу', 'атакую', 'война', 'ненавижу',
                          'против', 'враг', 'смерть', 'уничтожу', 'раздавлю']

        positive_count = sum(1 for word in positive_words if word in message_lower)
        negative_count = sum(1 for word in negative_words if word in message_lower)

        if positive_count > negative_count:
            return "positive"
        elif negative_count > positive_count:
            return "negative"
        else:
            return "neutral"

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