# main_ai_controller.py
import sqlite3
from ii import AIController

def initialize_all_ai_factions(db_path='lerdon.db'):
    """
    Инициализирует AI контроллеры для всех фракций
    """
    conn = sqlite3.connect(db_path)

    # Получаем список всех фракций (кроме игрока)
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT faction FROM cities WHERE faction != 'Игрок'")
    factions = [row[0] for row in cursor.fetchall()]

    ai_controllers = {}

    for faction in factions:
        ai = AIController(
            faction=faction,
            conn=conn,
            season_manager=None,  # Передайте сюда ваш SeasonManager
            use_neural_ai=True    # Включить нейро-ИИ
        )
        ai_controllers[faction] = ai

    return ai_controllers, conn

def run_ai_turn(ai_controllers):
    """
    Выполняет ход для всех ИИ фракций
    """
    results = {}

    for faction, ai in ai_controllers.items():
        print(f"\n{'='*60}")
        print(f"ХОД ФРАКЦИИ: {faction}")
        print(f"{'='*60}")

        result = ai.make_turn()
        results[faction] = result

    return results

# Пример использования
if __name__ == "__main__":
    # Инициализация
    all_ai, db_conn = initialize_all_ai_factions()

    # Выполнение хода
    results = run_ai_turn(all_ai)

    # Пример диалога с игроком
    player_message = "Привет, давай заключим союз"
    for faction, ai in all_ai.items():
        response = ai.process_player_dialogue(player_message)
        print(f"{faction}: {response}")

    db_conn.close()