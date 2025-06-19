import unittest
from unittest.mock import MagicMock, patch
from fight import fight

def create_test_unit(name, count, damage=100, health=100, armor=100, unit_class='1'):
    """Фабрика для создания тестовых юнитов"""
    return [{
        'unit_name': name,
        'unit_count': count,
        'unit_image': f'files/army/{name}.jpg',
        'units_stats': {
            'Урон': damage,
            'Живучесть': health,
            'Защита': armor,
            'Класс юнита': unit_class
        },
        'initial_count': count,
        'killed_count': 0
    }]


class TestBattleSystem(unittest.TestCase):

    @patch('fight.update_results_table')
    def test_simple_battle(self, mock_update_results):
        """Тест: простой бой 100 стрелков против 50 пехотинцев"""
        attacking_army = create_test_unit('Стрелок', 100, damage=100, health=50, armor=20, unit_class='1')
        defending_army = create_test_unit('Пехотинец', 50, damage=80, health=60, armor=30, unit_class='1')

        mock_conn = MagicMock()
        result = fight("Город А", "Город Б", defending_army, attacking_army,
                       "Фракция А", "Фракция Б", mock_conn)

        # Проверяем, что все пехотинцы мертвы
        self.assertEqual(result["defending_units"][0]["unit_count"], 0)
        # Проверяем, что стрелки выжили
        self.assertGreater(result["attacking_units"][0]["unit_count"], 0)

    @patch('fight.update_results_table')
    def test_chain_damage(self, mock_update_results):
        """Тест: один герой убивает нескольких врагов подряд"""
        attacking_army = create_test_unit('Герой', 1, damage=10000, health=1000, armor=1000, unit_class='3')
        defending_army = [
            create_test_unit('Пехотинец 1', 1, damage=100, health=100, armor=100, unit_class='1')[0],
            create_test_unit('Пехотинец 2', 1, damage=100, health=100, armor=100, unit_class='1')[0]
        ]

        mock_conn = MagicMock()

        result = fight("Город А", "Город Б", defending_army, attacking_army,
                       "Фракция А", "Фракция Б", mock_conn)

        # Оба пехотинца должны быть убиты
        for unit in result["defending_units"]:
            self.assertEqual(unit["unit_count"], 0)
        # Герой должен выжить
        self.assertEqual(result["attacking_units"][0]["unit_count"], 1)

    @patch('fight.update_results_table')
    def test_hero_survives_with_one_damage(self, mock_update_results):
        """Тест: герой выживает, если остался хотя бы 1 единица урона"""
        attacking_army = create_test_unit('Герой', 1, damage=10000, health=1000, armor=1000, unit_class='3')
        defending_army = create_test_unit('Легендарный', 1, damage=9999, health=1000, armor=1000, unit_class='4')

        mock_conn = MagicMock()

        result = fight("Город А", "Город Б", defending_army, attacking_army,
                       "Фракция А", "Фракция Б", mock_conn)

        # Герой должен выжить
        self.assertEqual(result["attacking_units"][0]["unit_count"], 1)
        # Легендарный юнит должен быть убит
        self.assertEqual(result["defending_units"][0]["unit_count"], 0)

    @patch('fight.update_results_table')
    def test_bonus_applied_to_base_units(self, mock_update_results):
        """Тест: бонусы от героев применяются к базовым юнитам"""
        attacking_army = [
            create_test_unit('Герой', 1, damage=100, health=100, armor=100, unit_class='3')[0],
            create_test_unit('Стрелок', 10, damage=50, health=50, armor=50, unit_class='1')[0]
        ]
        defending_army = create_test_unit('Цель', 1, damage=100, health=1000, armor=1000, unit_class='1')

        mock_conn = MagicMock()

        result = fight("Город А", "Город Б", defending_army, attacking_army,
                       "Фракция А", "Фракция Б", mock_conn)

        # Цель должна быть убита
        self.assertEqual(result["defending_units"][0]["unit_count"], 0)
        # Стрелки должны выжить
        self.assertGreater(result["attacking_units"][1]["unit_count"], 0)

    @patch('fight.update_results_table')
    def test_sorting_by_class_and_attack(self, mock_update_results):
        """Тест: сортировка юнитов по классу и урону работает верно"""
        army = [
            create_test_unit('Легендарный', 1, damage=10000, unit_class='4')[0],
            create_test_unit('Пехотинец', 10, damage=100, unit_class='1')[0],
            create_test_unit('Герой', 1, damage=1000, unit_class='3')[0]
        ]

        mock_conn = MagicMock()

        result = fight("Город А", "Город Б", [], army, "Фракция А", "Фракция Б", mock_conn)

        sorted_army = result["attacking_units"]

        # Ожидаемый порядок: Пехотинец (1), Герой (3), Легендарный (4)
        self.assertEqual(sorted_army[0]['unit_name'], 'Пехотинец')
        self.assertEqual(sorted_army[1]['unit_name'], 'Герой')
        self.assertEqual(sorted_army[2]['unit_name'], 'Легендарный')


if __name__ == '__main__':
    unittest.main()