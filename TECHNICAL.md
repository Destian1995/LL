# LL (Легенды Лэрдона) - Техническая документация

Подробное описание архитектуры, классов, функций и механик игры.

---

## 📑 Содержание

1. [Архитектура](#архитектура)
2. [Основные классы](#основные-классы)
3. [Игровые модули](#игровые-модули)
4. [Система ИИ](#система-иа)
5. [База данных](#база-данных)
6. [Интерфейс](#интерфейс)
7. [Механики игры](#механики-игры)

---

## 🏗️ Архитектура

### Слои приложения

```
┌─────────────────────────────────────┐
│  PRESENTATION (UI)                  │
│  Kivy widgets, screens, animations  │
└─────────┬───────────────────────────┘
          │
┌─────────▼───────────────────────────┐
│  GAME LOGIC                         │
│  game_process, economic, army, etc  │
└─────────┬───────────────────────────┘
          │
┌─────────▼───────────────────────────┐
│  AI & DECISION MAKING               │
│  ii.py, ai_models/                  │
└─────────┬───────────────────────────┘
          │
┌─────────▼───────────────────────────┐
│  DATA LAYER                         │
│  db_lerdon_connect, SQLite          │
└─────────────────────────────────────┘
```

### MVC паттерн

```
MODEL (game_process.py)
  ├── game_state
  ├── factions[]
  ├── cities[]
  └── armies[]
       │
VIEW (ui.py, game_process.py screen)
  ├── map rendering
  ├── city interface
  └── menus
       │
CONTROLLER (economic.py, army.py, politic.py)
  ├── process_building
  ├── process_attack
  └── process_treaty
```

---

## 👾 Основные классы

### 1. GameScreen (game_process.py)

```python
class GameScreen(Screen):
    """
    Главный экран игры - показывает карту и управляет игровым циклом
    """
    
    ATTRIBUTES:
        canvas              # Kivy canvas для отрисовки
        game_state          # dict с состоянием игры
        current_faction     # str название текущей фракции
        current_turn        # int номер текущего хода
        is_ai_turn         # bool ход ИИ или игрока
        selected_city      # City объект или None
        battle_mode        # bool режим битвы
        ai_controller      # AIController объект
        event_manager      # EventManager объект
        season_manager     # SeasonManager объект
        
    METHODS:
        on_enter()              # Called when screen appears
        on_leave()              # Called when screen hidden
        update_display()        # Redraw all graphics
        render_map()            # Draw map tiles
        render_cities()         # Draw city icons
        render_armies()         # Draw military units
        on_city_click(pos)      # Handle city selection
        on_button_click(action) # Handle action button
        process_turn()          # Execute game loop
        execute_ai_turn()       # Execute AI faction turn
        end_turn()              # Transition to next faction
        check_victory()         # Check win conditions
        save_game()             # Save current state
        load_game(save_id)      # Load saved game
```

**Интеграция с модулями:**
```
on_button_click("build_farm")
    → economic.EconomicCash.build_building("farm")
        → update DB
        → update screen

on_button_click("attack")
    → army.ArmyCash.attack(target_city)
        → fight.calculate_battle_result()
        → apply casualties
```

---

### 2. EconomicCash (economic.py)

```python
class EconomicCash:
    """
    Управление экономикой фракции
    """
    
    ATTRIBUTES:
        faction_name    # str названи фракции
        class_faction   # str класс фракции (warrior, merchant, mage)
        conn            # sqlite3 connection
        current_city    # str название текущего города
        _money          # float количество денег
        _population     # int численность населения
        _resources      # dict доступных ресурсов
        
    BUILDING_TYPES:
        "farm"              # Производит еду (+10 pop/turn)
        "barracks"          # Производит войска (+5 unit/turn)
        "market"            # Торговля (+15% доход)
        "wall"              # Защита города (+50 fortification)
        "tower"             # ПВО (+damage to air)
        "forge"             # Улучшение оружия (+damage)
        "library"           # Исследования (+1 research/turn)
        "bridge"            # Торговля (соединяет города)
        "shipyard"          # Боевые корабли
        "watchtower"        # Разведка (видимость)
        
    METHODS:
        def build_building(building_type: str, count: int = 1) -> bool:
            """
            Построить здание в текущем городе
            
            Параметры:
                building_type: тип здания (см. BUILDING_TYPES)
                count: количество зданий для постройки
                
            Возвращает:
                True если успешно, False если не хватает денег
                
            Побочные эффекты:
                - Вычитает стоимость из _money
                - Обновляет buildings таблицу в БД
                - Уведомляет UI об изменении
            """
            
        def calculate_income() -> float:
            """
            Рассчитать доход одного города за ход
            
            Возвращает:
                float: доход в золоте
                
            Формула:
                income = base_population * tax_rate
                for each market: income *= 1.15
                for each farm: population += 10
            """
            
        def pay_taxes() -> None:
            """
            Взять налоги в конце хода (добавить доход)
            
            Эффекты:
                - +income к _money
                - -population если налоги слишком высокие (восстание)
            """
            
        def trade_with(faction: str, resource: str, amount: int) -> bool:
            """
            Торговля ресурсами с другой фракцией
            
            Параметры:
                faction: название фракции-партнера
                resource: тип ресурса (gold, food, wood)
                amount: количество для обмена
                
            Возвращает:
                True если торговля согласована
                False если партнер отклонил
            """
            
        def apply_hunger() -> None:
            """
            Применить голод (если еды недостаточно)
            
            Эффекты:
                - -population при дефиците еды
                - -happiness населения
                - Возможность восстания
            """
            
        def get_building_cost(building_type: str) -> float:
            """
            Получить стоимость постройки здания
            
            Масштабирование затрат:
                base_cost * (1 + existing_buildings * 0.1)
            """
```

**Боевые здания и их функции:**

```python
MILITARY_BUILDINGS = {
    "barracks": {        # Казарма
        cost: 1000,
        production: ("infantry", 5),  # 5 пехотинцев в ход
        maintenance: 100,
        requires: None
    },
    "stable": {          # Конюшня
        cost: 1500,
        production: ("cavalry", 3),
        maintenance: 150,
        requires: "barracks"
    },
    "tower": {           # Боевая башня
        cost: 800,
        fortification: +50,
        maintenance: 80,
        requires: "wall"
    }
}
```

---

### 3. ArmyCash (army.py)

```python
class ArmyCash:
    """
    Управление армией фракции и боевыми операциями
    """
    
    ATTRIBUTES:
        faction_name     # str названи фракции
        class_faction    # str класс фракции
        conn             # sqlite3 connection
        current_city     # str название города
        _units           # dict {unit_type: count}
        _morale          # int боевой дух 0-100
        _experience      # int боевой опыт
        
    UNIT_TYPES:
        "infantry":      {"cost": 100, "power": 10, "health": 20}
        "cavalry":       {"cost": 200, "power": 15, "health": 15}
        "archer":        {"cost": 150, "power": 12, "health": 10}
        "siege_engine":  {"cost": 500, "power": 30, "health": 5}
        "mage":          {"cost": 300, "power": 20, "health": 8}
        
    MORALE_EFFECTS:
        100: +50% damage, -50% losses
        80:  +20% damage
        50:  normal
        30:  -20% damage
        10:  -50% damage, massive losses
        0:   army disbands
        
    METHODS:
        def recruit_units(unit_type: str, count: int) -> bool:
            """
            Набрать новые войска
            
            Требует:
                - Достаточно денег
                - Наличие казармы или конюшни (в зависимости от типа)
                - Достаточно населения (каждый боец = -1 население)
            """
            
        def attack(target_city: str) -> dict:
            """
            Атаковать целевой город
            
            Выполняет:
                1. Перемещение армии к городу
                2. Расчет боя через fight.calculate_battle_result()
                3. Применение урона и потерь
                4. Захват города если победа
                5. Обновление дипломатии (автоматическая война)
                
            Возвращает:
                {
                    "attacker_losses": int,
                    "defender_losses": int,
                    "winner": "attacker" | "defender",
                    "city_captured": bool
                }
            """
            
        def move_army(target_city: str) -> bool:
            """
            Переместить армию в другой город
            
            Требует:
                - Соседний город или дорога
                - Затраты: movement_points = distance * unit_count
            """
            
        def update_morale(delta: int) -> None:
            """
            Изменить боевой дух
            
            Причины изменения:
                +10 за победу
                -20 за поражение
                -5 за длительное неиспользование
                +5 за присутствие героя
            """
            
        def get_army_strength() -> float:
            """
            Получить общую боевую мощь армии
            
            Формула:
                strength = sum(count * unit_power for all units)
                strength *= morale_multiplier
                strength += fortification_bonus (если защита)
            """
```

---

### 4. AIController (ii.py)

```python
class AIController:
    """
    Управление ИИ фракции
    Анализирует ситуацию и принимает стратегические решения
    """
    
    ATTRIBUTES:
        faction_name         # str название фракции
        personality          # str "aggressive" | "defensive" | "diplomatic"
        economic_manager     # EconomicCash
        army_manager         # ArmyCash
        conn                 # sqlite3 connection
        threat_level        # int 0-100 (уровень угрозы от врагов)
        resource_level      # int 0-100 (уровень ресурсов)
        
    PERSONALITY_STRATEGIES:
        "aggressive": {
            build_priority: [barracks, stable, tower],
            attack_threshold: 0.7,  # атакует если армия в 70% сильнее
            trade_willingness: 0.3,
            ally_threshold: -50      # враждует при отношениях < -50
        }
        
        "defensive": {
            build_priority: [wall, tower, farm],
            attack_threshold: 1.0,  # атакует только если имеет 2x преимущество
            trade_willingness: 0.7,
            ally_threshold: 30
        }
        
        "diplomatic": {
            build_priority: [market, library, bridge],
            attack_threshold: 1.5,
            trade_willingness: 0.9,
            ally_threshold: 50
        }
        
    METHODS:
        def execute_turn() -> None:
            """
            Выполнить полный ход ИИ
            
            Последовательность:
                1. analyze_situation()
                2. make_strategic_decision()
                3. execute_decision()
                4. update_db_and_ui()
            """
            
        def analyze_situation() -> None:
            """
            Проанализировать текущую ситуацию
            
            Вычисляет:
                - resource_level = money / max_expected_money
                - threat_level = max_enemy_strength / own_strength
                - population_satisfaction = population / last_turn
                - city_protection = avg_fortification
            """
            
        def make_strategic_decision() -> str:
            """
            Принять решение о действии
            
            Логика:
                if money < 5000:
                    action = "expand_farms"
                elif army_count < needed_count:
                    action = "recruit"
                elif weak_neighbor and threat_level < 50:
                    action = "attack"
                elif need_ally:
                    action = "seek_alliance"
                else:
                    action = "improve_economy"
                    
            Возвращает:
                str: название выбранного действия
            """
            
        def execute_decision(action: str) -> None:
            """
            Выполнить выбранное действие
            
            Возможные действия:
                - "expand_farms": build multiple farms
                - "recruit": recruit units based on available money
                - "attack": find weak neighbor and attack
                - "seek_alliance": negotiate with compatible faction
                - "improve_economy": optimize trade routes
                - "improve_defense": build walls and towers
            """
            
        def find_attack_target() -> Optional[str]:
            """
            Найти целевой город для атаки
            
            Метод выбора:
                1. Найти соседние города
                2. Оценить защищенность каждого
                3. Выбрать самый слабо защищенный
                4. Проверить что армия может его захватить
            """
            
        def seek_alliance(other_faction: str) -> bool:
            """
            Предложить альянс другой фракции
            
            Условия для предложения:
                - Общий враг или враг одного из них
                - Близкие личности
                - Экономическая выгода от союза
                
            Возвращает:
                True если другая ИИ согласилась
            """
            
        def calculate_threat_from(other_faction: str) -> float:
            """
            Рассчитать угрозу от конкретной фракции
            
            Параметры для расчета:
                - army_strength_ratio (их армия / моя армия)
                - territorial_proximity (насколько близко граница)
                - diplo_relations (враждебные ли они)
                - tech_advantage (есть ли у них преимущество в технологиях)
            """
```

---

### 5. EventManager (event_manager.py)

```python
class EventManager:
    """
    Генерирование и обработка случайных событий в игре
    """
    
    EVENT_TYPES = {
        "plague":           {"probability": 0.05, "effect": "-population"},
        "treasure_found":   {"probability": 0.02, "effect": "+money"},
        "invasion":         {"probability": 0.10, "effect": "-army"},
        "good_harvest":     {"probability": 0.15, "effect": "+food"},
        "hero_arrival":     {"probability": 0.03, "effect": "+hero"},
        "rebellion":        {"probability": 0.08, "effect": "-money"},
        "dragon_attack":    {"probability": 0.01, "effect": "-city"},
        "trade_boom":       {"probability": 0.12, "effect": "+money"},
        "curse":            {"probability": 0.04, "effect": "-all_stats"},
        "blessing":         {"probability": 0.04, "effect": "+all_stats"}
    }
    
    METHODS:
        def generate_random_event(faction: str) -> dict:
            """
            Сгенерировать случайное событие для фракции
            
            Возвращает:
                {
                    "type": "plague",
                    "severity": 1-10,
                    "affected_city": str,
                    "duration": int (ходы)
                }
            """
            
        def apply_event_effect(event: dict, faction: str) -> None:
            """
            Применить эффект события к фракции
            
            Побочные эффекты:
                - Изменение ресурсов
                - Уведомление игрока
                - Логирование в БД
            """
            
        def generate_event_description(event: dict) -> str:
            """
            Генерировать описание события на русском
            
            Примеры:
                "В городе {city} вспыхнула чума! -30% население"
                "Найден клад! +5000 золота"
            """
```

---

### 6. SeasonManager (seasons.py)

```python
class SeasonManager:
    """
    Управление сезонами и их эффектами на игру
    """
    
    SEASONS = ["spring", "summer", "autumn", "winter"]
    
    SEASONAL_EFFECTS = {
        "spring": {
            "production_multiplier": 1.0,
            "population_growth": 1.05,
            "morale_change": +5
        },
        "summer": {
            "production_multiplier": 1.3,
            "population_growth": 1.1,
            "morale_change": +10
        },
        "autumn": {
            "production_multiplier": 1.2,
            "population_growth": 1.0,
            "morale_change": 0
        },
        "winter": {
            "production_multiplier": 0.5,
            "population_growth": 0.8,
            "morale_change": -10
        }
    }
    
    METHODS:
        def next_season() -> None:
            """
            Переключиться на следующий сезон (каждый 4-й ход)
            """
            
        def apply_seasonal_effects(faction: str) -> None:
            """
            Применить эффекты текущего сезона
            """
```

---

## 🎮 Игровые модули

### economic.py - Детальная механика

```python
# Стоимость построек (масштабируется)
BUILDING_COSTS = {
    "farm": 500,
    "barracks": 1000,
    "market": 1500,
    "wall": 800,
    "tower": 500,
    "forge": 2000,
    ...
}

# Производство зданий за ход
PRODUCTION_RATES = {
    "farm": {"food": 50, "population": 10},
    "barracks": {"soldiers": 5, "morale": 1},
    "market": {"gold": 100, "happiness": 2},
    ...
}

# Текущие функции валидации
def validate_building_construction(
    faction_name: str,
    city: str,
    building_type: str,
    count: int
) -> tuple[bool, str]:
    """
    Проверить возможность построить здание
    
    Возвращает:
        (можно_ли_строить, причина_отказа)
        
    Проверяет:
        ✓ Достаточно денег
        ✓ Город принадлежит фракции
        ✓ Осталось место (максимум зданий)
        ✓ Предварительные требования (例: wall перед tower)
    """
```

### army.py - Боевая механика

```python
def calculate_casualties(
    attacker_units: dict,
    defender_units: dict,
    defender_fortification: int
) -> tuple[dict, dict]:
    """
    Рассчитать потери обеих сторон
    
    Параметры:
        attacker_units: {unit_type: count}
        defender_units: {unit_type: count}
        defender_fortification: уровень укреплений 0-100
        
    Возвращает:
        (attacker_losses, defender_losses)
        
    Формула:
        enemy_strength = sum(count * unit_type_power)
        fortification_bonus = 0 if attack, (fortification/100) if defense
        raw_losses = (my_units / enemy_strength) * base_casualty_rate
        losses *= (1 - morale_factor)
    """

# Модификаторы боя
COMBAT_MODIFIERS = {
    "terrain": {
        "mountain": 1.3,  # защитник получает +30% к защите
        "plains": 1.0,
        "forest": 1.2,
        "water": 0.7      # мор флот слабее на суше
    },
    "season": {
        "winter": 0.7,    # все юниты слабее
        "summer": 1.1     # все юниты сильнее
    },
    "hero_presence": {
        "legendary": 1.5,
        "epic": 1.3,
        "rare": 1.1
    }
}
```

---

## 🗄️ База данных

### SQLite schema (schema_ii_acrh.txt)

```sql
-- Таблица фракций
CREATE TABLE factions (
    faction_id INTEGER PRIMARY KEY AUTOINCREMENT,
    faction_name TEXT UNIQUE NOT NULL,
    color TEXT NOT NULL,                           -- цвет на карте
    player_controlled BOOLEAN DEFAULT 0,           -- игрок ли управляет
    treasury REAL DEFAULT 5000,                    -- начальное золото
    total_population INTEGER DEFAULT 1000,
    tech_level INTEGER DEFAULT 0,
    current_season TEXT DEFAULT 'spring',
    turns_played INTEGER DEFAULT 0,
    victory_points INTEGER DEFAULT 0,
    status TEXT DEFAULT 'active'                   -- active, defeated, victorious
);

-- Таблица городов
CREATE TABLE cities (
    city_id INTEGER PRIMARY KEY AUTOINCREMENT,
    city_name TEXT NOT NULL,
    faction_name TEXT NOT NULL,
    x INTEGER NOT NULL,                            -- координата на карте
    y INTEGER NOT NULL,
    population INTEGER DEFAULT 500,
    fortification INTEGER DEFAULT 0,
    morale INTEGER DEFAULT 50,
    is_capital BOOLEAN DEFAULT 0,
    resources TEXT,                                -- JSON с ресурсами
    FOREIGN KEY (faction_name) REFERENCES factions(faction_name)
);

-- Таблица зданий
CREATE TABLE buildings (
    building_id INTEGER PRIMARY KEY AUTOINCREMENT,
    city_name TEXT NOT NULL,
    faction_name TEXT NOT NULL,
    building_type TEXT NOT NULL,
    count INTEGER NOT NULL DEFAULT 1,
    level INTEGER DEFAULT 1,                       -- улучшение здания
    construction_progress INTEGER DEFAULT 100,     -- % завершения
    FOREIGN KEY (city_name) REFERENCES cities(city_name)
);

-- Таблица армий
CREATE TABLE armies (
    army_id INTEGER PRIMARY KEY AUTOINCREMENT,
    faction_name TEXT NOT NULL,
    city_name TEXT,                                -- NULL если армия движется
    unit_type TEXT NOT NULL,                       -- infantry, cavalry, archer, etc
    count INTEGER NOT NULL,
    morale INTEGER DEFAULT 50,
    experience INTEGER DEFAULT 0,
    x INTEGER,                                     -- координата (для движущейся армии)
    y INTEGER,
    FOREIGN KEY (faction_name) REFERENCES factions(faction_name)
);

-- Таблица дипломатических отношений
CREATE TABLE diplomacy (
    diplomacy_id INTEGER PRIMARY KEY AUTOINCREMENT,
    faction1_name TEXT NOT NULL,
    faction2_name TEXT NOT NULL,
    relationship_type TEXT,                        -- alliance, war, trade, neutral
    relationship_level INTEGER DEFAULT 0,          -- -100 до +100
    treaty_turns_remaining INTEGER,
    FOREIGN KEY (faction1_name) REFERENCES factions(faction_name),
    FOREIGN KEY (faction2_name) REFERENCES factions(faction_name)
);

-- Таблица событий
CREATE TABLE events (
    event_id INTEGER PRIMARY KEY AUTOINCREMENT,
    faction_name TEXT NOT NULL,
    city_name TEXT,
    event_type TEXT NOT NULL,
    severity INTEGER DEFAULT 5,
    duration INTEGER,                              -- оставшиеся ходы
    turn_occurred INTEGER,
    FOREIGN KEY (faction_name) REFERENCES factions(faction_name)
);

-- Таблица героев
CREATE TABLE heroes (
    hero_id INTEGER PRIMARY KEY AUTOINCREMENT,
    hero_name TEXT NOT NULL,
    faction_name TEXT,
    rank TEXT,                                     -- "Главнокомандующий", "Генерал" и т.д.
    experience INTEGER DEFAULT 0,
    level INTEGER DEFAULT 1,
    strength INTEGER DEFAULT 10,
    intelligence INTEGER DEFAULT 10,
    leadership INTEGER DEFAULT 10,
    city_assigned TEXT                             -- город, где герой находится
);

-- Таблица артефактов
CREATE TABLE artifacts (
    artifact_id INTEGER PRIMARY KEY AUTOINCREMENT,
    artifact_name TEXT NOT NULL,
    hero_id INTEGER,
    rarity TEXT,                                   -- common, uncommon, rare, epic, legendary
    bonus_stat TEXT,
    bonus_value INTEGER,
    FOREIGN KEY (hero_id) REFERENCES heroes(hero_id)
);

-- Таблица игровых сохранений
CREATE TABLE game_saves (
    save_id INTEGER PRIMARY KEY AUTOINCREMENT,
    player_faction TEXT NOT NULL,
    turn_number INTEGER,
    save_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    game_state TEXT                                -- JSON с полным состоянием
);
```

---

## 🎨 Интерфейс (Kivy)

### Основные экраны

```python
from kivy.uix.screen import Screen
from kivy.uix.screenmanager import ScreenManager
from kivy.uix.boxlayout import BoxLayout

class MainMenuScreen(Screen):
    """Главное меню"""
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = BoxLayout(orientation='vertical')
        
        # Кнопки:
        # - New Game
        # - Load Game
        # - Settings
        # - Exit

class GameScreen(Screen):
    """Основной игровой экран"""
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Canvas для отрисовки карты
        # Кнопки действий (Economic, Army, Politic)
        # Информационная панель (текущий ход, ресурсы)

class CityInterfaceScreen(Screen):
    """Интерфейс управления городом"""
    def __init__(self, city_name, **kwargs):
        super().__init__(**kwargs)
        # Таблица зданий
        # Кнопки добавления зданий
        # Информация о населении и ресурсах

class BattleScreen(Screen):
    """Экран во время битвы"""
    def __init__(self, attacker_army, defender_army, **kwargs):
        super().__init__(**kwargs)
        # Анимация боя
        # Статистика потерь
        # Кнопки (продолжить, отступить)
```

### Кастомные виджеты

```python
class ModernButton(Button):
    """Кастомная кнопка с округлениями и анимацией"""
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.background_normal = ''
        self.background_color = PRIMARY_COLOR
        
        # Canvas с RoundedRectangle
        # bind к on_touch_down для анимации
        
class ResourceCard(BoxLayout):
    """Карточка с информацией о ресурсах"""
    text = StringProperty('Resource')
    icon = StringProperty('path/to/icon')
    
    # Отображает иконку и текст
    # Обновляется при изменении ресурсов

class TutorialHint(Popup):
    """Всплывающая подсказка для новичков"""
    def __init__(self, title, message, **kwargs):
        super().__init__(**kwargs)
        # Текст подсказки с стрелкой
        # Автоматически исчезает через 5 сек
```

---

## 🎮 Механики игры

### Система героев (heroes.py)

```python
# Ранги от высшего к низшему
RANKS = [
    "Главнокомандующий",      # 19 (максимум)
    "Верховный маршал",        # 18
    "Генерал-фельдмаршал",     # 17
    # ... 17 ещё рангов ...
    "Рядовой"                 # 1 (минимум)
]

class Hero:
    """Герой с характеристиками"""
    
    ATTRIBUTES:
        name: str
        faction: str
        rank: str                  # из RANKS
        level: int (1-100)
        experience: int            # exp к следующему уровню
        
        stats:
            strength: int          # атаковая сила
            intelligence: int      # магические способности
            leadership: int        # управление войсками
            
        artifacts: list[Artifact]  # экипировка
        city_assigned: str        # текущее место базирования
        
    METHODS:
        def gain_experience(amount: int)
        def level_up()
        def equip_artifact(artifact: Artifact)
        def get_total_bonus() -> float
```

### Система артефактов (heroes.py)

```python
ARTIFACT_RARITIES = {
    "common": {bonus: 5, probability: 0.40},
    "uncommon": {bonus: 15, probability: 0.30},
    "rare": {bonus: 30, probability: 0.20},
    "epic": {bonus: 50, probability: 0.08},
    "legendary": {bonus: 100, probability: 0.02}
}

ARTIFACT_BONUSES = {
    "sword_of_power": {stat: "strength", value: 20},
    "staff_of_wisdom": {stat: "intelligence", value: 20},
    "crown_of_leadership": {stat: "leadership", value: 30},
    ...
}
```

### Система диверсий (diversion.py)

```python
def send_diversion_squad(
    attacker_faction: str,
    target_city: str,
    squad_strength: int
) -> dict:
    """
    Отправить диверсионную группу для подрыва зданий
    
    Возвращает:
        {
            "success": bool,
            "buildings_destroyed": ["farm", "barracks"],
            "attacker_losses": int,
            "defender_alerted": bool
        }
    """
```

---

## 🔄 Game Loop (Главный цикл игры)

```python
def game_loop():
    while game_running:
        # 1. Обновление сезона (каждый 4-й ход)
        turn_number += 1
        if turn_number % 4 == 0:
            season_manager.next_season()
            for faction in all_factions:
                apply_seasonal_effects(faction)
        
        # 2. Ход игрока
        while waiting_for_player_input:
            render_game_screen()
            handle_input(player_action)
            
            if player_action in ["economic", "military", "diplomatic"]:
                execute_action(player_faction, player_action)
                player_finished_turn = True
        
        # 3. Ходы ИИ фракций
        for ai_faction in ai_factions:
            ai_controller = AIController(ai_faction)
            
            # Analyse
            ai_controller.analyze_situation()
            
            # Decide
            action = ai_controller.make_strategic_decision()
            
            # Execute
            ai_controller.execute_decision(action)
            
            # Event check
            if random() < EVENT_PROBABILITY:
                event = event_manager.generate_random_event(ai_faction)
                event_manager.apply_event_effect(event, ai_faction)
        
        # 4. Сбор доходов
        for faction in all_factions:
            economic.pay_taxes()
            economic.apply_hunger()
        
        # 5. Производство
        for city in all_cities:
            for building in city.buildings:
                produce_resources(city, building)
        
        # 6. Проверка условия победы
        if check_victory_condition():
            show_results_screen()
            break
        
        # 7. Сохранение
        if auto_save_enabled:
            save_game()
```

---

## 📦 Сборка и развертывание

### Buildozer конфигурация

```bash
# buildozer.spec

[app]
version = 4.7.9
title = Легенды Лэрдона
package.name = lerdonlegends

[buildozer]
log_level = 2
warn_on_root = 1

# Для Android
requirements = python3==3.11.0,kivy==2.2.0,kivymd,sqlite3

# Для iOS
ios.python_version = 3.11.0
```

### Команды сборки

```bash
# Debug APK (Android)
buildozer android debug

# Release APK
buildozer android release

# iOS
buildozer ios debug
```

---

## 🧪 Тестирование

### Пример unit теста

```python
import unittest
from economic import EconomicCash
from db_lerdon_connect import get_connection

class TestEconomic(unittest.TestCase):
    
    def setUp(self):
        self.conn = get_connection(":memory:")  # Временная БД
        self.econ = EconomicCash("test_faction", "warrior", self.conn)
    
    def test_building_cost_increases(self):
        """Проверить что стоимость здания растет с кол-вом"""
        cost1 = self.econ.get_building_cost("farm")
        # Построить 5 ферм
        for _ in range(5):
            self.econ.build_building("farm")
        cost2 = self.econ.get_building_cost("farm")
        self.assertGreater(cost2, cost1)
    
    def test_insufficient_funds(self):
        """Проверить что нельзя строить без денег"""
        self.econ._money = 100
        result = self.econ.build_building("tower")  # стоит 500+
        self.assertFalse(result)
    
    def tearDown(self):
        self.conn.close()
```

---

## 🐛 Debugging

### Useful logging

```python
import logging

logging.basicConfig(
    filename='game.log',
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

# В коде:
logger.debug(f"Faction {faction} started turn {turn}")
logger.info(f"Battle won: {attacker} vs {defender}")
logger.warning(f"Low resources for {faction}")
logger.error(f"Database error: {e}")
```

---

## 📚 Дополнительно

- Все функции форматирования чисел (`format_number()`) поддерживают до 12 порядков
- ИИ может быть трёх типов: aggressive, defensive, diplomatic
- Каждый сезон влияет на производство и мораль
- События имеют вероятность срабатывания от 1% до 15%
- Ранги героев соответствуют военным системам

---

**Версия документации:** 4.7.9  
**Последнее обновление:** 31.03.2026
