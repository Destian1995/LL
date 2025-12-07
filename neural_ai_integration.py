# neural_ai_integration.py
import sqlite3
from typing import Dict, Any

class AIAdapter:
    """
    Адаптер для соединения NeuralAICore с AIController из ii.py
    """
    def __init__(self, faction: str, conn: sqlite3.Connection, ai_controller_instance):
        self.faction = faction
        self.conn = conn
        self.ai_controller = ai_controller_instance

        # Создаем NeuralAICore для этой фракции
        from general_ii_neiro import NeuralAICore
        self.neural_core = NeuralAICore(faction, conn)

        print(f"[АДАПТЕР] Создан для {faction}")

    def make_turn(self):
        """Выполняет ход ИИ с использованием NeuralAICore"""
        print(f"[АДАПТЕР] {self.faction} начинает ход...")

        try:
            # 1. Анализируем ситуацию с помощью NeuralAICore
            analysis = self.neural_core.analyze_situation()
            print(f"[АДАПТЕР] Анализ: {analysis}")

            # 2. Принимаем стратегические решения
            decisions = self.neural_core.make_strategic_decision()

            if decisions:
                print(f"[АДАПТЕР] Принято решений: {len(decisions)}")

                # 3. Выполняем решения
                results = self.neural_core.execute_decisions(decisions)

                # 4. Выполняем стандартные действия через AIController
                self._execute_standard_actions(analysis)

                return {
                    'decisions': decisions,
                    'results': results,
                    'analysis': analysis
                }
            else:
                # Если нет решений, выполняем стандартный ход
                print(f"[АДАПТЕР] Нет стратегических решений, стандартный ход")
                self.ai_controller.make_turn()

                return {
                    'decisions': [],
                    'results': [],
                    'analysis': analysis
                }

        except Exception as e:
            print(f"[АДАПТЕР] Ошибка хода {self.faction}: {e}")

            # В случае ошибки - выполняем стандартный ход
            self.ai_controller.make_turn()
            return {'error': str(e)}

    def _execute_standard_actions(self, analysis: Dict[str, Any]):
        """Выполняет стандартные действия на основе анализа"""
        try:
            # Если проигрываем - фокусируемся на обороне
            if analysis.get('is_losing', False):
                print(f"[АДАПТЕР] {self.faction} проигрывает, фокус на обороне")

                # Строим оборонительные здания
                self._build_defensive_buildings()

                # Нанимаем армию для защиты
                self._hire_defensive_army()

            # Если можем атаковать - нанимаем атакующую армию
            elif analysis.get('can_attack', False):
                print(f"[АДАПТЕР] {self.faction} может атаковать")

                # Нанимаем атакующую армию
                self._hire_attacking_army()

            # Если все стабильно - развиваем экономику
            else:
                print(f"[АДАПТЕР] {self.faction} стабилен, развиваем экономику")

                # Строим экономические здания
                self._build_economic_buildings()

                # Нанимаем базовую армию
                self._hire_basic_army()

        except Exception as e:
            print(f"[АДАПТЕР] Ошибка выполнения действий: {e}")

    def _build_defensive_buildings(self):
        """Строит оборонительные здания"""
        try:
            # Больницы для защиты
            print(f"[АДАПТЕР] {self.faction} строит оборонительные здания")

            # Вызываем метод AIController для строительства
            # (заглушка - нужно адаптировать под реальный интерфейс)
            if hasattr(self.ai_controller, 'build_defensive'):
                self.ai_controller.build_defensive()

        except Exception as e:
            print(f"[АДАПТЕР] Ошибка строительства обороны: {e}")

    def _hire_defensive_army(self):
        """Нанимает оборонительную армию"""
        try:
            print(f"[АДАПТЕР] {self.faction} нанимает оборонительную армию")

            # Вызываем метод найма армии
            if hasattr(self.ai_controller, 'hire_army'):
                self.ai_controller.hire_army()

        except Exception as e:
            print(f"[АДАПТЕР] Ошибка найма обороны: {e}")

    def _hire_attacking_army(self):
        """Нанимает атакующую армию"""
        try:
            print(f"[АДАПТЕР] {self.faction} нанимает атакующую армию")

            # Вызываем метод найма армии с параметрами атаки
            if hasattr(self.ai_controller, 'hire_attack_army'):
                self.ai_controller.hire_attack_army()
            elif hasattr(self.ai_controller, 'hire_army'):
                self.ai_controller.hire_army()

        except Exception as e:
            print(f"[АДАПТЕР] Ошибка найма атаки: {e}")

    def _build_economic_buildings(self):
        """Строит экономические здания"""
        try:
            print(f"[АДАПТЕР] {self.faction} строит экономические здания")

            if hasattr(self.ai_controller, 'build_economic'):
                self.ai_controller.build_economic()

        except Exception as e:
            print(f"[АДАПТЕР] Ошибка строительства экономики: {e}")

    def _hire_basic_army(self):
        """Нанимает базовую армию"""
        try:
            print(f"[АДАПТЕР] {self.faction} нанимает базовую армию")

            if hasattr(self.ai_controller, 'hire_army'):
                self.ai_controller.hire_army()

        except Exception as e:
            print(f"[АДАПТЕР] Ошибка найма базовой армии: {e}")

    def process_player_message(self, player_message: str) -> str:
        """Обрабатывает сообщение игрока"""
        return self.neural_core.process_player_message(player_message)

    def get_status(self) -> Dict[str, Any]:
        """Возвращает статус ИИ"""
        return self.neural_core.get_status()


class NeuralAIIntegration:
    """
    Главный класс для интеграции NeuralAICore с игрой
    """

    def __init__(self, player_faction: str, conn: sqlite3.Connection):
        self.player_faction = player_faction
        self.conn = conn
        self.ai_adapters = {}  # {faction: AIAdapter}

        print(f"[ИНТЕГРАЦИЯ] Инициализирован для игрока {player_faction}")

    def create_controller_for_faction(self, faction: str):
        """
        Создает адаптер для фракции
        Вместо прямого создания AIController, создаем адаптер
        """
        try:
            # Сначала получаем стандартный AIController
            from ii import AIController
            standard_controller = AIController(faction, self.conn)

            # Создаем адаптер, который обернет стандартный контроллер
            adapter = AIAdapter(faction, self.conn, standard_controller)
            self.ai_adapters[faction] = adapter

            print(f"[ИНТЕГРАЦИЯ] Создан адаптер для {faction}")
            return adapter

        except Exception as e:
            print(f"[ИНТЕГРАЦИЯ] Ошибка создания адаптера для {faction}: {e}")

            # Если не удалось создать адаптер, возвращаем стандартный контроллер
            from ii import AIController
            return AIController(faction, self.conn)

    def make_all_turns(self) -> Dict[str, Any]:
        """
        Выполняет ходы для всех фракций ИИ
        """
        results = {}

        for faction, adapter in self.ai_adapters.items():
            try:
                print(f"[ИНТЕГРАЦИЯ] Выполняем ход для {faction}...")
                turn_result = adapter.make_turn()
                results[faction] = turn_result

            except Exception as e:
                print(f"[ИНТЕГРАЦИЯ] Ошибка хода {faction}: {e}")
                results[faction] = {'error': str(e)}

        return results

    def handle_player_conversation(self, ai_faction: str, player_message: str) -> str:
        """
        Обрабатывает разговор игрока с фракцией ИИ
        """
        if ai_faction in self.ai_adapters:
            try:
                return self.ai_adapters[ai_faction].process_player_message(player_message)
            except Exception as e:
                print(f"[ИНТЕГРАЦИЯ] Ошибка диалога с {ai_faction}: {e}")
                return "Произошла ошибка при обработке сообщения."
        else:
            return "Эта фракция недоступна для диалога."

    def update_game_state(self, turn_counter: int, player_faction: str):
        """
        Обновляет состояние игры
        """
        print(f"[ИНТЕГРАЦИЯ] Обновление состояния (ход {turn_counter})")

        # Обновляем все адаптеры
        for faction, adapter in self.ai_adapters.items():
            try:
                # Пересоздаем NeuralAICore с новыми данными
                from general_ii_neiro import NeuralAICore
                adapter.neural_core = NeuralAICore(faction, self.conn)

            except Exception as e:
                print(f"[ИНТЕГРАЦИЯ] Ошибка обновления {faction}: {e}")

    def get_ai_status(self) -> Dict[str, Dict]:
        """
        Возвращает статус всех фракций ИИ
        """
        status = {}

        for faction, adapter in self.ai_adapters.items():
            try:
                status[faction] = adapter.get_status()
            except Exception as e:
                status[faction] = {'error': str(e)}

        return status

    def train_on_game_data(self, game_data: Dict):
        """
        Сохраняет данные игры для анализа
        """
        try:
            cursor = self.conn.cursor()

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS neural_ai_training (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    turn INTEGER,
                    data TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            import json
            data_json = json.dumps(game_data, ensure_ascii=False)

            cursor.execute('''
                INSERT INTO neural_ai_training (turn, data)
                VALUES (?, ?)
            ''', (game_data.get('turn', 0), data_json))

            self.conn.commit()
            print(f"[ИНТЕГРАЦИЯ] Данные сохранены для обучения")

        except Exception as e:
            print(f"[ИНТЕГРАЦИЯ] Ошибка сохранения данных: {e}")

    def cleanup(self):
        """
        Очищает ресурсы
        """
        print("[ИНТЕГРАЦИЯ] Очистка...")

        for faction, adapter in self.ai_adapters.items():
            try:
                if hasattr(adapter.neural_core, 'cleanup'):
                    adapter.neural_core.cleanup()
            except:
                pass

        self.ai_adapters.clear()
        print("[ИНТЕГРАЦИЯ] Очистка завершена")


# -------------------------------------------------------------------
# ФУНКЦИЯ ДЛЯ БЫСТРОГО СОЗДАНИЯ ИНТЕГРАЦИИ
# -------------------------------------------------------------------

def create_neural_ai_integration(player_faction: str, conn: sqlite3.Connection) -> NeuralAIIntegration:
    """
    Создает и возвращает объект интеграции Neural AI
    """
    return NeuralAIIntegration(player_faction, conn)


