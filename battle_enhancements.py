"""
Модуль улучшений боевой системы
Добавляет:
1. Новые типы войск (Кавалерия, Осадные, Маги, Драконы)
2. Специальные способности юнитов
3. Систему элементов/стихий
4. Улучшенную матрицу эффективности
5. Статусные эффекты в бою
"""

import sqlite3
from typing import Dict, List, Tuple, Optional
import random

# ============================================================================
# 1. НОВЫЕ ТИПЫ ВОЙСК
# ============================================================================

UNIT_TYPE_INFANTRY = "Пехота"
UNIT_TYPE_ARCHER = "Стрелки"
UNIT_TYPE_CAVALRY = "Кавалерия"
UNIT_TYPE_SIEGE = "Осадные"
UNIT_TYPE_MAGE = "Маги"
UNIT_TYPE_DRAGON = "Драконы"
UNIT_TYPE_HEALER = "Целители"
UNIT_TYPE_ASSASSIN = "Убийцы"

ALL_UNIT_TYPES = [
    UNIT_TYPE_INFANTRY, UNIT_TYPE_ARCHER, UNIT_TYPE_CAVALRY, 
    UNIT_TYPE_SIEGE, UNIT_TYPE_MAGE, UNIT_TYPE_DRAGON,
    UNIT_TYPE_HEALER, UNIT_TYPE_ASSASSIN
]

# ============================================================================
# 2. УЛУЧШЕННАЯ МАТРИЦА ЭФФЕКТИВНОСТИ
# ============================================================================

ENHANCED_TYPE_EFFECTIVENESS = {
    # Пехота
    UNIT_TYPE_INFANTRY: {
        UNIT_TYPE_INFANTRY: 1.0,
        UNIT_TYPE_ARCHER: 1.2,      # Пехота эффективна против стрелков
        UNIT_TYPE_CAVALRY: 0.7,     # Пехота слаба против кавалерии
        UNIT_TYPE_SIEGE: 1.4,       # Пехота эффективна против осадных
        UNIT_TYPE_MAGE: 1.1,        # Пехота немного эффективна против магов (быстрое сближение)
        UNIT_TYPE_DRAGON: 0.6,      # Пехота очень слаба против драконов
        UNIT_TYPE_HEALER: 1.3,      # Пехота эффективна против целителей
        UNIT_TYPE_ASSASSIN: 0.9,    # Пехота немного слаба против убийц
    },
    # Стрелки
    UNIT_TYPE_ARCHER: {
        UNIT_TYPE_INFANTRY: 0.8,
        UNIT_TYPE_ARCHER: 1.0,
        UNIT_TYPE_CAVALRY: 0.6,     # Стрелки слабы против кавалерии
        UNIT_TYPE_SIEGE: 1.5,       # Стрелки эффективны против осадных
        UNIT_TYPE_MAGE: 1.2,        # Стрелки эффективны против магов (прерывают заклинания)
        UNIT_TYPE_DRAGON: 0.7,      # Стрелки слабы против драконов
        UNIT_TYPE_HEALER: 1.3,      # Стрелки эффективны против целителей
        UNIT_TYPE_ASSASSIN: 0.5,    # Стрелки очень слабы против убийц (быстрое сближение)
    },
    # Кавалерия
    UNIT_TYPE_CAVALRY: {
        UNIT_TYPE_INFANTRY: 1.4,    # Кавалерия эффективна против пехоты
        UNIT_TYPE_ARCHER: 1.5,      # Кавалерия очень эффективна против стрелков
        UNIT_TYPE_CAVALRY: 1.0,
        UNIT_TYPE_SIEGE: 1.6,       # Кавалерия разрушительна против осадных
        UNIT_TYPE_MAGE: 1.3,        # Кавалерия эффективна против магов
        UNIT_TYPE_DRAGON: 0.5,      # Кавалерия очень слаба против драконов
        UNIT_TYPE_HEALER: 1.4,      # Кавалерия эффективна против целителей
        UNIT_TYPE_ASSASSIN: 0.6,    # Кавалерия слаба против убийц (могут атаковать сзади)
    },
    # Осадные
    UNIT_TYPE_SIEGE: {
        UNIT_TYPE_INFANTRY: 0.6,    # Осадные слабы против пехоты
        UNIT_TYPE_ARCHER: 0.7,      # Осадные слабы против стрелков
        UNIT_TYPE_CAVALRY: 0.5,     # Осадные очень слабы против кавалерии
        UNIT_TYPE_SIEGE: 1.0,
        UNIT_TYPE_MAGE: 0.9,        # Осадные немного слабы против магов
        UNIT_TYPE_DRAGON: 0.4,      # Осадные очень слабы против драконов
        UNIT_TYPE_HEALER: 1.1,      # Осадные немного эффективны против целителей
        UNIT_TYPE_ASSASSIN: 0.5,    # Осадные очень слабы против убийц
    },
    # Маги
    UNIT_TYPE_MAGE: {
        UNIT_TYPE_INFANTRY: 0.9,
        UNIT_TYPE_ARCHER: 0.8,
        UNIT_TYPE_CAVALRY: 0.7,     # Маги слабы против кавалерии
        UNIT_TYPE_SIEGE: 1.2,       # Маги эффективны против осадных
        UNIT_TYPE_MAGE: 1.0,
        UNIT_TYPE_DRAGON: 0.8,      # Маги слабы против драконов (магическая устойчивость)
        UNIT_TYPE_HEALER: 1.1,      # Маги немного эффективны против целителей
        UNIT_TYPE_ASSASSIN: 0.4,    # Маги очень слабы против убийц
    },
    # Драконы
    UNIT_TYPE_DRAGON: {
        UNIT_TYPE_INFANTRY: 1.5,    # Драконы разрушительны против пехоты
        UNIT_TYPE_ARCHER: 1.4,      # Драконы эффективны против стрелков
        UNIT_TYPE_CAVALRY: 1.5,     # Драконы разрушительны против кавалерии
        UNIT_TYPE_SIEGE: 1.6,       # Драконы разрушительны против осадных
        UNIT_TYPE_MAGE: 1.2,        # Драконы эффективны против магов
        UNIT_TYPE_DRAGON: 1.0,
        UNIT_TYPE_HEALER: 1.4,      # Драконы эффективны против целителей
        UNIT_TYPE_ASSASSIN: 0.8,    # Драконы немного слабы против убийц (могут атаковать с воздуха)
    },
    # Целители
    UNIT_TYPE_HEALER: {
        UNIT_TYPE_INFANTRY: 0.7,
        UNIT_TYPE_ARCHER: 0.7,
        UNIT_TYPE_CAVALRY: 0.6,
        UNIT_TYPE_SIEGE: 0.8,
        UNIT_TYPE_MAGE: 0.9,
        UNIT_TYPE_DRAGON: 0.6,
        UNIT_TYPE_HEALER: 1.0,
        UNIT_TYPE_ASSASSIN: 0.5,    # Целители очень слабы против убийц
    },
    # Убийцы
    UNIT_TYPE_ASSASSIN: {
        UNIT_TYPE_INFANTRY: 1.2,    # Убийцы эффективны против пехоты
        UNIT_TYPE_ARCHER: 1.5,      # Убийцы очень эффективны против стрелков
        UNIT_TYPE_CAVALRY: 1.3,     # Убийцы эффективны против кавалерии (атака сзади)
        UNIT_TYPE_SIEGE: 1.6,       # Убийцы разрушительны против осадных
        UNIT_TYPE_MAGE: 1.7,        # Убийцы очень эффективны против магов
        UNIT_TYPE_DRAGON: 0.9,      # Убийцы немного слабы против драконов
        UNIT_TYPE_HEALER: 1.5,      # Убийцы эффективны против целителей
        UNIT_TYPE_ASSASSIN: 1.0,
    }
}

# ============================================================================
# 3. СИСТЕМА ЭЛЕМЕНТОВ/СТИХИЙ
# ============================================================================

ELEMENT_FIRE = "Огонь"
ELEMENT_WATER = "Вода"
ELEMENT_EARTH = "Земля"
ELEMENT_AIR = "Воздух"
ELEMENT_LIGHT = "Свет"
ELEMENT_DARK = "Тьма"
ELEMENT_NONE = None

ALL_ELEMENTS = [ELEMENT_FIRE, ELEMENT_WATER, ELEMENT_EARTH, ELEMENT_AIR, 
                ELEMENT_LIGHT, ELEMENT_DARK]

# Матрица эффективности элементов
ELEMENT_EFFECTIVENESS = {
    ELEMENT_FIRE: {
        ELEMENT_FIRE: 1.0,
        ELEMENT_WATER: 0.6,      # Огонь слаб против воды
        ELEMENT_EARTH: 1.1,      # Огонь немного эффективен против земли
        ELEMENT_AIR: 1.3,        # Огонь эффективен против воздуха
        ELEMENT_LIGHT: 1.0,
        ELEMENT_DARK: 1.2,       # Огонь эффективен против тьмы
        ELEMENT_NONE: 1.0,
    },
    ELEMENT_WATER: {
        ELEMENT_FIRE: 1.4,       # Вода эффективна против огня
        ELEMENT_WATER: 1.0,
        ELEMENT_EARTH: 0.8,      # Вода слаба против земли
        ELEMENT_AIR: 0.9,
        ELEMENT_LIGHT: 1.1,
        ELEMENT_DARK: 0.9,
        ELEMENT_NONE: 1.0,
    },
    ELEMENT_EARTH: {
        ELEMENT_FIRE: 0.9,
        ELEMENT_WATER: 1.2,      # Земля эффективна против воды
        ELEMENT_EARTH: 1.0,
        ELEMENT_AIR: 0.7,        # Земля слаба против воздуха
        ELEMENT_LIGHT: 1.0,
        ELEMENT_DARK: 1.1,
        ELEMENT_NONE: 1.0,
    },
    ELEMENT_AIR: {
        ELEMENT_FIRE: 0.7,       # Воздух слаб против огня
        ELEMENT_WATER: 1.1,
        ELEMENT_EARTH: 1.3,      # Воздух эффективен против земли
        ELEMENT_AIR: 1.0,
        ELEMENT_LIGHT: 1.2,
        ELEMENT_DARK: 0.9,
        ELEMENT_NONE: 1.0,
    },
    ELEMENT_LIGHT: {
        ELEMENT_FIRE: 1.0,
        ELEMENT_WATER: 0.9,
        ELEMENT_EARTH: 1.0,
        ELEMENT_AIR: 0.8,
        ELEMENT_LIGHT: 1.0,
        ELEMENT_DARK: 1.5,       # Свет очень эффективен против тьмы
        ELEMENT_NONE: 1.0,
    },
    ELEMENT_DARK: {
        ELEMENT_FIRE: 0.8,
        ELEMENT_WATER: 1.1,
        ELEMENT_EARTH: 0.9,
        ELEMENT_AIR: 1.1,
        ELEMENT_LIGHT: 0.5,      # Тьма очень слаба против света
        ELEMENT_DARK: 1.0,
        ELEMENT_NONE: 1.0,
    },
    ELEMENT_NONE: {
        ELEMENT_FIRE: 1.0,
        ELEMENT_WATER: 1.0,
        ELEMENT_EARTH: 1.0,
        ELEMENT_AIR: 1.0,
        ELEMENT_LIGHT: 1.0,
        ELEMENT_DARK: 1.0,
        ELEMENT_NONE: 1.0,
    }
}

# ============================================================================
# 4. СПЕЦИАЛЬНЫЕ СПОСОБНОСТИ ЮНИТОВ
# ============================================================================

ABILITY_CRITICAL_HIT = "critical_hit"         # Критический удар (x2 урон с шансом)
ABILITY_DODGE = "dodge"                       # Уклонение от атаки
ABILITY_VAMPIRISM = "vampirism"               # Вампиризм (восстановление здоровья)
ABILITY_FIRST_STRIKE = "first_strike"         # Первый удар
ABILITY_DOUBLE_ATTACK = "double_attack"       # Двойная атака
ABILITY_AREA_DAMAGE = "area_damage"           # Урон по области
ABILITY_HEAL_ALLY = "heal_ally"               # Лечение союзника
ABILITY_STUN = "stun"                         # Оглушение врага
ABILITY_POISON = "poison"                     # Отравление врага
ABILITY_ARMOR_PIERCE = "armor_pierce"         # Игнорирование части защиты
ABILITY_COUNTER_ATTACK = "counter_attack"     # Контратака
ABILITY_FLYING = "flying"                     # Летающий (игнорирует некоторые атаки)
ABILITY_REGENERATION = "regeneration"         # Регенерация здоровья каждый ход
ABILITY_BERSERK = "berserk"                   # Берсерк (больше урона при низком здоровье)
ABILITY_GUARDIAN = "guardian"                 # Защитник (защищает соседние юниты)
ABILITY_PROTECTED = "protected"               # Защищенный (сниженный входящий урон)

# Описание способностей
ABILITY_DESCRIPTIONS = {
    ABILITY_CRITICAL_HIT: {"name": "Критический удар", "desc": "Шанс нанести двойной урон", "chance": 0.25},
    ABILITY_DODGE: {"name": "Уклонение", "desc": "Шанс полностью избежать атаки", "chance": 0.20},
    ABILITY_VAMPIRISM: {"name": "Вампиризм", "desc": "Восстанавливает 30% от нанесенного урона", "rate": 0.3},
    ABILITY_FIRST_STRIKE: {"name": "Первый удар", "desc": "Атакует первым в раунде"},
    ABILITY_DOUBLE_ATTACK: {"name": "Двойная атака", "desc": "Атакует дважды за раунд"},
    ABILITY_AREA_DAMAGE: {"name": "Урон по области", "desc": "Наносит 50% урона соседним врагам"},
    ABILITY_HEAL_ALLY: {"name": "Лечение союзника", "desc": "Лечит случайного союзника на 20% от макс. здоровья"},
    ABILITY_STUN: {"name": "Оглушение", "desc": "Шанс оглушить врага на 1 ход", "chance": 0.15},
    ABILITY_POISON: {"name": "Отравление", "desc": "Наносит 10% от макс. здоровья каждый ход в течение 3 ходов"},
    ABILITY_ARMOR_PIERCE: {"name": "Пробивание брони", "desc": "Игнорирует 50% защиты врага"},
    ABILITY_COUNTER_ATTACK: {"name": "Контратака", "desc": "Атакует врага при получении урона"},
    ABILITY_FLYING: {"name": "Полет", "desc": "Игнорирует наземные препятствия, получает меньше урона от пехоты"},
    ABILITY_REGENERATION: {"name": "Регенерация", "desc": "Восстанавливает 5% здоровья в начале каждого хода"},
    ABILITY_BERSERK: {"name": "Берсерк", "desc": "+50% урона при здоровье ниже 30%"},
    ABILITY_GUARDIAN: {"name": "Защитник", "desc": "Снижает урон по соседним союзникам на 25%"},
}

# ============================================================================
# 5. СТАТУСНЫЕ ЭФФЕКТЫ
# ============================================================================

STATUS_BURN = "burn"              # Горение (урон каждый ход)
STATUS_FREEZE = "freeze"          # Заморозка (пропуск хода)
STATUS_POISONED = "poisoned"      # Отравление (урон каждый ход)
STATUS_STUNNED = "stunned"        # Оглушение (пропуск хода)
STATUS_SLOWED = "slowed"          # Замедление (меньше урон и защита)
STATUS_ENRAGED = "enraged"        # Ярость (больше урон, меньше защита)
STATUS_PROTECTED = "protected"    # Защита (меньше входящего урона)
STATUS_WEAKENED = "weakened"      # Ослабление (меньше урон)

STATUS_EFFECTS = {
    STATUS_BURN: {"name": "Горение", "damage_percent": 0.05, "duration": 3, "color": "#FF4500"},
    STATUS_FREEZE: {"name": "Заморозка", "skip_turn": True, "duration": 1, "color": "#00BFFF"},
    STATUS_POISONED: {"name": "Отравление", "damage_percent": 0.10, "duration": 3, "color": "#32CD32"},
    STATUS_STUNNED: {"name": "Оглушение", "skip_turn": True, "duration": 1, "color": "#FFD700"},
    STATUS_SLOWED: {"name": "Замедление", "damage_mult": 0.7, "defense_mult": 0.7, "duration": 2, "color": "#808080"},
    STATUS_ENRAGED: {"name": "Ярость", "damage_mult": 1.5, "defense_mult": 0.8, "duration": 2, "color": "#DC143C"},
    STATUS_PROTECTED: {"name": "Защита", "damage_reduction": 0.5, "duration": 2, "color": "#4169E1"},
    STATUS_WEAKENED: {"name": "Ослабление", "damage_mult": 0.6, "duration": 2, "color": "#8B4513"},
}

# ============================================================================
# 6. БОЕВЫЕ ФОРМАЦИИ
# ============================================================================

FORMATION_FRONT = "front"      # Фронт (получает первый удар)
FORMATION_FLANK_LEFT = "flank_left"   # Левый фланг
FORMATION_FLANK_RIGHT = "flank_right" # Правый фланг
FORMATION_BACK = "back"        # Тыл (защищен от прямых атак)

FORMATION_BONUSES = {
    FORMATION_FRONT: {"defense_bonus": 0.2, "attack_penalty": 0.0, "description": "+20% защиты"},
    FORMATION_FLANK_LEFT: {"defense_bonus": 0.0, "attack_bonus": 0.1, "description": "+10% атаки"},
    FORMATION_FLANK_RIGHT: {"defense_bonus": 0.0, "attack_bonus": 0.1, "description": "+10% атаки"},
    FORMATION_BACK: {"defense_bonus": 0.3, "attack_penalty": -0.2, "description": "+30% защиты, -20% атаки"},
}

# ============================================================================
# 7. ФУНКЦИИ ДЛЯ ОБНОВЛЕНИЯ БАЗЫ ДАННЫХ
# ============================================================================

def add_new_unit_types_to_db(db_path: str):
    """Добавляет новые типы войск в базу данных"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Получаем все существующие юниты
    cursor.execute("SELECT unit_name, unit_type FROM units")
    existing_units = cursor.fetchall()
    
    # Распределяем юниты по новым типам (если у них нет типа или он старый)
    updates = []
    for unit_name, current_type in existing_units:
        new_type = current_type
        
        # Если тип не установлен или требует обновления
        if not current_type or current_type == UNIT_TYPE_INFANTRY:
            # Распределяем на основе названия или других характеристик
            name_lower = unit_name.lower()
            
            if any(word in name_lower for word in ['дракон', 'dragon', 'змей']):
                new_type = UNIT_TYPE_DRAGON
            elif any(word in name_lower for word in ['маг', 'mage', 'волшеб', 'wizard']):
                new_type = UNIT_TYPE_MAGE
            elif any(word in name_lower for word in ['убийц', 'assassin', 'вор', 'rogue']):
                new_type = UNIT_TYPE_ASSASSIN
            elif any(word in name_lower for word in ['целит', 'healer', 'жриц', 'priest']):
                new_type = UNIT_TYPE_HEALER
            elif any(word in name_lower for word in ['рыцар', 'knight', 'кавалер', 'cavalry', 'конн']):
                new_type = UNIT_TYPE_CAVALRY
            elif any(word in name_lower for word in ['осад', 'siege', 'катапульт', 'баллист']):
                new_type = UNIT_TYPE_SIEGE
            elif any(word in name_lower for word in ['лучн', 'archer', 'стрел', 'bow']):
                new_type = UNIT_TYPE_ARCHER
            else:
                new_type = UNIT_TYPE_INFANTRY
        
        if new_type != current_type:
            updates.append((new_type, unit_name))
    
    # Применяем обновления
    if updates:
        cursor.executemany("UPDATE units SET unit_type = ? WHERE unit_name = ?", updates)
        conn.commit()
        print(f"Обновлено {len(updates)} юнитов с новыми типами войск")
    
    conn.close()


def add_element_column_to_db(db_path: str):
    """Добавляет колонку элемента в таблицу units"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Проверяем, существует ли колонка
        cursor.execute("PRAGMA table_info(units)")
        columns = [col[1] for col in cursor.fetchall()]
        
        if 'element' not in columns:
            cursor.execute("ALTER TABLE units ADD COLUMN element TEXT DEFAULT NULL")
            conn.commit()
            print("Добавлена колонка 'element' в таблицу units")
        else:
            print("Колонка 'element' уже существует")
    except Exception as e:
        print(f"Ошибка при добавлении колонки element: {e}")
    finally:
        conn.close()


def add_abilities_column_to_db(db_path: str):
    """Добавляет колонку способностей в таблицу units"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Проверяем, существует ли колонка
        cursor.execute("PRAGMA table_info(units)")
        columns = [col[1] for col in cursor.fetchall()]
        
        if 'abilities' not in columns:
            cursor.execute("ALTER TABLE units ADD COLUMN abilities TEXT DEFAULT NULL")
            conn.commit()
            print("Добавлена колонка 'abilities' в таблицу units")
        else:
            print("Колонка 'abilities' уже существует")
    except Exception as e:
        print(f"Ошибка при добавлении колонки abilities: {e}")
    finally:
        conn.close()


def assign_elements_to_units(db_path: str):
    """Назначает элементы юнитам на основе их фракции и типа"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Mapping фракций к элементам
    faction_elements = {
        'Север': ELEMENT_EARTH,
        'Эльфы': ELEMENT_AIR,
        'Вампиры': ELEMENT_DARK,
        # Добавьте другие фракции
    }
    
    # Mapping типов войск к элементам
    type_elements = {
        UNIT_TYPE_DRAGON: ELEMENT_FIRE,
        UNIT_TYPE_HEALER: ELEMENT_LIGHT,
        UNIT_TYPE_MAGE: ELEMENT_AIR,
    }
    
    updates = []
    cursor.execute("SELECT id, faction, unit_type, element FROM units")
    for unit_id, faction, unit_type, current_element in cursor.fetchall():
        new_element = current_element
        
        # Приоритет: тип войска > фракция
        if unit_type in type_elements:
            new_element = type_elements[unit_type]
        elif faction in faction_elements and not current_element:
            new_element = faction_elements[faction]
        
        if new_element != current_element:
            updates.append((new_element, unit_id))
    
    if updates:
        cursor.executemany("UPDATE units SET element = ? WHERE id = ?", updates)
        conn.commit()
        print(f"Назначены элементы для {len(updates)} юнитов")
    
    conn.close()


def assign_abilities_to_units(db_path: str):
    """Назначает способности юнитам на основе их класса и типа"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Способности по классам
    class_abilities = {
        '1': [ABILITY_COUNTER_ATTACK],  # Базовые юниты
        '2': [ABILITY_CRITICAL_HIT, ABILITY_DODGE],  # Герои 2 класса
        '3': [ABILITY_CRITICAL_HIT, ABILITY_VAMPIRISM, ABILITY_FIRST_STRIKE],  # Герои 3 класса
        '4': [ABILITY_CRITICAL_HIT, ABILITY_DOUBLE_ATTACK, ABILITY_AREA_DAMAGE, 
              ABILITY_REGENERATION, ABILITY_BERSERK],  # Легендарные
    }
    
    # Дополнительные способности по типам
    type_abilities = {
        UNIT_TYPE_ASSASSIN: [ABILITY_CRITICAL_HIT, ABILITY_FIRST_STRIKE, ABILITY_DODGE],
        UNIT_TYPE_DRAGON: [ABILITY_AREA_DAMAGE, ABILITY_FLYING, ABILITY_BERSERK],
        UNIT_TYPE_HEALER: [ABILITY_HEAL_ALLY, ABILITY_REGENERATION, ABILITY_PROTECTED],
        UNIT_TYPE_MAGE: [ABILITY_AREA_DAMAGE, ABILITY_STUN, ABILITY_POISON],
        UNIT_TYPE_CAVALRY: [ABILITY_FIRST_STRIKE, ABILITY_COUNTER_ATTACK],
        UNIT_TYPE_ARCHER: [ABILITY_FIRST_STRIKE, ABILITY_DODGE],
    }
    
    updates = []
    cursor.execute("SELECT id, unit_class, unit_type, abilities FROM units")
    for unit_id, unit_class, unit_type, current_abilities in cursor.fetchall():
        abilities = set()
        
        # Добавляем способности по классу
        if unit_class in class_abilities:
            abilities.update(class_abilities[unit_class])
        
        # Добавляем способности по типу
        if unit_type in type_abilities:
            # Выбираем 1-2 случайные способности из доступных
            available = type_abilities[unit_type]
            selected = random.sample(available, min(len(available), 2))
            abilities.update(selected)
        
        if abilities:
            abilities_str = ",".join(sorted(abilities))
            if abilities_str != current_abilities:
                updates.append((abilities_str, unit_id))
    
    if updates:
        cursor.executemany("UPDATE units SET abilities = ? WHERE id = ?", updates)
        conn.commit()
        print(f"Назначены способности для {len(updates)} юнитов")
    
    conn.close()


# ============================================================================
# 8. УЛУЧШЕННЫЕ ФУНКЦИИ РАСЧЕТА БОЯ
# ============================================================================

def get_type_effectiveness_enhanced(attacker_type: str, defender_type: str) -> float:
    """Получает множитель урона с учетом улучшенной матрицы"""
    if attacker_type in ENHANCED_TYPE_EFFECTIVENESS:
        return ENHANCED_TYPE_EFFECTIVENESS[attacker_type].get(defender_type, 1.0)
    return 1.0


def get_element_effectiveness(attacker_element: Optional[str], 
                               defender_element: Optional[str]) -> float:
    """Получает множитель урона от взаимодействия элементов"""
    if not attacker_element:
        attacker_element = ELEMENT_NONE
    if not defender_element:
        defender_element = ELEMENT_NONE
    
    if attacker_element in ELEMENT_EFFECTIVENESS:
        return ELEMENT_EFFECTIVENESS[attacker_element].get(defender_element, 1.0)
    return 1.0


def calculate_ability_modifier(attacker_abilities: List[str], 
                                defender_abilities: List[str],
                                context: Dict) -> Dict:
    """
    Рассчитывает модификаторы от способностей
    
    Args:
        attacker_abilities: Список способностей атакующего
        defender_abilities: Список способностей защитника
        context: Контекст боя (health_percent, is_first_turn, etc.)
    
    Returns:
        Dict с модификаторами: damage_mult, defense_mult, heal_amount, etc.
    """
    modifiers = {
        'damage_mult': 1.0,
        'defense_mult': 1.0,
        'crit_chance': 0.0,
        'dodge_chance': 0.0,
        'heal_amount': 0,
        'extra_attacks': 0,
        'status_effects': [],
    }
    
    # Обработка способностей атакующего
    for ability in attacker_abilities:
        if ability == ABILITY_CRITICAL_HIT:
            modifiers['crit_chance'] += ABILITY_DESCRIPTIONS[ability]['chance']
        elif ability == ABILITY_DOUBLE_ATTACK:
            modifiers['extra_attacks'] += 1
        elif ability == ABILITY_ARMOR_PIERCE:
            modifiers['armor_penetration'] = 0.5
        elif ability == ABILITY_BERSERK and context.get('health_percent', 100) < 30:
            modifiers['damage_mult'] *= 1.5
        elif ability == ABILITY_POISON:
            modifiers['status_effects'].append(STATUS_POISONED)
        elif ability == ABILITY_STUN:
            if random.random() < ABILITY_DESCRIPTIONS[ability]['chance']:
                modifiers['status_effects'].append(STATUS_STUNNED)
    
    # Обработка способностей защитника
    for ability in defender_abilities:
        if ability == ABILITY_DODGE:
            modifiers['dodge_chance'] += ABILITY_DESCRIPTIONS[ability]['chance']
        elif ability == ABILITY_GUARDIAN:
            modifiers['defense_mult'] *= 1.25
        elif ability == ABILITY_COUNTER_ATTACK and context.get('is_defending', False):
            modifiers['counter_attack'] = True
    
    return modifiers


def apply_status_effects(unit_stats: Dict, active_statuses: List[Dict]) -> Dict:
    """
    Применяет активные статусные эффекты к характеристикам юнита
    
    Args:
        unit_stats: Текущие характеристики юнита
        active_statuses: Список активных статусных эффектов
    
    Returns:
        Обновленные характеристики
    """
    modified_stats = unit_stats.copy()
    
    for status in active_statuses:
        status_type = status['type']
        effect_data = STATUS_EFFECTS.get(status_type, {})
        
        if 'damage_mult' in effect_data:
            current_dmg = modified_stats.get('attack', 0)
            modified_stats['attack'] = int(current_dmg * effect_data['damage_mult'])
        
        if 'defense_mult' in effect_data:
            current_def = modified_stats.get('defense', 0)
            modified_stats['defense'] = int(current_def * effect_data['defense_mult'])
        
        if 'damage_reduction' in effect_data:
            modified_stats['damage_reduction'] = effect_data['damage_reduction']
    
    return modified_stats


# ============================================================================
# 9. ГЛАВНАЯ ФУНКЦИЯ ИНИЦИАЛИЗАЦИИ УЛУЧШЕНИЙ
# ============================================================================

def initialize_battle_enhancements(db_path: str):
    """
    Инициализирует все улучшения боевой системы
    
    Args:
        db_path: Путь к файлу базы данных
    """
    print("=" * 60)
    print("Инициализация улучшений боевой системы")
    print("=" * 60)
    
    # 1. Добавляем новые колонки
    print("\n1. Добавление новых колонок...")
    add_element_column_to_db(db_path)
    add_abilities_column_to_db(db_path)
    
    # 2. Обновляем типы войск
    print("\n2. Обновление типов войск...")
    add_new_unit_types_to_db(db_path)
    
    # 3. Назначаем элементы
    print("\n3. Назначение элементов юнитам...")
    assign_elements_to_units(db_path)
    
    # 4. Назначаем способности
    print("\n4. Назначение способностей юнитам...")
    assign_abilities_to_units(db_path)
    
    print("\n" + "=" * 60)
    print("Инициализация завершена!")
    print("=" * 60)


# ============================================================================
# ПРИМЕР ИСПОЛЬЗОВАНИЯ
# ============================================================================

if __name__ == "__main__":
    # Пример использования
    DB_PATH = "game_data.db"
    
    # Инициализировать улучшения
    initialize_battle_enhancements(DB_PATH)
    
    # Пример расчета эффективности
    print("\nПример расчета эффективности:")
    print(f"Кавалерия vs Стрелки: x{get_type_effectiveness_enhanced(UNIT_TYPE_CAVALRY, UNIT_TYPE_ARCHER)}")
    print(f"Огонь vs Вода: x{get_element_effectiveness(ELEMENT_FIRE, ELEMENT_WATER)}")
    
    # Пример способностей
    print("\nПримеры способностей:")
    for ability, data in list(ABILITY_DESCRIPTIONS.items())[:5]:
        print(f"- {data['name']}: {data['desc']}")
