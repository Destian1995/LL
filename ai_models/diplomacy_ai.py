# ai_models/diplomacy_ai.py
import random
from datetime import datetime


class DiplomacyAI:
    def __init__(self, advisor_view):
        self.advisor = advisor_view
        self.faction = advisor_view.faction

    def generate_economy_advice(self, context):
        """Генерирует экономический совет"""
        advice = "🏦 **Экономические рекомендации:**\n\n"

        if context.get('resources'):
            advice += "1. Увеличивайте производство кристаллов\n"
            advice += "2. Стройте новые фабрики\n"
            advice += "3. Управляйте налогами разумно\n"
            advice += "4. Инвестируйте в развитие городов\n"

        advice += f"\nДля фракции {self.faction} особенно важно балансировать между производством и потреблением."
        return advice

    def generate_military_advice(self, context):
        """Генерирует военный совет"""
        army_count = context.get('army_count', 0)
        advice = f"⚔️ **Военные рекомендации:**\n\n"
        advice += f"Текущая численность армии: {army_count}\n\n"

        if army_count < 100:
            advice += "1. Срочно наращивайте армию\n"
            advice += "2. Нанимайте юнитов 1-2 классов\n"
            advice += "3. Укрепляйте оборону городов\n"
        elif army_count < 500:
            advice += "1. Улучшайте существующие войска\n"
            advice += "2. Нанимайте героев (3-4 класс)\n"
            advice += "3. Исследуйте новые технологии\n"
        else:
            advice += "1. Планируйте стратегические кампании\n"
            advice += "2. Используйте комбинированные отряды\n"
            advice += "3. Создавайте резервные армии\n"

        return advice

    def generate_diplomacy_advice(self, context):
        """Генерирует дипломатический совет"""
        advice = "🤝 **Дипломатические рекомендации:**\n\n"

        relations = context.get('relations', [])
        if relations:
            advice += "Текущие отношения:\n"
            for rel in relations[:3]:
                advice += f"• Уровень: {rel[0]}/100\n"

        advice += "\n1. Заключайте торговые договоры\n"
        advice += "2. Обменивайтесь культурными бонусами\n"
        advice += "3. Избегайте войн на два фронта\n"
        advice += "4. Используйте шпионаж для разведки\n"

        return advice

    def generate_development_advice(self, context):
        """Генерирует совет по развитию"""
        city_count = context.get('city_count', 0)
        advice = f"🏙️ **Развитие городов ({city_count} шт.):**\n\n"

        if city_count < 3:
            advice += "1. Сосредоточьтесь на захвате новых городов\n"
            advice += "2. Укрепляйте столицу\n"
            advice += "3. Развивайте инфраструктуру\n"
        elif city_count < 7:
            advice += "1. Улучшайте существующие города\n"
            advice += "2. Создавайте специализированные города\n"
            advice += "3. Инвестируйте в науку и культуру\n"
        else:
            advice += "1. Создавайте мегаполисы\n"
            advice += "2. Оптимизируйте логистику\n"
            advice += "3. Развивайте уникальные особенности городов\n"

        return advice

    def generate_general_advice(self, context):
        """Генерирует общий совет"""
        advice = "🎯 **Общие рекомендации:**\n\n"
        advice += "1. Балансируйте между развитием и экспансией\n"
        advice += "2. Следите за сезонными эффектами\n"
        advice += "3. Управляйте дворянами (советниками)\n"
        advice += "4. Планируйте долгосрочную стратегию\n"
        advice += f"\nКак правитель {self.faction}, вы должны быть гибкими и адаптироваться к изменяющимся условиям."

        return advice

    def generate_ai_response_based_on_context(self, user_message, context):
        """Генерирует ответ ИИ на основе контекста"""
        user_message_lower = user_message.lower()

        # Анализ ключевых слов в сообщении
        if any(word in user_message_lower for word in ['эконом', 'доход', 'деньги', 'ресурс', 'кроны']):
            return self.generate_economy_advice(context)

        elif any(word in user_message_lower for word in ['войн', 'арми', 'солдат', 'защит', 'атака']):
            return self.generate_military_advice(context)

        elif any(word in user_message_lower for word in ['дипломат', 'союз', 'враг', 'отношен']):
            return self.generate_diplomacy_advice(context)

        elif any(word in user_message_lower for word in ['город', 'строит', 'развит']):
            return self.generate_development_advice(context)

        else:
            return self.generate_general_advice(context)

    def get_game_context_for_faction(self, faction):
        """Получает игровой контекст для указанной фракции"""
        try:
            context = self.advisor.quick_actions.get_comprehensive_game_context()
            return context.get('factions', {}).get(faction, {})
        except:
            return {}

    def initialize_diplomacy_ai(self):
        """Инициализирует ИИ для дипломатических переговоров"""
        try:
            # Используем фабрику для создания ИИ
            from ai_models.lerdon_ai.ultralight_ai import DiplomacyAIFactory

            ai_factory = DiplomacyAIFactory()

            # Получаем текущий игровой контекст
            game_context = self.advisor.quick_actions.get_comprehensive_game_context()

            # Создаем ИИ с учетом фракции игрока и контекста
            diplomacy_ai = ai_factory.create_ai(
                self.faction,
                game_context
            )

            print(f"ИИ дипломатии инициализирован для фракции {self.faction}")
            return diplomacy_ai

        except Exception as e:
            print(f"Ошибка при инициализации ИИ дипломатии: {e}")
            return None