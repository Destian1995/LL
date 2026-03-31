# LL (Легенды Лэрдона) - Руководство разработчика

Инструкции по разработке, расширению и модификации проекта.

---

## 📋 Содержание

1. [Среда разработки](#среда-разработки)
2. [Структура проекта](#структура-проекта)
3. [Запуск локально](#запуск-локально)
4. [Добавление функционала](#добавление-функционала)
5. [Модификация ИИ](#модификация-иа)
6. [Тестирование](#тестирование)
7. [Сборка и публикация](#сборка-и-публикация)

---

## 🛠️ Среда разработки

### Требуемое ПО

```bash
# Python 3.11+ (обязательно!)
python --version
# Expected: Python 3.11.x

# Установка Kivy и зависимостей
pip install -r requirements.txt

# Для сборки под Android/iOS
pip install buildozer cython

# IDE рекомендуемые
- PyCharm Community Edition (бесплатна)
- VS Code + Python extension
- Sublime Text 3 + Python plugins
```

### requirements.txt (должны быть в корне проекта)

```
kivy==2.2.0
kivymd
python-decouple
pygame
pillow
pyjnius==1.5.0
cython==0.29.36
buildozer
sqlite3  # встроенная библиотека
```

### Структура вызовов для локальной разработки

```bash
# 1. Клонировать репозиторий
git clone <repo_url>
cd LL

# 2. Создать виртуальное окружение
python -m venv venv
source venv/bin/activate  # Linux/Mac
# или
venv\Scripts\activate  # Windows

# 3. Установить зависимости
pip install -r requirements.txt

# 4. Запустить игру
python main.py

# 5. Для отладки (с логированием)
python -u main.py 2>&1 | tee game_debug.log
```

---

## 📂 Структура проекта

### Слои архитектуры

```
LAYER 1: PRESENTATION (UI)
├── main.py (меню)
├── game_process.py (основной экран)
├── ui.py (интерфейс)
└── ui_components.py (виджеты)

LAYER 2: GAME LOGIC
├── economic.py (экономика)
├── army.py (армия)
├── politic.py (дипломатия)
├── event_manager.py (события)
├── seasons.py (сезоны)
├── heroes.py (герои)
└── fight.py (боевая система)

LAYER 3: AI & DECISION
├── ii.py (основной ИИ контроллер)
├── ai_models/
│   └── lerdon_ai/
│       └── ultralight_ai.py (продвинутые алгоритмы)
└── nobles_generator.py (генерация дворян)

LAYER 4: DATA
├── db_lerdon_connect.py (подключение БД)
├── db_manager.py (управление)
└── game_data.db (SQLite файл)
```

### Зависимости между модулями

```
main.py
  ↓
game_process.py (главный게임 цикл)
  ├→ economic.py (управление экономикой)
  ├→ army.py (управление войсками)
  ├→ politic.py (дипломатия)
  ├→ event_manager.py (события)
  ├→ seasons.py (сезоны)
  ├→ ii.py (ИИ)
  │   └→ ultralight_ai.py
  ├→ fight.py (боевая система)
  ├→ heroes.py (система героев)
  ├→ db_lerdon_connect.py (БД)
  └→ ui.py, ui_components.py (интерфейс)
```

---

## 🖥️ Запуск локально

### Debug режим

```python
# В main.py добавить:
import logging

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

if __name__ == '__main__':
    # Включить debug вывод
    Window.size = (1200, 800)  # Окно поменьше для отладки
    DebugApp().run()
```

### Горячие клавиши для отладки

```python
# Добавить в game_process.py:

def on_keyboard(self, window, key, scancode, codepoint, modifier):
    if key == 27:  # ESC
        self.show_debug_menu()
    elif key == 112:  # F
        self.toggle_fullscreen()
    elif codepoint == 'd':
        self.dump_game_state()  # Вывести состояние в консоль
    elif codepoint == 's':
        self.save_game()  # Быстрое сохранение
    elif codepoint == 'l':
        self.load_game()  # Быстрая загрузка
    return True

def dump_game_state(self):
    """Вывести все данные игры в консоль"""
    print("=== GAME STATE DUMP ===")
    print(f"Turn: {self.current_turn}")
    print(f"Current faction: {self.current_faction}")
    
    cursor = self.conn.cursor()
    cursor.execute("SELECT * FROM factions")
    print("\nFactions:")
    for row in cursor.fetchall():
        print(f"  {row}")
    
    cursor.execute("SELECT * FROM armies")
    print("\nArmies:")
    for row in cursor.fetchall():
        print(f"  {row}")
```

### Console вывод

```bash
# Смотреть логи в реальном времени
tail -f game.log

# Поиск ошибок
grep ERROR game.log

# Статистика использования памяти
python -m memory_profiler main.py
```

---

## ➕ Добавление функционала

### 1️⃣ Добавление нового типа здания

**Файл:** `economic.py`

```python
# ШАГ 1: Добавить в константы
BUILDING_COSTS = {
    ...
    "windmill": 600,      # Новое здание
    ...
}

BUILDING_PRODUCTION = {
    ...
    "windmill": {
        "gold": 75,      # производит 75 золота в ход
        "morale": 1      # +1 к морали города
    },
    ...
}

# ШАГ 2: Добавить проверку в validate_building_construction()
def validate_building_construction(...):
    ...
    if building_type == "windmill":
        # Ветряная мельница требует ровное место
        if city_terrain != "plains":
            return False, "Ветряную мельницу можно строить только в степи"
    ...

# ШАГ 3: Обновить БД схему (если нужны новые параметры)
# ALTER TABLE buildings ADD COLUMN rotation INTEGER DEFAULT 0;

# ШАГ 4: Добавить иконку в assets/
# assets/buildings/windmill.png
```

**Файл:** `ui.py` (обновить интерфейс)

```python
def show_building_menu(self, city):
    # Добавить кнопку для новой постройки
    windmill_btn = ModernButton(
        text="Построить ветряную мельницу\n[600 золота]",
        on_press=lambda: self.build("windmill")
    )
    self.building_menu.add_widget(windmill_btn)
```

### 2️⃣ Добавление новой фракции

**Файл:** `main.py`

```python
# ШАГ 1: Определить фракцию
FACTIONS = {
    "human": {
        "name": "Люди",
        "color": "#0066FF",
        "starting_units": {"infantry": 50, "archer": 20},
        "starting_buildings": {"farm": 5, "barracks": 2},
        "special_ability": "trade_bonus"  # +20% к торговле
    },
    "elves": {  # НОВАЯ
        "name": "Эльфы",
        "color": "#00FF00",
        "starting_units": {"archer": 60, "cavalry": 10},
        "starting_buildings": {"tower": 3, "library": 2},
        "special_ability": "magic_bonus"  # +30% к исследованиям
    },
    ...
}

# ШАГ 2: В base FACTION SELECTION, добавить кнопку
def create_faction_buttons(self):
    for faction_key, faction_data in FACTIONS.items():
        btn = Button(
            text=faction_data["name"],
            background_color=get_color_from_hex(faction_data["color"])
        )
        btn.bind(on_press=lambda *args, k=faction_key: self.select_faction(k))
        self.faction_grid.add_widget(btn)

# ШАГ 3: Инициализировать фракцию в БД
def initialize_faction(faction_key):
    faction_data = FACTIONS[faction_key]
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO factions (faction_name, color, treasury, total_population)
        VALUES (?, ?, 5000, 1000)
    """, (faction_data["name"], faction_data["color"]))
    conn.commit()
```

**Файл:** `ii.py` (настроить ИИ для новой фракции)

```python
# Добавить узкоспециальную стратегию для эльфов
class ElfAIStrategy(AIController):
    def __init__(self, faction_name):
        super().__init__(faction_name, personality="diplomatic")
        self.magic_focus = True  # Сфокусирован на магии
    
    def make_strategic_decision(self):
        if self.magic_focus and self.resource_level > 80:
            return "expand_libraries"  # Строить больше библиотек
        return super().make_strategic_decision()
```

### 3️⃣ Добавление новой системы событий

**Файл:** `event_manager.py`

```python
# ШАГ 1: Добавить новое событие
EVENT_TYPES["meteor_strike"] = {
    "probability": 0.01,
    "effect": "-city",  # Разрушает город
    "severity": 10,
    "description": "Метеорный удар уничтожил город {city}!"
}

# ШАГ 2: Имплементировать эффект события
def apply_event_effect(event, faction):
    if event["type"] == "meteor_strike":
        # Удалить город
        cursor = self.conn.cursor()
        cursor.execute(
            "DELETE FROM cities WHERE city_name = ? AND faction_name = ?",
            (event["affected_city"], faction)
        )
        
        # Удалить все здания и армии в городе
        cursor.execute(
            "DELETE FROM buildings WHERE city_name = ?",
            (event["affected_city"],)
        )
        
        # Уведомить игрока
        self.send_notification(
            f"Метеор упал на город {event['affected_city']}!",
            severity="critical"
        )
        
        self.conn.commit()
```

### 4️⃣ Добавление нового способности героя

**Файл:** `heroes.py`

```python
# ШАГ 1: Определить способность
HERO_ABILITIES = {
    ...
    "leadership_aura": {
        "name": "Аура лидера",
        "description": "+10% боевой дух всем войскам в городе",
        "cost": 5,  # очков магии в ход
        "effect": lambda hero: hero.leadership * 1.1
    }
    ...
}

# ШАГ 2: Применить эффект способности
class Hero:
    def apply_ability(self, ability_name):
        if ability_name in HERO_ABILITIES:
            ability = HERO_ABILITIES[ability_name]
            
            # Проверить хватает ли маны
            if self.mana >= ability["cost"]:
                effect = ability["effect"](self)
                self.mana -= ability["cost"]
                return effect
        return None
```

---

## 🤖 Модификация ИИ

### Изменение стратегии ИИ

**Файл:** `ii.py`

```python
class AIController:
    
    # Текущие пороги
    LOW_MONEY_THRESHOLD = 5000
    LOW_ARMY_THRESHOLD = 50
    
    # МОДИФИЦИРОВАТЬ ЭТИ ЗНАЧЕНИЯ для изменения поведения
    ATTACK_THRESHOLD = {
        "aggressive": 0.7,     # Атакует с 70% преимуществом
        "defensive": 1.5,      # Атакует с 150% преимуществом
        "diplomatic": 0.5      # Очень редко атакует
    }
    
    def make_strategic_decision(self):
        # Текущая логика (упрощённо):
        if self.money < self.LOW_MONEY_THRESHOLD:
            return "expand_farms"
        elif self.army_count < self.LOW_ARMY_THRESHOLD:
            return "recruit"
        elif self.has_weak_neighbor():
            return "attack"
        else:
            return "improve_economy"
        
        # МОДИФИКАЦИЯ: Добавить новое решение
        if self.diplomacy_level > 80:  # Много союзников
            return "form_coalition"     # Новое действие
```

### Создание специализированного ИИ

**Файл:** `ai_models/lerdon_ai/custom_ai.py` (новый файл)

```python
from ...ii import AIController

class MerchantsAI(AIController):
    """
    Специализированный ИИ торговцы
    Фокусируется на торговле и экономике
    """
    
    def __init__(self, faction_name):
        super().__init__(faction_name, personality="diplomatic")
        self.merchant_focus = True
        self.trade_routes = []
    
    def make_strategic_decision(self):
        # Приоритет: Торговля → Экономика → Война
        
        if len(self.trade_routes) < 3:
            return "establish_trade_route"
        
        if self.resource_level < 70:
            return "expand_markets"
        
        # Только если вынужден
        if self.threat_level > 80:
            return "defend"
        
        return "improve_economy"
    
    def execute_decision(self, action):
        if action == "establish_trade_route":
            # Найти соседнюю фракцию и предложить торговлю
            target = self.find_trade_partner()
            profit = self.calculate_trade_profit(target)
            self.initiate_trade(target, profit)
        else:
            super().execute_decision(action)
```

### Отладка ИИ

```python
# Добавить в ii.py для отладки

class AIController:
    DEBUG = True  # Включить отладку
    
    def make_strategic_decision(self):
        if self.DEBUG:
            print(f"\n=== AI DECISION MAKING ({self.faction_name}) ===")
            print(f"Money: {self.money}")
            print(f"Army strength: {self.calculate_army_strength()}")
            print(f"Threat level: {self.threat_level}")
            print(f"Diplomacy: {self.get_diplomacy_summary()}")
        
        decision = self._calculate_decision()
        
        if self.DEBUG:
            print(f"Decision: {decision}")
            print("=" * 40)
        
        return decision
```

---

## 🧪 Тестирование

### Unit тесты

**Файл:** `tests/test_economic.py`

```python
import unittest
import sqlite3
from economic import EconomicCash

class TestEconomics(unittest.TestCase):
    
    def setUp(self):
        # Создать временную БД для тестов
        self.conn = sqlite3.connect(":memory:")
        self.cursor = self.conn.cursor()
        
        # Создать таблицы
        self.cursor.execute("""
            CREATE TABLE buildings (
                city_name TEXT,
                faction TEXT,
                building_type TEXT,
                count INTEGER
            )
        """)
        self.conn.commit()
        
        self.econ = EconomicCash("test", "warrior", self.conn)
    
    def test_building_cost(self):
        """Проверить расчет стоимости здания"""
        cost = self.econ.get_building_cost("farm")
        self.assertEqual(cost, 500)
    
    def test_insufficient_funds(self):
        """Проверить что нельзя строить без денег"""
        self.econ._money = 100
        result = self.econ.build_building("farm")
        self.assertFalse(result)
    
    def tearDown(self):
        self.conn.close()

if __name__ == '__main__':
    unittest.main()
```

**Запуск тестов:**

```bash
# Все тесты
python -m unittest discover

# Конкретный тест
python -m unittest tests.test_economic.TestEconomics.test_building_cost

# С verbose выводом
python -m unittest discover -v
```

### Integration тесты

```python
# tests/test_game_flow.py

def test_full_game_turn():
    """Полный тест одного хода игры"""
    
    # 1. Инициализировать игру
    game = GameScreen()
    game.init_game("human", num_ai=2)
    
    # 2. Игрок делает ход
    game.build_building("farm")
    assert game.get_faction_money("human") < 5000
    
    # 3. ИИ делает ход
    game.execute_ai_turn()
    
    # 4. Проверить что состояние обновилось
    assert game.current_turn == 2
```

### Performance тесты

```python
# tests/test_performance.py

import time
from ii import AIController

def test_ai_decision_performance():
    """Проверить что ИИ делает решение быстро"""
    
    ai = AIController("test")
    
    start = time.time()
    for _ in range(100):
        ai.make_strategic_decision()
    elapsed = time.time() - start
    
    # Должно занять < 1 секунда
    assert elapsed < 1.0, f"AI decision took {elapsed}s"
```

---

## 📦 Сборка и публикация

### Подготовка к сборке

```bash
# Очистить временные файлы
find . -type d -name __pycache__ -exec rm -r {} +
find . -type f -name "*.pyc" -delete
find . -type d -name ".pytest_cache" -exec rm -r {} +

# Проверить что нет синтаксических ошибок
python -m py_compile *.py
python -m py_compile ai_models/**/*.py
```

### Сборка APK (Android)

```bash
# Подготовка
buildozer android clean
buildozer android update

# Debug сборка (для тестирования)
buildozer android debug

# Release сборка (для публикации)
buildozer android release

# Загрузить на устройство
adb install -r bin/lerdonlegends-4.7.9-debug.apk

# Запустить приложение
adb shell am start -n com.lerdonlegends.lerdonlegends/.MainActivity
```

### Versionning

**Обновить версию в:**

```python
# buildozer.spec
version = 4.7.9 → 4.8.0

# main.py (если есть)
__version__ = "4.7.9" → "4.8.0"

# git tag
git tag v4.8.0
git push origin v4.8.0
```

### Публикация в Play Store

1. Создать Google Play Developer account
2. Подписать APK:
   ```bash
   keytool -genkey -v -keystore lerdon.keystore \
       -keyalg RSA -keysize 2048 -validity 10000 \
       -alias lerdon_key
   
   jarsigner -verbose -sigalg SHA1withRSA -digestalg SHA1 \
       -keystore lerdon.keystore \
       bin/lerdonlegends-4.8.0-release-unsigned.apk \
       lerdon_key
   ```
3. Загрузить в Play Console
4. Заполнить metadata, скриншоты, описание
5. Отправить на review

---

## ⚡ Performance Optimization

### Профилирование

```bash
# Найти узкие места
python -m cProfile -s cumulative main.py > profile.txt
cat profile.txt | head -50

# Профилирование памяти
python -m memory_profiler main.py
```

### Оптимизация рендеринга

```python
# Избегать перерисовки всей карты каждый ход
class GameScreen(Screen):
    
    def update_display(self):
        # НЕПРАВИЛЬНО: перерисовать всю карту
        # self.canvas.clear()
        # для каждого города: отрисовать
        
        # ПРАВИЛЬНО: обновить только изменившиеся города
        if self.dirty_cities:
            for city in self.dirty_cities:
                self.update_city_graphics(city)
        self.dirty_cities = set()
```

---

## 📖 Git Workflow

```bash
# Создать feature branch
git checkout -b feature/new-building-type

# Коммитить регулярно со смыслом сообщения
git add .
git commit -m "Add windmill building with wind effect"

# После завершения - pull request
git push origin feature/new-building-type
# Создать PR на GitHub

# Мерж после review
git checkout main
git merge feature/new-building-type
git push origin main
```

---

## 🔗 Полезные ссылки

- [Kivy Documentation](https://kivy.org/doc/stable/)
- [KivyMD Documentation](https://kivymd.readthedocs.io/)
- [SQLite Documentation](https://www.sqlite.org/docs.html)
- [Python Documentation](https://docs.python.org/3/)
- [Buildozer Documentation](https://buildozer.readthedocs.io/)

---

## 🆘 Troubleshooting

### Проблема: ImportError при запуске

```bash
# Проверить что все зависимости установлены
pip install -r requirements.txt

# Проверить версию Python
python --version  # Должна быть 3.11+
```

### Проблема: Kivy не отрисовывает виджеты

```python
# Убедиться что Window не имеет size=None
from kivy.core.window import Window
Window.size = (1280, 720)

# Скрыть консоль ошибок Kivy
import os
os.environ['KIVY_WINDOW'] = 'pygame'
```

### Проблема: БД заблокирована

```python
# Использовать timeout для подключений
conn = sqlite3.connect("game_data.db", timeout=5.0)

# Или использовать WAL режим
conn.execute("PRAGMA journal_mode=WAL")
```

---

**Версия руководства:** 4.7.9  
**Последнее обновление:** 31.03.2026
