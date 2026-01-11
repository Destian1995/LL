# ai_models/diplomacy_chat.py
import random

from kivy.uix.boxlayout import BoxLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.label import Label
from kivy.uix.button import Button

from kivy.uix.textinput import TextInput
from kivy.uix.spinner import Spinner
from kivy.graphics import Color, Rectangle, RoundedRectangle, Line
from kivy.core.window import Window, Animation
from kivy.metrics import dp
from kivy.clock import Clock
from datetime import datetime

from .nlp_processor import NaturalLanguageProcessor
from .manipulation_strategy import ManipulationStrategy


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

        self.faction_phrases = {
            "Эльфы": {
                "war_declaration": "Еще один решил что может гадить в наших лесах!",
                "alliance": "Природа восторжествует!",
                "peace": "Мир в лесах восстановлен.",
                "rejection": "Деревья шепчут об осторожности..."
            },
            "Север": {
                "war_declaration": "Грядет холодный ветер перемен...",
                "alliance": "Светлого неба!",
                "peace": "Да стихнет буря...",
                "rejection": "Снежная буря заставляет быть осторожным."
            },
            "Адепты": {
                "war_declaration": "Смерть еретикам!",
                "alliance": "Да хранит нас Бог!",
                "peace": "Божья воля исполнена.",
                "rejection": "Нам нужно время для молитвы."
            },
            "Элины": {
                "war_declaration": "Песок поглотит Вас...",
                "alliance": "Огонь пустыни защитит Вас!",
                "peace": "Знойный ветер утих.",
                "rejection": "В пустыне нужно взвешивать каждый шаг."
            },
            "Вампиры": {
                "war_declaration": "Что с головушкой совсем беда? Ну ничего....исправим..",
                "alliance": "Теплокровных оставьте нам...",
                "peace": "Кровь больше не будет проливаться.",
                "rejection": "Ночь еще не наступила для таких решений."
            }
        }

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
        main_area = BoxLayout(
            orientation='vertical',
            size_hint=(1, 0.85),
            spacing=dp(6),
            padding=[dp(10), dp(8)]
        )

        with main_area.canvas.before:
            Color(0.1, 0.1, 0.15, 1)
            bg = Rectangle(pos=main_area.pos, size=main_area.size)

        main_area.bind(
            pos=lambda i, v: setattr(bg, 'pos', v),
            size=lambda i, v: setattr(bg, 'size', v)
        )

        chat_area = BoxLayout(
            orientation='vertical',
            size_hint=(1, 1),
            spacing=dp(6)
        )

        self.chat_scroll = ScrollView(
            size_hint=(1, 1),
            do_scroll_x=False,
            bar_width=dp(6),
            scroll_type=['bars']
        )

        self.chat_container = BoxLayout(
            orientation='vertical',
            size_hint_y=None,
            spacing=dp(8),
            padding=[dp(10), dp(10)]
        )
        self.chat_container.bind(minimum_height=self.chat_container.setter('height'))

        self.chat_scroll.add_widget(self.chat_container)
        chat_area.add_widget(self.chat_scroll)
        chat_area.add_widget(self.create_input_panel())

        main_area.add_widget(chat_area)
        return main_area

    def create_input_panel(self):
        panel = BoxLayout(
            orientation='horizontal',
            size_hint=(1, None),
            height=dp(56),
            spacing=dp(10),
            padding=[dp(10), dp(8)]
        )

        with panel.canvas.before:
            Color(0.14, 0.14, 0.2, 1)
            bg = Rectangle(pos=panel.pos, size=panel.size)

        panel.bind(
            pos=lambda i, v: setattr(bg, 'pos', v),
            size=lambda i, v: setattr(bg, 'size', v)
        )

        self.message_input = TextInput(
            hint_text="Введите сообщение…",
            multiline=False,
            background_normal='',
            background_active='',
            background_color=(0.18, 0.18, 0.25, 1),
            foreground_color=(1, 1, 1, 1),
            cursor_color=(0.5, 0.7, 1, 1),
            padding=[dp(12), dp(12)],
            font_size='14sp'
        )

        with self.message_input.canvas.after:
            Color(0.3, 0.3, 0.4, 1)
            border = Line(rectangle=[*self.message_input.pos, *self.message_input.size], width=1)

        self.message_input.bind(
            pos=lambda i, v: setattr(border, 'rectangle', [*i.pos, *i.size]),
            size=lambda i, v: setattr(border, 'rectangle', [*i.pos, *i.size]),
            focus=lambda i, v: setattr(border, 'width', 2 if v else 1)
        )

        send_btn = Button(
            text="Отправить",
            size_hint=(None, 1),
            width=dp(120),
            background_normal='',
            background_color=(0.25, 0.5, 0.9, 1),
            font_size='14sp'
        )
        send_btn.bind(on_press=self.send_diplomatic_message)

        panel.add_widget(self.message_input)
        panel.add_widget(send_btn)
        return panel

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

        # Обновляем заголовок
        self.chat_status.text = f"Переписка с {faction}"

        # Обновляем статус отношений
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

    def _handle_context_reset(self, message, faction):
        """Обрабатывает команду сброса контекста чата"""
        # Сбрасываем контекст переговоров для этой фракции
        if faction in self.negotiation_context:
            # Полностью очищаем контекст
            self.negotiation_context[faction] = {
                "stage": "idle",
                "counter_offers": 0
            }

        # Очищаем активные переговоры для этой фракции
        if faction in self.active_negotiations:
            del self.active_negotiations[faction]

        # Очищаем текущие предложения
        if faction in self.current_offers:
            del self.current_offers[faction]

        # Добавляем сообщение о сбросе контекста
        reset_responses = [
            "Хорошо, забыли. Начинаем заново.",
            "Ладно, сбрасываю контекст. Говори что хотел.",
            "Забыл. Что там у тебя было?",
            "Контекст очищен. Можешь начать сначала.",
            "Принято. Забываю предыдущий разговор.",
            "Проехали. О чем ты хотел поговорить?."
        ]

        # В зависимости от отношений можно добавить разные ответы
        relations = self.advisor.relations_manager.load_combined_relations()
        relation_data = relations.get(faction, {"relation_level": 50})
        relation_level = int(relation_data.get("relation_level", 50))

        if relation_level >= 80:
            reset_responses.extend([
                "Как скажешь, друг. Начинаем с чистого листа!",
                "Хорошо, союзник. Забываю всё предыдущее.",
                "Понимаю. Иногда нужно начать заново. Забыто!"
            ])
        elif relation_level < 30:
            reset_responses.extend([
                "Ну ладно, забью. Только говори понятнее.",
                "Забыл. Только не морочь мне голову снова.",
                "Сбрасываю. И что теперь тебе нужно?"
            ])

        return random.choice(reset_responses)

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
        max_width = Window.width * 0.65

        temp = Label(
            text=message,
            font_size='13sp',
            text_size=(max_width - dp(24), None)
        )
        temp.texture_update()
        text_height = temp.texture_size[1]

        bubble = BoxLayout(
            orientation='vertical',
            size_hint=(None, None),
            width=min(max_width, temp.texture_size[0] + dp(30)),
            height=text_height + dp(36),
            padding=[dp(12), dp(10)],
            pos_hint={'right': 1} if is_player else {'x': 0}
        )

        bg_color = (0.22, 0.42, 0.8, 1) if is_player else (0.28, 0.28, 0.36, 1)

        with bubble.canvas.before:
            Color(*bg_color)
            bg = RoundedRectangle(pos=bubble.pos, size=bubble.size, radius=[dp(10)])

        bubble.bind(
            pos=lambda i, v: setattr(bg, 'pos', v),
            size=lambda i, v: setattr(bg, 'size', v)
        )

        text_label = Label(
            text=message,
            font_size='13sp',
            color=(1, 1, 1, 1),
            halign='left',
            valign='top',
            text_size=(bubble.width - dp(24), None)
        )
        text_label.bind(
            size=lambda i, v: setattr(i, 'text_size', (v[0], None))
        )

        time_label = Label(
            text=timestamp,
            font_size='10sp',
            color=(0.7, 0.7, 0.7, 1),
            size_hint=(1, None),
            height=dp(14),
            halign='right'
        )

        bubble.add_widget(text_label)
        bubble.add_widget(time_label)

        self.chat_container.add_widget(bubble)
        Clock.schedule_once(lambda dt: self.scroll_chat_to_bottom(), 0)

    def add_chat_message_system(self, message):
        box = BoxLayout(
            size_hint=(0.9, None),
            padding=[dp(12), dp(8)],
            pos_hint={'center_x': 0.5}
        )

        label = Label(
            text=message,
            font_size='12sp',
            color=(1, 1, 0.8, 1),
            halign='center',
            valign='middle',
            text_size=(Window.width * 0.8, None)
        )
        label.texture_update()
        box.height = label.texture_size[1] + dp(20)

        with box.canvas.before:
            Color(0.18, 0.18, 0.28, 1)
            bg = RoundedRectangle(pos=box.pos, size=box.size, radius=[dp(8)])

        box.bind(
            pos=lambda i, v: setattr(bg, 'pos', v),
            size=lambda i, v: setattr(bg, 'size', v)
        )

        box.add_widget(label)
        self.chat_container.add_widget(box)
        Clock.schedule_once(lambda dt: self.scroll_chat_to_bottom(), 0)

    def scroll_chat_to_bottom(self):
        """Прокручивает чат вниз - с плавной анимацией"""
        if self.chat_scroll and hasattr(self.chat_scroll, 'scroll_y'):
            try:
                # Используем анимацию для плавной прокрутки
                Animation(scroll_y=0, duration=0.3).start(self.chat_scroll)
            except:
                # Если анимация не работает, просто устанавливаем scroll_y
                self.chat_scroll.scroll_y = 0

    def send_diplomatic_message(self, instance):
        """Отправляет дипломатическое сообщение"""
        message = self.message_input.text.strip()
        if not message:
            return

        if not hasattr(self, 'selected_faction') or not self.selected_faction:
            self.add_chat_message_system("Сначала выберите фракцию для переписки!")
            return

        # ПРОВЕРКА: если игрок предлагает союз, проверяем ресурсы заранее
        message_lower = message.lower()
        if any(word in message_lower for word in ['союз', 'альянс', 'объединиться', 'сотрудничать']):
            # Проверяем стоимость альянса
            try:
                cursor = self.db_connection.cursor()
                # Получаем количество городов у целевой фракции
                cursor.execute("SELECT COUNT(*) FROM cities WHERE faction = ?", (self.selected_faction,))
                target_city_count = cursor.fetchone()[0]
                alliance_cost = 100_000 + (300_000 * target_city_count)

                # Проверяем, есть ли у игрока достаточно крон
                cursor.execute("SELECT amount FROM resources WHERE faction = ? AND resource_type = 'Кроны'",
                               (self.faction,))
                player_crowns = cursor.fetchone()

                if player_crowns is None or player_crowns[0] < alliance_cost:
                    self.add_chat_message_system(
                        f"⚠️ У вас недостаточно крон для предложения союза! "
                        f"Нужно {alliance_cost:,}, а у вас {player_crowns[0] if player_crowns else 0:,}."
                    )
                    self.message_input.text = ""
                    return
            except Exception as e:
                print(f"Ошибка при проверке стоимости альянса: {e}")

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
        """Генерирует ответ ИИ на сообщение игрока со всеми политическими функциями"""

        print(f"DEBUG: Получено сообщение: '{player_message}' от игрока")

        # Загружаем данные об отношениях
        relations = self.advisor.relations_manager.load_combined_relations()
        relation_data = relations.get(target_faction, {"relation_level": 50, "status": "нейтралитет"})
        relation_level = int(relation_data.get("relation_level", 50))
        status = relation_data.get('status', 'нейтралитет')

        message_lower = player_message.lower()
        if self._is_context_reset(player_message):
            return self._handle_context_reset(player_message, target_faction)

        # 1. Проверяем контекст переговоров
        context = self.negotiation_context.get(target_faction, {})
        if context.get("stage") in ("ask_resource_type", "ask_resource_amount",
                                    "ask_player_offer", "counter_offer", "evaluate"):
            forced = self._handle_forced_dialog(player_message, target_faction, context)
            if forced:
                return forced

        # 2. ПРОВЕРКА НА ВОПРОСЫ О ДЕЛАХ/СОСТОЯНИИ/РЕСУРСАХ/АРМИИ
        if self._is_status_inquiry(player_message):
            return self._generate_status_response(target_faction)

        # 3. ПРОВЕРКА НА ПРЕДЛОЖЕНИЯ СОЮЗА
        if self._is_alliance_proposal(player_message):
            return self._handle_alliance_proposal(player_message, target_faction, relation_level)

        # 4. ПРОВЕРКА НА ПРЕДЛОЖЕНИЯ МИРА
        if self._is_peace_proposal(player_message):
            return self._handle_peace_proposal(player_message, target_faction)

        # 5. ПРОВЕРКА НА ОБЪЯВЛЕНИЕ ВОЙНЫ
        if self._is_war_declaration(player_message):
            return self._handle_war_declaration(player_message, target_faction)

        # 6. ПРОВЕРКА НА ПОДСТРЕКАТЕЛЬСТВО/ПРОВОКАЦИЮ
        if self._is_provocation(player_message):
            return self._handle_provocation(player_message, target_faction, relation_level)

        # 7. ПРОВЕРКА НА РАЗРЫВ ОТНОШЕНИЙ
        if self._is_relationship_break(player_message):
            return self._handle_relationship_break(player_message, target_faction)

        # 8. УЛУЧШЕНИЕ: Автоматическая обработка запросов ресурсов с количеством
        # ПРОБЛЕМА: _extract_trade_offer не правильно парсит "50 тыс"
        # Вместо этого сначала пробуем извлечь данные напрямую
        print(f"DEBUG: Проверяем сообщение на прямой запрос ресурсов")

        # Сначала ищем прямой шаблон "мне [число] [ресурс]"
        import re

        # Шаблоны для прямого поиска
        direct_patterns = [
            r'(?:да\s+)?(?:мне|хочу|нужно|нужен|нужны|дай|дайте)\s+(?P<amount>[\d\sтысмил\.]+)\s*(?P<resource>крон|золот|деньг|кристалл|ресурс|рабоч|люд|работник)',
            r'(?:хочу|нужно|получить|взять|предоставь)\s+(?P<amount>[\d\sтысмил\.]+)\s+(?P<resource>крон|золот|деньг|кристалл|ресурс|рабоч|люд)',
        ]

        for pattern in direct_patterns:
            match = re.search(pattern, message_lower)
            if match:
                amount_str = match.group('amount').strip()
                resource_word = match.group('resource')

                # Преобразуем ресурс
                resource_map = {
                    'крон': 'Кроны', 'золот': 'Кроны', 'деньг': 'Кроны',
                    'кристалл': 'Кристаллы', 'ресурс': 'Кристаллы',
                    'рабоч': 'Рабочие', 'люд': 'Рабочие', 'работник': 'Рабочие'
                }

                resource_type = resource_map.get(resource_word, 'Кроны')

                # Парсим количество с поддержкой "тыс", "миллионов" и т.д.
                amount = self._extract_number_from_text(amount_str)

                if amount and amount > 0:
                    print(f"DEBUG: Найден прямой запрос: {amount} {resource_type}")
                    self.negotiation_context[target_faction] = {
                        "stage": "ask_player_offer",
                        "resource": resource_type,
                        "amount": amount,
                        "counter_offers": 0
                    }
                    return f"Хочешь {amount:,} {resource_type}? Что предлагаешь взамен?"

        # Старый метод как запасной вариант
        trade_offer = self._extract_trade_offer(player_message)
        if trade_offer:
            print(f"DEBUG: Найден готовый trade_offer: {trade_offer}")
            if trade_offer.get("amount"):
                self.negotiation_context[target_faction] = {
                    "stage": "ask_player_offer",
                    "resource": trade_offer["type"],
                    "amount": trade_offer["amount"],
                    "counter_offers": 0
                }
                return f"Хочешь {trade_offer['amount']:,} {trade_offer['type']}? Что предлагаешь взамен?"

        # 9. Обработка запросов ресурсов
        is_resource_req = self._is_resource_request(player_message)
        resource_mentions = self._extract_resource_mentions(player_message)

        if is_resource_req and resource_mentions:
            amount = self._extract_number(player_message)

            if amount:
                resource_type = resource_mentions[0]
                self.negotiation_context[target_faction] = {
                    "stage": "ask_player_offer",
                    "resource": resource_type,
                    "amount": amount,
                    "counter_offers": 0
                }
                return f"Хочешь {amount:,} {resource_type}? Что предлагаешь взамен?"
            else:
                resource_type = resource_mentions[0]
                self.negotiation_context[target_faction] = {
                    "stage": "ask_resource_amount",
                    "resource": resource_type,
                    "counter_offers": 0
                }
                return f"Сколько {resource_type} тебе нужно?"

        # 10. Определяем intent через NLP
        intent = self.nlp_processor.process_message(player_message, context)
        print(f"DEBUG: Определен intent: {intent.name} с уверенностью {intent.confidence}")

        # 11. Обработка интентов для торговли
        if intent.name in ("demand_resources", "trade_propose"):
            resource_mentions = self._extract_resource_mentions(player_message)
            if resource_mentions:
                resource_type = resource_mentions[0]
                amount = self._extract_number(player_message)

                if amount:
                    self.negotiation_context[target_faction] = {
                        "stage": "ask_player_offer",
                        "resource": resource_type,
                        "amount": amount,
                        "counter_offers": 0
                    }
                    return f"Хочешь {amount:,} {resource_type}? Что предлагаешь взамен?"
                else:
                    self.negotiation_context[target_faction] = {
                        "stage": "ask_resource_amount",
                        "resource": resource_type,
                        "counter_offers": 0
                    }
                    return f"Сколько {resource_type} тебе нужно?"
            else:
                self.negotiation_context[target_faction] = {
                    "stage": "ask_resource_type",
                    "counter_offers": 0
                }
                return "Какой ресурс тебе нужен: Кроны, Кристаллы или Рабочие?"

        # 12. Простые интенты
        simple_responses = {
            "greeting": self._get_greeting_response(target_faction, relation_level),
            "farewell": self._get_farewell_response(target_faction),
            "ask_status": [
                f"Наши отношения с тобой на уровне {relation_level}/100 ({status}).",
                f"Сейчас я отношусь к тебе {status}.",
                f"Уровень наших отношений: {relation_level}/100 - {status}."
            ],
            "thanks": ["Пожалуйста!", "Рад помочь!", "Не за что!", "Всегда к твоим услугам."],
            "insult": [
                "Я не буду отвечать на оскорбления.",
                "Давай вести переговоры конструктивно.",
                "Такие слова не помогут нашим отношениям."
            ],
            "threat": [
                "Угрозы не помогут в переговорах.",
                "Я не реагирую на угрозы.",
                "Ты хочешь испортить наши отношения?"
            ]
        }

        if intent.name in simple_responses:
            if isinstance(simple_responses[intent.name], list):
                return random.choice(simple_responses[intent.name])
            else:
                return simple_responses[intent.name]

        # 13. ФОЛБЭК
        return self._generate_fallback_response(player_message, target_faction, relation_level)

    def _extract_number_from_text(self, text):
        """Извлекает число из текста с поддержкой 'тыс', 'миллионов' и т.д."""
        import re

        text = text.lower().strip()

        # Удаляем точки в числах (1.000 -> 1000)
        text = re.sub(r'(\d)\.(\d)', r'\1\2', text)

        # Прямые сопоставления
        if 'тыс' in text:
            # Ищем число перед "тыс"
            match = re.search(r'(\d+)\s*тыс', text)
            if match:
                return int(match.group(1)) * 1000

        if 'миллион' in text or 'милл' in text:
            match = re.search(r'(\d+)\s*(?:миллион|милл)', text)
            if match:
                return int(match.group(1)) * 1000000

        # Просто число
        match = re.search(r'(\d+)', text)
        if match:
            return int(match.group(1))

        # Словарные числа
        word_numbers = {
            'один': 1, 'два': 2, 'три': 3, 'четыре': 4, 'пять': 5,
            'шесть': 6, 'семь': 7, 'восемь': 8, 'девять': 9, 'десять': 10,
            'сто': 100, 'тысяча': 1000, 'миллион': 1000000
        }

        for word, value in word_numbers.items():
            if word in text:
                return value

        return None

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
            background_normal='files/pict/sov/back.png',
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

        # === Заголовок (нужен для update_chat_header) ===
        self.chat_title = Label(
            text="Дипломатическая переписка",
            font_size='18sp',
            bold=True,
            color=(1, 1, 1, 1),
            halign='center'
        )
        self.chat_title.bind(size=self.chat_title.setter('text_size'))
        faction_info.add_widget(self.chat_title)

        # === Статус чата (нужен для update_chat_header) ===
        self.chat_status = Label(
            text="",
            font_size='14sp',
            color=(0.85, 0.85, 0.9, 1),
            halign='center'
        )
        self.chat_status.bind(size=self.chat_status.setter('text_size'))
        faction_info.add_widget(self.chat_status)

        # === Статус отношений (нужен для update_chat_header) ===
        self.relation_status = Label(
            text="",
            font_size='13sp',
            color=(0.7, 0.7, 0.8, 1),
            halign='center'
        )
        self.relation_status.bind(size=self.relation_status.setter('text_size'))
        faction_info.add_widget(self.relation_status)

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

        # Кнопка информации об отношениях
        info_button = Button(
            text="",
            size_hint=(None, None),
            size=(dp(40), dp(40)),
            background_normal='files/pict/sov/warning.png',
            background_color=(0.4, 0.4, 0.6, 1),
            border=(0, 0, 0, 0),
            on_press=self.show_relation_info
        )

        # Кнопка обновления
        refresh_button = Button(
            text="",
            size_hint=(None, None),
            size=(dp(40), dp(40)),
            background_normal='files/pict/sov/switch.png',
            background_color=(0.4, 0.4, 0.6, 1),
            border=(0, 0, 0, 0),
            on_press=lambda x: self.load_chat_history()
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
        """Извлекает число из сообщения - улучшенная версия с поддержкой тысяч, миллионов и т.д."""
        import re

        message_lower = message.lower()

        # 1. Сначала ищем простые цифры (100, 5000 и т.д.)
        numbers = re.findall(r'\d+', message_lower)
        if numbers:
            return int(numbers[0])

        # 2. Словарь числительных с поддержкой тысяч и миллионов
        numeral_map = {
            # Единицы
            'один': 1, 'одну': 1, 'одного': 1, 'одной': 1,
            'два': 2, 'две': 2, 'двух': 2,
            'три': 3, 'трёх': 3, 'трех': 3,
            'четыре': 4, 'четырёх': 4, 'четырех': 4,
            'пять': 5, 'пяти': 5,
            'шесть': 6, 'шести': 6,
            'семь': 7, 'семи': 7,
            'восемь': 8, 'восьми': 8,
            'девять': 9, 'девяти': 9,

            # Десятки
            'десять': 10, 'десяти': 10,
            'одиннадцать': 11, 'двенадцать': 12,
            'тринадцать': 13, 'четырнадцать': 14,
            'пятнадцать': 15, 'шестнадцать': 16,
            'семнадцать': 17, 'восемнадцать': 18,
            'девятнадцать': 19,

            # Круглые числа
            'двадцать': 20, 'тридцать': 30, 'сорок': 40,
            'пятьдесят': 50, 'шестьдесят': 60,
            'семьдесят': 70, 'восемьдесят': 80,
            'девяносто': 90,
            'сто': 100, 'двести': 200, 'триста': 300,
            'четыреста': 400, 'пятьсот': 500,
            'шестьсот': 600, 'семьсот': 700,
            'восемьсот': 800, 'девятьсот': 900,

            # Тысячи
            'тыс': 1000,
            'тысяча': 1000, 'тысячу': 1000, 'тысяч': 1000,
            'одна тысяча': 1000, 'две тысячи': 2000,
            'три тысячи': 3000, 'четыре тысячи': 4000,
            'пять тысяч': 5000, 'шесть тысяч': 6000,
            'семь тысяч': 7000, 'восемь тысяч': 8000,
            'девять тысяч': 9000,

            # Миллионы
            'миллион': 1000000, 'миллиона': 1000000, 'миллионов': 1000000,
            'один миллион': 1000000, 'два миллиона': 2000000,
            'три миллиона': 3000000, 'четыре миллиона': 4000000,
            'пять миллионов': 5000000, 'шесть миллионов': 6000000,
            'семь миллионов': 7000000, 'восемь миллионов': 8000000,
            'девять миллионов': 9000000,

            # Десятки миллионов
            'десять миллионов': 10000000,
            'одиннадцать миллионов': 11000000,
            'двадцать миллионов': 20000000,
            'тридцать миллионов': 30000000,
            'сорок миллионов': 40000000,
            'пятьдесят миллионов': 50000000,
            'сто миллионов': 100000000,

            # Неопределенные количества
            'немного': 100, 'немножко': 100, 'чуть-чуть': 50,
            'мало': 50, 'немного': 100, 'кучу': 1000,
            'массу': 1000, 'уйму': 1000, 'гору': 1000,
            'пару': 2, 'несколько': 5, 'десяток': 10,
            'дюжину': 12, 'сотню': 100
        }

        # 3. Проверяем составные числительные (например, "четыре тысячи")
        # Обрабатываем фразы вроде "четыре тысячи пятьсот"
        compound_patterns = [
            # Паттерн для "4 тысячи 500"
            r'(?P<number1>\d+)\s*(?P<multiplier>тысяч|миллионов)\s*(?P<number2>\d+)',
            # Паттерн для "четыре тысячи пятьсот"
            r'(?P<word1>один|две|три|четыре|пять|шесть|семь|восемь|девять)\s+(?P<multiplier_word>тысяч|тысячи|тысяча|миллионов|миллиона)\s+(?P<word2>\w+)',
        ]

        for pattern in compound_patterns:
            match = re.search(pattern, message_lower)
            if match:
                try:
                    # Для цифрового формата "4 тысячи 500"
                    if 'number1' in match.groupdict():
                        num1 = int(match.group('number1'))
                        num2 = int(match.group('number2'))
                        multiplier = match.group('multiplier')

                        if 'тысяч' in multiplier:
                            return num1 * 1000 + num2
                        elif 'миллионов' in multiplier:
                            return num1 * 1000000 + num2

                    # Для словесного формата "четыре тысячи пятьсот"
                    elif 'word1' in match.groupdict():
                        word_to_num = {
                            'один': 1, 'две': 2, 'три': 3, 'четыре': 4,
                            'пять': 5, 'шесть': 6, 'семь': 7, 'восемь': 8,
                            'девять': 9
                        }

                        num1 = word_to_num.get(match.group('word1'), 0)
                        multiplier_word = match.group('multiplier_word')
                        word2 = match.group('word2')

                        # Преобразуем вторую часть
                        for word, value in numeral_map.items():
                            if word in word2:
                                num2 = value
                                break
                        else:
                            num2 = 0

                        if 'тысяч' in multiplier_word or 'тысяча' in multiplier_word or 'тысячи' in multiplier_word:
                            return num1 * 1000 + num2
                        elif 'миллион' in multiplier_word:
                            return num1 * 1000000 + num2
                except:
                    pass

        # 4. Проверяем отдельные слова и простые комбинации
        words = message_lower.split()

        # Проверяем комбинации вроде "4 тысячи"
        for i in range(len(words) - 1):
            word1 = words[i]
            word2 = words[i + 1]

            # Проверяем цифру + множитель
            if word1.isdigit():
                num = int(word1)
                if 'тысяч' in word2 or 'тысяча' in word2:
                    return num * 1000
                elif 'миллион' in word2:
                    return num * 1000000

            # Проверяем словесную комбинацию
            word_to_num_small = {
                'один': 1, 'две': 2, 'три': 3, 'четыре': 4,
                'пять': 5, 'шесть': 6, 'семь': 7, 'восемь': 8,
                'девять': 9, 'десять': 10
            }

            if word1 in word_to_num_small:
                num = word_to_num_small[word1]
                if 'тысяч' in word2 or 'тысяча' in word2:
                    return num * 1000
                elif 'миллион' in word2:
                    return num * 1000000

        # 5. Проверяем отдельные слова из словаря
        for numeral, value in numeral_map.items():
            if numeral in message_lower:
                return value

        # 6. Проверяем отдельные слова в сообщении
        for word in words:
            if word in numeral_map:
                return numeral_map[word]

        return None

    def _extract_resource_request_full(self, message):
        """Полностью извлекает информацию о запросе ресурсов с поддержкой любых числительных"""
        message_lower = message.lower()

        # Ресурсы для поиска
        resource_patterns = {
            r'крон': 'Кроны',
            r'золот': 'Кроны',
            r'деньг': 'Кроны',
            r'монет': 'Кроны',
            r'кристалл': 'Кристаллы',
            r'минерал': 'Кристаллы',
            r'ресурс': 'Кристаллы',
            r'рабоч': 'Рабочие',
            r'люд': 'Рабочие',
            r'крестьян': 'Рабочие',
            r'работник': 'Рабочие',
            r'арми': 'Солдаты',
            r'солдат': 'Солдаты',
            r'войск': 'Солдаты',
            r'воин': 'Солдаты'
        }

        # Ищем ресурс
        found_resource = None
        for pattern, resource in resource_patterns.items():
            if re.search(pattern, message_lower):
                found_resource = resource
                break

        if not found_resource:
            return None

        # Извлекаем количество с помощью улучшенного метода
        amount = self._extract_number(message)

        return {
            'type': found_resource,
            'amount': amount if amount else None
        }

    def _extract_trade_info_enhanced(self, message):
        """Улучшенное извлечение информации о торговом предложении"""
        message_lower = message.lower()

        # Паттерны для поиска торговых предложений
        patterns = [
            # "дай 100 крон"
            r'(?:дай|дайте|хочу|нужно|нужны|нужен|необходимо)\s+(?P<amount>\d+)\s+(?P<type>крон|золот|кристалл|ресурс|рабоч|люд)',
            # "мне нужно 500 кристаллов"
            r'(?:мне|нам)\s+(?:нужно|нужны|необходимо)\s+(?P<amount>\d+)\s+(?P<type>крон|золот|кристалл|ресурс|рабоч|люд)',
            # "хочу получить 200 рабочих"
            r'(?:хочу|желаю|хотел|хотела)\s+(?:получить|приобрести|взять)\s+(?P<amount>\d+)\s+(?P<type>крон|золот|кристалл|ресурс|рабоч|люд)'
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

                amount = int(match.group('amount'))
                resource_type = resource_map.get(match.group('type'), 'Кроны')

                return {
                    'type': resource_type,
                    'amount': amount
                }

        return None

    def _extract_trade_offer(self, message):
        """Извлекает торговое предложение из сообщения - УЛУЧШЕННЫЙ ВАРИАНТ"""
        import re

        message_lower = message.lower()

        # Словарь соответствий ресурсов
        resource_map = {
            'крон': 'Кроны', 'кронн': 'Кроны', 'золот': 'Кроны', 'деньг': 'Кроны',
            'кристалл': 'Кристаллы', 'кристал': 'Кристаллы', 'минерал': 'Кристаллы',
            'рабоч': 'Рабочие', 'люд': 'Рабочие', 'работник': 'Рабочие'
        }

        # Ищем тип ресурса
        resource_type = None
        for key, resource in resource_map.items():
            if key in message_lower:
                resource_type = resource
                break

        if not resource_type:
            return None

        # Используем новый метод для парсинга чисел
        amount = self._extract_number_from_text(message_lower)

        if amount is None:
            # Пробуем старый метод как запасной вариант
            amount = self._extract_number(message_lower)

        if amount is None or amount <= 0:
            return None

        return {
            "type": resource_type,
            "amount": amount
        }

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
                return f"Согласен! Если не возникнет форс-мажора, жди поставки через день."
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

    def _is_status_inquiry(self, message):
        """Определяет, является ли сообщение запросом о делах/состоянии"""
        inquiry_keywords = [
            'как дела', 'как ты', 'как ваши дела', 'что нового', 'как твои дела', 'ты как',
            'как поживаешь', 'как жизнь', 'как успехи', 'что по войскам',
            'как армия', 'какие ресурсы', 'сколько войск', 'сила армии',
            'ресурсы есть', 'есть ли войска', 'мощь', 'могущество', 'что у тебя с ресурсами',
            'состояние', 'положение', 'обстановка', 'ситуация', 'что с ресурсами', 'какие у тебя ресурсы'
        ]

        message_lower = message.lower()
        return any(keyword in message_lower for keyword in inquiry_keywords)

    def _generate_status_response(self, faction):
        """Генерирует ответ о состоянии дел фракции"""
        try:
            cursor = self.db_connection.cursor()

            # 1. Получаем ресурсы
            resources = {}
            cursor.execute("""
                SELECT resource_type, amount FROM resources 
                WHERE faction = ? AND resource_type IN ('Кроны', 'Кристаллы', 'Рабочие')
            """, (faction,))
            for res_type, amount in cursor.fetchall():
                resources[res_type] = amount

            # 2. Рассчитываем силу армии
            army_strength = self._calculate_army_strength(faction)

            # 3. Получаем количество городов
            cursor.execute("SELECT COUNT(*) FROM cities WHERE faction = ?", (faction,))
            city_count = cursor.fetchone()[0]

            # 4. Получаем текущие отношения
            relations = self.advisor.relations_manager.load_combined_relations()
            relation_data = relations.get(self.faction, {"relation_level": 50, "status": "нейтралитет"})
            relation_level = relation_data.get("relation_level", 50)

            # 5. Формируем ответ
            responses = [
                f"Дела идут своим чередом. У нас {city_count} городов, армия силой {army_strength:,}. "
                f"Ресурсы: {resources.get('Кроны', 0):,} крон, {resources.get('Кристаллы', 0):,} кристаллов, "
                f"{resources.get('Рабочие', 0):,} рабочих.",

                f"Все под контролем. Владеем {city_count} поселениями, военная мощь - {army_strength:,}. "
                f"Казна: {resources.get('Кроны', 0):,}, минералы: {resources.get('Кристаллы', 0):,}, "
                f"рабочие руки: {resources.get('Рабочие', 0):,}.",

                f"Ситуация стабильна. {city_count} городов под нашей властью, армия в {army_strength:,} мощи. "
                f"Ресурсы позволяют нам развиваться."
            ]

            return random.choice(responses)

        except Exception as e:
            print(f"Ошибка при генерации статуса: {e}")
            return "Дела идут своим чередом. Что конкретно тебя интересует?"

    def _calculate_army_strength(self, faction):
        """Рассчитывает силу армии фракции"""
        try:
            cursor = self.db_connection.cursor()

            cursor.execute("""
                SELECT g.unit_name, g.unit_count, u.attack, u.defense, u.durability, u.unit_class 
                FROM garrisons g
                JOIN units u ON g.unit_name = u.unit_name
                WHERE u.faction = ?
            """, (faction,))
            units_data = cursor.fetchall()

            total_strength = 0
            class_1_count = 0
            hero_bonus = 0
            others_stats = 0

            for unit_name, unit_count, attack, defense, durability, unit_class in units_data:
                stats_sum = attack + defense + durability

                if unit_class == "1":
                    class_1_count += unit_count
                    total_strength += stats_sum * unit_count
                elif unit_class in ("2", "3"):
                    hero_bonus += stats_sum * unit_count
                else:
                    others_stats += stats_sum * unit_count

            if class_1_count > 0:
                total_strength += hero_bonus * class_1_count

            total_strength += others_stats

            return total_strength

        except Exception as e:
            print(f"Ошибка при расчете силы армии: {e}")
            return 0

    def _is_alliance_proposal(self, message):
        """Определяет, является ли сообщение предложением союза"""
        alliance_keywords = [
            'союз', 'альянс', 'объединиться', 'сотрудничать',
            'вместе', 'союзники', 'дружить', 'помогать друг другу',
            'заключить союз', 'создать альянс', 'стать союзниками',
            'общий союз', 'военный союз', 'договор о союзе'
        ]

        message_lower = message.lower()
        return any(keyword in message_lower for keyword in alliance_keywords)



    def _handle_alliance_proposal(self, message, faction, relation_level):
        """Обрабатывает предложение союза с разнообразными репликами"""
        try:
            cursor = self.db_connection.cursor()

            # Проверяем существующий союз
            cursor.execute("""
                SELECT COUNT(*) FROM diplomacies 
                WHERE ((faction1 = ? AND faction2 = ?) OR (faction1 = ? AND faction2 = ?)) 
                AND relationship = 'союз'
            """, (self.faction, faction, faction, self.faction))

            if cursor.fetchone()[0] > 0:
                existing_alliance_responses = [
                    "У нас уже есть действующий союз! Зачем его заключать снова?",
                    "Ты что, забыл? Мы уже союзники!",
                    "Наш союз и так действует. Ты проверяешь мою память?",
                    "Мы уже связаны договором. Хочешь укрепить его дополнительными клятвами?"
                ]
                return random.choice(existing_alliance_responses)

            # Проверяем уровень отношений и выбираем соответствующие реплики
            if relation_level >= 90:
                # Получаем количество городов у целевой фракции
                cursor.execute("SELECT COUNT(*) FROM cities WHERE faction = ?", (faction,))
                target_city_count = cursor.fetchone()[0]

                # Стоимость альянса
                alliance_cost = 100_000 + (300_000 * target_city_count)

                # Проверяем, есть ли у игрока достаточно крон
                cursor.execute("SELECT amount FROM resources WHERE faction = ? AND resource_type = 'Кроны'",
                               (self.faction,))
                player_crowns = cursor.fetchone()

                if player_crowns is None or player_crowns[0] < alliance_cost:
                    insufficient_responses = [
                        f"У тебя недостаточно крон для заключения союза! Нужно {alliance_cost:,}, а у тебя всего {player_crowns[0] if player_crowns else 0:,}.",
                        f"Сначала накопи {alliance_cost:,} крон, тогда поговорим о союзе. У тебя сейчас {player_crowns[0] if player_crowns else 0:,}.",
                        f"Союз стоит {alliance_cost:,} крон. Проверь свою казну!",
                        f"Без {alliance_cost:,} крон в казне союз невозможен."
                    ]
                    return random.choice(insufficient_responses)

                # Союзнические отношения (90-100)
                alliance_responses = [
                    "С радостью принимаю предложение! Наши народы станут едины!",
                    "Наконец-то! Я ждал этого момента. Союз заключён!",
                    "Это исторический день! Отныне наши судьбы переплетены навеки!",
                    "Сердце моё ликует! Принимаю твоё предложение о союзе без колебаний!"
                ]

                # СПИСЫВАЕМ КРОНЫ У ИГРОКА
                cursor.execute("""
                    UPDATE resources 
                    SET amount = amount - ? 
                    WHERE faction = ? AND resource_type = 'Кроны'
                """, (alliance_cost, self.faction))

                # ОБНОВЛЯЕМ ОТНОШЕНИЯ В ДИПЛОМАЦИЯХ
                cursor.execute("""
                    UPDATE diplomacies 
                    SET relationship = 'союз' 
                    WHERE (faction1 = ? AND faction2 = ?) OR (faction1 = ? AND faction2 = ?)
                """, (self.faction, faction, faction, self.faction))

                # ОБНОВЛЯЕМ ОТНОШЕНИЯ В RELATIONS
                cursor.execute("""
                    UPDATE relations 
                    SET relationship = 100 
                    WHERE (faction1 = ? AND faction2 = ?) OR (faction1 = ? AND faction2 = ?)
                """, (self.faction, faction, faction, self.faction))

                # Создаем запись в trade_agreements как подтверждение союза
                cursor.execute("""
                    INSERT INTO trade_agreements 
                    (initiator, target_faction, initiator_type_resource, initiator_summ_resource,
                     target_type_resource, target_summ_resource, agree, agreement_type, timestamp)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))
                """, (
                    self.faction, faction, "Союз", alliance_cost,
                    "Согласие", 1, 1, "alliance"  # agree = 1 (принято)
                ))

                # Добавляем запись в историю переговоров
                cursor.execute("""
                    INSERT INTO negotiation_history 
                    (faction1, faction2, message, is_player, timestamp)
                    VALUES (?, ?, ?, ?, datetime('now'))
                """, (self.faction, faction, f"Заключён союз! Стоимость: {alliance_cost:,} крон.", 0))

                self.db_connection.commit()

                # Получаем фразу для фракции
                phrase = self.faction_phrases.get(faction, {}).get("alliance", "Союз заключён!")

                response = random.choice(alliance_responses)
                return f"{phrase} {response} Союз заключён! С твоей казны списано {alliance_cost:,} крон."

            elif 75 <= relation_level < 90:
                # Получаем количество городов для информации
                cursor.execute("SELECT COUNT(*) FROM cities WHERE faction = ?", (faction,))
                target_city_count = cursor.fetchone()[0]
                alliance_cost = 100_000 + (300_000 * target_city_count)

                # Очень дружественные отношения (75-89)
                friendly_responses = [
                    f"Друг, мы должны сильнее доверять друг другу, тогда союз будет крепким. Он обойдётся тебе в {alliance_cost:,} крон.",
                    f"Твоё предложение лестно, но давай сначала укрепим наше взаимное доверие. Союз стоит {alliance_cost:,} крон.",
                    f"Мы на верном пути! Ещё немного, и наши знамёна сольются воедино. Будь готов заплатить {alliance_cost:,} крон.",
                    f"Сердце говорит 'да', но разум советует немного подождать. Укрепим дружбу, а потом поговорим о союзе за {alliance_cost:,} крон."
                ]
                return random.choice(friendly_responses)

            elif 50 <= relation_level < 75:
                # Получаем количество городов для информации
                cursor.execute("SELECT COUNT(*) FROM cities WHERE faction = ?", (faction,))
                target_city_count = cursor.fetchone()[0]
                alliance_cost = 100_000 + (300_000 * target_city_count)

                # Дружественные отношения (50-74)
                neutral_responses = [
                    f"Приятель, пока рано говорить о союзе. Для начала {alliance_cost:,} крон нужно накопить.",
                    f"Интересное предложение, но спешить не стоит. Союз стоит {alliance_cost:,} крон - серьёзная сумма.",
                    f"Союз — серьёзный шаг. Начнём с малого, а там посмотрим. Кстати, цена вопроса: {alliance_cost:,} крон.",
                    f"Ты забегаешь вперёд, друг мой. Сначала докажи, что нам можно доверять. И накопи {alliance_cost:,} крон."
                ]
                return random.choice(neutral_responses)

            elif 30 <= relation_level < 50:
                # Напряжённые отношения (30-49)
                tense_responses = [
                    "Не сказал бы, что в данный момент нас интересуют подобные предложения.",
                    "Ты серьёзно? Сейчас не самое подходящее время для таких разговоров.",
                    "Наши отношения ещё не готовы к подобным серьёзным шагам.",
                    "Пока не чувствую достаточного доверия для заключения союза. Давай сначала наладим отношения."
                ]
                return random.choice(tense_responses)

            elif 15 <= relation_level < 30:
                # Плохие отношения (15-29)
                bad_responses = [
                    "Я скорее башку в осиное гнездо засуну, чем заключу союз с тобой!",
                    "Да лучше я себя кастрирую тупыми ножницами!",
                    "Мои предки в гробу перевернулись бы от такого предложения!",
                    "Союз с тобой? Я лучше с голодным медведем в берлоге заночую!"
                ]
                return random.choice(bad_responses)

            else:
                # Враждебные отношения (0-14)
                hostile_responses = [
                    "Вы там ещё не сдохли? Ну ничего, мы это исправим!",
                    "Шутите что-ли? Ничего мы знаем что с такими шутниками делать.",
                    "Неужели вы действительно в таком отчаянном положении чтобы обращаться к нам за союзом?",
                    "Я сейчас кому-то в лицо плюну."
                ]
                return random.choice(hostile_responses)

        except Exception as e:
            print(f"Ошибка при обработке предложения союза: {e}")
            error_responses = [
                "Что-то пошло не так при обработке твоего предложения.",
                "Мои советники сообщают о технических неполадках. Повтори позже.",
                "Сейчас не могу обработать твоё предложение. Попробуй ещё раз.",
                "Система дала сбой. Давай обсудим это в другой раз."
            ]
            return random.choice(error_responses)

    def _is_peace_proposal(self, message):
        """Определяет, является ли сообщение предложением мира"""
        peace_keywords = [
            'мир', 'перемирие', 'закончить войну', 'прекратить войну',
            'договор о мире', 'заключить мир', 'прекратить боевые действия',
            'остановить войну', 'мирный договор', 'примирение'
        ]

        message_lower = message.lower()
        return any(keyword in message_lower for keyword in peace_keywords)

    def _handle_peace_proposal(self, message, faction):
        """Обрабатывает предложение мира с разнообразными репликами"""
        try:
            cursor = self.db_connection.cursor()

            # Проверяем текущие отношения
            cursor.execute("""
                SELECT relationship FROM diplomacies 
                WHERE (faction1 = ? AND faction2 = ?) OR (faction1 = ? AND faction2 = ?)
            """, (self.faction, faction, faction, self.faction))

            result = cursor.fetchone()
            if not result or result[0] != "война":
                no_war_responses = [
                    "Мы с тобой и так не воюем. Зачем мир?",
                    "Ты что, не в курсе? Между нами нет войны!",
                    "Мир? Но мы и так не сражаемся!",
                    "Какая война? У нас и так тишина."
                ]
                return random.choice(no_war_responses)

            # Рассчитываем силы армий
            player_strength = self._calculate_army_strength(self.faction)
            enemy_strength = self._calculate_army_strength(faction)

            if player_strength == 0 and enemy_strength > 0:
                player_weak_responses = [
                    "Обойдёшься. Сейчас я отыграюсь по полной.",
                    "Ты без армии, а у меня войска есть. Какие могут быть переговоры?",
                    "Сначала собери хоть какую-то армию, тогда и поговорим о мире.",
                    "Мир предлагает тот, у кого есть сила. А у тебя её нет."
                ]
                return random.choice(player_weak_responses)

            # Если у противника нет армии
            if enemy_strength == 0 and player_strength >= enemy_strength:
                cursor.execute("""
                    UPDATE diplomacies SET relationship = 'нейтралитет' 
                    WHERE (faction1 = ? AND faction2 = ?) OR (faction1 = ? AND faction2 = ?)
                """, (self.faction, faction, faction, self.faction))
                self.db_connection.commit()

                enemy_weak_responses = [
                    "Мы согласны на мир! Нам пока и воевать-то нечем...",
                    "Что ж... раз армии нет, приходится соглашаться. Мир!",
                    "Без войск сопротивляться нечем. Принимаем твоё предложение о мире.",
                    "С мечом у груди не спорят. Мир заключён по твоей милости."
                ]
                return random.choice(enemy_weak_responses)

            # Если превосходство игрока
            if player_strength > enemy_strength:
                superiority = ((player_strength - enemy_strength) / max(enemy_strength, 1)) * 100

                if superiority >= 70:
                    crushing_superiority_responses = [
                        "Ваша милость наконец соизволила нас пощадить...",
                        "Мы разбиты вдребезги. Соглашаемся на мир, пока ещё живы.",
                        "Перед такой мощью не устоять. Принимаем твои условия.",
                        "Когда противник сильнее вдесятеро, о победе не мечтают. Мир."
                    ]
                    response = random.choice(crushing_superiority_responses)
                elif 50 <= superiority < 70:
                    strong_superiority_responses = [
                        "Мы уже сдаёмся, что Вам ещё надо?...",
                        "Силы слишком неравны. Заключаем мир на твоих условиях.",
                        "Продолжать сопротивление - самоубийство. Согласны на мир.",
                        "Твоё превосходство очевидно. Принимаем предложение."
                    ]
                    response = random.choice(strong_superiority_responses)
                elif 20 <= superiority < 50:
                    moderate_superiority_responses = [
                        "У нас не осталось тех, кто готов сопротивляться...",
                        "Потери слишком велики. Лучше мир, чем полное уничтожение.",
                        "Ещё немного, и нас не останется. Заключаем мир.",
                        "Силы на исходе. Вынуждены принять твоё предложение."
                    ]
                    response = random.choice(moderate_superiority_responses)
                elif 5 <= superiority < 20:
                    slight_superiority_responses = [
                        "Это геноцид... мы вряд ли когда-то сможем воевать...",
                        "Едва держимся. Мир - единственный шанс выжить.",
                        "Капля переполнила чашу. Соглашаемся на перемирие.",
                        "Ещё один удар - и нас не станет. Принимаем мир."
                    ]
                    response = random.choice(slight_superiority_responses)
                else:
                    minimal_superiority_responses = [
                        "В следующий раз мы будем лучше готовы.",
                        "Отступаем, но не сдаёмся. Мир - лишь передышка.",
                        "Сейчас вы сильнее, но это временно. Заключаем перемирие.",
                        "Уступаем поле боя. Но война ещё не окончена."
                    ]
                    response = random.choice(minimal_superiority_responses)

                cursor.execute("""
                    UPDATE diplomacies SET relationship = 'нейтралитет' 
                    WHERE (faction1 = ? AND faction2 = ?) OR (faction1 = ? AND faction2 = ?)
                """, (self.faction, faction, faction, self.faction))
                self.db_connection.commit()

                return response

            # Если превосходство врага
            elif player_strength < enemy_strength:
                inferiority = ((enemy_strength - player_strength) / max(player_strength, 1)) * 100

                if inferiority <= 15:
                    slight_inferiority_responses = [
                        "Может Вы и правы, но мы ещё готовы продолжать сопротивление...",
                        "Не время для мира! Мы ещё можем дать бой.",
                        "Победа не так уж и далека. Отказываемся от перемирия.",
                        "Слишком рано сдаваться. Битва продолжается!"
                    ]
                    return random.choice(slight_inferiority_responses)
                else:
                    strong_inferiority_responses = [
                        "Уже сдаётесь?! Мы ещё не закончили Вас бить!",
                        "Победа близка! Зачем нам мир сейчас?",
                        "Вы на грани поражения! Сами предлагайте капитуляцию.",
                        "Мир? Только после вашей безоговорочной капитуляции!"
                    ]
                    return random.choice(strong_inferiority_responses)
            else:
                equal_responses = [
                    "Сейчас передохнём и в рыло дадим!",
                    "Никто не побеждён! Зачем прекращать битву?",
                    "Равные силы - лучший повод продолжить сражение!",
                    "Исход не ясен. Битва должна решиться!"
                ]
                return random.choice(equal_responses)

        except Exception as e:
            print(f"Ошибка при обработке предложения мира: {e}")
            error_responses = [
                "Что-то пошло не так при рассмотрении твоего предложения.",
                "Мои полководцы не могут дать ответ. Попробуй позже.",
                "В ставке разлад. Не могу принять решение сейчас.",
                "Ситуация неясна. Не могу ответить на твоё предложение."
            ]
            return random.choice(error_responses)

    def _is_war_declaration(self, message):
        """Определяет, является ли сообщение объявлением войны"""
        war_keywords = [
            'война', 'объявить войну', 'напасть', 'атаковать',
            'вторгнуться', 'воевать', 'военные действия',
            'уничтожить', 'разгромить', 'сокрушить', 'битва',
            'конфликт', 'столкновение', 'военный конфликт'
        ]

        message_lower = message.lower()
        return any(keyword in message_lower for keyword in war_keywords)

    def _handle_war_declaration(self, message, faction):
        """Обрабатывает объявление войны с разнообразными репликами"""
        try:
            cursor = self.db_connection.cursor()

            # Проверяем текущий ход
            cursor.execute("SELECT turn_count FROM turn")
            turn_result = cursor.fetchone()
            if turn_result is None or turn_result[0] < 14:
                early_turn_responses = [
                    "Слишком рано для войны. Подожди 14-го хода.",
                    "Ещё не время начинать войны. Давай подождём 14 ходов.",
                    "Потерпи до 14-го хода. Тогда и поговорим о войне.",
                    "Рано размахивать мечами. Сначала окрепнем."
                ]
                return random.choice(early_turn_responses)

            # Проверяем текущие отношения
            cursor.execute("""
                SELECT relationship FROM diplomacies 
                WHERE (faction1 = ? AND faction2 = ?) OR (faction1 = ? AND faction2 = ?)
            """, (self.faction, faction, faction, self.faction))

            result = cursor.fetchone()
            if result and result[0] == "война":
                already_war_responses = [
                    "Мы с тобой уже воюем! Ты что, забыл?",
                    "Война уже идёт! Ты опоздал с объявлением.",
                    "Наши мечи уже скрестились! Не нужно повторных объявлений.",
                    "Битва продолжается. Зачем объявлять войну дважды?"
                ]
                return random.choice(already_war_responses)

            # Объявляем войну
            cursor.execute("""
                UPDATE diplomacies 
                SET relationship = 'война' 
                WHERE (faction1 = ? AND faction2 = ?) OR (faction1 = ? AND faction2 = ?)
            """, (self.faction, faction, faction, self.faction))

            cursor.execute("""
                UPDATE relations 
                SET relationship = 0 
                WHERE (faction1 = ? AND faction2 = ?) OR (faction1 = ? AND faction2 = ?)
            """, (self.faction, faction, faction, self.faction))

            self.db_connection.commit()

            # Получаем фразу для фракции
            phrases = self.faction_phrases.get(faction, {})
            war_phrase = phrases.get("war_declaration", f"Война объявлена против {faction}!")

            # Дополнительные вариации в зависимости от фракции
            faction_war_responses = {
                "Эльфы": [
                    "Ты осквернил наши леса в последний раз!",
                    "Природа восстанет против тебя!",
                    "Деревья запомнят твоё предательство!",
                    "Ты разбудил древний гнев леса!"
                ],
                "Север": [
                    "Холодная смерть найдёт тебя!",
                    "Ледяной ветер выдует твою жизнь!",
                    "Мороз скрепил наши клинки!",
                    "Зима пришла за твоей душой!"
                ],
                "Адепты": [
                    "Ересь будет сожжена!",
                    "Бог покарает тебя через нашу руку!",
                    "Священная война началась!",
                    "Очистим мир от неверного!"
                ],
                "Элины": [
                    "Песок поглотит твои кости!",
                    "Зной пустыни иссушит твою кровь!",
                    "Огонь пустыни сожжёт тебя!",
                    "Ветер унесёт память о тебе!"
                ],
                "Вампиры": [
                    "Твоя кровь будет нашей!",
                    "Ночь вечной тьмы настала для тебя!",
                    "Ты станешь нашей вечной игрушкой!",
                    "Кровная вражда началась!"
                ]
            }

            # Добавляем случайную реплику для фракции
            faction_responses = faction_war_responses.get(faction, [])
            if faction_responses:
                additional_response = random.choice(faction_responses)
                return f"{war_phrase} {additional_response}"

            return war_phrase

        except Exception as e:
            print(f"Ошибка при объявлении войны: {e}")
            error_responses = [
                "Что-то пошло не так при объявлении войны.",
                "Моя канцелярия не смогла обработать объявление.",
                "Войну объявить не удалось. Попробуй позже.",
                "Не могу начать войну сейчас. Что-то мешает."
            ]
            return random.choice(error_responses)

    def _is_provocation(self, message):
        """Определяет, является ли сообщение подстрекательством"""
        provocation_keywords = [
            'напади на', 'атакуй', 'уничтожь', 'разгроми',
            'воевать с', 'напасть на', 'атаковать', 'убить',
            'устранить', 'ликвидировать', 'подстрекать',
            'спровоцировать', 'спровоцируй', 'спровоцируйте'
        ]

        message_lower = message.lower()

        # Проверяем наличие ключевых слов провокации
        has_provocation = any(keyword in message_lower for keyword in provocation_keywords)

        # Проверяем, упоминается ли третья фракция
        all_factions = ["Север", "Эльфы", "Адепты", "Вампиры", "Элины"]
        mentioned_factions = [f for f in all_factions if f.lower() in message_lower and f != self.faction]

        return has_provocation and len(mentioned_factions) > 0

    def _handle_provocation(self, message, faction, relation_level):
        """Обрабатывает подстрекательство"""
        try:
            # Извлекаем упомянутую фракцию
            all_factions = ["Север", "Эльфы", "Адепты", "Вампиры", "Элины"]
            mentioned_factions = [f for f in all_factions if f.lower() in message.lower() and f != self.faction]

            if not mentioned_factions:
                return "На кого именно ты предлагаешь напасть?"

            target_faction = mentioned_factions[0]

            # Проверяем отношения с целевой фракцией
            cursor = self.db_connection.cursor()
            cursor.execute("""
                SELECT relationship FROM relations 
                WHERE (faction1 = ? AND faction2 = ?) OR (faction1 = ? AND faction2 = ?)
            """, (faction, target_faction, target_faction, faction))

            result = cursor.fetchone()
            target_relation = result[0] if result else 50

            # Проверяем наши отношения с подстрекателем
            if relation_level < 30:
                return "Ты думаешь, я буду слушать твои провокации? У нас с тобой плохие отношения."

            # Анализируем выгоду
            if target_relation < 30:
                # Если и так плохие отношения с целью
                responses = [
                    f"С {target_faction} у нас и так напряженные отношения. Но зачем мне нападать первым?",
                    f"Ты хочешь, чтобы я начал войну с {target_faction}? Что ты предлагаешь взамен?",
                    f"{target_faction} и так нам не друг. Но начинать войну без причины - глупо."
                ]
                return random.choice(responses)
            elif 30 <= target_relation < 60:
                # Нейтральные отношения
                if relation_level > 70:
                    responses = [
                        f"С {target_faction} у нас нейтральные отношения. Зачем их портить?",
                        f"Ты предлагаешь мне поссориться с {target_faction}? Это рискованно.",
                        f"Напасть на {target_faction}? Мне нужно подумать о последствиях."
                    ]
                else:
                    responses = [
                        f"Я не настолько тебе доверяю, чтобы идти на войну с {target_faction}.",
                        f"Твои провокации против {target_faction} кажутся мне подозрительными.",
                        f"Зачем тебе нужно, чтобы я воевал с {target_faction}? Что ты задумал?"
                    ]
                return random.choice(responses)
            else:
                # Хорошие отношения с целью
                responses = [
                    f"С {target_faction} у нас хорошие отношения! Я не собираюсь их портить.",
                    f"Ты предлагаешь мне предать {target_faction}? Это недостойно.",
                    f"{target_faction} - наш друг. Я не стану на них нападать."
                ]
                return random.choice(responses)

        except Exception as e:
            print(f"Ошибка при обработке провокации: {e}")
            return "Я не понимаю, о чем ты говоришь."

    def _is_relationship_break(self, message):
        """Определяет, является ли сообщение разрывом отношений"""
        break_keywords = [
            'разорвать', 'прекратить', 'конец', 'хватит',
            'достало', 'надоело', 'закончить', 'покончить',
            'больше не', 'не хочу', 'не буду', 'хватит общаться',
            'прекращаю', 'заканчиваю', 'прощай навсегда'
        ]

        message_lower = message.lower()
        return any(keyword in message_lower for keyword in break_keywords)

    def _handle_relationship_break(self, message, faction):
        """Обрабатывает разрыв отношений"""
        try:
            cursor = self.db_connection.cursor()

            # Ухудшаем отношения
            cursor.execute("""
                UPDATE relations 
                SET relationship = relationship - 30 
                WHERE (faction1 = ? AND faction2 = ?) OR (faction1 = ? AND faction2 = ?)
            """, (self.faction, faction, faction, self.faction))

            self.db_connection.commit()

            responses = [
                "Как скажешь. Наши отношения ухудшились.",
                "Жаль. Теперь ты мне нравишься еще меньше.",
                "Хорошо, я понял. Но помни - ты сам этого захотел.",
                "Как хочешь. Тебе будет сложнее вести со мной дела."
            ]

            return random.choice(responses)

        except Exception as e:
            print(f"Ошибка при разрыве отношений: {e}")
            return "Что-то пошло не так."

    def _get_greeting_response(self, faction, relation_level):
        """Генерирует приветствие в зависимости от отношений"""
        if relation_level >= 80:
            greetings = [
                f"Привет, друг! Рад тебя видеть!",
                f"Здравствуй, союзник! Как твои дела?",
                f"Приветствую тебя, верный друг!"
            ]
        elif relation_level >= 60:
            greetings = [
                f"Привет! Рад тебя видеть.",
                f"Здравствуйте! Как ваши дела?",
                f"Приветствую!"
            ]
        elif relation_level >= 40:
            greetings = [
                f"Здравствуйте.",
                f"Привет.",
                f"Добрый день."
            ]
        elif relation_level >= 20:
            greetings = [
                f"Что тебе нужно?",
                f"Говори.",
                f"Я слушаю."
            ]
        else:
            greetings = [
                f"Чего пришел?",
                f"Говори быстро.",
                f"У меня мало времени."
            ]

        return random.choice(greetings)

    def _get_farewell_response(self, faction):
        """Генерирует прощание"""
        farewells = [
            "До свидания!",
            "Пока! Будем ждать ваших предложений.",
            "Всего хорошего!",
            "Удачи!",
            "Береги себя!"
        ]

        return random.choice(farewells)

    def _generate_fallback_response(self, message, faction, relation_level):
        """Генерирует ответ, когда не распознан интент"""

        # Проверяем вручную на ключевые слова
        message_lower = message.lower()

        # Приветствия
        greeting_words = ['привет', 'здравствуй', 'здравствуйте', 'добрый', 'хай', 'здаров', 'ку', 'hello', 'hi']
        if any(word in message_lower for word in greeting_words):
            return self._get_greeting_response(faction, relation_level)

        # Прощания
        farewell_words = ['пока', 'до свидания', 'прощай', 'удачи', 'всего', 'bye', 'goodbye']
        if any(word in message_lower for word in farewell_words):
            return self._get_farewell_response(faction)

        # Благодарности
        thanks_words = ['спасибо', 'благодарю', 'thanks', 'thank you']
        if any(word in message_lower for word in thanks_words):
            return random.choice(["Пожалуйста!", "Рад помочь!", "Не за что!"])

        # Если ничего не распознано
        if relation_level >= 60:
            fallbacks = [
                "Я не совсем понял твой запрос. Можешь уточнить?",
                "Попробуй перефразировать, я не понял.",
                "Прости, я не уловил суть твоего сообщения."
            ]
        elif relation_level >= 30:
            fallbacks = [
                "Что?",
                "Не понял.",
                "Повтори."
            ]
        else:
            fallbacks = [
                "Говори понятнее.",
                "Чего бормочешь?",
                "Выражайся яснее."
            ]

        return random.choice(fallbacks)

    def _is_context_reset(self, message):
        """Определяет, является ли сообщение командой сброса контекста"""
        reset_keywords = [
            'забудь', 'забей', 'обнули', 'сбрось', 'начнем заново', 'отстань', 'отвали',
            'очисти', 'удали контекст', 'стереть', 'забудь все',
            'сбросить контекст', 'забудь что было', 'начни сначала',
            'рестарт', 'перезагрузка', 'очистить историю',
            'сбросим', 'забудем', 'начать с начала',
            'очистить чат', 'стереть память', 'новый диалог',
            'сбрось все', 'забудь предыдущее', 'очисти разговор'
        ]

        message_lower = message.lower()

        # Также проверяем комбинации с дополнениями
        reset_phrases = [
            'забудь все что было',
            'сбрось контекст чата',
            'очисти историю разговора',
            'начнем диалог заново',
            'забудь предыдущий разговор',
            'стереть память о чате',
            'новый разговор'
        ]

        # Проверяем отдельные слова
        if any(keyword in message_lower for keyword in reset_keywords):
            return True

        # Проверяем фразы
        if any(phrase in message_lower for phrase in reset_phrases):
            return True

        return False