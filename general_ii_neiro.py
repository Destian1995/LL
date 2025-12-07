# general_ii_neiro.py
import sqlite3
import json
import random
from typing import Dict, List, Any, Optional
from datetime import datetime
import threading
from enum import Enum

class AIPersonality(Enum):
    """4 типа личности для каждой фракции"""
    FRIENDLY = "friendly"      # Союзник (отношения > 50)
    NEUTRAL = "neutral"       # Нейтрал (отношения 0-50)
    HOSTILE = "hostile"       # Враждебный (отношения -50-0)
    ENEMY = "enemy"          # Враг (отношения < -50)

class NeuralAICore:
    """
    ЯДРО НЕЙРО-ИИ - главный мозг, который управляет ii.py
    """
    def __init__(self, faction: str, db_connection: sqlite3.Connection):
        self.faction = faction
        self.db = db_connection
        self.cursor = db_connection.cursor()

        # Связь с исполнительным модулем ii.py
        self.executive = None  # Будет установлен позже

        # Состояние ИИ
        self.memory = self.load_memory()
        self.personality = self.determine_personality()
        self.strategy_plan = {}
        self.conversation_history = []

        # Загрузка нейросети (опционально)
        self.neural_model = self.load_neural_model()

        # Конфигурация
        self.config = {
            'use_neural_for_dialogue': True,
            'use_neural_for_strategy': True,
            'max_response_time': 3.0,  # секунд
            'model_path': 'models/tinyllama.q4.gguf'
        }

        print(f"[НЕЙРО-ИИ] Инициализирован для фракции: {faction}")

    def connect_executive(self, executive_module):
        """
        Подключает исполнительный модуль ii.py
        executive_module: экземпляр AIController из ii.py
        """
        self.executive = executive_module
        print(f"[НЕЙРО-ИИ] Подключен исполнительный модуль для {self.faction}")

    def load_memory(self) -> Dict:
        """Загружает долговременную память ИИ из БД"""
        try:
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS ai_memory (
                    faction TEXT PRIMARY KEY,
                    memories TEXT,
                    personality_history TEXT,
                    last_updated TIMESTAMP
                )
            ''')

            self.cursor.execute(
                "SELECT memories FROM ai_memory WHERE faction = ?",
                (self.faction,)
            )
            result = self.cursor.fetchone()

            if result and result[0]:
                return json.loads(result[0])
            else:
                return {
                    'player_interactions': [],
                    'battles_won': 0,
                    'battles_lost': 0,
                    'trade_deals': [],
                    'diplomatic_events': [],
                    'goals_achieved': [],
                    'grudges': [],  # Обиды и предательства
                    'alliances': []  # Союзы и дружба
                }
        except Exception as e:
            print(f"[ОШИБКА] Не удалось загрузить память: {e}")
            return {}

    def save_memory(self):
        """Сохраняет память ИИ в БД"""
        try:
            memories_json = json.dumps(self.memory, ensure_ascii=False)

            self.cursor.execute('''
                INSERT OR REPLACE INTO ai_memory 
                (faction, memories, personality_history, last_updated)
                VALUES (?, ?, ?, ?)
            ''', (
                self.faction,
                memories_json,
                self.personality.value,
                datetime.now().isoformat()
            ))

            self.db.commit()
            print(f"[НЕЙРО-ИИ] Память сохранена для {self.faction}")
        except Exception as e:
            print(f"[ОШИБКА] Не удалось сохранить память: {e}")

    def determine_personality(self) -> AIPersonality:
        """Определяет текущую личность на основе отношений с игроком"""
        try:
            # Получаем отношения с игроком
            self.cursor.execute('''
                SELECT relationship FROM relations 
                WHERE faction1 = ? AND faction2 = 'Игрок'
            ''', (self.faction,))

            result = self.cursor.fetchone()
            relation = result[0] if result else 0

            # Определяем личность
            if relation > 50:
                return AIPersonality.FRIENDLY
            elif relation > 0:
                return AIPersonality.NEUTRAL
            elif relation > -50:
                return AIPersonality.HOSTILE
            else:
                return AIPersonality.ENEMY

        except Exception as e:
            print(f"[ОШИБКА] Не удалось определить личность: {e}")
            return AIPersonality.NEUTRAL

    def load_neural_model(self):
        """Загружает нейросеть (опционально, для офлайн работы)"""
        try:
            # Проверяем, доступна ли нейросеть
            from llama_cpp import Llama

            print(f"[НЕЙРО-ИИ] Загрузка модели: {self.config['model_path']}")

            model = Llama(
                model_path=self.config['model_path'],
                n_ctx=384,  # Уменьшенный контекст для экономии памяти
                n_threads=2,  # Меньше потоков для Android
                n_gpu_layers=0,  # Только CPU для совместимости
                verbose=False
            )

            print("[НЕЙРО-ИИ] Модель загружена успешно")
            return model

        except ImportError:
            print("[НЕЙРО-ИИ] Библиотека нейросети не найдена, используем rule-based")
            return None
        except Exception as e:
            print(f"[НЕЙРО-ИИ] Ошибка загрузки модели: {e}")
            return None

    # ------------------------------------------------------------
    # ОСНОВНОЙ ИНТЕРФЕЙС ДЛЯ УПРАВЛЕНИЯ ii.py
    # ------------------------------------------------------------

    def make_strategic_decision(self) -> Dict[str, Any]:
        """
        Главный метод: принимает стратегические решения на ход
        Возвращает команды для исполнительного модуля ii.py
        """
        print(f"[НЕЙРО-ИИ] {self.faction} принимает стратегическое решение...")

        # 1. Собираем информацию о состоянии
        game_state = self.analyze_game_state()

        # 2. Определяем приоритеты
        priorities = self.determine_priorities(game_state)

        # 3. Генерируем план действий (через нейросеть или rule-based)
        if self.config['use_neural_for_strategy'] and self.neural_model:
            plan = self.generate_neural_plan(game_state, priorities)
        else:
            plan = self.generate_rule_based_plan(game_state, priorities)

        # 4. Формируем команды для ii.py
        commands = self.create_commands_for_executive(plan)

        # 5. Сохраняем в память
        self.strategy_plan = plan
        self.save_memory()

        print(f"[НЕЙРО-ИИ] Сгенерировано {len(commands)} команд для выполнения")
        return commands

    def analyze_game_state(self) -> Dict[str, Any]:
        """Анализирует текущее состояние игры"""
        state = {
            'resources': self.get_current_resources(),
            'military': self.get_military_status(),
            'diplomacy': self.get_diplomatic_status(),
            'economy': self.get_economic_status(),
            'threats': self.identify_threats(),
            'opportunities': self.identify_opportunities(),
            'player_status': self.get_player_status(),
            'turn': self.get_current_turn()
        }

        # Добавляем исторический контекст из памяти
        state['memory_context'] = {
            'recent_battles': self.memory.get('recent_battles', []),
            'player_interactions': self.memory.get('player_interactions', [])[-5:],
            'grudges': self.memory.get('grudges', []),
            'alliances': self.memory.get('alliances', [])
        }

        return state

    def get_current_resources(self) -> Dict:
        """Получает текущие ресурсы фракции"""
        try:
            self.cursor.execute('''
                SELECT resource_type, amount FROM resources 
                WHERE faction = ?
            ''', (self.faction,))

            resources = {row[0]: row[1] for row in self.cursor.fetchall()}

            # Добавляем вычисляемые показатели
            if self.executive:
                resources.update({
                    'army_limit': self.executive.army_limit,
                    'current_consumption': self.executive.total_consumption,
                    'city_count': self.executive.city_count
                })

            return resources
        except Exception as e:
            print(f"[ОШИБКА] Не удалось получить ресурсы: {e}")
            return {}

    def get_military_status(self) -> Dict:
        """Анализирует военный статус"""
        status = {
            'total_strength': 0,
            'unit_count': 0,
            'heroes': [],
            'garrison_distribution': {},
            'attack_power': 0,
            'defense_power': 0
        }

        try:
            # Получаем все юниты фракции
            self.cursor.execute('''
                SELECT g.city_name, g.unit_name, g.unit_count, 
                       u.attack, u.defense, u.unit_class
                FROM garrisons g
                JOIN units u ON g.unit_name = u.unit_name
                WHERE u.faction = ?
            ''', (self.faction,))

            for city, unit_name, count, attack, defense, unit_class in self.cursor.fetchall():
                status['unit_count'] += count
                status['total_strength'] += (attack + defense) * count

                if unit_class in ['2', '3', '4']:  # Герои
                    status['heroes'].append({
                        'name': unit_name,
                        'class': unit_class,
                        'city': city,
                        'count': count
                    })

                # Распределение по городам
                if city not in status['garrison_distribution']:
                    status['garrison_distribution'][city] = 0
                status['garrison_distribution'][city] += count

                # Атакующая/оборонительная сила
                if attack > defense:
                    status['attack_power'] += attack * count
                else:
                    status['defense_power'] += defense * count

        except Exception as e:
            print(f"[ОШИБКА] Военный анализ: {e}")

        return status

    def determine_priorities(self, game_state: Dict) -> List[str]:
        """Определяет приоритеты на основе состояния"""
        priorities = []

        # Экономические приоритеты
        resources = game_state['resources']
        if resources.get('Кроны', 0) < 1000:
            priorities.append('ECONOMY_GROWTH')
        if resources.get('Кристаллы', 0) < 500:
            priorities.append('RESOURCE_PRODUCTION')

        # Военные приоритеты
        military = game_state['military']
        if military['unit_count'] < 100:
            priorities.append('ARMY_RECRUITMENT')

        # Угрозы
        threats = game_state['threats']
        if any(t['severity'] == 'HIGH' for t in threats):
            priorities.append('DEFENSE')

        # Возможности для экспансии
        opportunities = game_state['opportunities']
        if any(o['type'] == 'WEAK_NEIGHBOR' for o in opportunities):
            priorities.append('EXPANSION')

        # Дипломатические цели
        if self.personality == AIPersonality.FRIENDLY:
            priorities.append('DIPLOMACY')
        elif self.personality == AIPersonality.ENEMY:
            priorities.append('CONQUEST')

        return priorities[:3]  # Не более 3 главных приоритетов

    def generate_neural_plan(self, game_state: Dict, priorities: List[str]) -> Dict:
        """Генерирует план через нейросеть"""
        try:
            # Создаем промпт для нейросети
            prompt = self.create_strategy_prompt(game_state, priorities)

            # Получаем ответ от нейросети
            response = self.neural_model(
                prompt,
                max_tokens=256,
                temperature=0.5,
                stop=["\n\n", "###", "Player:"]
            )

            plan_text = response['choices'][0]['text'].strip()

            # Парсим ответ
            plan = self.parse_neural_response(plan_text)

            print(f"[НЕЙРО-ПЛАН] {plan.get('summary', 'Без названия')}")
            return plan

        except Exception as e:
            print(f"[ОШИБКА] Нейросеть не сработала: {e}")
            return self.generate_rule_based_plan(game_state, priorities)

    def create_strategy_prompt(self, game_state: Dict, priorities: List[str]) -> str:
        """Создает промпт для стратегического планирования"""
        return f"""
Ты - стратег фракции "{self.faction}" в стратегической игре.
Твоя личность: {self.personality.value}

ТЕКУЩЕЕ СОСТОЯНИЕ:
- Ресурсы: {json.dumps(game_state['resources'], ensure_ascii=False)}
- Военная сила: {game_state['military']['total_strength']}
- Количество юнитов: {game_state['military']['unit_count']}
- Города: {game_state['resources'].get('city_count', 0)}
- Отношения с игроком: {self.get_relation_with_player()}/100

ГЛАВНЫЕ ПРИОРИТЕТЫ: {', '.join(priorities)}
УГРОЗЫ: {len(game_state['threats'])} обнаружено
ВОЗМОЖНОСТИ: {len(game_state['opportunities'])} доступно

ИСТОРИЧЕСКИЙ КОНТЕКСТ:
{json.dumps(game_state['memory_context'], ensure_ascii=False)}

Какие действия следует предпринять на этом ходу?
Верни ответ в формате JSON:
{{
    "summary": "краткое описание стратегии",
    "actions": [
        {{"type": "BUILD", "target": "Больница/Фабрика", "intensity": 0-1}},
        {{"type": "RECRUIT", "unit_class": "1/2/3/4", "priority": "HIGH/MEDIUM/LOW"}},
        {{"type": "ATTACK", "target_faction": "имя", "target_city": "имя"}},
        {{"type": "DIPLOMACY", "action": "TRADE/WAR/PEACE", "with_faction": "имя"}}
    ],
    "reasoning": "обоснование решений",
    "expected_outcome": "чего ожидаем достичь"
}}
"""

    def generate_rule_based_plan(self, game_state: Dict, priorities: List[str]) -> Dict:
        """Генерирует rule-based план"""
        plan = {
            "summary": "",
            "actions": [],
            "reasoning": "",
            "expected_outcome": ""
        }

        # Анализируем приоритеты
        if 'ECONOMY_GROWTH' in priorities:
            plan['summary'] = "Экономический рост"
            plan['actions'].append({
                "type": "BUILD",
                "target": "Фабрика",
                "intensity": 0.7,
                "reason": "Увеличить производство Кристалл"
            })

        if 'ARMY_RECRUITMENT' in priorities:
            plan['summary'] += " и военная экспансия"
            plan['actions'].append({
                "type": "RECRUIT",
                "unit_class": "1",
                "priority": "HIGH",
                "reason": "Укрепить базовую армию"
            })

        if 'DEFENSE' in priorities:
            plan['actions'].append({
                "type": "BUILD",
                "target": "Больница",
                "intensity": 0.5,
                "reason": "Укрепить оборону городов"
            })

        # Добавляем действия в зависимости от личности
        if self.personality == AIPersonality.ENEMY:
            weak_target = self.find_weakest_neighbor()
            if weak_target:
                plan['actions'].append({
                    "type": "ATTACK",
                    "target_faction": weak_target['faction'],
                    "target_city": weak_target['city'],
                    "reason": "Экспансия за счет слабого соседа"
                })

        plan['reasoning'] = f"Приоритеты: {', '.join(priorities)}"
        plan['expected_outcome'] = "Укрепление позиций фракции"

        return plan

    def create_commands_for_executive(self, plan: Dict) -> List[Dict]:
        """
        Преобразует стратегический план в команды для ii.py
        Каждая команда - это вызов метода AIController
        """
        commands = []

        for action in plan.get('actions', []):
            cmd = self.translate_action_to_command(action)
            if cmd:
                commands.append(cmd)

        return commands

    def translate_action_to_command(self, action: Dict) -> Optional[Dict]:
        """Преобразует действие в команду для исполнительного модуля"""
        action_type = action.get('type')

        if action_type == "BUILD":
            target = action.get('target')
            intensity = action.get('intensity', 0.5)

            return {
                'command': 'BUILD_BUILDINGS',
                'params': {
                    'building_type': target,
                    'intensity': intensity,
                    'budget_percentage': intensity * 100
                },
                'description': f"Построить {target} с интенсивностью {intensity}"
            }

        elif action_type == "RECRUIT":
            unit_class = action.get('unit_class', '1')
            priority = action.get('priority', 'MEDIUM')

            return {
                'command': 'HIRE_ARMY',
                'params': {
                    'focus_class': unit_class,
                    'priority': priority,
                    'percentage_of_resources': 0.4 if priority == 'HIGH' else 0.2
                },
                'description': f"Нанять армию класса {unit_class} (приоритет: {priority})"
            }

        elif action_type == "ATTACK":
            target_faction = action.get('target_faction')
            target_city = action.get('target_city')

            return {
                'command': 'ATTACK_CITY',
                'params': {
                    'city_name': target_city,
                    'target_faction': target_faction,
                    'force_percentage': 0.6  # 60% сил на атаку
                },
                'description': f"Атаковать город {target_city} ({target_faction})"
            }

        elif action_type == "DIPLOMACY":
            diplomacy_action = action.get('action')
            target_faction = action.get('with_faction')

            return {
                'command': 'DIPLOMATIC_ACTION',
                'params': {
                    'action': diplomacy_action,
                    'target_faction': target_faction,
                    'intensity': 1.0
                },
                'description': f"Дипломатия: {diplomacy_action} с {target_faction}"
            }

        return None

    # ------------------------------------------------------------
    # ДИАЛОГОВАЯ СИСТЕМА
    # ------------------------------------------------------------

    def process_player_message(self, message: str, player_faction: str) -> str:
        """
        Обрабатывает сообщение от игрока и генерирует ответ
        """
        print(f"[ДИАЛОГ] Игрок ({player_faction}): {message}")

        # Сохраняем в историю
        self.conversation_history.append({
            'sender': player_faction,
            'message': message,
            'timestamp': datetime.now().isoformat()
        })

        # Обновляем личность на основе новых взаимодействий
        self.update_personality_based_on_message(message)

        # Генерируем ответ
        if self.config['use_neural_for_dialogue'] and self.neural_model:
            response = self.generate_neural_response(message, player_faction)
        else:
            response = self.generate_rule_based_response(message)

        # Сохраняем ответ в память
        self.memory.setdefault('player_interactions', []).append({
            'player_message': message,
            'ai_response': response,
            'personality': self.personality.value,
            'timestamp': datetime.now().isoformat()
        })

        return response

    def generate_neural_response(self, message: str, player_faction: str) -> str:
        """Генерирует ответ через нейросеть"""
        try:
            prompt = self.create_dialogue_prompt(message, player_faction)

            response = self.neural_model(
                prompt,
                max_tokens=150,
                temperature=0.7,
                stop=["\n\n", "Player:", "Игрок:"]
            )

            ai_response = response['choices'][0]['text'].strip()

            # Проверяем и фильтруем ответ
            ai_response = self.filter_response(ai_response)

            return ai_response

        except Exception as e:
            print(f"[ОШИБКА] Нейросеть диалога: {e}")
            return self.generate_rule_based_response(message)

    def create_dialogue_prompt(self, message: str, player_faction: str) -> str:
        """Создает промпт для диалога"""
        # Получаем текущие отношения
        relation = self.get_relation_with_player()

        # Последние 3 сообщения из истории
        recent_history = self.conversation_history[-3:] if len(self.conversation_history) > 3 else self.conversation_history

        prompt = f"""
Ты - правитель фракции "{self.faction}" в стратегической игре.
Твоя личность: {self.personality.value}
Отношения с игроком ({player_faction}): {relation}/100

ТВОЁ ТЕКУЩЕЕ СОСТОЯНИЕ:
{json.dumps(self.get_current_resources(), ensure_ascii=False)}

ИСТОРИЯ ДИАЛОГА:
{json.dumps(recent_history, ensure_ascii=False)}

Игрок ({player_faction}) говорит: "{message}"

Твой ответ должен:
1. Соответствовать личности {self.personality.value}
2. Учитывать отношения ({relation}/100)
3. Быть кратким (1-3 предложения)
4. Отвечать на суть сообщения
5. Можно предложить сделку, угрожать или обсуждать текущие события в зависимости от отношений

Ответ:
"""
        return prompt

    def generate_rule_based_response(self, message: str) -> str:
        """Rule-based ответы"""
        message_lower = message.lower()

        # Ответы по типам личности
        personality_responses = {
            AIPersonality.FRIENDLY: {
                'greeting': "Приветствую, друг! Как поживают твои земли?",
                'trade': "Я открыт для торговли. Что ты предлагаешь?",
                'threat': "Я надеюсь, нам не придется сражаться. Давай обсудим мирно.",
                'default': "Я слушаю тебя. Что ты хочешь обсудить?"
            },
            AIPersonality.NEUTRAL: {
                'greeting': "Здравствуй. У тебя есть деловое предложение?",
                'trade': "Предложи условия, и я рассмотрю их.",
                'threat': "Ты угрожаешь мне? Подумай еще раз.",
                'default': "Говори, я слушаю."
            },
            AIPersonality.HOSTILE: {
                'greeting': "Что тебе нужно? Говори быстрее.",
                'trade': "Торговля? Только на моих условиях.",
                'threat': "Ты ищешь смерти? Я исполню твое желание.",
                'default': "Не трать мое время."
            },
            AIPersonality.ENEMY: {
                'greeting': "Ты осмелился обратиться ко мне? Говори, пока я терплю.",
                'trade': "С тобой я не торгую, только воюю.",
                'threat': "Готовься к войне. Твои дни сочтены.",
                'default': "Убирайся с моих глаз."
            }
        }

        responses = personality_responses.get(self.personality, personality_responses[AIPersonality.NEUTRAL])

        # Определяем тип сообщения
        if any(word in message_lower for word in ['привет', 'здравствуй', 'добрый']):
            return responses['greeting']
        elif any(word in message_lower for word in ['торгов', 'сделк', 'обмен']):
            return responses['trade']
        elif any(word in message_lower for word in ['война', 'атака', 'нападу', 'уничтожу']):
            return responses['threat']
        else:
            return responses['default']

    # ------------------------------------------------------------
    # ВСПОМОГАТЕЛЬНЫЕ МЕТОДЫ
    # ------------------------------------------------------------

    def get_relation_with_player(self) -> int:
        """Получает текущие отношения с игроком"""
        try:
            self.cursor.execute('''
                SELECT relationship FROM relations 
                WHERE faction1 = ? AND faction2 = 'Игрок'
            ''', (self.faction,))

            result = self.cursor.fetchone()
            return result[0] if result else 0
        except:
            return 0

    def find_weakest_neighbor(self) -> Optional[Dict]:
        """Находит самого слабого соседа для атаки"""
        try:
            # Получаем всех соседей (фракции с городами рядом)
            self.cursor.execute('''
                SELECT DISTINCT c2.faction, c2.name
                FROM cities c1
                JOIN cities c2 ON c1.faction != c2.faction
                WHERE c1.faction = ?
                AND ABS(CAST(SUBSTR(c1.coordinates, 2, INSTR(c1.coordinates, ',')-2) AS INTEGER) - 
                        CAST(SUBSTR(c2.coordinates, 2, INSTR(c2.coordinates, ',')-2) AS INTEGER)) < 280
                AND ABS(CAST(SUBSTR(c1.coordinates, INSTR(c1.coordinates, ',')+1, LENGTH(c1.coordinates)-INSTR(c1.coordinates, ',')-1) AS INTEGER) - 
                        CAST(SUBSTR(c2.coordinates, INSTR(c2.coordinates, ',')+1, LENGTH(c2.coordinates)-INSTR(c2.coordinates, ',')-1) AS INTEGER)) < 280
            ''', (self.faction,))

            neighbors = self.cursor.fetchall()

            # Находим самого слабого по силе армии
            weakest = None
            min_strength = float('inf')

            for faction, city in neighbors:
                strength = self.calculate_faction_strength(faction)
                if strength < min_strength:
                    min_strength = strength
                    weakest = {'faction': faction, 'city': city, 'strength': strength}

            return weakest

        except Exception as e:
            print(f"[ОШИБКА] Поиск слабого соседа: {e}")
            return None

    def calculate_faction_strength(self, faction: str) -> int:
        """Вычисляет силу фракции"""
        try:
            self.cursor.execute('''
                SELECT SUM(g.unit_count * (u.attack + u.defense))
                FROM garrisons g
                JOIN units u ON g.unit_name = u.unit_name
                WHERE u.faction = ?
            ''', (faction,))

            result = self.cursor.fetchone()
            return result[0] if result[0] else 0
        except:
            return 0

    def filter_response(self, response: str) -> str:
        """Фильтрует ответ нейросети от нежелательного контента"""
        # Удаляем HTML/XML теги
        import re
        response = re.sub(r'<[^>]+>', '', response)

        # Ограничиваем длину
        if len(response) > 500:
            response = response[:497] + "..."

        # Заменяем нежелательные слова
        bad_words = ['смерть', 'убийство', 'насилие']
        for word in bad_words:
            response = response.replace(word, '[скрыто]')

        return response.strip()

    def update_personality_based_on_message(self, message: str):
        """Обновляет личность на основе сообщения игрока"""
        message_lower = message.lower()

        # Если игрок угрожает - становиться более враждебным
        if any(word in message_lower for word in ['уничтожу', 'убью', 'сотру', 'война']):
            if self.personality == AIPersonality.FRIENDLY:
                self.personality = AIPersonality.NEUTRAL
            elif self.personality == AIPersonality.NEUTRAL:
                self.personality = AIPersonality.HOSTILE

        # Если игрок предлагает союз - становиться дружелюбнее
        elif any(word in message_lower for word in ['союз', 'дружба', 'помощь', 'поддержка']):
            if self.personality == AIPersonality.HOSTILE:
                self.personality = AIPersonality.NEUTRAL
            elif self.personality == AIPersonality.NEUTRAL:
                self.personality = AIPersonality.FRIENDLY

    def execute_commands(self, commands: List[Dict]):
        """
        Выполняет команды через исполнительный модуль ii.py
        """
        if not self.executive:
            print("[ОШИБКА] Исполнительный модуль не подключен")
            return

        results = []

        for cmd in commands:
            try:
                result = self._execute_single_command(cmd)
                results.append({
                    'command': cmd['command'],
                    'success': True,
                    'result': result
                })
            except Exception as e:
                results.append({
                    'command': cmd['command'],
                    'success': False,
                    'error': str(e)
                })

        return results

    def _execute_single_command(self, command: Dict) -> Any:
        """Выполняет одну команду через executive (ii.py)"""
        cmd_type = command['command']
        params = command.get('params', {})

        if cmd_type == 'BUILD_BUILDINGS':
            return self.executive.build_in_city(
                building_type=params.get('building_type', 'Фабрика'),
                count=int(params.get('intensity', 0.5) * 10)  # Конвертируем в количество
            )

        elif cmd_type == 'HIRE_ARMY':
            # Активируем найм армии в ii.py
            self.executive.hire_army()
            return "Армия нанята"

        elif cmd_type == 'ATTACK_CITY':
            return self.executive.attack_city(
                city_name=params.get('city_name'),
                faction=params.get('target_faction')
            )

        elif cmd_type == 'DIPLOMATIC_ACTION':
            action = params.get('action')
            target = params.get('target_faction')

            if action == 'WAR':
                # Объявляем войну
                self.executive.update_diplomacy_status(target, "война")
                return f"Объявлена война {target}"

            elif action == 'TRADE':
                # Создаем торговое предложение
                self.cursor.execute('''
                    INSERT INTO queries (resource, faction)
                    VALUES (?, ?)
                ''', (f"Торговое предложение от {self.faction}", self.faction))
                return f"Предложена торговля {target}"

        return f"Команда {cmd_type} выполнена"

    def get_status_report(self) -> str:
        """Возвращает отчет о состоянии нейро-ИИ"""
        return f"""
=== НЕЙРО-ИИ ОТЧЕТ: {self.faction} ===
Личность: {self.personality.value}
Текущий ход: {self.get_current_turn()}
Отношения с игроком: {self.get_relation_with_player()}/100
Ресурсы: {json.dumps(self.get_current_resources(), ensure_ascii=False)}
Память: {len(self.memory.get('player_interactions', []))} взаимодействий
Нейросеть: {'Активна' if self.neural_model else 'Неактивна'}
=====================================
"""