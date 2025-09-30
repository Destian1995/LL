# seasons.py

import sqlite3
from db_lerdon_connect import db_path

class SeasonManager:
    """
    Менеджер сезонов, теперь с учётом фракций и таблицей effects_seasons.

    При первом вызове update(new_idx) просто накладывается эффект для сезона new_idx.
    При смене с last_idx на new_idx:
      1. Откатываем всё, что накладывалось для last_idx (_revert_season).
      2. Накладываем эффект для new_idx (_apply_season).
      3. Сохраняем last_idx = new_idx.

    Если new_idx == last_idx, ничего не делаем.
    """

    # Для удобства: названия сезонов (индексы 0–3)
    SEASON_NAMES = ['Зима', 'Весна', 'Лето', 'Осень']

    # Для каждого сезона (по индексу) храним словарь:
    #   ключ = название фракции,
    #   значение = { 'stat': коэффициент для attack/defense, 'cost': коэффициент для cost_money/cost_time }
    FACTION_EFFECTS = [
        # 0 = Зима
        {
            'Люди':  {'stat': 1.25,  'cost': 0.65},   # +25% атак/защита, -35% стоимости
            'Эльфы': {'stat': 0.65,  'cost': 1.25},   # -35% атак/защита, +25% стоимости
            'Вампиры': {'stat': 0.97,  'cost': 1.00},   # -3% атак/защита, нет эффекта стоимости
            'Адепты':   {'stat': 0.90,  'cost': 1.17},   # -10% атак/защита, +17% стоимости
            'Элины':  {'stat': 0.45,  'cost': 1.45},   # -55% атак/защита, +45% стоимости
        },
        # 1 = Весна
        {
            'Люди':  {'stat': 0.90,  'cost': 1.17},   # -10% атак/защита, +17% стоимости
            'Эльфы': {'stat': 0.97,  'cost': 1.00},   # -3% атак/защита, нет эффекта стоимости
            'Вампиры': {'stat': 1.25,  'cost': 0.65},   # +25% атак/защита, -35% стоимости
            'Адепты':   {'stat': 0.65,  'cost': 1.25},   # -35% атак/защита, +25% стоимости
            'Элины':  {'stat': 0.99,  'cost': 0.90},   # -1% атак/защита, -10% стоимости
        },
        # 2 = Лето
        {
            'Люди':  {'stat': 0.65,  'cost': 1.25},   # -35% атак/защита, +25% стоимости
            'Эльфы': {'stat': 1.25,  'cost': 0.65},   # +25% атак/защита, -35% стоимости
            'Вампиры': {'stat': 0.90,  'cost': 1.17},   # -10% атак/защита, +17% стоимости
            'Адепты':   {'stat': 0.97,  'cost': 1.00},   # -3% атак/защита, нет эффекта стоимости
            'Элины':  {'stat': 1.70,  'cost': 0.60},   # +70% атак/защита, -40% стоимости
        },
        # 3 = Осень
        {
            'Люди':  {'stat': 0.97,  'cost': 1.00},   # -3% атак/защита, нет эффекта стоимости
            'Эльфы': {'stat': 0.90,  'cost': 1.17},   # -10% атак/защита, +17% стоимости
            'Вампиры': {'stat': 0.65,  'cost': 1.25},   # -35% атак/защита, +25% стоимости
            'Адепты':   {'stat': 1.25,  'cost': 0.65},   # +25% атак/защита, -35% стоимости
            'Элины':  {'stat': 0.90,  'cost': 1.17},   # -10% атак/защита, +17% стоимости
        },
    ]

    # Сопоставление полей артефактов с полями юнитов
    ARTIFACT_STAT_MAPPING = {
        'attack': 'attack',
        'defense': 'defense',
        'health': 'durability',
    }

    def __init__(self):
        # last_idx = индекс сезона, бафф которого уже наложен.
        # None означает, что до этого ни один сезон не применялся.
        self.last_idx = None

    def initialize_season_effects(self, conn):
        """
        Инициализирует таблицу effects_seasons при старте игры.
        Рассчитывает бонусы для каждого юнита по каждому сезону.
        """
        cur = conn.cursor()

        # Очищаем таблицу
        cur.execute("DELETE FROM effects_seasons")

        # Получаем все юниты и их базовые характеристики
        cur.execute("""
            SELECT unit_name, faction, attack, defense, cost_money, cost_time
            FROM units_default
        """)

        units = cur.fetchall()

        for unit in units:
            unit_name, faction, base_attack, base_defense, base_cost_money, base_cost_time = unit

            # Для каждого сезона рассчитываем бонусы
            for season_idx in range(4):  # 0-3 сезоны
                faction_effects = self.FACTION_EFFECTS[season_idx]

                if faction in faction_effects:
                    effects = faction_effects[faction]
                    stat_f = effects['stat']
                    cost_f = effects['cost']

                    # Рассчитываем бонусы (новое значение - базовое значение)
                    attack_bonus = int(round(base_attack * stat_f)) - base_attack
                    defense_bonus = int(round(base_defense * stat_f)) - base_defense
                    cost_money_bonus = int(round(base_cost_money * cost_f)) - base_cost_money
                    cost_time_bonus = int(round(base_cost_time * cost_f)) - base_cost_time

                    # Вставляем в таблицу
                    cur.execute("""
                        INSERT INTO effects_seasons 
                        (unit_name, season, attack_bonus, defense_bonus, cost_money_bonus, cost_time_bonus)
                        VALUES (?, ?, ?, ?, ?, ?)
                    """, (unit_name, season_idx, attack_bonus, defense_bonus, cost_money_bonus, cost_time_bonus))

        conn.commit()
        print("[SEASON] Таблица effects_seasons инициализирована")

    def update(self, new_idx: int, conn):
        """
        Вызывается при смене сезона на new_idx (0–3).
        Если last_idx != new_idx, то:
          1) Если last_idx не None, откатываем _revert_season(last_idx).
          2) Накладываем _apply_season(new_idx).
          3) Сохраняем last_idx = new_idx.
        Если new_idx == last_idx, ничего не делаем.
        """
        # Проверяем, инициализирована ли таблица effects_seasons
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM effects_seasons")
        count = cur.fetchone()[0]

        if count == 0:
            self.initialize_season_effects(conn)

        if self.last_idx is None:
            # Первый раз — просто накладываем
            self._apply_season(new_idx, conn)
            self.last_idx = new_idx
        elif new_idx != self.last_idx:
            # Сначала откатить предыдущий сезон
            self._revert_season(self.last_idx, conn)
            # Потом применить новый
            self._apply_season(new_idx, conn)
            self.last_idx = new_idx
        # Если new_idx == last_idx, остаёмся как есть
        self.apply_artifact_bonuses(conn)

    def _apply_season(self, idx: int, conn):
        """
        Накладывает все эффекты сезона idx на таблицу units,
        беря бонусы из таблицы effects_seasons.
        """
        cur = conn.cursor()

        # Получаем бонусы для данного сезона
        cur.execute("""
            SELECT unit_name, attack_bonus, defense_bonus, cost_money_bonus, cost_time_bonus
            FROM effects_seasons
            WHERE season = ?
        """, (idx,))

        effects = cur.fetchall()

        for effect in effects:
            unit_name, attack_bonus, defense_bonus, cost_money_bonus, cost_time_bonus = effect

            # Применяем бонусы
            cur.execute("""
                UPDATE units
                SET
                    attack = attack + ?,
                    defense = defense + ?,
                    cost_money = cost_money + ?,
                    cost_time = cost_time + ?
                WHERE unit_name = ?
            """, (attack_bonus, defense_bonus, cost_money_bonus, cost_time_bonus, unit_name))

        conn.commit()

    def _revert_season(self, idx: int, conn):
        """
        Откатывает эффекты сезона idx, вычитая бонусы из таблицы effects_seasons.
        """
        cur = conn.cursor()

        # Получаем бонусы для данного сезона
        cur.execute("""
            SELECT unit_name, attack_bonus, defense_bonus, cost_money_bonus, cost_time_bonus
            FROM effects_seasons
            WHERE season = ?
        """, (idx,))

        effects = cur.fetchall()

        for effect in effects:
            unit_name, attack_bonus, defense_bonus, cost_money_bonus, cost_time_bonus = effect

            # Откатываем бонусы (вычитаем)
            cur.execute("""
                UPDATE units
                SET
                    attack = attack - ?,
                    defense = defense - ?,
                    cost_money = cost_money - ?,
                    cost_time = cost_time - ?
                WHERE unit_name = ?
            """, (attack_bonus, defense_bonus, cost_money_bonus, cost_time_bonus, unit_name))

        conn.commit()

    def apply_artifact_bonuses(self, conn):
        """
        Применяет бонусы от артефактов, если они экипированы и сезон совпадает.
        Управляет эффектами через artifact_effects_log.
        Обрабатывает артефакты из hero_equipment (игрок) и ai_hero_equipment (ИИ).
        """
        if self.last_idx is None:
            print("[ARTIFACT] Season not set, skipping artifact application.")
            return

        cur = conn.cursor()
        current_season = self.SEASON_NAMES[self.last_idx]

        # 1. Получаем список всех экипированных артефактов из ОБОИХ таблиц
        # Для hero_equipment (игрок)
        cur.execute("""
            SELECT hero_name, artifact_id FROM hero_equipment
            WHERE artifact_id IS NOT NULL
        """)
        player_equipped_artifacts = cur.fetchall()

        # Для ai_hero_equipment (ИИ)
        cur.execute("""
            SELECT hero_name, artifact_id FROM ai_hero_equipment
            WHERE artifact_id IS NOT NULL
        """)
        ai_equipped_artifacts = cur.fetchall()

        # Объединяем списки
        all_equipped_artifacts = player_equipped_artifacts + ai_equipped_artifacts

        # 2. Получаем список уже примененных эффектов
        cur.execute("""
            SELECT hero_name, artifact_id FROM artifact_effects_log
            GROUP BY hero_name, artifact_id
        """)
        applied_effects = set(cur.fetchall())  # Множество (hero_name, artifact_id)

        # 3. Определяем, что нужно сделать
        # Артефакты, которые должны быть активны
        should_be_active = set()
        # Артефакты, которые нужно проверить/применить
        to_check_apply = set()

        for hero_name, artifact_id in all_equipped_artifacts:
            should_be_active.add((hero_name, artifact_id))
            if (hero_name, artifact_id) not in applied_effects:
                # Новый артефакт, нужна проверка и возможное применение
                to_check_apply.add((hero_name, artifact_id))

        # Артефакты, которые нужно отменить (были применены, но больше не экипированы или не подходят по сезону)
        to_revert = applied_effects - should_be_active

        # 4. Отменяем ненужные эффекты
        for hero_name, artifact_id in to_revert:
            self._revert_artifact_effect(hero_name, artifact_id, conn)

        # 5. Проверяем и применяем новые/измененные эффекты
        for hero_name, artifact_id in to_check_apply:
            # Получаем данные артефакта
            cur.execute("""
                SELECT attack, defense, season_name
                FROM artifacts
                WHERE id = ?
            """, (artifact_id,))
            artifact = cur.fetchone()

            if not artifact:
                continue

            (a_atk, a_def, a_season_name) = artifact

            # Проверяем сезон
            season_ok = True
            if a_season_name is not None:
                allowed_seasons = [s.strip() for s in a_season_name.split(',')]
                if current_season not in allowed_seasons:
                    season_ok = False

            if season_ok:
                # Применяем бонусы
                bonuses = {
                    'attack': a_atk,
                    'defense': a_def
                }
                self._apply_artifact_effect(hero_name, artifact_id, bonuses, conn)
            else:
                pass  # Уже обработано в to_revert

        # 6. Проверяем существующие эффекты на соответствие сезону
        # (на случай, если сезон сменился, а артефакт остался тот же)
        # Получаем все примененные эффекты с их артефактами
        cur.execute("""
            SELECT DISTINCT ael.hero_name, ael.artifact_id, a.season_name
            FROM artifact_effects_log ael
            JOIN artifacts a ON ael.artifact_id = a.id
        """)
        active_artifact_details = cur.fetchall()

        for hero_name, artifact_id, a_season_name in active_artifact_details:
            season_ok = True
            if a_season_name is not None:
                allowed_seasons = [s.strip() for s in a_season_name.split(',')]
                if current_season not in allowed_seasons:
                    season_ok = False

            if not season_ok:
                self._revert_artifact_effect(hero_name, artifact_id, conn)
                # Этот артефакт теперь нужно проверить заново, если он все еще экипирован
                if (hero_name, artifact_id) in should_be_active:
                    to_check_apply.add((hero_name, artifact_id))

    def _calculate_stat_change(self, base_value, bonus_percent):
        """Рассчитывает абсолютное изменение характеристики."""
        if bonus_percent == 0 or bonus_percent is None:
            return 0
        change = int(round(base_value * (bonus_percent / 100)))
        return change

    def _apply_artifact_effect(self, hero_name: str, artifact_id: int, bonuses: dict, conn):
        """
        Рассчитывает и применяет эффект артефакта к герою.
        Записывает эффект в artifact_effects_log.
        """
        cur = conn.cursor()

        # Получаем БАЗОВЫЕ значения из units_default
        cur.execute("""
            SELECT attack, defense
            FROM units_default WHERE unit_name = ?
        """, (hero_name,))
        base = cur.fetchone()

        if not base:
            print(f"[ARTIFACT] Hero {hero_name} not found in units_default")
            return

        (b_atk, b_def) = base


        effects_to_apply = []

        # Рассчитываем изменения для каждой характеристики
        for artifact_stat, unit_stat in self.ARTIFACT_STAT_MAPPING.items():
            bonus_value = bonuses.get(artifact_stat)
            if bonus_value is None or bonus_value == 0:
                continue

            base_val = None
            if unit_stat == 'attack':
                base_val = b_atk
            elif unit_stat == 'defense':
                base_val = b_def

            if base_val is not None:
                change = self._calculate_stat_change(base_val, bonus_value)
                if change != 0:  # Только если есть изменение
                    effects_to_apply.append((unit_stat, change))

        if not effects_to_apply:
            print(f"[ARTIFACT] No applicable effects for {hero_name} from artifact {artifact_id}")
            return

        # Применяем изменения к units и записываем в лог
        for stat_name, change in effects_to_apply:
            # Обновляем характеристику в units
            cur.execute(f"""
                UPDATE units
                SET {stat_name} = {stat_name} + ?
                WHERE unit_name = ?
            """, (change, hero_name))

            # Записываем эффект в лог
            cur.execute("""
                INSERT OR REPLACE INTO artifact_effects_log 
                (hero_name, artifact_id, stat_name, value_change)
                VALUES (?, ?, ?, ?)
            """, (hero_name, artifact_id, stat_name, change))

        conn.commit()


    def _revert_artifact_effect(self, hero_name: str, artifact_id: int, conn):
        """
        Отменяет эффект артефакта для героя.
        Вычитает изменения из units и удаляет запись из artifact_effects_log.
        """
        cur = conn.cursor()

        # Получаем все эффекты этого артефакта на этого героя
        cur.execute("""
            SELECT stat_name, value_change
            FROM artifact_effects_log
            WHERE hero_name = ? AND artifact_id = ?
        """, (hero_name, artifact_id))

        effects = cur.fetchall()

        if not effects:
            print(f"[ARTIFACT] No effects found to revert for artifact {artifact_id} on hero {hero_name}")
            return

        # Отменяем каждый эффект
        for stat_name, value_change in effects:
            # Вычитаем изменение из характеристики в units
            cur.execute(f"""
                UPDATE units
                SET {stat_name} = {stat_name} - ?
                WHERE unit_name = ?
            """, (value_change, hero_name))


        # Удаляем записи об эффектах из лога
        cur.execute("""
            DELETE FROM artifact_effects_log
            WHERE hero_name = ? AND artifact_id = ?
        """, (hero_name, artifact_id))

        conn.commit()

    def reset_absent_third_class_units(self, conn):
        """
        Проверяет каждый юнит 3 класса в таблице units. Если юнит 3 класса отсутствует в garrisons,
        сбрасывает его характеристики к значениям из units_default с пересчетом на эффект текущего сезона.
        """
        try:
            cursor = conn.cursor()

            # Получаем все юниты 3 класса из таблицы units
            cursor.execute("""
                SELECT unit_name, faction 
                FROM units 
                WHERE unit_class = 3
            """)

            third_class_units = cursor.fetchall()

            if not third_class_units:
                print("[INFO] Нет юнитов 3 класса в таблице units.")
                return

            reset_count = 0

            for unit_name, faction in third_class_units:
                # Проверяем, есть ли этот юнит в garrisons
                cursor.execute("""
                    SELECT COUNT(*) 
                    FROM garrisons 
                    WHERE unit_name = ?
                """, (unit_name,))

                count_in_garrisons = cursor.fetchone()[0]

                # Если юнит отсутствует в garrisons, сбрасываем его характеристики
                if count_in_garrisons == 0:
                    print(
                        f"[INFO] Юнит '{unit_name}' (фракция '{faction}') отсутствует в garrisons. Сброс характеристик...")

                    # Сбрасываем характеристики к значениям по умолчанию
                    cursor.execute("""
                        UPDATE units 
                        SET 
                            attack = (SELECT attack FROM units_default WHERE units_default.unit_name = units.unit_name),
                            defense = (SELECT defense FROM units_default WHERE units_default.unit_name = units.unit_name),
                            durability = (SELECT durability FROM units_default WHERE units_default.unit_name = units.unit_name),
                            cost_money = (SELECT cost_money FROM units_default WHERE units_default.unit_name = units.unit_name),
                            cost_time = (SELECT cost_time FROM units_default WHERE units_default.unit_name = units.unit_name)
                        WHERE unit_name = ?
                    """, (unit_name,))

                    # Если сезон установлен, применяем сезонные эффекты
                    if self.last_idx is not None:
                        # Получаем бонусы для текущего сезона
                        cursor.execute("""
                            SELECT attack_bonus, defense_bonus, cost_money_bonus, cost_time_bonus
                            FROM effects_seasons
                            WHERE unit_name = ? AND season = ?
                        """, (unit_name, self.last_idx))

                        season_effect = cursor.fetchone()

                        if season_effect:
                            attack_bonus, defense_bonus, cost_money_bonus, cost_time_bonus = season_effect

                            # Применяем бонусы
                            cursor.execute("""
                                UPDATE units
                                SET
                                    attack = attack + ?,
                                    defense = defense + ?,
                                    cost_money = cost_money + ?,
                                    cost_time = cost_time + ?
                                WHERE unit_name = ?
                            """, (attack_bonus, defense_bonus, cost_money_bonus, cost_time_bonus, unit_name))

                            print(
                                f"[SUCCESS] Сезонные бонусы применены к юниту '{unit_name}' для сезона {self.SEASON_NAMES[self.last_idx]}.")

                    reset_count += 1
                    print(f"[SUCCESS] Характеристики юнита '{unit_name}' сброшены и пересчитаны.")

            if reset_count > 0:
                conn.commit()
                print(f"[INFO] Сброшены характеристики {reset_count} юнитов 3 класса.")
            else:
                print("[INFO] Все юниты 3 класса присутствуют в garrisons. Сброс не требуется.")

            return reset_count

        except sqlite3.Error as e:
            print(f"[ERROR] Ошибка базы данных при сбросе характеристик юнитов 3 класса: {e}")
            try:
                conn.rollback()
            except:
                pass
            return 0
        except Exception as e:
            print(f"[ERROR] Неожиданная ошибка при сбросе характеристик юнитов 3 класса: {e}")
            import traceback
            traceback.print_exc()
            try:
                conn.rollback()
            except:
                pass
            return 0