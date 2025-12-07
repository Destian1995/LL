# general_ii_neiro.py
import sqlite3
import json
import random
from typing import Dict, List, Any, Optional
from datetime import datetime
from enum import Enum

class AIPersonality(Enum):
    """Типы личности ИИ"""
    FRIENDLY = "friendly"      # Дружелюбный (отношения > 60)
    NEUTRAL = "neutral"        # Нейтральный (отношения 30-60)
    HOSTILE = "hostile"        # Враждебный (отношения 10-30)
    ENEMY = "enemy"            # Враг (отношения < 10)

class DiplomaticStage(Enum):
    """Этапы переговоров"""
    STAGE_1 = "stage_1"        # Просто предложение мира
    STAGE_2 = "stage_2"        # 25% ресурсов
    STAGE_3 = "stage_3"        # 60% ресурсов + союз

class StrategicDecision(Enum):
    """Типы стратегических решений"""
    PEACE_PROPOSAL = "peace_proposal"
    HELP_REQUEST = "help_request"
    WAR_INVITATION = "war_invitation"
    TRADE_OFFER = "trade_offer"
    ALLIANCE_OFFER = "alliance_offer"

class NeuralAICore:
    """
    Основной класс нейро-ИИ для одной фракции
    """

    def __init__(self, faction: str, conn: sqlite3.Connection):
        self.faction = faction
        self.conn = conn
        self.cursor = conn.cursor()

        # Состояние ИИ
        self.personality = self.determine_personality()
        self.peace_proposals = {}  # {target_faction: stage}
        self.memory = self.load_memory()

        # Пороговые значения
        self.thresholds = {
            'min_cities_for_help': 4,
            'max_enemies_for_peace': 2,
            'good_relation': 60,
            'weak_army_ratio': 0.5,
            'strong_army_ratio': 1.5
        }

        print(f"[ИИ] Инициализирован для {faction} ({self.personality.value})")

    def load_memory(self) -> Dict:
        """Загружает память ИИ из БД"""
        try:
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS ai_memory (
                    faction TEXT PRIMARY KEY,
                    data TEXT,
                    updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            self.cursor.execute(
                "SELECT data FROM ai_memory WHERE faction = ?",
                (self.faction,)
            )
            result = self.cursor.fetchone()

            if result and result[0]:
                return json.loads(result[0])
            else:
                return {
                    'interactions': [],
                    'decisions': [],
                    'offers_sent': [],
                    'requests_sent': []
                }

        except Exception as e:
            print(f"[ИИ] Ошибка загрузки памяти: {e}")
            return {'interactions': [], 'decisions': []}

    def save_memory(self):
        """Сохраняет память ИИ"""
        try:
            data_json = json.dumps(self.memory, ensure_ascii=False)

            self.cursor.execute('''
                INSERT OR REPLACE INTO ai_memory (faction, data)
                VALUES (?, ?)
            ''', (self.faction, data_json))

            self.conn.commit()
        except Exception as e:
            print(f"[ИИ] Ошибка сохранения памяти: {e}")

    def determine_personality(self) -> AIPersonality:
        """Определяет личность на основе отношений с игроком"""
        try:
            relation = self.get_relation_with_player()

            if relation > 60:
                return AIPersonality.FRIENDLY
            elif relation > 30:
                return AIPersonality.NEUTRAL
            elif relation > 10:
                return AIPersonality.HOSTILE
            else:
                return AIPersonality.ENEMY

        except Exception:
            return AIPersonality.NEUTRAL

    def get_relation_with_player(self) -> int:
        """Получает отношения с игроком"""
        try:
            self.cursor.execute('''
                SELECT relationship FROM relations 
                WHERE faction1 = ? AND faction2 = ?
            ''', (self.faction, 'Игрок'))

            result = self.cursor.fetchone()
            return result[0] if result else 0
        except:
            return 0

    def get_city_count(self) -> int:
        """Получает количество городов"""
        try:
            self.cursor.execute('''
                SELECT COUNT(*) FROM cities WHERE faction = ?
            ''', (self.faction,))
            result = self.cursor.fetchone()
            return result[0] if result else 0
        except:
            return 0

    def get_army_strength(self) -> int:
        """Получает силу армии"""
        try:
            self.cursor.execute('''
                SELECT SUM(g.unit_count * (u.attack + u.defense))
                FROM garrisons g
                JOIN units u ON g.unit_name = u.unit_name
                JOIN cities c ON g.city_name = c.name
                WHERE c.faction = ?
            ''', (self.faction,))

            result = self.cursor.fetchone()
            return result[0] if result[0] else 0
        except:
            return 0

    def get_enemies(self) -> List[str]:
        """Получает список врагов"""
        enemies = []
        try:
            self.cursor.execute('''
                SELECT faction2 FROM diplomacies 
                WHERE faction1 = ? AND relationship = 'война'
            ''', (self.faction,))

            for row in self.cursor.fetchall():
                enemies.append(row[0])
        except:
            pass

        return enemies

    def get_allies(self) -> List[str]:
        """Получает список союзников"""
        allies = []
        try:
            self.cursor.execute('''
                SELECT faction2 FROM diplomacies 
                WHERE faction1 = ? AND relationship = 'союз'
            ''', (self.faction,))

            for row in self.cursor.fetchall():
                allies.append(row[0])
        except:
            pass

        return allies

    def analyze_situation(self) -> Dict[str, Any]:
        """
        Анализирует текущую ситуацию для принятия решений
        """
        city_count = self.get_city_count()
        army_strength = self.get_army_strength()
        enemies = self.get_enemies()
        allies = self.get_allies()

        # Получаем силу всех врагов
        enemy_strength = 0
        for enemy in enemies:
            enemy_strength += self.get_faction_strength(enemy)

        # Анализируем состояние
        analysis = {
            'city_count': city_count,
            'army_strength': army_strength,
            'enemy_count': len(enemies),
            'enemy_strength': enemy_strength,
            'ally_count': len(allies),
            'is_losing': city_count < 3 or (enemy_strength > army_strength * 2),
            'has_many_enemies': len(enemies) > 2,
            'needs_help': city_count < self.thresholds['min_cities_for_help'],
            'can_attack': army_strength > 100 and len(enemies) < 2,
            'player_relation': self.get_relation_with_player()
        }

        return analysis

    def get_faction_strength(self, faction: str) -> int:
        """Получает силу фракции"""
        try:
            self.cursor.execute('''
                SELECT SUM(g.unit_count * (u.attack + u.defense))
                FROM garrisons g
                JOIN units u ON g.unit_name = u.unit_name
                JOIN cities c ON g.city_name = c.name
                WHERE c.faction = ?
            ''', (faction,))

            result = self.cursor.fetchone()
            return result[0] if result[0] else 0
        except:
            return 0

    def get_resources(self) -> Dict[str, int]:
        """Получает ресурсы фракции"""
        resources = {}
        try:
            self.cursor.execute('''
                SELECT resource_type, amount FROM resources 
                WHERE faction = ?
            ''', (self.faction,))

            for resource_type, amount in self.cursor.fetchall():
                resources[resource_type] = amount
        except:
            pass

        return resources

    def make_strategic_decision(self) -> List[Dict[str, Any]]:
        """
        Принимает стратегические решения на основе анализа
        Возвращает список решений для выполнения
        """
        decisions = []
        analysis = self.analyze_situation()

        # 1. Если проигрываем - предлагаем мир
        if analysis['is_losing'] or analysis['has_many_enemies']:
            strongest_enemy = self.find_strongest_enemy()
            if strongest_enemy:
                stage = self.get_next_peace_stage(strongest_enemy)
                decisions.append({
                    'type': StrategicDecision.PEACE_PROPOSAL,
                    'target': strongest_enemy,
                    'stage': stage,
                    'reason': 'Проигрываем или много врагов'
                })

        # 2. Если мало городов - просим помощи у союзников
        if analysis['needs_help']:
            good_allies = self.find_good_allies()
            for ally in good_allies:
                decisions.append({
                    'type': StrategicDecision.HELP_REQUEST,
                    'target': ally,
                    'reason': 'Мало городов для обороны'
                })

        # 3. Если много врагов - приглашаем на войну
        if analysis['has_many_enemies']:
            potential_allies = self.find_potential_war_allies()
            weakest_enemy = self.find_weakest_enemy()

            if potential_allies and weakest_enemy:
                for ally in potential_allies[:2]:  # Не более 2 приглашений
                    decisions.append({
                        'type': StrategicDecision.WAR_INVITATION,
                        'target': ally,
                        'enemy': weakest_enemy,
                        'reason': 'Много врагов, нужна помощь'
                    })

        # 4. Если хорошие отношения с игроком - предлагаем союз
        if analysis['player_relation'] > 70 and self.personality != AIPersonality.ENEMY:
            decisions.append({
                'type': StrategicDecision.ALLIANCE_OFFER,
                'target': 'Игрок',
                'reason': 'Отличные отношения'
            })

        # 5. Если есть ресурсы - предлагаем торговлю
        resources = self.get_resources()
        if resources.get('Кристаллы', 0) > 500 or resources.get('Кроны', 0) > 2000:
            trade_partner = self.find_trade_partner()
            if trade_partner:
                decisions.append({
                    'type': StrategicDecision.TRADE_OFFER,
                    'target': trade_partner,
                    'reason': 'Избыток ресурсов'
                })

        # Ограничиваем количество решений (максимум 3 за ход)
        decisions = decisions[:3]

        # Сохраняем решения в память
        for decision in decisions:
            self.memory.setdefault('decisions', []).append({
                'type': decision['type'].value,
                'target': decision.get('target'),
                'reason': decision.get('reason'),
                'timestamp': datetime.now().isoformat()
            })

        self.save_memory()

        return decisions

    def find_strongest_enemy(self) -> Optional[str]:
        """Находит самого сильного врага"""
        enemies = self.get_enemies()
        strongest = None
        max_strength = 0

        for enemy in enemies:
            strength = self.get_faction_strength(enemy)
            if strength > max_strength:
                max_strength = strength
                strongest = enemy

        return strongest

    def find_weakest_enemy(self) -> Optional[str]:
        """Находит самого слабого врага"""
        enemies = self.get_enemies()
        weakest = None
        min_strength = float('inf')

        for enemy in enemies:
            strength = self.get_faction_strength(enemy)
            if strength < min_strength:
                min_strength = strength
                weakest = enemy

        return weakest

    def find_good_allies(self) -> List[str]:
        """Находит союзников с хорошими отношениями"""
        good_allies = []
        allies = self.get_allies()

        for ally in allies:
            relation = self.get_relation_with_faction(ally)
            if relation > self.thresholds['good_relation']:
                good_allies.append(ally)

        return good_allies

    def find_potential_war_allies(self) -> List[str]:
        """Находит потенциальных союзников для войны"""
        potential = []

        # Все фракции кроме нас и врагов
        all_factions = ['Север', 'Эльфы', 'Адепты', 'Вампиры', 'Элины', 'Игрок']
        enemies = self.get_enemies()

        for faction in all_factions:
            if faction != self.faction and faction not in enemies:
                relation = self.get_relation_with_faction(faction)
                if relation > 30:  # Хотя бы нейтральные отношения
                    potential.append(faction)

        return potential

    def find_trade_partner(self) -> Optional[str]:
        """Находит партнера для торговли"""
        all_factions = ['Север', 'Эльфы', 'Адепты', 'Вампиры', 'Элины', 'Игрок']

        for faction in all_factions:
            if faction != self.faction:
                relation = self.get_relation_with_faction(faction)
                if 20 < relation < 80:  # Не враги и не лучшие друзья
                    return faction

        return None

    def get_relation_with_faction(self, target_faction: str) -> int:
        """Получает отношения с фракцией"""
        try:
            self.cursor.execute('''
                SELECT relationship FROM relations 
                WHERE faction1 = ? AND faction2 = ?
            ''', (self.faction, target_faction))

            result = self.cursor.fetchone()
            return result[0] if result else 0
        except:
            return 0

    def get_next_peace_stage(self, target_faction: str) -> DiplomaticStage:
        """Определяет следующий этап мирных переговоров"""
        if target_faction not in self.peace_proposals:
            self.peace_proposals[target_faction] = DiplomaticStage.STAGE_1
        else:
            current = self.peace_proposals[target_faction]

            if current == DiplomaticStage.STAGE_1:
                self.peace_proposals[target_faction] = DiplomaticStage.STAGE_2
            elif current == DiplomaticStage.STAGE_2:
                self.peace_proposals[target_faction] = DiplomaticStage.STAGE_3

        return self.peace_proposals[target_faction]

    def execute_decisions(self, decisions: List[Dict]) -> List[Dict]:
        """
        Выполняет принятые решения
        """
        results = []

        for decision in decisions:
            try:
                result = self._execute_decision(decision)
                results.append({
                    'decision': decision['type'].value,
                    'target': decision.get('target'),
                    'success': True,
                    'result': result
                })

                # Сохраняем в историю предложений
                self.memory.setdefault('offers_sent', []).append({
                    'type': decision['type'].value,
                    'target': decision.get('target'),
                    'result': result,
                    'timestamp': datetime.now().isoformat()
                })

            except Exception as e:
                results.append({
                    'decision': decision['type'].value,
                    'target': decision.get('target'),
                    'success': False,
                    'error': str(e)
                })

        self.save_memory()
        return results

    def _execute_decision(self, decision: Dict) -> str:
        """Выполняет одно решение"""
        decision_type = decision['type']
        target = decision.get('target')

        if decision_type == StrategicDecision.PEACE_PROPOSAL:
            stage = decision.get('stage', DiplomaticStage.STAGE_1)
            return self._send_peace_proposal(target, stage)

        elif decision_type == StrategicDecision.HELP_REQUEST:
            return self._send_help_request(target)

        elif decision_type == StrategicDecision.WAR_INVITATION:
            enemy = decision.get('enemy')
            return self._send_war_invitation(target, enemy)

        elif decision_type == StrategicDecision.TRADE_OFFER:
            return self._send_trade_offer(target)

        elif decision_type == StrategicDecision.ALLIANCE_OFFER:
            return self._send_alliance_offer(target)

        else:
            return "Неизвестный тип решения"

    def _send_peace_proposal(self, target_faction: str, stage: DiplomaticStage) -> str:
        """Отправляет предложение мира"""
        # Сохраняем в историю переговоров
        self._save_to_negotiation_history(
            target_faction,
            f"Предложение мира (этап {stage.value})"
        )

        # Создаем сообщение
        if stage == DiplomaticStage.STAGE_1:
            message = f"Предлагаю прекратить войну. Давай заключим мир."
        elif stage == DiplomaticStage.STAGE_2:
            resources = self.get_resources()
            offer = {}
            for res in ['Кроны', 'Кристаллы']:
                if res in resources:
                    offer[res] = int(resources[res] * 0.25)
            message = f"Предлагаю мир в обмен на 25% ресурсов: {offer}"
        else:  # STAGE_3
            resources = self.get_resources()
            offer = {}
            for res in ['Кроны', 'Кристаллы', 'Рабочие']:
                if res in resources:
                    offer[res] = int(resources[res] * 0.6)
            message = f"Предлагаю мир, союз и 60% ресурсов: {offer}"

        return f"Отправлено предложение мира {target_faction}: {message}"

    def _send_help_request(self, target_faction: str) -> str:
        """Отправляет запрос помощи"""
        city_count = self.get_city_count()

        if city_count < 3:
            message = f"У нас осталось всего {city_count} города! Просим срочной военной помощи!"
        else:
            message = f"Нас атакуют! Просим помощи, {target_faction}!"

        self._save_to_negotiation_history(target_faction, message)
        return f"Отправлен запрос помощи {target_faction}"

    def _send_war_invitation(self, target_faction: str, enemy: str) -> str:
        """Отправляет приглашение на войну"""
        message = f"Давайте вместе атакуем {enemy}! Вместе мы сильнее!"

        self._save_to_negotiation_history(target_faction, message)
        return f"Отправлено приглашение на войну {target_faction} против {enemy}"

    def _send_trade_offer(self, target_faction: str) -> str:
        """Отправляет торговое предложение"""
        resources = self.get_resources()

        # Находим, что можем предложить
        for resource in ['Кристаллы', 'Кроны', 'Рабочие']:
            if resources.get(resource, 0) > 100:
                message = f"Предлагаю торговлю {resource}. Что можете предложить взамен?"
                break
        else:
            message = "Предлагаю взаимовыгодную торговлю."

        self._save_to_negotiation_history(target_faction, message)
        return f"Отправлено торговое предложение {target_faction}"

    def _send_alliance_offer(self, target_faction: str) -> str:
        """Отправляет предложение союза"""
        message = f"Давайте заключим союз! Вместе мы непобедимы!"

        self._save_to_negotiation_history(target_faction, message)
        return f"Отправлено предложение союза {target_faction}"

    def _save_to_negotiation_history(self, target_faction: str, message: str):
        """Сохраняет переговоры в историю"""
        try:
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS negotiation_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    faction1 TEXT,
                    faction2 TEXT,
                    message TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            self.cursor.execute('''
                INSERT INTO negotiation_history (faction1, faction2, message)
                VALUES (?, ?, ?)
            ''', (self.faction, target_faction, message))

            self.conn.commit()
        except Exception as e:
            print(f"[ИИ] Ошибка сохранения истории переговоров: {e}")

    def process_player_message(self, player_message: str) -> str:
        """
        Обрабатывает сообщение от игрока
        Возвращает ответ ИИ
        """
        print(f"[ИИ] Игрок: {player_message}")

        # Сохраняем взаимодействие
        self.memory.setdefault('interactions', []).append({
            'message': player_message,
            'timestamp': datetime.now().isoformat(),
            'personality': self.personality.value
        })

        # Генерируем ответ
        response = self._generate_response(player_message)

        self.save_memory()
        return response

    def _generate_response(self, message: str) -> str:
        """Генерирует ответ на сообщение игрока"""
        message_lower = message.lower()

        # Ответы в зависимости от личности
        responses = {
            AIPersonality.FRIENDLY: {
                'peace': "Конечно, давай заключим мир! Мы же друзья!",
                'war': "Не надо войны! Мы можем договориться!",
                'trade': "С удовольствием! Что предлагаешь?",
                'alliance': "Отличная идея! Давай заключим союз!",
                'help': "Конечно помогу! Что случилось?",
                'default': "Приветствую, друг! Как дела?"
            },
            AIPersonality.NEUTRAL: {
                'peace': "Мир возможен. Какие условия?",
                'war': "Война никому не нужна. Что ты предлагаешь?",
                'trade': "Рассмотрю твое предложение.",
                'alliance': "Союз требует взаимных обязательств.",
                'help': "Помощь возможна. Что случилось?",
                'default': "Здравствуй. Что привело тебя ко мне?"
            },
            AIPersonality.HOSTILE: {
                'peace': "Мир? На каких условиях?",
                'war': "Угрожаешь? Я готов дать отпор!",
                'trade': "Торговля? Только на выгодных для меня условиях.",
                'alliance': "Сначала докажи свою надежность.",
                'help': "Помощь? А что ты предложишь взамен?",
                'default': "Что тебе нужно? Говори быстрее."
            },
            AIPersonality.ENEMY: {
                'peace': "Мир? После всего, что было?",
                'war': "Наконец-то! Я ждал этого!",
                'trade': "Торговать с врагом? Ты шутишь?",
                'alliance': "Союз с тобой? Никогда!",
                'help': "Просишь помощи у врага? Смешно.",
                'default': "Ты осмелился обратиться ко мне?"
            }
        }

        # Определяем тип сообщения
        if any(word in message_lower for word in ['мир', 'перемирие']):
            msg_type = 'peace'
        elif any(word in message_lower for word in ['война', 'атака', 'нападу']):
            msg_type = 'war'
        elif any(word in message_lower for word in ['торгов', 'сделк', 'обмен']):
            msg_type = 'trade'
        elif any(word in message_lower for word in ['союз', 'дружба']):
            msg_type = 'alliance'
        elif any(word in message_lower for word in ['помощ', 'помоги']):
            msg_type = 'help'
        else:
            msg_type = 'default'

        # Получаем ответ
        personality_responses = responses.get(self.personality, responses[AIPersonality.NEUTRAL])
        response = personality_responses.get(msg_type, personality_responses['default'])

        return response

    def get_status(self) -> Dict[str, Any]:
        """Возвращает статус ИИ"""
        analysis = self.analyze_situation()

        return {
            'faction': self.faction,
            'personality': self.personality.value,
            'city_count': analysis['city_count'],
            'army_strength': analysis['army_strength'],
            'enemy_count': analysis['enemy_count'],
            'player_relation': analysis['player_relation'],
            'is_losing': analysis['is_losing']
        }

    def cleanup(self):
        """Очистка ресурсов"""
        self.save_memory()


# -------------------------------------------------------------------
# КЛАСС ДЛЯ ИНТЕГРАЦИИ С ИГРОЙ
# -------------------------------------------------------------------

class NeuralAIIntegration:
    """
    Класс для управления всеми фракциями ИИ в игре
    """

    def __init__(self, player_faction: str, conn: sqlite3.Connection):
        self.player_faction = player_faction
        self.conn = conn
        self.ai_cores = {}  # {faction: NeuralAICore}

        self.initialize_ai_cores()
        print(f"[ИИ-ИНТЕГРАЦИЯ] Инициализирован для игрока {player_faction}")

    def initialize_ai_cores(self):
        """Инициализирует NeuralAICore для всех фракций ИИ"""
        ai_factions = ['Север', 'Эльфы', 'Адепты', 'Вампиры', 'Элины']

        for faction in ai_factions:
            if faction != self.player_faction:
                try:
                    self.ai_cores[faction] = NeuralAICore(faction, self.conn)
                except Exception as e:
                    print(f"[ИИ] Ошибка создания ИИ для {faction}: {e}")

    def make_all_turns(self) -> Dict[str, List[Dict]]:
        """
        Выполняет ход для всех фракций ИИ
        Возвращает результаты решений
        """
        results = {}

        for faction, ai_core in self.ai_cores.items():
            try:
                # Принимаем стратегические решения
                decisions = ai_core.make_strategic_decision()

                # Выполняем решения
                execution_results = ai_core.execute_decisions(decisions)

                results[faction] = {
                    'decisions': decisions,
                    'results': execution_results
                }

                print(f"[ИИ] {faction} принял {len(decisions)} решений")

            except Exception as e:
                print(f"[ИИ] Ошибка хода {faction}: {e}")
                results[faction] = {'error': str(e)}

        return results

    def handle_player_conversation(self, ai_faction: str, player_message: str) -> str:
        """
        Обрабатывает сообщение игрока к фракции ИИ
        Возвращает ответ ИИ
        """
        if ai_faction not in self.ai_cores:
            return "Эта фракция недоступна для диалога."

        try:
            ai_core = self.ai_cores[ai_faction]
            response = ai_core.process_player_message(player_message)
            return response

        except Exception as e:
            print(f"[ИИ] Ошибка диалога с {ai_faction}: {e}")
            return "Произошла ошибка. Попробуйте позже."

    def get_ai_status(self) -> Dict[str, Dict]:
        """
        Возвращает статус всех фракций ИИ
        """
        status = {}

        for faction, ai_core in self.ai_cores.items():
            try:
                status[faction] = ai_core.get_status()
            except:
                status[faction] = {'error': 'Не удалось получить статус'}

        return status

    def update_game_state(self, turn_counter: int):
        """
        Обновляет состояние игры для ИИ
        """
        print(f"[ИИ] Обновление состояния (ход {turn_counter})")

        for faction, ai_core in self.ai_cores.items():
            try:
                # Обновляем личность на основе новых отношений
                ai_core.personality = ai_core.determine_personality()

                # Сохраняем память
                ai_core.save_memory()

            except Exception as e:
                print(f"[ИИ] Ошибка обновления {faction}: {e}")

    def train_on_game_data(self, game_data: Dict):
        """
        Сохраняет данные игры для анализа (упрощенная версия)
        """
        try:
            cursor = self.conn.cursor()

            # Создаем таблицу для данных
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS ai_game_data (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    turn INTEGER,
                    data TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            # Сохраняем данные
            data_json = json.dumps(game_data, ensure_ascii=False)
            cursor.execute('''
                INSERT INTO ai_game_data (turn, data)
                VALUES (?, ?)
            ''', (game_data.get('turn', 0), data_json))

            self.conn.commit()
            print(f"[ИИ] Данные игры сохранены (ход {game_data.get('turn', 0)})")

        except Exception as e:
            print(f"[ИИ] Ошибка сохранения данных: {e}")

    def create_controller_for_faction(self, faction: str):
        """
        Создает прокси-контроллер для интеграции с ii.py
        """
        if faction not in self.ai_cores:
            print(f"[ИИ] Нет ИИ для фракции {faction}")
            return None

        # Создаем простой прокси-класс
        class AIControllerProxy:
            def __init__(self, faction, ai_core):
                self.faction = faction
                self.ai_core = ai_core

            def make_turn(self):
                """Выполняет ход ИИ"""
                try:
                    decisions = self.ai_core.make_strategic_decision()
                    results = self.ai_core.execute_decisions(decisions)

                    print(f"[AIControllerProxy] {self.faction} выполнил ход: {len(results)} результатов")

                    # Здесь можно добавить вызовы к ii.py для реальных действий
                    # Например: строительство, найм армии, атаки

                    return True

                except Exception as e:
                    print(f"[AIControllerProxy] Ошибка хода {self.faction}: {e}")
                    return False

            def hire_army(self):
                """Упрощенный найм армии"""
                print(f"[AIControllerProxy] {self.faction} нанимает армию")
                return True

            def build_in_city(self, building_type: str, count: int):
                """Упрощенное строительство"""
                print(f"[AIControllerProxy] {self.faction} строит {building_type} x{count}")
                return True

        return AIControllerProxy(faction, self.ai_cores[faction])

    def cleanup(self):
        """Очистка всех ресурсов"""
        print("[ИИ] Очистка всех ядер ИИ...")

        for faction, ai_core in self.ai_cores.items():
            try:
                ai_core.cleanup()
                print(f"[ИИ] Очищен ИИ {faction}")
            except Exception as e:
                print(f"[ИИ] Ошибка очистки {faction}: {e}")

        self.ai_cores.clear()
        print("[ИИ] Все ядра ИИ очищены")


# -------------------------------------------------------------------
# УТИЛИТЫ ДЛЯ БАЗЫ ДАННЫХ
# -------------------------------------------------------------------

def initialize_ai_database(conn: sqlite3.Connection):
    """
    Инициализирует таблицы для ИИ в базе данных
    """
    cursor = conn.cursor()

    try:
        # Таблица памяти ИИ
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS ai_memory (
                faction TEXT PRIMARY KEY,
                data TEXT,
                updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Таблица истории переговоров
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS negotiation_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                faction1 TEXT,
                faction2 TEXT,
                message TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Таблица данных игры
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS ai_game_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                turn INTEGER,
                data TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        conn.commit()
        print("[БД] Таблицы ИИ инициализированы")

    except Exception as e:
        print(f"[БД] Ошибка инициализации: {e}")
        conn.rollback()


