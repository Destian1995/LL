# ai_models/diplomacy_chat_enhanced.py
from . import DiplomacyChat
from .nlp_processor import NaturalLanguageProcessor, Intent
from .manipulation_strategy import ManipulationStrategy, StrategyContext, ManipulationTactic
import random
from datetime import datetime

# ai_models/diplomacy_chat_enhanced.py
# (Дополнение к EnhancedDiplomacyChat)

class EnhancedDiplomacyChat(DiplomacyChat):
    """Улучшенная версия дипломатического чата с обработкой запросов"""

    def __init__(self, advisor_view):
        super().__init__(advisor_view)

        # Инициализируем NLP процессор
        self.nlp_processor = NaturalLanguageProcessor()

        # Инициализируем стратегию манипуляций
        self.manipulation_strategy = ManipulationStrategy()

        # Контекст переговоров
        self.negotiation_context = {}

        # Активные переговоры (resource_request, alliance_request, trade_request)
        self.active_negotiations = {}

        # История предложений в текущей сессии
        self.current_offers = {}

        # Ожидаемые ответы от ИИ
        self.expected_responses = {}

    def generate_diplomatic_response(self, player_message, target_faction, relation_data):
        """Генерация дипломатического ответа с обработкой запросов"""

        # Обрабатываем сообщение игрока
        intent = self.nlp_processor.process_message(
            player_message,
            self.negotiation_context.get(target_faction, {})
        )

        # Обновляем контекст переговоров
        if target_faction not in self.negotiation_context:
            self.negotiation_context[target_faction] = {
                'stage': 'initial',  # initial, negotiation, agreement, rejection
                'active_request': None,
                'offer_history': [],
                'counter_offers': 0
            }

        context = self.negotiation_context[target_faction]

        # Если у нас есть активные ожидаемые ответы, проверяем их
        response = self._check_expected_response(player_message, target_faction, intent, context)
        if response:
            return response

        # Обрабатываем намерения
        if intent.name in ['demand_resources', 'trade_propose', 'alliance_propose', 'alliance_request']:
            return self._handle_negotiation_intent(intent, player_message, target_faction, relation_data, context)

        # Стандартный ответ
        return super().generate_diplomatic_response(player_message, target_faction, relation_data)

    def _check_expected_response(self, message, faction, intent, context):
        """Проверяет, является ли сообщение ответом на ожидаемый вопрос"""
        if faction not in self.expected_responses:
            return None

        expected = self.expected_responses[faction]

        # Проверяем, содержит ли сообщение числа (для ресурсов)
        import re
        numbers = re.findall(r'\d+', message)

        if expected['type'] == 'resource_amount':
            if numbers:
                amount = int(numbers[0])
                resource_type = self._extract_resource_type(message)

                if resource_type:
                    # Создаем предложение
                    offer = {
                        'type': 'resource_trade',
                        'player_offers': {'type': resource_type, 'amount': amount},
                        'ai_offers': expected.get('ai_offers'),
                        'stage': 'counter_offer'
                    }

                    # Проверяем соотношение сделки
                    deal_ratio = self._calculate_deal_ratio(offer, faction)

                    if deal_ratio > 0.8:  # Выгодная сделка
                        del self.expected_responses[faction]
                        context['stage'] = 'agreement'
                        return f"Хорошо, принимаю твое предложение. Давай заключим сделку!"
                    else:
                        # Просим больше
                        context['counter_offers'] += 1

                        if context['counter_offers'] >= 3:
                            # Слишком много контр-предложений - отказ
                            del self.expected_responses[faction]
                            context['stage'] = 'rejection'
                            return "Твои предложения неинтересны. Давай закончим этот разговор."

                        expected_value = amount * (1 / deal_ratio)
                        del self.expected_responses[faction]
                        self.expected_responses[faction] = {
                            'type': 'resource_amount',
                            'ai_offers': expected.get('ai_offers'),
                            'min_value': expected_value
                        }

                        return f"Мало. Предложи хотя бы {int(expected_value)} {resource_type}, и мы договоримся."

        return None

    def _handle_negotiation_intent(self, intent, message, faction, relation_data, context):
        """Обрабатывает намерения переговоров"""

        if intent.name == 'demand_resources':
            return self._handle_resource_request(intent, message, faction, relation_data, context)

        elif intent.name == 'trade_propose':
            return self._handle_trade_proposal(intent, message, faction, relation_data, context)

        elif intent.name in ['alliance_propose', 'alliance_request']:
            return self._handle_alliance_request(intent, message, faction, relation_data, context)

        return f"Я услышал твой запрос, {faction}. Дай мне подумать..."

    def _handle_resource_request(self, intent, message, faction, relation_data, context):
        """Обрабатывает запрос ресурсов от игрока"""

        # Извлекаем информацию о запросе
        request_info = self._extract_resource_request_info(message)

        if not request_info:
            # Если не поняли, что просит игрок
            self.expected_responses[faction] = {
                'type': 'resource_specification',
                'question': 'Какие именно ресурсы тебе нужны?'
            }
            return "Какие ресурсы тебе нужны? Уточни, пожалуйста."

        resource_type = request_info['type']
        requested_amount = request_info.get('amount', 0)

        # Проверяем, есть ли у нас столько ресурсов
        ai_resources = self._get_ai_resources(faction)
        ai_amount = ai_resources.get(resource_type, 0)

        if ai_amount < requested_amount or requested_amount == 0:
            # Не хватает или не указано количество
            if requested_amount == 0:
                self.expected_responses[faction] = {
                    'type': 'resource_amount',
                    'ai_offers': {'type': resource_type, 'amount': '?'},
                    'question': f'Сколько {resource_type.lower()} тебе нужно?'
                }
                return f"У меня есть {ai_amount} {resource_type.lower()}. Сколько тебе нужно?"
            else:
                self.expected_responses[faction] = {
                    'type': 'resource_counter_offer',
                    'question': f'У меня только {ai_amount} {resource_type.lower()}. Это достаточно?'
                }
                return f"У меня только {ai_amount} {resource_type.lower()}. Это достаточно?"

        # У нас достаточно ресурсов, спрашиваем что игрок предлагает взамен
        context['active_request'] = {
            'type': 'resource_request',
            'resource': resource_type,
            'amount': requested_amount,
            'status': 'waiting_offer'
        }

        self.expected_responses[faction] = {
            'type': 'player_offer',
            'requested_resource': resource_type,
            'requested_amount': requested_amount,
            'question': f'Что ты предлагаешь взамен за {requested_amount} {resource_type.lower()}?'
        }

        return f"У меня есть {requested_amount} {resource_type.lower()}. Что ты предлагаешь взамен?"

    def _handle_trade_proposal(self, intent, message, faction, relation_data, context):
        """Обрабатывает торговые предложения"""

        # Извлекаем информацию о предложении
        trade_info = self._extract_trade_info(message)

        if not trade_info:
            self.expected_responses[faction] = {
                'type': 'trade_specification',
                'question': 'Что именно ты хочешь обменять и на что?'
            }
            return "Не совсем понял твое предложение. Уточни, пожалуйста."

        # Проверяем соотношение сделки
        deal_ratio = self._calculate_trade_ratio(trade_info, faction, relation_data)

        if deal_ratio >= 1.0:  # Выгодная сделка
            # Создаем запись в таблице queries для выполнения сделки
            self._create_trade_query(faction, trade_info)
            context['stage'] = 'agreement'

            return f"Хорошее предложение! Принимаю. Сделка будет выполнена."
        elif deal_ratio >= 0.6:  # Приемлемая, но можно лучше
            # Просим улучшить предложение
            suggested_improvement = self._suggest_trade_improvement(trade_info, deal_ratio)

            self.expected_responses[faction] = {
                'type': 'trade_counter_offer',
                'current_offer': trade_info,
                'suggestion': suggested_improvement,
                'question': f'Можешь предложить лучше? Например: {suggested_improvement}'
            }

            return f"Интересно, но могло бы быть и лучше. Можешь предложить что-то более выгодное?"
        else:  # Невыгодная сделка
            context['stage'] = 'rejection'
            return f"Извини, но это предложение меня не устраивает. Давай поговорим о чем-то другом."

    def _handle_alliance_request(self, intent, message, faction, relation_data, context):
        """Обрабатывает запросы альянса"""

        # Проверяем текущие отношения
        relation_level = int(relation_data.get("relation_level", 50))

        if relation_level >= 75:
            # Хорошие отношения - можно обсуждать
            context['active_request'] = {
                'type': 'alliance_request',
                'status': 'considering'
            }

            self.expected_responses[faction] = {
                'type': 'alliance_terms',
                'question': 'Какие условия союза ты предлагаешь?'
            }

            return "Союз возможен. Какие условия ты предлагаешь?"

        elif relation_level >= 50:
            # Средние отношения - нужны гарантии
            self.expected_responses[faction] = {
                'type': 'alliance_guarantees',
                'question': 'Наши отношения еще не так крепки. Что ты можешь предложить для укрепления доверия?'
            }

            return "Наши отношения еще не так крепки для союза. Что ты можешь предложить для укрепления доверия?"

        else:
            # Слабые отношения - отказ
            context['stage'] = 'rejection'
            return "Сейчас не лучшее время для обсуждения союза. Давай сначала улучшим наши отношения."

    def _extract_resource_request_info(self, message):
        """Извлекает информацию о запросе ресурсов из сообщения"""
        message_lower = message.lower()

        resources = {
            'крон': 'Кроны',
            'золот': 'Кроны',
            'деньг': 'Кроны',
            'кристалл': 'Кристаллы',
            'ресурс': 'Кристаллы',
            'материал': 'Кристаллы',
            'рабоч': 'Рабочие',
            'люд': 'Рабочие',
            'населен': 'Население',
            'народ': 'Население'
        }

        import re
        numbers = re.findall(r'\d+', message)
        amount = int(numbers[0]) if numbers else 0

        for key, resource_type in resources.items():
            if key in message_lower:
                return {
                    'type': resource_type,
                    'amount': amount
                }

        return None

    def _extract_trade_info(self, message):
        """Извлекает информацию о торговом предложении"""
        message_lower = message.lower()

        # Паттерны для поиска торговых предложений
        patterns = [
            r'(?P<give_amount>\d+)\s*(?P<give_type>крон|золот|кристалл|ресурс|рабоч|люд|населен)[^\d]*(?P<get_amount>\d+)\s*(?P<get_type>крон|золот|кристалл|ресурс|рабоч|люд|населен)',
            r'(?P<give_type>крон|золот|кристалл|ресурс|рабоч|люд|населен)[^\d]*(?P<give_amount>\d+)[^\d]*(?P<get_type>крон|золот|кристалл|ресурс|рабоч|люд|населен)[^\d]*(?P<get_amount>\d+)'
        ]

        import re
        for pattern in patterns:
            match = re.search(pattern, message_lower)
            if match:
                resource_map = {
                    'крон': 'Кроны', 'золот': 'Кроны',
                    'кристалл': 'Кристаллы', 'ресурс': 'Кристаллы',
                    'рабоч': 'Рабочие', 'люд': 'Рабочие',
                    'населен': 'Население'
                }

                return {
                    'give_type': resource_map.get(match.group('give_type'), 'Кроны'),
                    'give_amount': int(match.group('give_amount')),
                    'get_type': resource_map.get(match.group('get_type'), 'Кристаллы'),
                    'get_amount': int(match.group('get_amount'))
                }

        return None

    def _extract_resource_type(self, message):
        """Извлекает тип ресурса из сообщения"""
        message_lower = message.lower()

        if any(word in message_lower for word in ['крон', 'золот', 'деньг']):
            return 'Кроны'
        elif any(word in message_lower for word in ['кристалл', 'ресурс', 'материал']):
            return 'Кристаллы'
        elif any(word in message_lower for word in ['рабоч', 'люд']):
            return 'Рабочие'
        elif any(word in message_lower for word in ['населен', 'народ']):
            return 'Население'

        return None

    def _get_ai_resources(self, faction):
        """Получает текущие ресурсы ИИ фракции"""
        # Используем соединение из AIController
        from ii import AIController

        # Создаем временный контроллер для проверки ресурсов
        ai = AIController(faction, self.db_connection)
        ai.load_resources_from_db()

        return {
            'Кроны': ai.resources.get('Кроны', 0),
            'Кристаллы': ai.resources.get('Кристаллы', 0),
            'Рабочие': ai.resources.get('Рабочие', 0),
            'Население': ai.resources.get('Население', 0)
        }

    def _calculate_deal_ratio(self, offer, faction):
        """Рассчитывает соотношение сделки"""
        if not offer or 'player_offers' not in offer:
            return 0

        player_offer = offer['player_offers']
        ai_offer = offer.get('ai_offers', {})

        if not ai_offer or 'type' not in ai_offer:
            return 0

        # Получаем ресурсы ИИ
        ai_resources = self._get_ai_resources(faction)

        # Рассчитываем ценность предложений
        # Базовая ценность ресурсов (можно настроить)
        resource_values = {
            'Кроны': 1.0,
            'Кристаллы': 1.2,
            'Рабочие': 0.8,
            'Население': 1.5
        }

        player_value = player_offer.get('amount', 0) * resource_values.get(player_offer.get('type', 'Кроны'), 1.0)
        ai_value = ai_offer.get('amount', 0) * resource_values.get(ai_offer.get('type', 'Кроны'), 1.0)

        # Учитываем доступность ресурсов у ИИ
        ai_resource_amount = ai_resources.get(ai_offer.get('type', 'Кроны'), 0)
        availability_factor = min(1.0, ai_resource_amount / max(1, ai_offer.get('amount', 1)))

        # Учитываем отношения
        relations = self.advisor.relations_manager.load_combined_relations()
        relation_data = relations.get(faction, {"relation_level": 50})
        relation_level = int(relation_data.get("relation_level", 50))

        relation_factor = relation_level / 100.0

        # Итоговое соотношение
        if ai_value > 0:
            base_ratio = player_value / ai_value
            adjusted_ratio = base_ratio * availability_factor * (1 + relation_factor * 0.5)
            return adjusted_ratio

        return 0

    def _calculate_trade_ratio(self, trade_info, faction, relation_data):
        """Рассчитывает соотношение торговой сделки"""

        # Получаем ресурсы ИИ
        ai_resources = self._get_ai_resources(faction)

        # Ценности ресурсов (можно настроить)
        resource_values = {
            'Кроны': 1.0,
            'Кристаллы': 1.2,
            'Рабочие': 0.8,
            'Население': 1.5
        }

        # Что ИИ отдает
        ai_gives_value = trade_info['give_amount'] * resource_values.get(trade_info['give_type'], 1.0)

        # Что ИИ получает
        ai_gets_value = trade_info['get_amount'] * resource_values.get(trade_info['get_type'], 1.0)

        # Учитываем доступность ресурсов
        ai_has_amount = ai_resources.get(trade_info['give_type'], 0)
        availability = min(1.0, ai_has_amount / max(1, trade_info['give_amount']))

        # Учитываем отношения
        relation_level = int(relation_data.get("relation_level", 50))
        relation_factor = 1.0 + (relation_level - 50) / 100.0

        # Рассчитываем выгодность
        if ai_gives_value > 0:
            base_ratio = ai_gets_value / ai_gives_value
            final_ratio = base_ratio * availability * relation_factor
            return final_ratio

        return 0

    def _suggest_trade_improvement(self, trade_info, current_ratio):
        """Предлагает улучшение торгового предложения"""

        # На сколько нужно улучшить предложение
        improvement_needed = 1.0 - current_ratio

        if improvement_needed > 0:
            # Предлагаем увеличить то, что игрок дает
            suggested_amount = int(trade_info['give_amount'] * (1 + improvement_needed))

            return f"Предложи {suggested_amount} {trade_info['give_type'].lower()} вместо {trade_info['give_amount']}"

        return f"Предложи больше {trade_info['give_type'].lower()} или меньше {trade_info['get_type'].lower()}"

    def _create_trade_query(self, faction, trade_info):
        """Создает запись в таблице queries для выполнения сделки"""
        try:
            cursor = self.db_connection.cursor()

            # Создаем запись о сделке
            cursor.execute('''
                INSERT INTO queries (resource, faction, trade_info)
                VALUES (?, ?, ?)
            ''', (
                f"{trade_info['give_type']}:{trade_info['give_amount']}",
                faction,
                f"{trade_info['get_type']}:{trade_info['get_amount']}"
            ))

            self.db_connection.commit()
            print(f"Создан торговый запрос для фракции {faction}")

        except Exception as e:
            print(f"Ошибка при создании торгового запроса: {e}")

    def execute_agreed_trade(self, faction, offer):
        """Выполняет согласованную сделку"""
        try:
            if offer['type'] == 'resource_trade':
                player_offers = offer['player_offers']
                ai_offers = offer['ai_offers']

                # Здесь нужно интегрировать с AIController для фактического обмена
                # Создаем запись в queries для обработки
                cursor = self.db_connection.cursor()

                cursor.execute('''
                    INSERT INTO queries (resource, faction, trade_info, status)
                    VALUES (?, ?, ?, 'pending')
                ''', (
                    f"{ai_offers['type']}:{ai_offers['amount']}",
                    faction,
                    f"{player_offers['type']}:{player_offers['amount']}"
                ))

                self.db_connection.commit()

                # Очищаем контекст переговоров
                if faction in self.negotiation_context:
                    self.negotiation_context[faction]['stage'] = 'completed'
                    self.negotiation_context[faction]['active_request'] = None

                return True

        except Exception as e:
            print(f"Ошибка при выполнении сделки: {e}")
            return False