# neural_ai_integration.py
import sqlite3
import json
import os
from typing import Optional, Dict, Any, List
from datetime import datetime
from general_ii_neiro import NeuralAICore, AIPersonality


class NeuralAIIntegration:
    """
    Фасад для упрощенной интеграции нейронного ИИ
    """

    def __init__(self, selected_faction, conn):
        self.selected_faction = selected_faction  # Фракция игрока
        self.conn = conn
        self.ai_adapters = {}  # Словарь адаптеров по фракциям
        self.game_history = []  # История игры для обучения
        self.model_version = "1.0"

        # Создаем директорию для моделей, если её нет
        self.models_dir = "ai_models"
        os.makedirs(self.models_dir, exist_ok=True)

    def create_controller_for_faction(self, faction):
        """
        Создает адаптер ИИ для указанной фракции
        Возвращает улучшенный контроллер с нейронными методами
        """
        print(f"[НЕЙРОННЫЙ ИИ] Создание контроллера для фракции: {faction}")

        # Сначала создаем стандартный AIController из ii.py
        from ii import AIController
        from seasons import SeasonManager

        # Создаем season_manager
        season_manager = SeasonManager()

        # Создаем стандартный контроллер
        standard_controller = AIController(faction, self.conn, season_manager)

        # Создаем адаптер нейронного ИИ
        adapter = AIAdapter(faction, self.conn, standard_controller)

        # Сохраняем адаптер
        self.ai_adapters[faction] = adapter

        # Возвращаем улучшенный контроллер
        return self._enhance_controller(standard_controller, adapter)

    def _enhance_controller(self, standard_controller, adapter):
        """
        Добавляет нейронные методы к стандартному контроллеру
        """
        # Сохраняем ссылки на адаптер и оригинальные методы
        standard_controller.neural_adapter = adapter
        original_make_turn = standard_controller.make_turn

        def neural_make_turn():
            """
            Гибридный метод: сначала нейронная логика, затем стандартная
            """
            try:
                # 1. Выполняем нейронные решения
                neural_report = adapter.make_ai_turn()

                # 2. Выполняем стандартные действия для заполнения пропущенного
                standard_report = adapter.execute_standard_actions()

                # 3. Сохраняем результаты для обучения
                self._record_turn_results(
                    faction=adapter.faction,
                    neural_actions=len(neural_report.get('neural_commands', [])),
                    standard_actions=standard_report
                )

                return {**neural_report, 'standard_complement': standard_report}

            except Exception as e:
                print(f"[НЕЙРОННЫЙ ИИ] Ошибка в нейронном ходе: {e}")
                # Возвращаемся к стандартной логике
                return original_make_turn()

        # Добавляем новые методы
        standard_controller.make_neural_turn = neural_make_turn

        # Переопределяем стандартный метод (опционально)
        # Если хотите всегда использовать нейронный ИИ:
        standard_controller.make_turn = neural_make_turn

        # Или оставляем выбор:
        # standard_controller.make_turn = original_make_turn

        # Добавляем метод для обработки сообщений игрока
        standard_controller.process_player_message = adapter.process_player_message

        # Добавляем метод для получения статуса ИИ
        standard_controller.get_neural_status = adapter.get_ai_status

        return standard_controller

    def update_game_state(self, turn_counter, player_faction):
        """
        Обновляет состояние игры для всех адаптеров
        """
        print(f"[НЕЙРОННЫЙ ИИ] Обновление состояния игры, ход: {turn_counter}")

        # Собираем данные о текущем состоянии игры
        game_state = self._collect_game_state(turn_counter, player_faction)

        # Обновляем каждый адаптер
        for faction, adapter in self.ai_adapters.items():
            try:
                # Обновляем память нейронного ядра
                adapter.neural_core.update_game_state(game_state)

                # Анализируем изменения в отношениях
                self._analyze_diplomatic_changes(faction, game_state)

            except Exception as e:
                print(f"[НЕЙРОННЫЙ ИИ] Ошибка обновления для {faction}: {e}")

    def _collect_game_state(self, turn_counter, player_faction) -> Dict[str, Any]:
        """
        Собирает данные о текущем состоянии игры
        """
        cursor = self.conn.cursor()
        game_state = {
            'turn': turn_counter,
            'player_faction': player_faction,
            'timestamp': datetime.now().isoformat(),
            'factions': {},
            'cities': {},
            'diplomacy': {},
            'resources': {}
        }

        try:
            # Собираем данные о фракциях
            cursor.execute("SELECT name, faction, population, defense FROM cities")
            cities = cursor.fetchall()
            for name, faction, population, defense in cities:
                game_state['cities'][name] = {
                    'faction': faction,
                    'population': population,
                    'defense': defense
                }

                # Агрегируем по фракциям
                if faction not in game_state['factions']:
                    game_state['factions'][faction] = {
                        'city_count': 0,
                        'total_population': 0,
                        'total_defense': 0
                    }

                game_state['factions'][faction]['city_count'] += 1
                game_state['factions'][faction]['total_population'] += (population or 0)
                game_state['factions'][faction]['total_defense'] += (defense or 0)

            # Собираем дипломатические данные
            cursor.execute("SELECT faction1, faction2, relationship FROM diplomacies")
            diplomacies = cursor.fetchall()
            for faction1, faction2, relationship in diplomacies:
                key = f"{faction1}_{faction2}"
                game_state['diplomacy'][key] = relationship

            # Собираем ресурсы для AI фракций
            cursor.execute("SELECT faction, resource_type, amount FROM ai_resources")
            resources = cursor.fetchall()
            for faction, resource_type, amount in resources:
                if faction not in game_state['resources']:
                    game_state['resources'][faction] = {}
                game_state['resources'][faction][resource_type] = amount

        except Exception as e:
            print(f"[НЕЙРОННЫЙ ИИ] Ошибка сбора данных игры: {e}")

        return game_state

    def _analyze_diplomatic_changes(self, faction, game_state):
        """
        Анализирует изменения в дипломатической ситуации
        """
        try:
            adapter = self.ai_adapters.get(faction)
            if not adapter:
                return

            # Проверяем отношения с игроком
            player_key = f"{faction}_Игрок"
            if player_key in game_state['diplomacy']:
                current_relation = game_state['diplomacy'][player_key]

                # Сохраняем в историю для анализа трендов
                self._record_diplomatic_trend(faction, 'Игрок', current_relation)

        except Exception as e:
            print(f"[НЕЙРОННЫЙ ИИ] Ошибка анализа дипломатии: {e}")

    def train_on_game_data(self, game_data):
        """
        Обучение на игровых данных
        """
        print(f"[НЕЙРОННЫЙ ИИ] Обучение на игровых данных...")

        # Сохраняем данные для последующего обучения
        self.game_history.append({
            'timestamp': datetime.now().isoformat(),
            'data': game_data,
            'turn': game_data.get('turn', 0)
        })

        # Ограничиваем размер истории
        if len(self.game_history) > 100:
            self.game_history = self.game_history[-100:]

        # Периодическое обучение (каждые 10 ходов)
        if game_data.get('turn', 0) % 10 == 0:
            self._perform_training_cycle()

    def _perform_training_cycle(self):
        """
        Выполняет цикл обучения на накопленных данных
        """
        try:
            if len(self.game_history) < 5:
                print("[НЕЙРОННЫЙ ИИ] Недостаточно данных для обучения")
                return

            # Анализируем успешные стратегии
            successful_strategies = self._analyze_successful_strategies()

            # Обновляем нейронные ядра на основе успешных стратегий
            for faction, adapter in self.ai_adapters.items():
                if faction in successful_strategies:
                    adapter.neural_core.learn_from_success(successful_strategies[faction])

            print(f"[НЕЙРОННЫЙ ИИ] Цикл обучения завершен. Анализировано {len(successful_strategies)} стратегий")

        except Exception as e:
            print(f"[НЕЙРОННЫЙ ИИ] Ошибка обучения: {e}")

    def _analyze_successful_strategies(self) -> Dict[str, List[Dict]]:
        """
        Анализирует историю игр для выявления успешных стратегий
        """
        strategies = {}

        # Здесь можно добавить логику анализа успешных стратегий
        # Например, какие действия привели к росту городов/ресурсов

        return strategies

    def update_with_game_result(self, result, reason, turn_count):
        """
        Обновление нейронной сети с результатами игры
        """
        print(f"[НЕЙРОННЫЙ ИИ] Обновление с результатом игры: {result}, причина: {reason}")

        game_result = {
            'result': result,
            'reason': reason,
            'turn_count': turn_count,
            'timestamp': datetime.now().isoformat(),
            'player_faction': self.selected_faction
        }

        # Сохраняем результат для обучения
        for adapter in self.ai_adapters.values():
            try:
                adapter.neural_core.record_game_result(result, turn_count)

                # Обновляем личность на основе результатов
                if result == "win" and adapter.faction != self.selected_faction:
                    # Если ИИ победил игрока - становится более агрессивным
                    adapter.neural_core.adjust_personality_based_on_result(result)
                elif result == "lose" and adapter.faction != self.selected_faction:
                    # Если ИИ проиграл - становится более осторожным
                    adapter.neural_core.adjust_personality_based_on_result(result)

            except Exception as e:
                print(f"[НЕЙРОННЫЙ ИИ] Ошибка обновления результата для {adapter.faction}: {e}")

        # Сохраняем результат в историю
        self._save_game_result(game_result)

    def _save_game_result(self, game_result):
        """
        Сохраняет результат игры в файл
        """
        try:
            results_file = os.path.join(self.models_dir, "game_results.json")

            results = []
            if os.path.exists(results_file):
                with open(results_file, 'r', encoding='utf-8') as f:
                    results = json.load(f)

            results.append(game_result)

            # Ограничиваем размер файла
            if len(results) > 50:
                results = results[-50:]

            with open(results_file, 'w', encoding='utf-8') as f:
                json.dump(results, f, ensure_ascii=False, indent=2)

        except Exception as e:
            print(f"[НЕЙРОННЫЙ ИИ] Ошибка сохранения результата: {e}")

    def save_model(self):
        """
        Сохранение моделей нейросети
        """
        print("[НЕЙРОННЫЙ ИИ] Сохранение моделей...")

        saved_count = 0
        for faction, adapter in self.ai_adapters.items():
            try:
                adapter.save_all_data()
                saved_count += 1
            except Exception as e:
                print(f"[НЕЙРОННЫЙ ИИ] Ошибка сохранения для {faction}: {e}")

        # Сохраняем общую конфигурацию
        self._save_integration_config()

        print(f"[НЕЙРОННЫЙ ИИ] Сохранено {saved_count} моделей")

    def _save_integration_config(self):
        """
        Сохраняет конфигурацию интеграции
        """
        config = {
            'model_version': self.model_version,
            'last_update': datetime.now().isoformat(),
            'player_faction': self.selected_faction,
            'active_adapters': list(self.ai_adapters.keys()),
            'game_history_count': len(self.game_history)
        }

        try:
            config_file = os.path.join(self.models_dir, "integration_config.json")
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"[НЕЙРОННЫЙ ИИ] Ошибка сохранения конфигурации: {e}")

    def load_model(self):
        """
        Загрузка сохраненных моделей
        """
        print("[НЕЙРОННЫЙ ИИ] Загрузка моделей...")

        try:
            config_file = os.path.join(self.models_dir, "integration_config.json")
            if os.path.exists(config_file):
                with open(config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    print(f"[НЕЙРОННЫЙ ИИ] Загружена конфигурация версии {config.get('model_version')}")

                    # Здесь можно добавить логику загрузки моделей для адаптеров

        except Exception as e:
            print(f"[НЕЙРОННЫЙ ИИ] Ошибка загрузки моделей: {e}")

    def _record_turn_results(self, faction, neural_actions, standard_actions):
        """
        Записывает результаты хода для последующего анализа
        """
        turn_record = {
            'faction': faction,
            'neural_actions': neural_actions,
            'standard_actions': standard_actions,
            'timestamp': datetime.now().isoformat()
        }

        # Можно сохранять в базу данных или файл
        # Для простоты - просто логируем
        if neural_actions > 0:
            print(f"[НЕЙРОННЫЙ ИИ] {faction}: {neural_actions} нейронных действий")

    def _record_diplomatic_trend(self, faction1, faction2, relation):
        """
        Записывает тренд в дипломатических отношениях
        """
        # Здесь можно реализовать анализ трендов отношений
        pass

    def get_integration_status(self) -> Dict[str, Any]:
        """
        Возвращает статус интеграции нейронного ИИ
        """
        return {
            'model_version': self.model_version,
            'player_faction': self.selected_faction,
            'active_ai_count': len(self.ai_adapters),
            'ai_factions': list(self.ai_adapters.keys()),
            'game_history_count': len(self.game_history),
            'adapters_status': {
                faction: adapter.get_ai_status()
                for faction, adapter in self.ai_adapters.items()
            }
        }

    def cleanup(self):
        """
        Очистка ресурсов перед завершением
        """
        print("[НЕЙРОННЫЙ ИИ] Очистка ресурсов...")
        self.save_model()
        self.ai_adapters.clear()


class AIAdapter:
    """
    Адаптер для интеграции нейро-ИИ с вашим ii.py
    """

    def __init__(self, faction: str, db_connection: sqlite3.Connection,
                 ai_controller_instance):
        """
        :param faction: Название фракции
        :param db_connection: Соединение с БД
        :param ai_controller_instance: Экземпляр AIController из ii.py
        """
        self.faction = faction
        self.db_connection = db_connection
        self.ai_controller = ai_controller_instance

        # Инициализируем нейро-ИИ ядро
        self.neural_core = NeuralAICore(faction, db_connection)

        # Подключаем исполнительный модуль (ваш AIController)
        self.neural_core.connect_executive(ai_controller_instance)

        print(f"[AI АДАПТЕР] Инициализирован для фракции {faction}")

    def make_ai_turn(self) -> Dict[str, Any]:
        """
        Выполняет ход ИИ с использованием нейро-логики
        Возвращает отчет о выполненных действиях
        """
        print(f"[AI АДАПТЕР] {self.faction} начинает ход с нейро-логикой...")

        # 1. Получаем стратегические решения от нейро-ИИ
        commands = self.neural_core.make_strategic_decision()

        # 2. Выполняем команды через ваш AIController
        execution_results = self.neural_core.execute_commands(commands)

        # 3. Выполняем стандартные действия из ii.py
        standard_results = self.execute_standard_actions()

        # 4. Сохраняем все данные
        self.save_all_data()

        # 5. Формируем отчет
        report = {
            'neural_commands': len(commands),
            'execution_results': execution_results,
            'standard_actions': standard_results,
            'personality': self.neural_core.personality.value,
            'relation_with_player': self.neural_core.get_relation_with_player()
        }

        print(f"[AI АДАПТЕР] Ход завершен. Отчет: {report}")
        return report

    def execute_standard_actions(self) -> Dict[str, Any]:
        """
        Выполняет стандартные действия из ii.py
        """
        results = {}

        try:
            # Для мятежников - только военные действия
            if self.faction == "Мятежники":
                print(f"[AI АДАПТЕР] Мятежники - только военные действия")
                self.ai_controller.attack_enemy_cities()
                results['action'] = 'military_only'
            else:
                # Полный цикл действий
                # 1. Обновление ресурсов
                self.ai_controller.update_resources()
                results['resources_updated'] = True

                # 2. Обработка запросов
                self.ai_controller.process_queries()
                results['queries_processed'] = True

                # 3. Применяем ДИПЛОМАТИЧЕСКУЮ ЛОГИКУ вместо автоматической войны
                self.apply_diplomatic_logic()
                results['diplomacy_applied'] = True

                # 4. Бонусы от политической системы
                self.ai_controller.apply_political_system_bonus()
                results['political_bonus'] = True

                # 5. Обновление отношений
                self.ai_controller.update_relations_based_on_political_system()
                results['relations_updated'] = True

                # 6. Строительство (нейро-ИИ уже мог это сделать через команды)
                # Если не было команд на строительство, выполняем стандартное
                if not self.was_building_command_executed():
                    self.ai_controller.manage_buildings()
                    results['buildings_managed'] = True

                # 7. Продажа ресурсов
                self.ai_controller.sell_resources()
                results['resources_sold'] = True

                # 8. Найм армии
                if self.ai_controller.resources['Кроны'] > 0:
                    self.ai_controller.hire_army()
                    results['army_hired'] = True

                # 9. Артефакты (после 40 хода)
                self.ai_controller.generate_and_buy_artifacts_for_ai_hero()
                results['artifacts_checked'] = True

        except Exception as e:
            results['error'] = str(e)
            print(f"[AI АДАПТЕР] Ошибка в стандартных действиях: {e}")

        return results

    def apply_diplomatic_logic(self):
        """
        НОВАЯ ДИПЛОМАТИЧЕСКАЯ ЛОГИКА:
        - Анализирует поведение игрока
        - Принимает решение о войне/мире на основе множества факторов
        """
        try:
            # Получаем текущую личность ИИ
            personality = self.neural_core.personality

            # Получаем историю взаимодействий с игроком
            player_interactions = self.neural_core.memory.get('player_interactions', [])

            # Анализируем поведение игрока
            player_behavior = self.analyze_player_behavior(player_interactions)

            # Получаем текущие отношения
            current_relation = self.neural_core.get_relation_with_player()

            # Получаем силу армий
            army_strength = self.ai_controller.calculate_army_strength()
            our_strength = army_strength.get(self.faction, 0)
            player_strength = army_strength.get('Игрок', 0)

            # Принимаем решение на основе:
            # 1. Личности ИИ
            # 2. Отношений
            # 3. Силы армий
            # 4. Поведения игрока
            # 5. Исторического контекста

            should_declare_war = self.decide_war_or_peace(
                personality=personality,
                relation=current_relation,
                our_strength=our_strength,
                player_strength=player_strength,
                player_behavior=player_behavior,
                history=player_interactions
            )

            if should_declare_war:
                print(f"[ДИПЛОМАТИЯ] {self.faction} объявляет войну игроку")
                self.ai_controller.update_diplomacy_status('Игрок', "война")
                self.ai_controller.notify_player_about_war('Игрок')

                # Атакуем ближайший город игрока
                target_city = self.ai_controller.find_nearest_city('Игрок')
                if target_city:
                    self.ai_controller.attack_city(target_city, 'Игрок')
            else:
                print(f"[ДИПЛОМАТИЯ] {self.faction} поддерживает мир с игроком")

                # Если отношения низкие, но войну не объявляем,
                # можно попытаться улучшить отношения
                if current_relation < 30:
                    self.try_improve_relations()

        except Exception as e:
            print(f"[ДИПЛОМАТИЯ] Ошибка: {e}")

    def analyze_player_behavior(self, interactions: list) -> Dict[str, Any]:
        """
        Анализирует поведение игрока на основе истории взаимодействий
        """
        behavior = {
            'aggression_level': 0,  # 0-100
            'friendliness_level': 0,  # 0-100
            'trade_frequency': 0,  # частота торговых предложений
            'threat_frequency': 0,  # частота угроз
            'average_response_time': 0,
            'consistency': 0  # последовательность поведения
        }

        if not interactions:
            return behavior

        # Анализ последних 10 взаимодействий
        recent_interactions = interactions[-10:] if len(interactions) > 10 else interactions

        threats = 0
        friendly = 0
        trades = 0

        for interaction in recent_interactions:
            message = interaction.get('player_message', '').lower()

            if any(word in message for word in ['война', 'атака', 'убью', 'уничтожу']):
                threats += 1
            elif any(word in message for word in ['союз', 'дружба', 'помощь', 'торгов']):
                friendly += 1
            elif any(word in message for word in ['сделка', 'обмен', 'купить', 'продать']):
                trades += 1

        total = len(recent_interactions)

        behavior['aggression_level'] = (threats / total * 100) if total > 0 else 0
        behavior['friendliness_level'] = (friendly / total * 100) if total > 0 else 0
        behavior['trade_frequency'] = (trades / total * 100) if total > 0 else 0
        behavior['threat_frequency'] = threats

        print(f"[АНАЛИЗ] Поведение игрока: {behavior}")
        return behavior

    def decide_war_or_peace(self, personality: AIPersonality, relation: int,
                            our_strength: int, player_strength: int,
                            player_behavior: Dict, history: list) -> bool:
        """
        Принимает решение: объявлять ли войну игроку
        Возвращает True если нужно объявить войну
        """

        # БАЗОВЫЕ ПРАВИЛА ПО ЛИЧНОСТИ
        if personality == AIPersonality.ENEMY:
            # Враг почти всегда объявляет войну
            base_war_chance = 0.8
        elif personality == AIPersonality.HOSTILE:
            base_war_chance = 0.6
        elif personality == AIPersonality.NEUTRAL:
            base_war_chance = 0.3
        elif personality == AIPersonality.FRIENDLY:
            base_war_chance = 0.1
        else:
            base_war_chance = 0.5

        # МОДИФИКАТОРЫ РЕШЕНИЯ

        # 1. Модификатор отношений
        relation_modifier = 1.0 - (relation / 100)  # Чем лучше отношения, тем меньше шанс войны

        # 2. Модификатор силы
        strength_ratio = player_strength / our_strength if our_strength > 0 else 2.0
        if strength_ratio > 1.5:
            strength_modifier = 0.3  # Противник сильнее - меньше шанс войны
        elif strength_ratio < 0.7:
            strength_modifier = 1.5  # Противник слабее - больше шанс войны
        else:
            strength_modifier = 1.0

        # 3. Модификатор поведения игрока
        aggression = player_behavior.get('aggression_level', 0)
        friendliness = player_behavior.get('friendliness_level', 0)

        if aggression > 50:
            behavior_modifier = 1.5  # Агрессивный игрок - выше шанс войны
        elif friendliness > 50:
            behavior_modifier = 0.5  # Дружелюбный игрок - ниже шанс войны
        else:
            behavior_modifier = 1.0

        # 4. Модификатор исторического контекста
        history_modifier = self.calculate_history_modifier(history)

        # ИТОГОВЫЙ ШАНС ВОЙНЫ
        war_chance = base_war_chance * relation_modifier * strength_modifier * behavior_modifier * history_modifier

        # ОГРАНИЧЕНИЯ ПО ПОВЕДЕНИЮ ИГРОКА
        # Если игрок очень дружелюбный (>70%) - снижаем шанс войны еще больше
        if friendliness > 70:
            war_chance *= 0.3

        # Если были предательства в истории - повышаем шанс
        if self.has_betrayal_in_history(history):
            war_chance *= 1.8

        # ФИНАЛЬНОЕ РЕШЕНИЕ
        import random
        decision = war_chance > 0.5

        print(f"[РЕШЕНИЕ] Шанс войны: {war_chance:.2%}, Решение: {'ВОЙНА' if decision else 'МИР'}")
        print(f"  Личность: {personality.value}")
        print(f"  Отношения: {relation}/100")
        print(f"  Сила: мы={our_strength}, игрок={player_strength}")
        print(f"  Поведение: агрессия={aggression:.0f}%, дружелюбие={friendliness:.0f}%")

        return decision

    def calculate_history_modifier(self, history: list) -> float:
        """Рассчитывает модификатор на основе истории взаимодействий"""
        if not history:
            return 1.0

        # Анализируем последние 5 взаимодействий
        recent = history[-5:] if len(history) > 5 else history

        positive = 0
        negative = 0

        for interaction in recent:
            # Простой анализ тональности
            message = interaction.get('player_message', '').lower()
            response = interaction.get('ai_response', '').lower()

            positive_words = ['спасибо', 'хорошо', 'согласен', 'договорились', 'дружба']
            negative_words = ['война', 'убью', 'предатель', 'ненавижу', 'враг']

            if any(word in message for word in positive_words):
                positive += 1
            elif any(word in message for word in negative_words):
                negative += 1

        total = len(recent)
        if total == 0:
            return 1.0

        balance = (positive - negative) / total

        if balance > 0.3:  # Положительная история
            return 0.7
        elif balance < -0.3:  # Отрицательная история
            return 1.3
        else:  # Нейтральная
            return 1.0

    def has_betrayal_in_history(self, history: list) -> bool:
        """Проверяет, были ли предательства в истории"""
        betrayal_keywords = ['предатель', 'обман', 'коварный', 'вероломный', 'измена']

        for interaction in history:
            message = interaction.get('player_message', '').lower()
            if any(keyword in message for keyword in betrayal_keywords):
                return True

        return False

    def try_improve_relations(self):
        """Пытается улучшить отношения с игроком"""
        try:
            # Создаем торговое предложение
            self.ai_controller.cursor.execute('''
                INSERT INTO trade_agreements 
                (initiator, target_faction, initiator_type_resource, 
                 initiator_summ_resource, target_type_resource, target_summ_resource)
                VALUES (?, ?, 'Кроны', 1000, 'Кристаллы', 500)
            ''', (self.faction, 'Игрок'))

            self.db_connection.commit()
            print(f"[ДИПЛОМАТИЯ] {self.faction} предлагает торговую сделку игроку")

        except Exception as e:
            print(f"[ДИПЛОМАТИЯ] Ошибка при улучшении отношений: {e}")

    def was_building_command_executed(self) -> bool:
        """Проверяет, были ли выполнены команды на строительство"""
        # Здесь можно добавить логику отслеживания выполненных команд
        return False

    def save_all_data(self):
        """Сохраняет все данные"""
        try:
            self.ai_controller.save_all_data()
            self.neural_core.save_memory()
        except Exception as e:
            print(f"[AI АДАПТЕР] Ошибка сохранения: {e}")

    def process_player_message(self, message: str) -> str:
        """
        Обрабатывает сообщение от игрока
        Возвращает ответ от нейро-ИИ
        """
        return self.neural_core.process_player_message(message, 'Игрок')

    def get_ai_status(self) -> str:
        """Возвращает статус ИИ"""
        return self.neural_core.get_status_report()