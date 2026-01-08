# ai_models/manipulation_strategy.py
import random
from typing import Dict, List, Tuple, Any
from enum import Enum
from dataclasses import dataclass

class ManipulationTactic(Enum):
    """Тактики манипуляций"""
    APPEASEMENT = "умиротворение"  # Уступки для снижения напряжения
    INTIMIDATION = "запугивание"   # Угрозы для получения преимущества
    DECEPTION = "обман"           # Ложные обещания/информация
    FLATTERY = "лесть"            # Лесть для получения расположения
    GUILT_TRIP = "чувство вины"   # Вызов чувства вины
    DIVERSION = "отвлечение"      # Отвлечение внимания
    URGENCY = "срочность"         # Создание срочности
    RECIPROCITY = "взаимность"    # Ожидание ответной услуги

@dataclass
class StrategyContext:
    """Контекст для принятия стратегических решений"""
    relation_level: int
    faction_personality: Dict[str, int]
    player_reputation: Dict[str, float]  # репутация игрока
    recent_interactions: List[Dict]
    faction_needs: Dict[str, int]  # текущие нужды фракции
    game_state: Dict[str, Any]     # общее состояние игры

class ManipulationStrategy:
    """Стратегический модуль манипуляций"""

    def __init__(self):
        self.tactic_weights = self._init_tactic_weights()
        self.response_templates = self._init_response_templates()

    def _init_tactic_weights(self):
        """Инициализация весов тактик в зависимости от личности фракции"""
        return {
            "Север": {
                ManipulationTactic.INTIMIDATION: 0.8,
                ManipulationTactic.RECIPROCITY: 0.7,
                ManipulationTactic.APPEASEMENT: 0.3,
                ManipulationTactic.DECEPTION: 0.4
            },
            "Эльфы": {
                ManipulationTactic.FLATTERY: 0.9,
                ManipulationTactic.RECIPROCITY: 0.8,
                ManipulationTactic.INTIMIDATION: 0.2,
                ManipulationTactic.DECEPTION: 0.1
            },
            "Адепты": {
                ManipulationTactic.DECEPTION: 0.9,
                ManipulationTactic.DIVERSION: 0.8,
                ManipulationTactic.INTIMIDATION: 0.5,
                ManipulationTactic.URGENCY: 0.7
            },
            "Вампиры": {
                ManipulationTactic.INTIMIDATION: 0.9,
                ManipulationTactic.DECEPTION: 0.8,
                ManipulationTactic.GUILT_TRIP: 0.6,
                ManipulationTactic.FLATTERY: 0.3
            },
            "Элины": {
                ManipulationTactic.RECIPROCITY: 0.9,
                ManipulationTactic.FLATTERY: 0.7,
                ManipulationTactic.APPEASEMENT: 0.6,
                ManipulationTactic.DIVERSION: 0.5
            }
        }

    def _init_response_templates(self):
        """Шаблоны ответов для разных тактик"""
        return {
            ManipulationTactic.APPEASEMENT: [
                "Мы понимаем вашу позицию и готовы пойти на уступки.",
                "Для сохранения мира мы можем рассмотреть ваши условия.",
                "Ваше предложение имеет смысл. Давайте найдем компромисс."
            ],
            ManipulationTactic.INTIMIDATION: [
                "Вы играете с огнем. Наши армии всегда наготове.",
                "Подумайте о последствиях такого решения.",
                "Сила - единственный язык, который понимают враги."
            ],
            ManipulationTactic.DECEPTION: [
                "Мы уже работаем над этим вопросом.",
                "Наши ресурсы ограничены, но мы постараемся помочь.",
                "Это возможно, но потребуется время."
            ],
            ManipulationTactic.FLATTERY: [
                "Мы всегда уважали вашу мудрость в таких вопросах.",
                "Ваше предложение показывает вашу дальновидность.",
                "С вами приятно иметь дело, правитель."
            ],
            ManipulationTactic.GUILT_TRIP: [
                "После всего, что мы для вас сделали...",
                "Мы надеялись на большее понимание с вашей стороны.",
                "Ваш запрос ставит нас в трудное положение."
            ],
            ManipulationTactic.DIVERSION: [
                "Это важный вопрос, но сначала давайте обсудим...",
                "У нас есть более срочные дела на повестке дня.",
                "Может, лучше поговорим о наших общих интересах?"
            ],
            ManipulationTactic.URGENCY: [
                "Нам нужно принять решение быстро, ситуация меняется.",
                "Каждый день промедления стоит нам ресурсов.",
                "Время работает против нас в этом вопросе."
            ],
            ManipulationTactic.RECIPROCITY: [
                "Мы поможем, но ожидаем аналогичной поддержки в будущем.",
                "Это должно быть взаимовыгодное соглашение.",
                "Что вы готовы предложить взамен?"
            ]
        }

    def select_tactic(self, intent, context: StrategyContext) -> ManipulationTactic:
        """Выбирает тактику манипуляции на основе контекста"""
        faction = context.faction_personality.get('name', 'Элины')
        base_weights = self.tactic_weights.get(faction, self.tactic_weights["Элины"])

        # Корректируем веса на основе отношений
        adjusted_weights = {}
        for tactic, weight in base_weights.items():
            adjusted = weight

            # Учитываем уровень отношений
            if context.relation_level > 70:
                if tactic in [ManipulationTactic.INTIMIDATION, ManipulationTactic.DECEPTION]:
                    adjusted *= 0.5  # Меньше агрессии к друзьям
                else:
                    adjusted *= 1.2
            elif context.relation_level < 30:
                if tactic in [ManipulationTactic.INTIMIDATION, ManipulationTactic.DECEPTION]:
                    adjusted *= 1.5  # Больше агрессии к врагам
                else:
                    adjusted *= 0.7

            # Учитываем тип запроса
            if intent.name == 'demand_resources':
                if tactic == ManipulationTactic.RECIPROCITY:
                    adjusted *= 1.5
                if tactic == ManipulationTactic.URGENCY:
                    adjusted *= 1.3

            adjusted_weights[tactic] = adjusted

        # Выбираем тактику с учетом весов
        tactics = list(adjusted_weights.keys())
        weights = list(adjusted_weights.values())

        selected = random.choices(tactics, weights=weights, k=1)[0]
        return selected

    def generate_manipulative_response(self,
                                       intent,
                                       tactic: ManipulationTactic,
                                       context: StrategyContext) -> str:
        """Генерирует манипулятивный ответ"""

        # Базовый ответ из шаблона
        templates = self.response_templates.get(tactic, [])
        base_response = random.choice(templates) if templates else ""

        # Добавляем контекстуальную информацию
        enhanced_response = self._enhance_with_context(base_response, intent, context)

        return enhanced_response

    def _enhance_with_context(self, response: str, intent, context: StrategyContext) -> str:
        """Улучшает ответ контекстуальной информацией"""

        # Для запросов ресурсов
        if intent.name == 'demand_resources':
            if 'resource' in intent.entities:
                resources = [e.value for e in intent.entities['resource']]
                if resources:
                    resource_str = ", ".join(resources[:3])

                    if context.relation_level > 60:
                        response += f" Мы можем выделить {resource_str}, но нам понадобится помощь в другом деле."
                    else:
                        response += f" {resource_str} - это серьезный запрос. Что вы предлагаете взамен?"

        # Для предложений союза
        elif intent.name in ['alliance_propose', 'alliance_request']:
            if context.relation_level > 75:
                response += " Наш союз может стать крепким, если мы найдем общие цели."
            else:
                response += " Но сначала нам нужно укрепить доверие между нами."

        # Для угроз
        elif intent.name in ['war_declare', 'threat_indirect']:
            if context.faction_personality.get('aggressive', 0) > 7:
                response += " Наши легионы жаждут битвы!"
            else:
                response += " Но мы надеемся на дипломатическое решение."

        return response

    def calculate_concession(self,
                             player_demand: Dict[str, Any],
                             context: StrategyContext) -> Dict[str, Any]:
        """Рассчитывает уступки, которые фракция готова сделать"""
        concession = {}

        # Базовая готовность к уступкам зависит от отношений
        base_willingness = context.relation_level / 100.0

        # Корректировка в зависимости от тактики
        if context.faction_needs.get('resource_shortage', False):
            base_willingness *= 0.7  # Меньше уступок при недостатке ресурсов

        if context.player_reputation.get('trustworthy', 0.5) > 0.7:
            base_willingness *= 1.3  # Больше уступок надежным партнерам

        # Рассчитываем конкретные уступки
        if 'resources' in player_demand:
            demanded_resources = player_demand['resources']
            for resource, amount in demanded_resources.items():
                # Максимум, что готовы отдать (процент от запрошенного)
                max_percent = min(0.9, base_willingness * 0.8)
                concession[resource] = int(amount * max_percent)

        if 'military_support' in player_demand:
            # Готовность предоставить военную поддержку
            support_level = min(3, int(base_willingness * 5))  # от 0 до 3
            if support_level > 0:
                concession['military_support'] = support_level

        return concession