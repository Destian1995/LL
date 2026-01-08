# ai_models/quick_actions.py
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout
from kivy.uix.popup import Popup
from kivy.uix.checkbox import CheckBox
from kivy.metrics import dp
from kivy.graphics import Color, RoundedRectangle
from datetime import datetime


class QuickActions:
    def __init__(self, advisor_view):
        self.advisor = advisor_view
        self.faction = advisor_view.faction
        self.db_connection = advisor_view.db_connection

    def show_diplomatic_analysis(self):
        """Показывает анализ дипломатической ситуации"""
        analysis = self.get_diplomatic_situation_analysis()

        content = BoxLayout(orientation='vertical', spacing=dp(10), padding=dp(20))

        title = Label(
            text="Анализ дипломатической ситуации",
            font_size='18sp',
            bold=True,
            color=(1, 1, 1, 1)
        )

        analysis_label = Label(
            text=analysis,
            font_size='14sp',
            color=(0.9, 0.9, 0.9, 1),
            halign='left',
            valign='top',
            size_hint_y=None
        )

        analysis_label.bind(
            texture_size=lambda *x: analysis_label.setter('height')(analysis_label,
                                                                    analysis_label.texture_size[1] + dp(20))
        )

        scroll = ScrollView(size_hint=(1, 0.8))
        scroll.add_widget(analysis_label)

        close_button = Button(
            text="Закрыть",
            size_hint=(1, None),
            height=dp(40),
            background_color=(0.3, 0.5, 0.8, 1),
            on_press=lambda x: self.advisor.popup.dismiss()
        )

        content.add_widget(title)
        content.add_widget(scroll)
        content.add_widget(close_button)

        analysis_popup = Popup(
            title="",
            content=content,
            size_hint=(0.7, 0.6),
            background=''
        )
        analysis_popup.open()

    def get_diplomatic_situation_analysis(self):
        """Получает анализ дипломатической ситуации от ИИ"""
        # Временная реализация - можно интегрировать с ИИ
        try:
            relations = self.advisor.relations_manager.load_combined_relations()

            analysis = "📊 **Анализ дипломатической ситуации:**\n\n"

            allies = []
            enemies = []
            neutrals = []

            for faction, data in relations.items():
                status = data.get("status", "нейтралитет")
                level = data.get("relation_level", 50)

                if status == "союз":
                    allies.append(f"{faction} ({level}/100)")
                elif status == "война":
                    enemies.append(f"{faction} ({level}/100)")
                else:
                    neutrals.append(f"{faction} ({level}/100)")

            if allies:
                analysis += f"✅ **Союзники ({len(allies)}):**\n"
                analysis += " • " + "\n • ".join(allies) + "\n\n"

            if enemies:
                analysis += f"⚠️ **Враги ({len(enemies)}):**\n"
                analysis += " • " + "\n • ".join(enemies) + "\n\n"

            if neutrals:
                analysis += f"⚪ **Нейтральные ({len(neutrals)}):**\n"
                analysis += " • " + "\n • ".join(neutrals) + "\n\n"

            # Рекомендации
            analysis += "🎯 **Рекомендации:**\n"

            if len(enemies) > 1:
                analysis += "1. Избегайте войны на несколько фронтов\n"
                analysis += "2. Попробуйте заключить перемирие с одним из врагов\n"

            if len(allies) < 2:
                analysis += "1. Укрепляйте отношения с нейтральными фракциями\n"
                analysis += "2. Предлагайте торговые соглашения\n"

            analysis += "3. Используйте дипломатию для ослабления вражеских альянсов\n"
            analysis += "4. Инвестируйте в разведку для получения информации о намерениях врагов\n"

            return analysis

        except Exception as e:
            print(f"Ошибка при анализе дипломатической ситуации: {e}")
            return "Не удалось проанализировать ситуацию. Проверьте данные об отношениях."

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

    def ask_quick_question(self, question):
        """Задает быстрый вопрос из панели"""
        # Этот метод будет вызываться из чата
        if hasattr(self.advisor, 'diplomacy_chat') and hasattr(self.advisor.diplomacy_chat, 'message_input'):
            self.advisor.diplomacy_chat.message_input.text = question
            # Здесь можно вызвать метод отправки сообщения
            print(f"Быстрый вопрос: {question}")

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
        if hasattr(self.advisor.diplomacy_chat, 'selected_faction') and self.advisor.diplomacy_chat.selected_faction:
            faction = self.advisor.diplomacy_chat.selected_faction

            # Добавляем сообщение в чат
            if hasattr(self.advisor.diplomacy_chat, 'add_chat_message'):
                current_time = datetime.now().strftime("%d.%m %H:%M")
                self.advisor.diplomacy_chat.add_chat_message(
                    message=f"Предлагаю договор '{treaty_type}'.",
                    sender=self.faction,
                    timestamp=current_time,
                    is_player=True
                )

            # Сохраняем в историю переговоров
            self.advisor.diplomacy_chat.save_negotiation_message(
                faction,
                f"Предложение договора: {treaty_type}",
                is_player=True
            )

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
            on_press=lambda x: self.advisor.return_to_main_tab()
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

    def load_recent_negotiation_history(self, limit=20):
        """Загружает последнюю историю переговоров для контекста ИИ"""
        try:
            cursor = self.db_connection.cursor()
            cursor.execute('''
                SELECT faction1, faction2, message, is_player, timestamp 
                FROM negotiation_history 
                ORDER BY timestamp DESC 
                LIMIT ?
            ''', (limit,))

            history = cursor.fetchall()
            return [
                {
                    'faction1': msg[0],
                    'faction2': msg[1],
                    'message': msg[2],
                    'is_player': bool(msg[3]),
                    'timestamp': msg[4]
                }
                for msg in history
            ]
        except Exception as e:
            print(f"Ошибка при загрузке истории переговоров: {e}")
            return []

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

    def get_comprehensive_game_context(self):
        """Получает полный контекст игры для ИИ"""
        try:
            cursor = self.db_connection.cursor()

            context = {
                'player_faction': self.faction,
                'factions': {},
                'global_state': {}
            }

            # Получаем информацию обо всех фракциях
            all_factions = ["Север", "Эльфы", "Адепты", "Вампиры", "Элины"]

            for faction in all_factions:
                faction_data = {
                    'resources': None,
                    'cities': 0,
                    'army': 0,
                    'political_system': None,
                    'relations': {}
                }

                # Ресурсы
                all_resources = self.get_resources_data()
                faction_resources = all_resources.get(faction, {})
                faction_data['resources'] = (
                    faction_resources.get('gold', 0),
                    faction_resources.get('crystals', 0),
                    faction_resources.get('workers', 0)
                )

                # Города
                cursor.execute("SELECT COUNT(*) FROM cities WHERE faction = ?", (faction,))
                faction_data['cities'] = cursor.fetchone()[0] or 0

                # Армия
                cursor.execute("""
                    SELECT SUM(g.unit_count), u.unit_name 
                    FROM garrisons g 
                    JOIN units u ON g.unit_name = u.unit_name 
                    WHERE u.faction = ?
                    GROUP BY u.unit_name
                """, (faction,))
                units = cursor.fetchall()
                faction_data['army'] = sum([unit[0] for unit in units]) if units else 0
                faction_data['unit_composition'] = {unit[1]: unit[0] for unit in units}

                # Политическая система
                cursor.execute("SELECT system FROM political_systems WHERE faction = ?", (faction,))
                political = cursor.fetchone()
                faction_data['political_system'] = political[0] if political else "Неизвестно"

                # Отношения с другими фракциями
                cursor.execute("SELECT faction2, relationship FROM relations WHERE faction1 = ?", (faction,))
                relations = cursor.fetchall()
                faction_data['relations'] = {rel[0]: rel[1] for rel in relations}

                context['factions'][faction] = faction_data

            # История переговоров
            context['negotiation_history'] = self.load_recent_negotiation_history()

            return context

        except Exception as e:
            print(f"Ошибка при получении контекста игры: {e}")
            return {}

    def get_resources_data(self):
        """Получает ресурсы фракций"""
        try:
            cursor = self.db_connection.cursor()

            cursor.execute("SELECT faction, resource_type, amount FROM resources")

            resources = {}
            for faction, resource_type, amount in cursor.fetchall():
                if faction not in resources:
                    resources[faction] = {}
                resources[faction][resource_type] = amount

            # Структурируем важные ресурсы
            structured_resources = {}
            for faction, res in resources.items():
                structured_resources[faction] = {
                    'gold': res.get('Кроны', 0),
                    'crystals': res.get('Кристаллы', 0),
                    'workers': res.get('Рабочие', 0),
                    'army_limit': res.get('Лимит Армии', 0),
                    'consumption': res.get('Потребление', 0)
                }

            return structured_resources

        except Exception as e:
            print(f"Ошибка при получении ресурсов: {e}")
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