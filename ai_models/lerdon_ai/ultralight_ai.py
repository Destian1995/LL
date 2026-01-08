import json
import os
import re
import random
from datetime import datetime
from collections import defaultdict, Counter
import pickle
import gzip
from typing import Dict, List, Optional, Tuple
import sqlite3

class UltraLightDiplomacyAI:
    """Самый легковесный дипломатический ИИ - полностью на Python, без зависимостей"""

    def __init__(self, faction: str, db_connection=None):
        self.faction = faction
        self.db = db_connection

        # Минимальные данные модели
        self.keyword_patterns = {}      # Ключевые слова → намерения
        self.response_templates = {}    # Намерения → шаблоны ответов
        self.conversation_memory = []   # Краткая память диалога
        self.learned_patterns = {}      # Выученные паттерны от игрока
        self.personality = self._get_faction_personality(faction)

        # Состояние
        self.mood = 50  # 0-100 (настроение к игроку)
        self.trust = 50  # 0-100 (доверие)

        # Инициализация
        self._initialize_from_files()

        print(f"⚡ UltraLight AI для '{faction}' готов! (Размер: {self._get_model_size()} байт)")

    def _get_model_size(self) -> int:
        """Возвращает примерный размер модели в байтах"""
        import sys
        size = 0
        size += sys.getsizeof(self.keyword_patterns)
        size += sys.getsizeof(self.response_templates)
        size += sys.getsizeof(self.conversation_memory)
        size += sys.getsizeof(self.learned_patterns)
        return size

    def _get_faction_personality(self, faction: str) -> Dict:
        """Возвращает личность фракции"""
        personalities = {
            "Север": {
                "name": "Лорд-Советник",
                "traits": ["прямой", "честный", "традиционный"],
                "formality": 8,
                "aggression": 4,
                "friendliness": 6,
                "speech_style": "формальный, прямой"
            },
            "Эльфы": {
                "name": "Советник Леса",
                "traits": ["мудрый", "загадочный", "терпеливый"],
                "formality": 7,
                "aggression": 2,
                "friendliness": 7,
                "speech_style": "поэтичный, метафоричный"
            },
            "Вампиры": {
                "name": "Граф Ночной",
                "traits": ["хитрый", "аристократичный", "терпеливый"],
                "formality": 9,
                "aggression": 7,
                "friendliness": 4,
                "speech_style": "изысканный, с намёками"
            },
            "Адепты": {
                "name": "Магистр Ордена",
                "traits": ["логичный", "точный", "осторожный"],
                "formality": 8,
                "aggression": 5,
                "friendliness": 5,
                "speech_style": "техничный, точный"
            },
            "Элины": {
                "name": "Торговый Дипломат",
                "traits": ["прагматичный", "гибкий", "общительный"],
                "formality": 6,
                "aggression": 3,
                "friendliness": 8,
                "speech_style": "деловой, убедительный"
            }
        }
        return personalities.get(faction, personalities["Север"])

    def _initialize_from_files(self):
        """Инициализация из файлов или создание базовых"""
        model_dir = f"ai_models/{self.faction}"
        os.makedirs(model_dir, exist_ok=True)

        # 1. Загружаем или создаем ключевые слова
        keywords_path = f"{model_dir}/keywords.json"
        if os.path.exists(keywords_path):
            with open(keywords_path, 'r', encoding='utf-8') as f:
                self.keyword_patterns = json.load(f)
        else:
            self.keyword_patterns = self._create_base_keywords()
            self._save_keywords(keywords_path)

        # 2. Загружаем или создаем шаблоны ответов
        templates_path = f"{model_dir}/templates.json"
        if os.path.exists(templates_path):
            with open(templates_path, 'r', encoding='utf-8') as f:
                self.response_templates = json.load(f)
        else:
            self.response_templates = self._create_base_templates()
            self._save_templates(templates_path)

        # 3. Загружаем выученные паттерны
        learned_path = f"{model_dir}/learned.pkl"
        if os.path.exists(learned_path):
            try:
                with open(learned_path, 'rb') as f:
                    self.learned_patterns = pickle.load(f)
            except:
                self.learned_patterns = {}

    def _create_base_keywords(self) -> Dict:
        """Создает базовые ключевые слова для классификации"""
        return {
            "greeting": {
                "keywords": ["привет", "здравствуй", "добрый", "день", "приветствую", "здравия"],
                "weight": 1.0,
                "examples": ["привет", "добрый день", "здравствуйте"]
            },
            "farewell": {
                "keywords": ["пока", "до свидания", "прощай", "удачи", "всего", "доброго"],
                "weight": 1.0,
                "examples": ["пока", "до свидания", "всего доброго"]
            },
            "alliance": {
                "keywords": ["союз", "объединиться", "вместе", "альянс", "помощь военная", "союзники"],
                "weight": 1.2,  # Более важное намерение
                "examples": ["предлагаю союз", "давайте объединимся", "хочу союз"]
            },
            "trade": {
                "keywords": ["торговля", "обмен", "ресурсы", "куплю", "продам", "торговый", "договор"],
                "weight": 1.1,
                "examples": ["хочу торговать", "обмен ресурсами", "торговый договор"]
            },
            "war": {
                "keywords": ["война", "атака", "нападу", "уничтожу", "объявляю войну", "воевать", "битва"],
                "weight": 1.3,  # Важное намерение
                "examples": ["объявляю войну", "атакую вас", "будем воевать"]
            },
            "peace": {
                "keywords": ["мир", "перемирие", "прекратить войну", "заключить мир", "прекратим", "конфликт"],
                "weight": 1.2,
                "examples": ["предлагаю мир", "давайте прекратим войну", "заключим перемирие"]
            },
            "threat": {
                "keywords": ["угроза", "осторожно", "предупреждаю", "будет плохо", "накажу", "ответите"],
                "weight": 1.1,
                "examples": ["это угроза", "вы пожалеете", "осторожнее"]
            },
            "question": {
                "keywords": ["?", "почему", "зачем", "когда", "сколько", "где", "кто", "что", "как"],
                "weight": 0.9,
                "examples": ["как дела?", "сколько войск?", "что нового?"]
            },
            "request": {
                "keywords": ["прошу", "нужно", "требуется", "помогите", "дайте", "помощь", "поддержка"],
                "weight": 1.0,
                "examples": ["прошу помощи", "нужны ресурсы", "дайте золото"]
            },
            "info": {
                "keywords": ["расскажи", "информация", "данные", "отчет", "ситуация", "состояние", "новости"],
                "weight": 1.0,
                "examples": ["расскажите о себе", "какая информация?", "как дела?"]
            }
        }

    def _create_base_templates(self) -> Dict:
        """Создает базовые шаблоны ответов"""

        # Базовые шаблоны для всех фракций
        base_templates = {
            "greeting": [
                "{greeting}, {player}. {faction} вас слушает.",
                "Приветствую, {player}. Что вас беспокоит?",
                "Добро пожаловать, {player}. Говорите."
            ],
            "farewell": [
                "До новых встреч, {player}.",
                "Прощайте. Пусть удача сопутствует вам.",
                "Всего доброго, {player}."
            ],
            "alliance": [
                "Союз требует доверия. Что вы предлагаете?",
                "Интересное предложение. Обсудим условия?",
                "{faction} рассматривает возможность союза."
            ],
            "trade": [
                "Торговля должна быть взаимовыгодной. Ваше предложение?",
                "Что предлагаете и что хотите взамен?",
                "Готов обсудить торговые условия."
            ],
            "war": [
                "Это серьезное заявление. Вы уверены?",
                "Война принесет потери обеим сторонам.",
                "{faction} готов к защите, если потребуется."
            ],
            "peace": [
                "Мир всегда лучше войны. Какие условия?",
                "Готовы обсудить прекращение конфликта.",
                "Давайте найдем мирное решение."
            ],
            "threat": [
                "Угрозы не помогут делу. Говорите яснее.",
                "Мы слышим ваши слова. Предлагайте конструктив.",
                "Такие слова не способствуют диалогу."
            ],
            "question": [
                "{faction} обдумывает ваш вопрос.",
                "Интересный вопрос. Дайте мне подумать.",
                "Что конкретно вас интересует?"
            ],
            "request": [
                "Рассмотрим вашу просьбу. Что именно нужно?",
                "Помощь возможна при определенных условиях.",
                "Что вы предлагаете взамен?"
            ],
            "info": [
                "Что конкретно вы хотите узнать?",
                "О чем именно спрашиваете?",
                "Уточните ваш запрос."
            ],
            "default": [
                "Я вас слушаю, {player}.",
                "Понял ваше сообщение.",
                "{faction} принимает к сведению."
            ]
        }

        # Адаптируем под личность фракции
        return self._personalize_templates(base_templates)

    def _personalize_templates(self, templates: Dict) -> Dict:
        """Адаптирует шаблоны под личность фракции"""
        personality = self.personality

        # Добавляем характерные фразы
        faction_flavors = {
            "Север": {
                "greeting": ["Честь имею, {player}. Север вас слушает."],
                "alliance": ["Честный союз - крепкий союз. Давайте договоримся."],
                "war": ["Угрозы не пугают Север. Наша сталь остра."]
            },
            "Эльфы": {
                "greeting": ["Под сенью древних дерев приветствую вас, {player}."],
                "alliance": ["Союз должен быть как переплетение корней - прочным."],
                "peace": ["Мир - это гармония. Давайте восстановим её."]
            },
            "Вампиры": {
                "greeting": ["Добро пожаловать в сумерки переговоров, {player}."],
                "alliance": ["Союз... интересно. Что вы предлагаете за вечность?"],
                "threat": ["Вы играете с бессмертием. Опасно."]
            },
            "Адепты": {
                "greeting": ["Канал связи установлен, {player}. Говорите."],
                "info": ["Запрос принят. Обрабатываю данные."],
                "question": ["Вопрос требует анализа. Подождите."]
            },
            "Элины": {
                "greeting": ["Добро пожаловать за стол переговоров, {player}."],
                "trade": ["Торговля - основа процветания. Ваши условия?"],
                "peace": ["Мир выгоден для бизнеса. Обсуждаем?"]
            }
        }

        # Объединяем шаблоны
        faction_templates = templates.copy()
        faction_flavor = faction_flavors.get(self.faction, {})

        for intent, custom_templates in faction_flavor.items():
            if intent in faction_templates:
                faction_templates[intent] = custom_templates + faction_templates[intent]

        return faction_templates

    def _save_keywords(self, path: str):
        """Сохраняет ключевые слова"""
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(self.keyword_patterns, f, ensure_ascii=False, indent=2)

    def _save_templates(self, path: str):
        """Сохраняет шаблоны"""
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(self.response_templates, f, ensure_ascii=False, indent=2)

    def save_model(self):
        """Сохраняет всю модель"""
        model_dir = f"ai_models/{self.faction}"
        os.makedirs(model_dir, exist_ok=True)

        self._save_keywords(f"{model_dir}/keywords.json")
        self._save_templates(f"{model_dir}/templates.json")

        # Сохраняем выученные паттерны
        with open(f"{model_dir}/learned.pkl", 'wb') as f:
            pickle.dump(self.learned_patterns, f)

        # Сохраняем состояние
        state = {
            "mood": self.mood,
            "trust": self.trust,
            "last_updated": datetime.now().isoformat(),
            "version": "1.0"
        }
        with open(f"{model_dir}/state.json", 'w', encoding='utf-8') as f:
            json.dump(state, f, ensure_ascii=False, indent=2)

        print(f"💾 Модель сохранена в {model_dir}")

    # ========== ОСНОВНАЯ ЛОГИКА ==========

    def analyze_message(self, message: str) -> Dict:
        """Анализирует сообщение игрока - САМАЯ БЫСТРАЯ РЕАЛИЗАЦИЯ"""

        message_lower = message.lower().strip()

        # 1. Определяем намерение по ключевым словам (УЛЬТРА-БЫСТРО)
        intent_scores = {}

        for intent, data in self.keyword_patterns.items():
            score = 0
            keywords = data["keywords"]
            weight = data["weight"]

            for keyword in keywords:
                if keyword in message_lower:
                    score += 1

            if score > 0:
                intent_scores[intent] = score * weight

        # 2. Проверяем выученные паттерны
        for pattern, intent in self.learned_patterns.items():
            if pattern in message_lower:
                intent_scores[intent] = intent_scores.get(intent, 0) + 2.0  # Бонус за выученное

        # 3. Определяем победителя
        if intent_scores:
            best_intent = max(intent_scores.items(), key=lambda x: x[1])[0]
        else:
            best_intent = "default"

        # 4. Быстрый анализ настроения
        sentiment = self._quick_sentiment(message_lower)

        # 5. Извлекаем сущности (быстро)
        entities = self._extract_entities_fast(message_lower)

        return {
            "intent": best_intent,
            "sentiment": sentiment,
            "entities": entities,
            "original_message": message,
            "timestamp": datetime.now().isoformat()
        }

    def _quick_sentiment(self, text: str) -> str:
        """Сверхбыстрый анализ настроения"""
        positive = {'спасибо', 'благодарю', 'рад', 'отличн', 'прекрасн', 'замечательн'}
        negative = {'война', 'угроз', 'уничтож', 'ненавижу', 'враг', 'смерть'}

        pos_count = sum(1 for word in positive if word in text)
        neg_count = sum(1 for word in negative if word in text)

        if pos_count > neg_count:
            return "positive"
        elif neg_count > pos_count:
            return "negative"
        else:
            return "neutral"

    def _extract_entities_fast(self, text: str) -> Dict:
        """Быстрое извлечение сущностей"""
        entities = {
            "resources": [],
            "numbers": [],
            "targets": []
        }

        # Ищем числа
        numbers = re.findall(r'\d+', text)
        entities["numbers"] = [int(n) for n in numbers]

        # Ищем ресурсы
        resource_keywords = ["золот", "кристал", "еда", "пищ", "ресурс", "материал"]
        for word in resource_keywords:
            if word in text:
                entities["resources"].append(word)

        # Ищем названия фракций (упрощенно)
        factions = ["север", "эльф", "вампир", "адепт", "элин", "мятежник"]
        for faction in factions:
            if faction in text:
                entities["targets"].append(faction)

        return entities

    def generate_response(self, analysis: Dict, game_context: Dict = None) -> str:
        """Генерирует ответ на основе анализа"""

        intent = analysis["intent"]
        sentiment = analysis["sentiment"]

        # 1. Получаем шаблоны для этого намерения
        templates = self.response_templates.get(intent, self.response_templates["default"])

        if not templates:
            templates = ["Я вас слушаю."]

        # 2. Выбираем шаблон с учетом настроения
        if sentiment == "positive":
            # Предпочитаем дружественные шаблоны
            filtered = [t for t in templates if "рад" in t.lower() or "добро" in t.lower()]
            if filtered:
                templates = filtered
        elif sentiment == "negative":
            # Более осторожные шаблоны
            filtered = [t for t in templates if "осторож" in t.lower() or "серьез" in t.lower()]
            if filtered:
                templates = filtered

        # 3. Выбираем случайный шаблон
        template = random.choice(templates)

        # 4. Заполняем шаблон
        response = template.format(
            player="правитель",
            faction=self.faction,
            greeting=self._get_greeting(),
            mood=self._get_mood_text()
        )

        # 5. Добавляем контекстную информацию если есть
        if game_context:
            response = self._add_context(response, game_context, analysis)

        # 6. Обновляем состояние
        self._update_state(analysis, response)

        # 7. Сохраняем в память диалога
        self._remember_conversation(analysis, response)

        return response

    def _get_greeting(self) -> str:
        """Возвращает приветствие в зависимости от настроения"""
        if self.mood > 70:
            return "Рад вас видеть"
        elif self.mood > 40:
            return "Приветствую"
        else:
            return "Здравствуйте"

    def _get_mood_text(self) -> str:
        """Возвращает текстовое описание настроения"""
        if self.mood > 70:
            return "в хорошем настроении"
        elif self.mood > 40:
            return "в нормальном настроении"
        else:
            return "не в духе"

    def _add_context(self, response: str, context: Dict, analysis: Dict) -> str:
        """Добавляет контекстную информацию"""

        # Если спрашивают про ресурсы
        if analysis["intent"] in ["info", "request"] and "ресурс" in analysis.get("entities", {}).get("resources", []):
            resources = context.get("resources", {})
            if resources:
                response += f" Наши текущие ресурсы: {resources.get('gold', 0)} золота, {resources.get('crystals', 0)} кристаллов."

        # Если угрожают
        if analysis["intent"] in ["war", "threat"]:
            army = context.get("army", 0)
            if army:
                response += f" Наша армия из {army} воинов готова к обороне."

        return response

    def _update_state(self, analysis: Dict, response: str):
        """Обновляет внутреннее состояние ИИ"""

        # Обновляем настроение
        sentiment = analysis["sentiment"]
        if sentiment == "positive":
            self.mood = min(100, self.mood + 5)
        elif sentiment == "negative":
            self.mood = max(0, self.mood - 10)

        # Обновляем доверие
        intent = analysis["intent"]
        if intent in ["alliance", "peace", "trade"]:
            self.trust = min(100, self.trust + 3)
        elif intent in ["war", "threat"]:
            self.trust = max(0, self.trust - 15)

    def _remember_conversation(self, analysis: Dict, response: str):
        """Сохраняет ход разговора в память"""
        memory_entry = {
            "player": analysis["original_message"],
            "ai": response,
            "intent": analysis["intent"],
            "timestamp": analysis["timestamp"],
            "mood": self.mood,
            "trust": self.trust
        }

        self.conversation_memory.append(memory_entry)

        # Ограничиваем память
        if len(self.conversation_memory) > 20:
            self.conversation_memory = self.conversation_memory[-10:]

    # ========== ОБУЧЕНИЕ ОТ ИГРОКА ==========

    def learn_from_feedback(self, player_message: str, ai_response: str,
                           player_feedback: Optional[str] = None,
                           was_good: bool = True):
        """Учится на обратной связи от игрока"""

        message_lower = player_message.lower()

        # 1. Определяем намерение игрока (для обучения)
        analysis = self.analyze_message(player_message)
        detected_intent = analysis["intent"]

        # 2. Если игрок дал явную обратную связь
        if player_feedback:
            feedback_lower = player_feedback.lower()

            if "неправильно" in feedback_lower or "ошибся" in feedback_lower:
                # ИИ ошибся - запоминаем чтобы не повторять
                self._learn_mistake(message_lower, detected_intent)
                return

            if "правильно" in feedback_lower or "верно" in feedback_lower:
                # ИИ ответил правильно - усиливаем паттерн
                self._reinforce_pattern(message_lower, detected_intent)
                return

        # 3. Автоматическое обучение на основе качества ответа
        if was_good:
            # Хороший ответ - запоминаем успешный паттерн
            self._learn_successful_pattern(message_lower, detected_intent, ai_response)
        else:
            # Плохой ответ - ослабляем паттерн
            self._weaken_pattern(message_lower, detected_intent)

    def _learn_successful_pattern(self, message: str, intent: str, response: str):
        """Запоминает успешный паттерн"""
        # Извлекаем ключевые слова из сообщения
        words = message.split()
        key_words = [w for w in words if len(w) > 3]  # Берем только слова длиннее 3 симв

        if len(key_words) >= 2:
            # Создаем паттерн из 2 ключевых слов
            pattern = f"{key_words[0]} {key_words[1]}"

            # Запоминаем
            self.learned_patterns[pattern] = {
                "intent": intent,
                "response_pattern": response[:50],  # Сохраняем часть ответа
                "strength": 1.0,
                "learned_at": datetime.now().isoformat()
            }

    def _reinforce_pattern(self, message: str, intent: str):
        """Усиливает существующий паттерн"""
        for pattern in list(self.learned_patterns.keys()):
            if pattern in message:
                data = self.learned_patterns[pattern]
                data["strength"] = min(5.0, data["strength"] + 0.5)  # Максимум сила 5.0

    def _weaken_pattern(self, message: str, intent: str):
        """Ослабляет паттерн"""
        for pattern in list(self.learned_patterns.keys()):
            if pattern in message:
                data = self.learned_patterns[pattern]
                data["strength"] = max(0.1, data["strength"] - 1.0)

                # Если сила упала ниже 0.5, удаляем паттерн
                if data["strength"] < 0.5:
                    del self.learned_patterns[pattern]

    def _learn_mistake(self, message: str, wrong_intent: str):
        """Запоминает ошибку"""
        # Находим правильные ключевые слова в сообщении
        for correct_intent, data in self.keyword_patterns.items():
            if correct_intent != wrong_intent:
                for keyword in data["keywords"]:
                    if keyword in message:
                        # Добавляем этот ключевое слово с бОльшим весом
                        self.keyword_patterns[correct_intent]["weight"] += 0.1
                        break

    # ========== ИНТЕГРАЦИЯ С ИГРОЙ ==========

    def respond(self, player_message: str, game_context: Dict = None) -> str:
        """Основной метод для ответа игроку - вызывается из игры"""

        # 1. Анализируем сообщение
        analysis = self.analyze_message(player_message)

        # 2. Генерируем ответ
        response = self.generate_response(analysis, game_context)

        # 3. Логируем (опционально)
        if self.db:
            self._log_to_database(player_message, response, analysis)

        return response

    def _log_to_database(self, player_message: str, ai_response: str, analysis: Dict):
        """Логирует диалог в базу данных"""
        try:
            cursor = self.db.cursor()
            cursor.execute('''
                INSERT INTO ai_conversation_log 
                (faction, player_message, ai_response, intent, sentiment, timestamp)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                self.faction,
                player_message,
                ai_response,
                analysis["intent"],
                analysis["sentiment"],
                datetime.now().isoformat()
            ))
            self.db.commit()
        except Exception as e:
            print(f"⚠️ Ошибка логирования: {e}")

    def get_conversation_history(self, limit: int = 10) -> List[Dict]:
        """Возвращает историю разговоров"""
        return self.conversation_memory[-limit:] if self.conversation_memory else []

    def get_ai_stats(self) -> Dict:
        """Возвращает статистику ИИ"""
        return {
            "faction": self.faction,
            "mood": self.mood,
            "trust": self.trust,
            "conversations_count": len(self.conversation_memory),
            "learned_patterns": len(self.learned_patterns),
            "model_size_bytes": self._get_model_size(),
            "personality": self.personality["name"]
        }

    def export_model(self, filepath: str = None):
        """Экспортирует модель в один файл"""
        if filepath is None:
            filepath = f"ai_models/{self.faction}_exported.ai"

        model_data = {
            "faction": self.faction,
            "keyword_patterns": self.keyword_patterns,
            "response_templates": self.response_templates,
            "learned_patterns": self.learned_patterns,
            "personality": self.personality,
            "state": {
                "mood": self.mood,
                "trust": self.trust
            },
            "version": "1.0",
            "exported_at": datetime.now().isoformat()
        }

        # Сохраняем в сжатом виде
        with gzip.open(filepath, 'wt', encoding='utf-8') as f:
            json.dump(model_data, f, ensure_ascii=False, indent=2)

        print(f"📦 Модель экспортирована в {filepath}")
        return filepath

    def import_model(self, filepath: str):
        """Импортирует модель из файла"""
        try:
            with gzip.open(filepath, 'rt', encoding='utf-8') as f:
                model_data = json.load(f)

            # Проверяем совместимость
            if model_data["faction"] != self.faction:
                print(f"⚠️ Модель для фракции {model_data['faction']}, а текущая {self.faction}")

            self.keyword_patterns = model_data["keyword_patterns"]
            self.response_templates = model_data["response_templates"]
            self.learned_patterns = model_data["learned_patterns"]

            if "state" in model_data:
                self.mood = model_data["state"].get("mood", 50)
                self.trust = model_data["state"].get("trust", 50)

            print(f"📥 Модель импортирована из {filepath}")
            return True

        except Exception as e:
            print(f"❌ Ошибка импорта: {e}")
            return False


# ========== ФАБРИКА ИИ ==========

class DiplomacyAIFactory:
    """Фабрика для создания и управления ИИ"""
    
    @staticmethod
    def create_ai(faction: str, db_connection=None) -> UltraLightDiplomacyAI:
        """Создает ИИ для указанной фракции"""
        return UltraLightDiplomacyAI(faction, db_connection)
    
    @staticmethod
    def get_available_factions() -> List[str]:
        """Возвращает список фракций с обученными моделями"""
        factions = []
        
        if os.path.exists("ai_models"):
            for item in os.listdir("ai_models"):
                if os.path.isdir(os.path.join("ai_models", item)):
                    factions.append(item)
        
        return factions or ["Север", "Эльфы", "Вампиры", "Адепты", "Элины"]
    
    @staticmethod
    def train_all_factions():
        """Обучает модели для всех фракций"""
        factions = ["Север", "Эльфы", "Вампиры", "Адепты", "Элины"]
        
        for faction in factions:
            print(f"\n🎓 Обучаем ИИ для {faction}...")
            ai = UltraLightDiplomacyAI(faction)
            ai.save_model()
        
        print("\n✅ Все модели обучены и сохранены!")

