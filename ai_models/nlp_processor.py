# ai_models/nlp_processor.py
import re
import random
from typing import Dict, List, Tuple, Any
from dataclasses import dataclass

@dataclass
class Intent:
    """Распознанный намерение пользователя"""
    name: str
    confidence: float
    entities: Dict[str, Any]
    context: Dict[str, Any]
    sentiment: str  # positive, negative, neutral

@dataclass
class Entity:
    """Извлеченная сущность из сообщения"""
    type: str
    value: str
    confidence: float

class NaturalLanguageProcessor:
    """Улучшенный процессор естественного языка для дипломатии"""

    def __init__(self):
        self.intent_patterns = self._init_intent_patterns()
        self.entity_patterns = self._init_entity_patterns()
        self.context_memory = {}

    def _init_intent_patterns(self):
        """Шаблоны для распознавания намерений"""
        return {
            # Альянсы и союзы
            'alliance_propose': [
                r'(предлагаю|хочу|прошу|желаю).*(союз|альянс|объединение|вместе)',
                r'(заключить|создать|начать).*(союз|альянс)',
                r'(давай|давайте).*(союзничать|объединиться)',
                r'(хочу|хотим).*(стать|быть).*(союзник|партнер)'
            ],
            'alliance_request': [
                r'(помоги|помощь|поддержк).*(против|противник|враг)',
                r'(нужна|нужна).*(военная|военн).*(помощь|поддержка)',
                r'(вступи|вступить).*(война|конфликт|войну)',
                r'(защити|защита).*(от|против).*'
            ],

            # Торговля и ресурсы
            'trade_propose': [
                r'(торгов|торговать|продать|купить|обмен).*(ресурс|золот|кристалл|еда|пища|материал)',
                r'(предлагаю|хочу).*(купить|продать|обменять).*',
                r'(цена|стоимость|обмен).*(на|за).*',
                r'(ресурс|товар).*(для|в обмен).*'
            ],

            # Война и угрозы
            'war_declare': [
                r'(объявляю|объявляем).*(война|войну|войны)',
                r'(нападу|атакую|атака).*(на|против).*',
                r'(уничтожу|раздавлю|сокрушу).*',
                r'(ультаматум|требую|приказываю).*'
            ],

            # Мир и переговоры
            'peace_propose': [
                r'(предлагаю|прошу|хочу).*(мир|перемирие|прекратить.*войну)',
                r'(закончить|остановить|прекратить).*(война|конфликт|боевые действия)',
                r'(мирный|мирн).*(договор|соглашение)'
            ],

            # Информация и разведка
            'info_request': [
                r'(сколько|как.*много|какое.*количество).*(ресурс|крон|золот|кристалл|армия|войск)',
                r'(информация|данные|сведения).*(о|об|насчет).*',
                r'(расскажи|сообщи|скажи).*(о|об).*',
                r'(как.*дела|как.*поживаешь|как.*ситуация)'
            ],

            # Действия и манипуляции
            'demand_resources': [
                r'(требую|нужно|надо|хочу).*((\d+).*(крон|золот|кристалл|ресурс)|ресурс|материал)',
                r'(дай|предоставь|отдай).*((\d+).*крон|золот|кристалл)',
                r'(плата|компенсация|выкуп).*(за|в обмен).*'
            ],

            'threat_indirect': [
                r'(если.*не|иначе|в противном случае).*',
                r'(будет.*плохо|пожалеешь|раскаешься)',
                r'(последствия|ответственность).*(будешь|несешь)'
            ],

            # Дипломатические формальности
            'greeting': [
                r'(привет|здравствуй|добрый.*день|здорово)',
                r'(рад.*видеть|снова.*здесь)'
            ],

            'farewell': [
                r'(пока|до.*свидания|прощай|всего.*доброго)'
            ],

            'compliment': [
                r'(молодец|хорошо|отлично|великолепно|восхитительно)',
                r'(уважаю|восхищаюсь|нравишься)'
            ],

            'insult': [
                r'(дурак|идиот|глупец|предатель|трус)',
                r'(ненавижу|презираю|презираю)'
            ]
        }

    def _init_entity_patterns(self):
        """Шаблоны для извлечения сущностей"""
        return {
            'resource': [
                r'(\d+).*(золот|кристалл|кристаллов|ресурс|единиц.*ресурс)',
                r'(золот|кристалл|ресурс).*(\d+)'
            ],
            'number': [
                r'(\d+)'
            ],
            'faction': [
                r'(север|эльф|адепт|вампир|элин)'
            ],
            'action': [
                r'(атаковать|защищать|помогать|поддерживать|торговать)'
            ],
            'condition': [
                r'(если|при.*условии|в обмен.*на|только.*если)'
            ]
        }

    def process_message(self, message: str, context: Dict = None) -> Intent:
        """Основной метод обработки сообщения"""
        message_lower = message.lower().strip()

        # Анализ настроения
        sentiment = self._analyze_sentiment(message_lower)

        # Извлечение сущностей
        entities = self._extract_entities(message_lower)

        # Распознавание намерений
        intents = self._recognize_intents(message_lower, entities)

        # Определение контекста
        current_context = context or {}
        enhanced_context = self._enhance_context(current_context, message_lower, entities)

        # Выбор главного намерения
        main_intent = self._select_main_intent(intents, enhanced_context)

        return Intent(
            name=main_intent['name'],
            confidence=main_intent['confidence'],
            entities=entities,
            context=enhanced_context,
            sentiment=sentiment
        )

    def _analyze_sentiment(self, message: str) -> str:
        """Анализирует настроение сообщения"""
        positive_words = {
            'спасибо', 'благодарю', 'прошу', 'пожалуйста', 'уважаем', 'ценю',
            'рад', 'рады', 'отличн', 'прекрасн', 'замечательн', 'согласн',
            'дружб', 'мир', 'сотрудничество', 'доверие', 'честь', 'совместно'
        }

        negative_words = {
            'угроз', 'уничтож', 'нападу', 'атакую', 'война', 'ненавижу',
            'против', 'враг', 'смерть', 'уничтожу', 'раздавлю', 'сокрушу',
            'требую', 'заставлю', 'приказываю', 'ультиматум', 'предатель'
        }

        positive_count = sum(1 for word in positive_words if word in message)
        negative_count = sum(1 for word in negative_words if word in message)

        if positive_count > negative_count * 1.5:
            return "positive"
        elif negative_count > positive_count * 1.5:
            return "negative"
        else:
            return "neutral"

    def _extract_entities(self, message: str) -> Dict[str, List[Entity]]:
        """Извлекает сущности из сообщения"""
        entities = {}

        for entity_type, patterns in self.entity_patterns.items():
            entities[entity_type] = []
            for pattern in patterns:
                matches = re.finditer(pattern, message)
                for match in matches:
                    value = match.group(1) if match.groups() else match.group(0)
                    entities[entity_type].append(Entity(
                        type=entity_type,
                        value=value,
                        confidence=0.8  # Можно улучшить с ML моделью
                    ))

        return entities

    def _recognize_intents(self, message: str, entities: Dict) -> List[Dict]:
        """Распознает намерения в сообщении"""
        intents = []

        for intent_name, patterns in self.intent_patterns.items():
            max_confidence = 0

            for pattern in patterns:
                match = re.search(pattern, message)
                if match:
                    # Базовое совпадение
                    confidence = 0.7

                    # Увеличиваем уверенность если найдены соответствующие сущности
                    if intent_name in ['trade_propose', 'demand_resources'] and 'resource' in entities:
                        confidence += 0.2
                    if intent_name in ['alliance_propose', 'alliance_request'] and 'faction' in entities:
                        confidence += 0.1

                    max_confidence = max(max_confidence, confidence)

            if max_confidence > 0:
                intents.append({
                    'name': intent_name,
                    'confidence': min(max_confidence, 0.95)
                })

        # Если не распознали намерения, используем общее
        if not intents:
            intents.append({
                'name': 'general_conversation',
                'confidence': 0.6
            })

        return intents

    def _select_main_intent(self, intents: List[Dict], context: Dict) -> Dict:
        """Выбирает главное намерение с учетом контекста"""
        if not intents:
            return {'name': 'unknown', 'confidence': 0.0}

        # Учитываем контекст для повышения уверенности
        for intent in intents:
            intent_name = intent['name']

            # Если в контексте есть предыдущие связанные намерения
            if 'previous_intent' in context:
                prev_intent = context['previous_intent']

                # Логические цепочки
                if prev_intent == 'greeting' and intent_name == 'greeting':
                    intent['confidence'] *= 1.1
                elif prev_intent == 'alliance_propose' and intent_name in ['alliance_request', 'demand_resources']:
                    intent['confidence'] *= 1.2
                elif prev_intent == 'war_declare' and intent_name == 'peace_propose':
                    intent['confidence'] *= 1.3

        # Возвращаем намерение с максимальной уверенностью
        return max(intents, key=lambda x: x['confidence'])

    def _enhance_context(self, context: Dict, message: str, entities: Dict) -> Dict:
        """Улучшает контекст на основе текущего сообщения"""
        enhanced = context.copy()

        # Сохраняем ключевые слова
        enhanced['last_message_keywords'] = self._extract_keywords(message)

        # Сохраняем важные сущности
        if 'resource' in entities:
            enhanced['mentioned_resources'] = [e.value for e in entities['resource']]
        if 'number' in entities:
            enhanced['mentioned_numbers'] = [e.value for e in entities['number']]

        return enhanced

    def _extract_keywords(self, message: str) -> List[str]:
        """Извлекает ключевые слова из сообщения"""
        # Удаляем стоп-слова
        stop_words = {'и', 'в', 'на', 'с', 'по', 'о', 'об', 'не', 'но', 'а', 'или'}
        words = re.findall(r'\b\w+\b', message.lower())

        keywords = [word for word in words if word not in stop_words and len(word) > 3]

        return keywords[:10]  # Ограничиваем количество ключевых слов