from db_lerdon_connect import *


def merge_units(army):
    """
    Объединяет юниты одного типа в одну группу.
    :param army: Список юнитов (атакующих или обороняющихся).
    :return: Объединенный список юнитов.
    """
    merged_army = {}
    for unit in army:
        unit_name = unit['unit_name']
        if unit_name not in merged_army:
            merged_army[unit_name] = {
                "unit_name": unit['unit_name'],
                "unit_count": unit['unit_count'],
                "unit_image": unit.get('unit_image', ''),
                "units_stats": unit['units_stats']
            }
        else:
            merged_army[unit_name]['unit_count'] += unit['unit_count']
    return list(merged_army.values())


def update_results_table(db_connection, faction, units_destroyed, enemy_losses):
    """
    Обновляет или создает запись в таблице results для указанной фракции.

    :param db_connection: Соединение с базой данных.
    :param faction: Название фракции.
    :param units_destroyed: Общие потери фракции после боя.
    :param enemy_losses: Потери противника (количество уничтоженных юнитов).
    """
    try:
        with db_connection:  # BEGIN + commit() / rollback() автоматически
            cursor = db_connection.cursor()
            # Применяем abs() чтобы избежать отрицательных значений
            units_destroyed = abs(units_destroyed)
            enemy_losses = abs(enemy_losses)

            # Проверяем, существует ли уже запись для этой фракции
            cursor.execute("SELECT COUNT(*) FROM results WHERE faction = ?", (faction,))
            exists = cursor.fetchone()[0]

            if exists > 0:
                # Обновляем существующую запись
                cursor.execute("""
                    UPDATE results
                    SET 
                        Units_Destroyed = Units_Destroyed + ?,
                        Units_killed = Units_killed + ?
                    WHERE faction = ?
                """, ( units_destroyed, enemy_losses, faction))
            else:
                # Вставляем новую запись
                cursor.execute("""
                    INSERT INTO results (
                        Units_Destroyed, Units_killed, 
                        Army_Efficiency_Ratio, Average_Deal_Ratio, 
                        Average_Net_Profit_Coins, Average_Net_Profit_Raw, 
                        Economic_Efficiency, faction
                    )
                    VALUES (?, ?, ?, 0, 0, 0, 0, 0, ?)
                """, (units_destroyed, enemy_losses, faction))

    except sqlite3.IntegrityError as e:
        print(f"[ERROR] Ошибка целостности данных в results: {e}")
    except sqlite3.Error as e:
        print(f"[ERROR] Ошибка базы данных в update_results_table: {e}")
    except Exception as e:
        print(f"[ERROR] Неожиданная ошибка в update_results_table: {e}")

def generate_battle_report(attacking_army, defending_army, winner, attacking_fraction, defending_fraction, user_faction,
                           city):
    """
    Генерирует отчет о бое.
    :param attacking_army: Данные об атакующей армии (список словарей).
    :param defending_army: Данные об обороняющейся армии (список словарей).
    :param winner: Результат боя ('attacking' или 'defending').
    :param attacking_fraction: Название атакующей фракции.
    :param defending_fraction: Название обороняющейся фракции.
    :return: Отчет о бое (список словарей).
    """
    global attacking_result, defending_result
    report_data = []  # ← Теперь это список, а не словарь

    def process_army(army, side, result=None):
        for unit in army:
            initial_count = unit.get('initial_count', 0)
            final_count = unit['unit_count']
            losses = abs(initial_count - final_count)
            report_data.append({
                'unit_name': unit['unit_name'],
                'initial_count': initial_count,
                'final_count': final_count,
                'losses': losses,
                'side': side,
                'result': result,
                'city': city
            })

    # Определяем результат только для фракции игрока
    if user_faction:
        if winner == 'attacking' and attacking_fraction == user_faction:
            attacking_result = "Победа"
            defending_result = None
        elif winner == 'defending' and defending_fraction == user_faction:
            attacking_result = None
            defending_result = "Победа"
        else:
            # Игрок проиграл
            if attacking_fraction == user_faction:
                attacking_result = "Поражение"
                defending_result = None
            elif defending_fraction == user_faction:
                attacking_result = None
                defending_result = "Поражение"
    else:
        # Если игрок не участвует, результаты не нужны
        attacking_result = None
        defending_result = None

    # Обработка армий
    process_army(attacking_army, 'attacking', attacking_result)
    process_army(defending_army, 'defending', defending_result)

    return report_data


def show_battle_report(report_data, is_user_involved=False, user_faction=None, conn=None):
    """
    Отображает стильный и центрированный отчет о боe с использованием Kivy.
    Текст по центру окна статистики, заголовки строго друг под другом.
    :param report_data: Данные отчета о боe.
    :param is_user_involved: Участвовал ли пользователь в бою.
    :param user_faction: Фракция пользователя (если участвовал).
    :param conn: Соединение/контекст для обновления досье (если нужно).
    """
    if not report_data:
        print("Нет данных для отображения.")
        return

    # === Вспомогательная функция для центровки текста в Label ===
    def make_center_label(text, font_size_sp=14, markup=False, height_dp=None):
        lbl = Label(
            text=text,
            markup=markup,
            font_size=sp(font_size_sp),
            halign='center',
            valign='middle',
            size_hint_y=None,
        )
        # Если явно передали высоту — применим
        if height_dp is None:
            # приближённая высота, чтобы текст поместился
            lbl.height = dp(int(font_size_sp * 2.2))
        else:
            lbl.height = dp(height_dp)
        # Настроим text_size так, чтобы valign/halign работали корректно и обновлялись при изменении размера
        lbl.text_size = (lbl.width, lbl.height)
        lbl.bind(width=lambda inst, w: setattr(inst, 'text_size', (w, inst.height)))
        lbl.bind(height=lambda inst, h: setattr(inst, 'text_size', (inst.width, h)))
        return lbl

    # Определяем popup заранее (будет создан позже) чтобы binding кнопки работал корректно
    popup = None

    # === Внешняя якорная оболочка — центрирует всё окно отчета ===
    outer = AnchorLayout(anchor_x='center', anchor_y='center', size_hint=(1, 1))

    # Основной контент-бокс, он ограничит внутреннюю ширину/высоту и будет центрирован Outer
    content = BoxLayout(orientation='vertical', padding=dp(12), spacing=dp(12), size_hint=(0.95, 0.95))

    # Фон у контента
    with content.canvas.before:
        Color(0.12, 0.12, 0.18, 1)
        content.rect = Rectangle(size=content.size, pos=content.pos)
        content.bind(pos=lambda inst, value: setattr(inst.rect, 'pos', value),
                     size=lambda inst, value: setattr(inst.rect, 'size', value))

    # === Заголовок: результат (большой) и город (ниже) строго друг под другом ===
    header_layout = BoxLayout(orientation='vertical', size_hint_y=None, spacing=dp(6))
    header_layout.bind(minimum_height=header_layout.setter('height'))

    # Определяем текст результата и цвет
    result_text = ""
    result_color = "#FFFFFF"
    for item in report_data:
        if item.get("result"):
            result_text = item["result"].upper()
            result_color = "#33FF57" if result_text == "ПОБЕДА" else "#FF5733"
            break

    result_label = make_center_label(f"[b][color={result_color}]{result_text}[/color][/b]",
                                     font_size_sp=28, markup=True, height_dp=48)
    city_name = report_data[0].get('city', '—') if report_data else '—'
    city_label = make_center_label(f"[color=#FFD700]Город: {city_name}[/color]",
                                   font_size_sp=16, markup=True, height_dp=28)

    header_layout.add_widget(result_label)
    header_layout.add_widget(city_label)
    header_layout.height = result_label.height + city_label.height + header_layout.spacing

    content.add_widget(header_layout)

    # === Основная область со статистикой ===
    # Мы строим единую таблицу с 4 колонками:
    # [Атака: Юнит] [Атака: Потери|Осталось] [Оборона: Юнит] [Оборона: Потери|Осталось]
    scroll = ScrollView(size_hint=(1, 1))

    # Таблица строк: 4 колонки
    table = GridLayout(cols=4, spacing=dp(12), padding=[0, 0, 0, 0], size_hint_y=None)
    table.bind(minimum_height=table.setter('height'))

    # Отбираем единицы по сторонам
    attacking_units = [item for item in report_data if item.get('side') == 'attacking']
    defending_units = [item for item in report_data if item.get('side') == 'defending']

    # --- Заголовки сторон (делаем как первая строка, но "занимают" по 2 колонки визуально) ---
    # Для корректного позиционирования добавляем по 2 виджета на сторону (текст + пустышка),
    # чтобы ширины соответствовали колонкам таблицы.
    title_attack = Label(text=f"[b][color=#4CAF50]Атака[/color][/b]", markup=True,
                         halign='center', valign='middle', size_hint_y=None, height=dp(28))
    title_attack.text_size = (title_attack.width, title_attack.height)
    title_attack.bind(width=lambda inst, w: setattr(inst, 'text_size', (w, inst.height)))
    title_attack.bind(height=lambda inst, h: setattr(inst, 'text_size', (inst.width, h)))

    title_attack_spacer = Label(text="", size_hint_y=None, height=dp(28))

    title_def = Label(text=f"[b][color=#F44336]Оборона[/color][/b]", markup=True,
                      halign='center', valign='middle', size_hint_y=None, height=dp(28))
    title_def.text_size = (title_def.width, title_def.height)
    title_def.bind(width=lambda inst, w: setattr(inst, 'text_size', (w, inst.height)))
    title_def.bind(height=lambda inst, h: setattr(inst, 'text_size', (inst.width, h)))

    title_def_spacer = Label(text="", size_hint_y=None, height=dp(28))

    table.add_widget(title_attack)
    table.add_widget(title_attack_spacer)
    table.add_widget(title_def)
    table.add_widget(title_def_spacer)

    # --- Строка заголовков столбцов для каждой стороны ---
    hdr_attack_unit = make_center_label("[b]Юнит[/b]", font_size_sp=13, markup=True, height_dp=28)
    hdr_attack_status = make_center_label("[b]Потери | Осталось[/b]", font_size_sp=13, markup=True, height_dp=28)
    hdr_def_unit = make_center_label("[b]Юнит[/b]", font_size_sp=13, markup=True, height_dp=28)
    hdr_def_status = make_center_label("[b]Потери | Осталось[/b]", font_size_sp=13, markup=True, height_dp=28)

    table.add_widget(hdr_attack_unit)
    table.add_widget(hdr_attack_status)
    table.add_widget(hdr_def_unit)
    table.add_widget(hdr_def_status)

    # --- Построение параллельных строк (чтобы первая строка обеих сторон была на одном уровне) ---
    max_rows = max(len(attacking_units), len(defending_units))
    row_height = dp(32)

    for i in range(max_rows):
        # Левая сторона (атака)
        if i < len(attacking_units):
            u = attacking_units[i]
            unit_name = u.get('unit_name', '—')
            initial_count = u.get('initial_count', 0)
            final_count = u.get('final_count', 0)

            if initial_count == 1 and final_count == 1:
                status = "Выжил!"
            elif initial_count == 1 and final_count == 0:
                status = "Погиб..."
            else:
                status = f"{u.get('losses', 0)} | {final_count}"

            lbl_unit_left = make_center_label(f"[b]{unit_name}[/b]", font_size_sp=13, markup=True, height_dp=row_height)
            lbl_status_left = make_center_label(status, font_size_sp=13, height_dp=row_height)
        else:
            # пустые ячейки, чтобы выровнять строки
            lbl_unit_left = make_center_label("", font_size_sp=13, height_dp=row_height)
            lbl_status_left = make_center_label("", font_size_sp=13, height_dp=row_height)

        # Правая сторона (оборона)
        if i < len(defending_units):
            u = defending_units[i]
            unit_name = u.get('unit_name', '—')
            initial_count = u.get('initial_count', 0)
            final_count = u.get('final_count', 0)

            if initial_count == 1 and final_count == 1:
                status = "Выжил!"
            elif initial_count == 1 and final_count == 0:
                status = "Погиб..."
            else:
                status = f"{u.get('losses', 0)} | {final_count}"

            lbl_unit_right = make_center_label(f"[b]{unit_name}[/b]", font_size_sp=13, markup=True, height_dp=row_height)
            lbl_status_right = make_center_label(status, font_size_sp=13, height_dp=row_height)
        else:
            lbl_unit_right = make_center_label("", font_size_sp=13, height_dp=row_height)
            lbl_status_right = make_center_label("", font_size_sp=13, height_dp=row_height)

        # Добавляем 4 ячейки строки: левое имя, левый статус, правое имя, правый статус
        table.add_widget(lbl_unit_left)
        table.add_widget(lbl_status_left)
        table.add_widget(lbl_unit_right)
        table.add_widget(lbl_status_right)

    scroll.add_widget(table)
    content.add_widget(scroll)

    # Кнопка закрытия — по центру внизу
    btn_box = AnchorLayout(size_hint_y=None, height=dp(60), anchor_x='center', anchor_y='center')
    close_button = Button(
        text="Закрыть",
        size_hint=(0.4, None),
        height=dp(44),
        background_color=(0.2, 0.6, 1, 1),
        font_size=sp(16),
        color=(1, 1, 1, 1)
    )
    btn_box.add_widget(close_button)
    content.add_widget(btn_box)

    # Вставляем content в outer и создаем popup
    outer.add_widget(content)

    popup = Popup(
        title="",
        content=outer,
        size_hint=(0.95, 0.85),
        background_color=(0.1, 0.1, 0.15, 1)
    )

    # Привязываем закрытие popup к кнопке (popup уже создан)
    close_button.bind(on_release=lambda instance: popup.dismiss())

    # Обновление досье (если нужно)
    if is_user_involved and user_faction and report_data:
        is_victory = any(item.get('result') == "Победа" for item in report_data)
        try:
            # предполагается, что функция update_dossier_battle_stats определена где-то в коде
            update_dossier_battle_stats(conn, user_faction, is_victory)
        except Exception as e:
            print(f"[Ошибка] Не удалось обновить досье: {e}")

    popup.open()


def cleanup_equipment_after_battle(conn):
    """
    Очищает таблицы hero_equipment и ai_hero_equipment после боя.
    Удаляет записи о героях, которых больше нет в garrisons.
    """
    try:
        cursor = conn.cursor()
        print("[DEBUG] Начало очистки таблиц экипировки после боя...")

        # --- 1. Очистка hero_equipment ---
        print("[DEBUG] Проверка hero_equipment...")
        # Получаем всех уникальных героев из hero_equipment
        cursor.execute("SELECT DISTINCT hero_name FROM hero_equipment")
        hero_equipment_heroes = cursor.fetchall()

        for (hero_name,) in hero_equipment_heroes:
            # Проверяем, есть ли этот герой в garrisons
            cursor.execute("SELECT 1 FROM garrisons WHERE unit_name = ? LIMIT 1", (hero_name,))
            if cursor.fetchone() is None:
                # Героя нет в garrisons, удаляем его записи из hero_equipment
                print(f"[INFO] Герой '{hero_name}' не найден в garrisons. Удаление из hero_equipment.")
                cursor.execute("DELETE FROM hero_equipment WHERE hero_name = ?", (hero_name,))
            else:
                print(f"[DEBUG] Герой '{hero_name}' найден в garrisons. Записи сохранены.")

        # --- 2. Очистка ai_hero_equipment ---
        print("[DEBUG] Проверка ai_hero_equipment...")
        # Получаем всех уникальных героев из ai_hero_equipment
        cursor.execute("SELECT DISTINCT hero_name FROM ai_hero_equipment")
        ai_hero_equipment_heroes = cursor.fetchall()

        for (hero_name,) in ai_hero_equipment_heroes:
            # Проверяем, есть ли этот герой в garrisons
            cursor.execute("SELECT 1 FROM garrisons WHERE unit_name = ? LIMIT 1", (hero_name,))
            if cursor.fetchone() is None:
                # Героя нет в garrisons, удаляем его записи из ai_hero_equipment
                print(f"[INFO] Герой ИИ '{hero_name}' не найден в garrisons. Удаление из ai_hero_equipment.")
                cursor.execute("DELETE FROM ai_hero_equipment WHERE hero_name = ?", (hero_name,))
            else:
                print(f"[DEBUG] Герой ИИ '{hero_name}' найден в garrisons. Записи сохранены.")

        conn.commit()
        print("[SUCCESS] Очистка таблиц экипировки завершена.")

    except sqlite3.Error as e:
        print(f"[ERROR] Ошибка базы данных при очистке экипировки: {e}")
        try:
            conn.rollback()
        except:
            pass
    except Exception as e:
        print(f"[ERROR] Неожиданная ошибка при очистке экипировки: {e}")
        import traceback
        traceback.print_exc()


def fight(attacking_city, defending_city, defending_army, attacking_army,
          attacking_fraction, defending_fraction, conn):
    """
    Основная функция боя между двумя армиями.
    """

    print('Армия attacking_army:', attacking_army)
    print('Армия defending_army:', defending_army)

    # Получаем фракцию игрока
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT faction_name FROM user_faction")
        result = cursor.fetchone()
        user_faction = result[0] if result else None
    except Exception as e:
        print(f"[ERROR] Не удалось получить фракцию игрока: {e}")
        user_faction = None

    is_user_involved = False
    if user_faction:
        for unit in attacking_army:
            if isinstance(unit, dict) and 'unit_name' in unit:
                unit_name = unit['unit_name']
            elif isinstance(unit, (list, tuple)) and len(unit) > 0:
                unit_name = unit[0]
            else:
                continue
            try:
                cursor.execute("SELECT faction FROM units WHERE unit_name = ?", (unit_name,))
                result = cursor.fetchone()
                if result and result[0] == user_faction:
                    is_user_involved = True
                    break
            except sqlite3.Error as e:
                print(f"[ERROR] Не удалось проверить фракцию для '{unit_name}': {e}")

        if not is_user_involved:
            for unit in defending_army:
                if isinstance(unit, dict) and 'unit_name' in unit:
                    unit_name = unit['unit_name']
                elif isinstance(unit, (list, tuple)) and len(unit) > 0:
                    unit_name = unit[0]
                else:
                    continue
                try:
                    cursor.execute("SELECT faction FROM units WHERE unit_name = ?", (unit_name,))
                    result = cursor.fetchone()
                    if result and result[0] == user_faction:
                        is_user_involved = True
                        break
                except sqlite3.Error as e:
                    print(f"[ERROR] Не удалось проверить фракцию для '{unit_name}': {e}")
    cursor.close()

    # Объединяем одинаковые юниты
    merged_attacking = merge_units(attacking_army)
    merged_defending = merge_units(defending_army)

    # Инициализируем потери
    for u in merged_attacking + merged_defending:
        u['initial_count'] = u['unit_count']
        u['killed_count'] = 0

    # Функция для извлечения класса юнита
    def get_unit_class(u):
        stats = u.get('units_stats', {})
        class_str = stats.get('Класс юнита', '1 класс')
        return int(class_str.split()[0])

    # Разделяем юниты по классам
    def split_units(units):
        base_units = []
        hero_2 = []
        hero_3 = []
        legendary = []
        for u in units:
            cls = get_unit_class(u)
            if cls == 1:
                base_units.append(u)
            elif cls == 2:
                hero_2.append(u)
            elif cls == 3:
                hero_3.append(u)
            elif cls == 4:
                legendary.append(u)
        return base_units, hero_2, hero_3, legendary

    # Разделяем атакующих и обороняющихся
    atk_base, atk_hero_2, atk_hero_3, atk_legendary = split_units(merged_attacking)
    def_base, def_hero_2, def_hero_3, def_legendary = split_units(merged_defending)

    # Подсчёт бонусов от героев
    def calculate_bonuses(hero_list):
        bonus_attack = 0
        bonus_defense = 0
        bonus_health = 0
        for hero in hero_list:
            stats = hero.get('units_stats', {})
            bonus_attack += stats.get('Урон', 0)
            bonus_defense += stats.get('Защита', 0)
            bonus_health += stats.get('Живучесть', 0)
        return bonus_attack, bonus_defense, bonus_health

    # Применение бонусов к базовым юнитам
    def apply_bonus(base_units, attack_bonus, defense_bonus, bonus_health):
        for u in base_units:
            u['units_stats']['Урон'] += attack_bonus
            u['units_stats']['Защита'] += defense_bonus
            u['units_stats']['Живучесть'] += bonus_health
        return base_units

    # Расчет бонусов от героев
    atk_attack_bonus, atk_defense_bonus, atk_health_bonus = calculate_bonuses(atk_hero_2 + atk_hero_3)
    def_attack_bonus, def_defense_bonus, def_health_bonus = calculate_bonuses(def_hero_2 + def_hero_3)

    # Накладываем бонусы на базовые юниты
    modified_atk_base = apply_bonus(atk_base, atk_attack_bonus, atk_defense_bonus, atk_health_bonus)
    modified_def_base = apply_bonus(def_base, def_attack_bonus, def_defense_bonus, def_health_bonus)

    # Объединяем обратно
    modified_attacking = modified_atk_base + atk_hero_2 + atk_hero_3 + atk_legendary
    modified_defending = modified_def_base + def_hero_2 + def_hero_3 + def_legendary

    # Сортировка по классу и урону
    def priority(u):
        stats = u.get('units_stats', {})
        unit_class = int(stats.get('Класс юнита', '1 класс').split()[0])
        attack = int(stats.get('Урон', 0))
        return (unit_class, -attack)

    modified_attacking.sort(key=priority)
    modified_defending.sort(key=priority)

    # Бой
    # Цепочка боя: один атакующий может атаковать несколько целей, но только если убивает каждую
    for atk in modified_attacking:
        if atk['unit_count'] <= 0:
            continue

        i = 0
        while i < len(modified_defending) and atk['unit_count'] > 0:
            df = modified_defending[i]
            if df['unit_count'] <= 0:
                i += 1
                continue

            # Проводим бой
            atk_copy = atk.copy()
            df_copy = df.copy()
            atk_new, df_new = battle_chain(atk_copy, df_copy, defending_city, user_faction, conn)

            # Обновляем данные
            atk['unit_count'] = atk_new['unit_count']
            df['unit_count'] = df_new['unit_count']

            # Если защитник погиб — переходим к следующему
            if df['unit_count'] <= 0:
                i += 1
            else:
                # Защитник жив — больше не можем атаковать других
                break

    # Потери
    for u in modified_attacking + modified_defending:
        u['killed_count'] = u['initial_count'] - u['unit_count']

    # Определяем победителя
    winner = 'attacking' if any(u['unit_count'] > 0 for u in modified_attacking) else 'defending'

    # Обновляем гарнизоны
    update_garrisons_after_battle(
        winner=winner,
        attacking_city=attacking_city,
        defending_city=defending_city,
        attacking_army=modified_attacking,
        defending_army=modified_defending,
        attacking_fraction=attacking_fraction,
        defending_fraction=defending_fraction,
        conn=conn
    )

    # Обновляем таблицу results
    total_attacking_losses = sum(u['killed_count'] for u in modified_attacking)
    total_defending_losses = sum(u['killed_count'] for u in modified_defending)

    update_results_table(db_connection=conn, faction=attacking_fraction, units_destroyed=total_attacking_losses,
                         enemy_losses=total_defending_losses)
    update_results_table(db_connection=conn, faction=defending_fraction, units_destroyed=total_defending_losses,
                         enemy_losses=total_attacking_losses)

    # Генерируем отчет
    final_report_attacking = [{
        'unit_name': u['unit_name'],
        'initial_count': u['initial_count'],
        'unit_count': u['unit_count'],
        'killed_count': u['killed_count']
    } for u in modified_attacking]

    final_report_defending = [{
        'unit_name': u['unit_name'],
        'initial_count': u['initial_count'],
        'unit_count': u['unit_count'],
        'killed_count': u['killed_count']
    } for u in modified_defending]

    # Отображаем отчет
    if is_user_involved:
        report_data = generate_battle_report(
            final_report_attacking,
            final_report_defending,
            winner=winner,
            attacking_fraction=attacking_fraction,
            defending_fraction=defending_fraction,
            user_faction=user_faction,
            city=defending_city
        )
        show_battle_report(report_data, is_user_involved=is_user_involved, user_faction=user_faction, conn=conn)
    cleanup_equipment_after_battle(conn)
    return {
        "winner": winner,
        "attacking_fraction": attacking_fraction,
        "defending_fraction": defending_fraction,
        "attacking_losses": total_attacking_losses,
        "defending_losses": total_defending_losses,
        "attacking_units": final_report_attacking,
        "defending_units": final_report_defending
    }


def battle_chain(attacker, defender, city, user_faction, conn):
    attack_power = calculate_unit_power(attacker, is_attacking=True)
    defense_power = calculate_unit_power(defender, is_attacking=False)

    if defense_power <= 0:
        defense_power = 1  # защита от деления на 0

    total_attack = attack_power * attacker['unit_count']
    total_defense = defense_power * defender['unit_count']

    damage_to_infrastructure(total_attack, city, user_faction, conn)

    if total_attack > total_defense:
        remaining_power = total_attack - total_defense
        attacker_class = get_unit_class(attacker)

        if attacker_class >= 2:
            attacker['unit_count'] = 1 if remaining_power >= 1 else 0
        else:
            surviving = max(int(remaining_power // attack_power), 0)
            attacker['unit_count'] = surviving
        defender['unit_count'] = 0
    else:
        remaining_power = total_defense - total_attack
        defender_class = get_unit_class(defender)

        if defender_class >= 2:
            defender['unit_count'] = 1 if remaining_power >= 1 else 0
        else:
            surviving = max(int(remaining_power // defense_power), 0)
            defender['unit_count'] = surviving
        attacker['unit_count'] = 0

    return attacker, defender


def get_unit_class(unit):
    return int(unit['units_stats'].get('Класс юнита', '1'))


def calculate_army_power(army):
    """
    Рассчитывает общую силу армии.
    :param army: Список юнитов в армии.
    :return: Общая сила армии (float).
    """
    total_power = 0
    for unit in army:
        unit_damage = unit['units_stats']['Урон']
        unit_count = unit['unit_count']
        total_power += unit_damage * unit_count
    return total_power


def calculate_unit_power(unit, is_attacking):
    """
    Рассчитывает силу одного юнита.
    :param unit: Данные о юните (словарь с характеристиками).
    :param is_attacking: True, если юнит атакующий; False, если защитный.
    :return: Сила юнита (float).
    """
    if is_attacking:
        # Для атакующих юнитов
        attack = unit['units_stats']['Урон']
        return attack
    else:
        # Для защитных юнитов
        durability = unit['units_stats']['Живучесть']
        defense = unit['units_stats']['Защита']
        return durability + defense


def update_garrisons_after_battle(winner, attacking_city, defending_city,
                                  attacking_army, defending_army,
                                  attacking_fraction, defending_fraction, conn):
    """
    Обновляет гарнизоны после боя.
    """
    try:
        cursor = conn.cursor()
        if winner == 'attacking':
            # Если победила атакующая сторона
            # Удаляем гарнизон обороняющейся стороны
            cursor.execute("DELETE FROM garrisons WHERE city_name = ?", (defending_city,))

            # Перемещаем оставшиеся атакующие войска в захваченный город
            for unit in attacking_army:
                if unit['unit_count'] > 0:
                    cursor.execute("""
                        INSERT INTO garrisons (city_name, unit_name, unit_count, unit_image)
                        VALUES (?, ?, ?, ?)
                        ON CONFLICT(city_name, unit_name) DO UPDATE SET
                            unit_count = excluded.unit_count,
                            unit_image = excluded.unit_image
                    """, (
                        defending_city,
                        unit['unit_name'],
                        unit['unit_count'],
                        unit.get('unit_image', '')
                    ))
            # обновляем фракцию
            cursor.execute("UPDATE cities SET faction = ? WHERE name = ?", (attacking_fraction, defending_city))

            # Обновляем фракцию зданий
            cursor.execute("UPDATE buildings SET faction = ? WHERE city_name = ?", (attacking_fraction, defending_city))

        else:
            # Если победила обороняющаяся сторона
            # Очищаем гарнизон и восстанавливаем оставшихся юнитов
            cursor.execute("DELETE FROM garrisons WHERE city_name = ?", (defending_city,))
            for unit in defending_army:
                if unit['unit_count'] > 0:
                    cursor.execute("""
                        INSERT INTO garrisons (city_name, unit_name, unit_count, unit_image)
                        VALUES (?, ?, ?, ?)
                        ON CONFLICT(city_name, unit_name) DO UPDATE SET
                            unit_count = excluded.unit_count,
                            unit_image = excluded.unit_image
                    """, (
                        defending_city,
                        unit['unit_name'],
                        unit['unit_count'],
                        unit.get('unit_image', '')
                    ))

        # Обновляем гарнизон атакующего города (общий блок для обоих случаев)
        original_counts = {}
        cursor.execute("SELECT unit_name, unit_count FROM garrisons WHERE city_name = ?", (attacking_city,))
        for row in cursor.fetchall():
            original_counts[row['unit_name']] = row['unit_count']

        for unit in attacking_army:
            remaining_in_source = original_counts.get(unit['unit_name'], 0) - unit['initial_count']
            if remaining_in_source > 0:
                cursor.execute("""
                    UPDATE garrisons 
                    SET unit_count = ? 
                    WHERE city_name = ? AND unit_name = ?
                """, (remaining_in_source, attacking_city, unit['unit_name']))
            else:
                cursor.execute("""
                    DELETE FROM garrisons 
                    WHERE city_name = ? AND unit_name = ?
                """, (attacking_city, unit['unit_name']))

        # Проверяем необходимость сброса характеристик для обеих фракций
        reset_third_class_units_if_empty(conn, attacking_fraction)
        reset_third_class_units_if_empty(conn, defending_fraction)

    except sqlite3.Error as e:
        print(f"Ошибка при обновлении гарнизонов: {e}")



#------------------------------------

def damage_to_infrastructure(all_damage, city_name, user_faction, conn):
    """
    Вычисляет урон по инфраструктуре города и обновляет данные в базе данных.

    :param all_damage: Общий урон, который нужно нанести.
    :param city_name: Название города, по которому наносится урон.
    """

    # Константа для урона, необходимого для разрушения одного здания
    global damage_info
    DAMAGE_PER_BUILDING = 45900

    # Подключение к базе данных
    try:
        cursor = conn.cursor()

        # Загрузка данных о зданиях для указанного города
        cursor.execute('''
            SELECT building_type, count 
            FROM buildings 
            WHERE city_name = ? AND count > 0
        ''', (city_name,))
        rows = cursor.fetchall()

        # Преобразование данных в словарь
        city_data = {}
        for row in rows:
            building_type, count = row
            city_data[building_type] = count

        if not city_data:
            return

        print(f"Данные инфраструктуры до удара: {city_data}")

        effective_weapon_damage = all_damage
        print(f"Эффективный урон по инфраструктуре: {effective_weapon_damage}")

        # Подсчет общего числа зданий
        total_buildings = sum(city_data.values())
        if total_buildings == 0:
            print("В городе нет зданий для нанесения урона.")
            return

        # Сколько зданий может быть разрушено этим уроном
        potential_destroyed_buildings = int(effective_weapon_damage // DAMAGE_PER_BUILDING)
        print(f"Максимально возможное количество разрушенных зданий: {potential_destroyed_buildings}")

        # Уничтожаем здания, начиная с больниц и фабрик
        damage_info = {}
        priority_buildings = ['Больница', 'Фабрика']  # Приоритетные типы зданий для уничтожения

        for building in priority_buildings:
            if building in city_data and city_data[building] > 0:
                count = city_data[building]
                if potential_destroyed_buildings >= count:
                    # Уничтожаем все здания этого типа
                    damage_info[building] = count
                    city_data[building] = 0
                    potential_destroyed_buildings -= count

                    # Обновляем данные в базе данных
                    cursor.execute('''
                        UPDATE buildings 
                        SET count = 0 
                        WHERE city_name = ? AND building_type = ?
                    ''', (city_name, building))
                else:
                    # Уничтожаем часть зданий
                    damage_info[building] = potential_destroyed_buildings
                    city_data[building] -= potential_destroyed_buildings

                    # Обновляем данные в базе данных
                    cursor.execute('''
                        UPDATE buildings 
                        SET count = count - ? 
                        WHERE city_name = ? AND building_type = ?
                    ''', (potential_destroyed_buildings, city_name, building))

                    potential_destroyed_buildings = 0

                if potential_destroyed_buildings == 0:
                    break

        print(f"Данные инфраструктуры после удара: {city_data}")

        # Сохраняем изменения в базе данных
        conn.commit()
        print('Обновленная инфраструктура сохранена.')

    except Exception as e:
        print(f"Ошибка при работе с базой данных: {e}")


def update_dossier_battle_stats(conn, user_faction, is_victory):
    """
    Обновляет статистику по боям в таблице dossier для текущей фракции пользователя.

    :param conn: Соединение с базой данных.
    :param user_faction: Название фракции игрока.
    :param is_victory: True, если игрок победил, False — если проиграл.
    """
    try:
        cursor = conn.cursor()
        # Проверяем, существует ли запись для этой фракции
        cursor.execute("SELECT battle_victories, battle_defeats FROM dossier WHERE faction = ?", (user_faction,))
        result = cursor.fetchone()

        if result:
            # Если запись есть — обновляем нужное поле
            if is_victory:
                cursor.execute("""
                    UPDATE dossier
                    SET battle_victories = battle_victories + 1,
                        last_data = datetime('now')
                    WHERE faction = ?
                """, (user_faction,))
            else:
                cursor.execute("""
                    UPDATE dossier
                    SET battle_defeats = battle_defeats + 1,
                        last_data = datetime('now')
                    WHERE faction = ?
                """, (user_faction,))
        else:
            # Если записи нет — создаём новую
            if is_victory:
                cursor.execute("""
                    INSERT INTO dossier (
                        faction, battle_victories, battle_defeats, last_data
                    ) VALUES (?, 1, 0, datetime('now'))
                """, (user_faction,))
            else:
                cursor.execute("""
                    INSERT INTO dossier (
                        faction, battle_victories, battle_defeats, last_data
                    ) VALUES (?, 0, 1, datetime('now'))
                """, (user_faction,))
        conn.commit()
        print(f"[Досье] Обновлены данные для фракции '{user_faction}'")
    except Exception as e:
        conn.rollback()
        print(f"[Ошибка] Не удалось обновить досье: {e}")



def reset_third_class_units_if_empty(conn, faction_name):
    """
    Сбрасывает характеристики юнитов 3 класса указанной фракции до значений по умолчанию,
    если в гарнизонах этой фракции не осталось юнитов 3 класса.

    :param conn: Соединение с базой данных
    :param faction_name: Название фракции
    """
    try:
        cursor = conn.cursor()

        # Проверяем, есть ли юниты 3 класса в гарнизонах этой фракции
        cursor.execute("""
            SELECT COUNT(*) 
            FROM garrisons g
            JOIN units u ON g.unit_name = u.unit_name
            WHERE u.faction = ? AND u.unit_class = 3
        """, (faction_name,))

        third_class_count = cursor.fetchone()[0]

        # Если юнитов 3 класса нет в гарнизонах
        if third_class_count == 0:
            print(f"[INFO] Юниты 3 класса фракции '{faction_name}' отсутствуют в гарнизонах. Сброс характеристик...")

            # Сбрасываем характеристики юнитов 3 класса до значений по умолчанию
            cursor.execute("""
                UPDATE units 
                SET 
                    attack = (SELECT attack FROM units_default WHERE units_default.unit_name = units.unit_name),
                    defense = (SELECT defense FROM units_default WHERE units_default.unit_name = units.unit_name),
                    durability = (SELECT durability FROM units_default WHERE units_default.unit_name = units.unit_name),
                    cost_money = (SELECT cost_money FROM units_default WHERE units_default.unit_name = units.unit_name),
                    cost_time = (SELECT cost_time FROM units_default WHERE units_default.unit_name = units.unit_name)
                WHERE faction = ? AND unit_class = 3
            """, (faction_name,))

            print(f"[SUCCESS] Характеристики юнитов 3 класса фракции '{faction_name}' сброшены до значений по умолчанию.")

            # Получаем текущий сезон для применения бонусов
            cursor.execute("SELECT current_season FROM season LIMIT 1")
            season_result = cursor.fetchone()

            if season_result:
                current_season = season_result[0]

                # Применяем сезонные бонусы к сброшенным характеристикам
                faction_effects = [
                    # 0 = Зима
                    {
                        'Люди':  {'stat': 1.25,  'cost': 0.65},
                        'Эльфы': {'stat': 0.65,  'cost': 1.25},
                        'Вампиры': {'stat': 0.97,  'cost': 1.00},
                        'Адепты':   {'stat': 0.90,  'cost': 1.17},
                        'Элины':  {'stat': 0.45,  'cost': 1.45},
                    },
                    # 1 = Весна
                    {
                        'Люди':  {'stat': 0.90,  'cost': 1.17},
                        'Эльфы': {'stat': 0.97,  'cost': 1.00},
                        'Вампиры': {'stat': 1.25,  'cost': 0.65},
                        'Адепты':   {'stat': 0.65,  'cost': 1.25},
                        'Элины':  {'stat': 0.99,  'cost': 0.90},
                    },
                    # 2 = Лето
                    {
                        'Люди':  {'stat': 0.65,  'cost': 1.25},
                        'Эльфы': {'stat': 1.25,  'cost': 0.65},
                        'Вампиры': {'stat': 0.90,  'cost': 1.17},
                        'Адепты':   {'stat': 0.97,  'cost': 1.00},
                        'Элины':  {'stat': 1.70,  'cost': 0.60},
                    },
                    # 3 = Осень
                    {
                        'Люди':  {'stat': 0.97,  'cost': 1.00},
                        'Эльфы': {'stat': 0.90,  'cost': 1.17},
                        'Вампиры': {'stat': 0.65,  'cost': 1.25},
                        'Адепты':   {'stat': 1.25,  'cost': 0.65},
                        'Элины':  {'stat': 0.90,  'cost': 1.17},
                    },
                ]

                if current_season in [0, 1, 2, 3] and faction_name in faction_effects[current_season]:
                    effects = faction_effects[current_season][faction_name]
                    stat_f = effects['stat']
                    cost_f = effects['cost']

                    # Применяем stat-коэффициент (attack, defense)
                    if stat_f != 1.0:
                        cursor.execute("""
                            UPDATE units
                            SET
                                attack  = CAST(ROUND(attack  * ?) AS INTEGER),
                                defense = CAST(ROUND(defense * ?) AS INTEGER)
                            WHERE faction = ? AND unit_class = 3
                        """, (stat_f, stat_f, faction_name))

                    # Применяем cost-коэффициент (cost_money, cost_time)
                    if cost_f != 1.0:
                        cursor.execute("""
                            UPDATE units
                            SET
                                cost_money = CAST(ROUND(cost_money * ?) AS INTEGER),
                                cost_time  = CAST(ROUND(cost_time  * ?) AS INTEGER)
                            WHERE faction = ? AND unit_class = 3
                        """, (cost_f, cost_f, faction_name))

                    print(f"[SUCCESS] Сезонные бонусы применены к юнитам 3 класса фракции '{faction_name}' для сезона {current_season}.")

            conn.commit()
            return True
        else:
            print(f"[INFO] У фракции '{faction_name}' остались юниты 3 класса в гарнизонах. Сброс не требуется.")
            return False

    except sqlite3.Error as e:
        print(f"[ERROR] Ошибка базы данных при сбросе характеристик юнитов 3 класса: {e}")
        try:
            conn.rollback()
        except:
            pass
        return False
    except Exception as e:
        print(f"[ERROR] Неожиданная ошибка при сбросе характеристик юнитов 3 класса: {e}")
        import traceback
        traceback.print_exc()
        try:
            conn.rollback()
        except:
            pass
        return False