from lerdon_libraries import *
from db_lerdon_connect import *

def restore_from_backup(conn):
    """
    Восстанавливает данные из стандартных таблиц в рабочие.
    :param conn: Активное соединение с базой данных.
    """
    cursor = conn.cursor()
    tables_to_restore = [
        ("diplomacies_default", "diplomacies"),
        ("relations_default", "relations"),
        ("resources_default", "resources"),
        ("units_default", "units"),
        ("artifacts_default", "artifacts"),
        ("artifacts_ai_default", "artifacts_ai")
    ]

    try:
        cursor.execute("BEGIN IMMEDIATE")  # Блокируем на время восстановления

        for default_table, working_table in tables_to_restore:
            cursor.execute(f"DELETE FROM {working_table}")
            cursor.execute(f"INSERT INTO {working_table} SELECT * FROM {default_table}")

        conn.commit()
        print("Данные успешно восстановлены из бэкапа.")
    except sqlite3.Error as e:
        conn.rollback()
        print(f"Ошибка восстановления данных: {e}")


def clear_tables(conn):
    """
    Очищает данные из указанных таблиц базы данных.
    :param conn: Подключение к базе данных SQLite.
    """
    tables_to_clear = [
        "buildings",
        "cities",
        "diplomacies",
        "garrisons",
        "resources",
        "trade_agreements",
        "turn",
        "turn_save",
        "armies",
        "political_systems",
        "karma",
        "user_faction",
        "units",
        "results",
        "auto_build_settings",
        "interface_coord",
        "hero_equipment",
        "ai_hero_equipment",
        "effects_seasons",
        "nobles",
        "noble_events",
        "coup_attempts",
        "artifacts",
        "artifacts_ai",
        "artifact_effects_log",
        "player_allies",
        "negotiation_history",
    ]

    cursor = conn.cursor()

    try:
        for table in tables_to_clear:
            # Используем TRUNCATE или DELETE для очистки таблицы
            cursor.execute(f"DELETE FROM {table};")
            print(f"Таблица '{table}' успешно очищена.")

        # Фиксируем изменения
        conn.commit()
    except sqlite3.Error as e:
        print(f"Ошибка при очистке таблиц: {e}")
        conn.rollback()  # Откат изменений в случае ошибки

class ResultsGame:
    def __init__(self, game_status, reason, conn):
        self.game_status = game_status  # Статус игры: "win" или "lose"
        self.reason = reason  # Причина завершения игры
        self.conn = conn  # Соединение с базой
    def load_results(self):
        """
        Загрузка результатов игры из базы данных.
        :return: Список результатов.
        """
        conn = self.conn
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM results')
        results = cursor.fetchall()
        return results


    def calculate_results(self):
        """
        Вычисляет дополнительные показатели на основе данных из таблицы results.
        :return: Список словарей с полными данными, включая вычисленные значения.
        """
        results = self.load_results()

        calculated_results = []
        for row in results:
            (
                id,
                units_combat,
                units_destroyed,
                units_killed,
                army_efficiency_ratio,
                average_deal_ratio,
                average_net_profit_coins,
                average_net_profit_raw,
                economic_efficiency,
                faction,
            ) = row

            if units_combat != 0:
                bonus_arms = round(units_killed / units_combat, 2)
            else:
                bonus_arms = 0
            # Вычисляем Army_Efficiency_Ratio
            if units_destroyed != 0:
                army_efficiency_ratio = round((units_killed / units_destroyed) * bonus_arms, 2)
            else:
                army_efficiency_ratio = 0  # Защита от деления на ноль

            # Добавляем все значения в список, включая вычисленные
            calculated_results.append(
                {
                    "id": id,
                    "units_combat": units_combat,
                    "units_destroyed": units_destroyed,
                    "units_killed": units_killed,
                    "army_efficiency_ratio": army_efficiency_ratio,
                    "average_deal_ratio": average_deal_ratio,
                    "faction": faction,
                }
            )

        return calculated_results

    def update_dossier_stats(self):
        conn = self.conn
        cursor = conn.cursor()

        # Получаем последний результат (или можно передавать как параметр)
        calculated_results = self.calculate_results()

        # Находим запись с текущей фракцией
        for data in calculated_results:
            if data["faction"] == self.current_faction:
                rating = data["army_efficiency_ratio"]
                break
        else:
            return

        # Определяем, победа или поражение
        victories = 1 if self.game_status == "win" else 0
        defeats = 1 if self.game_status == "lose" else 0

        # Обновляем dossier ТОЛЬКО для текущей фракции
        cursor.execute('''
            UPDATE dossier SET 
                avg_military_rating_per_faction = ?,
                matches_won = matches_won + ?,
                matches_lost = matches_lost + ?
            WHERE faction = ?
        ''', (rating, victories, defeats, self.current_faction))

        conn.commit()

    def show_results(self, faction_name, status, reason):
        self.game_status = status
        self.reason = reason
        self.current_faction = faction_name
        self.update_dossier_stats()  # ← ОБНОВЛЯЕМ СТАТИСТИКУ
        self.calculate_military_rank()  # ← ТЕПЕРЬ РАСЧЁТ ЗВАНИЙ РАБОТАЕТ

        # Загружаем и фильтруем результаты (исключая Нейтралов)
        calculated_results = [r for r in self.calculate_results()
                              if r["faction"] != "Нейтрал"]

        # Формируем заголовок
        if self.game_status == "win":
            title = "Победа!"
            color = (0, 1, 0, 1)  # Зеленый
            message = f"[b]{faction_name} одержали победу![/b]\n {reason}\n"
        elif self.game_status == "lose":
            title = "Поражение!"
            color = (1, 0, 0, 1)  # Красный
            message = f"[b]{faction_name} потерпели поражение.[/b]\n {reason}\n"
        else:
            title = "Результаты игры"
            color = (1, 1, 1, 1)
            message = "Неизвестный статус завершения игры.\n"

        # Отображаем результаты в графическом интерфейсе
        self.show_results_popup(title, message, calculated_results, color)

    def calculate_military_rank(self):
        """
        Обновляет military_rank только для фракции self.current_faction
        в таблице dossier на основе расчёта итоговых очков.
        Использует новые системы званий (уровни 1-19).
        """
        if not hasattr(self, 'current_faction') or self.current_faction is None:
            return

        # Новые системы званий для разных фракций (Уровень 1 - высший, 19 - низший)
        rank_tables = {
            'Вампиры': [
                ("Повелитель ночи", 1),
                ("Вечный граф", 2),
                ("Темный лорд", 3),
                ("Князь тьмы", 4),
                ("Старший вампир", 5),
                ("Ночной страж", 6),
                ("Теневой охотник", 7),
                ("Призрачный убийца", 8),
                ("Темный воитель", 9),
                ("Ночной рейнджер", 10),
                ("Младший вампир", 11),
                ("Темный слуга", 12),
                ("Послушник вампира", 13),
                ("Жнец", 14),
                ("Капитан следопытов", 15),
                ("Багровый следопыт", 16),
                ("Вестник смерти", 17),
                ("Пепел прошлого", 18),
                ("Укушенный", 19),
            ],
            'Север': [
                ("Министр Войны", 1),
                ("Верховный маршал", 2),
                ("Генерал-фельдмаршал", 3),
                ("Генерал армии", 4),
                ("Генерал-полковник", 5),
                ("Генерал-лейтенант", 6),
                ("Генерал-майор", 7),
                ("Бригадный генерал", 8),
                ("Коммандер", 9),
                ("Полковник", 10),
                ("Подполковник", 11),
                ("Майор", 12),
                ("Капитан-лейтенант", 13),
                ("Капитан", 14),
                ("Платиновый лейтенант", 15),
                ("Серебряный лейтенант", 16),
                ("Сержант", 17),
                ("Прапорщик", 18),
                ("Рядовой", 19),
            ],
            'Эльфы': [
                ("Верховный правитель", 1),
                ("Лесной повелитель", 2),
                ("Вечный страж", 3),
                ("Магистр природы", 4),
                ("Лесной воевода", 5),
                ("Хранитель лесов", 6),
                ("Мастер стрелы", 7),
                ("Лесной командир", 8),
                ("Древесный защитник", 9),
                ("Мастер лука", 10),
                ("Ловкий стрелок", 11),
                ("Юркий воин", 12),
                ("Стремительный охотник", 13),
                ("Лесной страж", 14),
                ("Природный следопыт", 15),
                ("Ученик жрицы", 16),
                ("Начинающий охотник", 17),
                ("Молодой эльф", 18),
                ("Младший ученик эльфа", 19),
            ],
            'Адепты': [
                ("Верховный Инквизитор", 1),
                ("Великий Охотник", 2),
                ("Магистр Аббатства", 3),
                ("Гранд-Инквизитор", 4),
                ("Судья Правой Руки", 5),
                ("Главный Следователь", 6),
                ("Огонь Вердикта", 7),
                ("Страж Чистоты", 8),
                ("Палач Ереси", 9),
                ("Исполнитель Клятвы", 10),
                ("Сержант Ордена", 11),
                ("Офицер Инквизиции", 12),
                ("Кандидат Света", 13),
                ("Новичок Клятвы", 14),
                ("Причастный Костра", 15),
                ("Ученик Веры", 16),
                ("Искренний", 17),
                ("Слушающий Слово", 18),
                ("Пепел Греха", 19),
            ],
            'Элины': [
                ("Повелитель Пламени", 1),
                ("Око Бури", 2),
                ("Хранитель Песков", 3),
                ("Гнев Ветров", 4),
                ("Тень Дракона", 5),
                ("Жар Пустыни", 6),
                ("Клинок Солнца", 7),
                ("Пустынный Судья", 8),
                ("Мастер Ярости", 9),
                ("Искра Пламени", 10),
                ("Бегущий по Пескам", 11),
                ("Вестник Жара", 12),
                ("Порождение Торнадо", 13),
                ("Песчаный Странник", 14),
                ("Пыль Гривы", 15),
                ("Песчинка", 16),
                ("Забытый Ветром", 17),
                ("Проклятый Солнцем", 18),
                ("Пепел Пустыни", 19),
            ],
        }

        conn = self.conn
        cursor = conn.cursor()

        # Получаем данные по фракции игрока
        cursor.execute('''
            SELECT avg_military_rating_per_faction, avg_soldiers_starving, 
                   battle_victories, battle_defeats 
            FROM dossier
            WHERE faction = ?
        ''', (self.current_faction,))

        row = cursor.fetchone()
        if row is None:
            return

        rating, starving, victories, defeats = row

        # Защита от None
        rating = rating or 0
        starving = starving or 0
        victories = victories or 0
        defeats = defeats or 0

        rait_score = int((rating / 0.5) * 550)
        starving_penalty = int((starving / 100) * 50)

        # Если defeats = 0, используем просто victories, иначе victories/defeats
        if defeats == 0:
            b = victories
        else:
            b = victories / defeats

        final_score = max((int(rait_score - starving_penalty) * b), 0)

        # Пороговые значения для 19 уровней званий (от высшего к низшему)
        # Соответствуют старой логике распределения, но теперь для 19 уровней
        rank_thresholds = [
            11000000, 1800000, 1680000, 1565000, 1505000,
            1448000, 1368000, 1294000, 1240000, 1200000,
            1172000, 1140000, 1120000, 190000, 178000,
            160000, 140000, 80000, -float('inf')
        ]

        # Получаем соответствующую таблицу званий или используем систему по умолчанию (Север)
        rank_table = rank_tables.get(self.current_faction, rank_tables['Север'])

        # Определяем звание по итоговым баллам через пороги
        assigned_rank = rank_table[-1][0]  # По умолчанию последнее звание
        for i, threshold in enumerate(rank_thresholds):
            if final_score >= threshold:
                assigned_rank = rank_table[i][0]
                break

        # Обновляем ранг только для текущей фракции
        cursor.execute('''
            UPDATE dossier 
            SET military_rank = ?
            WHERE faction = ?
        ''', (assigned_rank, self.current_faction))

        conn.commit()


    def show_results_popup(self, title, message, results, text_color):
        # Создаем основной контейнер
        layout = FloatLayout(size_hint=(1, 1))

        # Расчет параметров адаптации
        def adapt_value(base, factor=0.5):
            """Динамический расчет размеров на основе плотности пикселей"""
            dpi = max(Window.width / (Window.width / dp(100)), 1)
            return max(dp(base * factor * (dpi / 160)), dp(base))

        # Стилизация фона
        bg_color = (0.12, 0.12, 0.12, 1)
        radius = [adapt_value(15)] * 4

        # Инициализация фона
        with layout.canvas.before:
            Color(*bg_color)
            self.background_rect = RoundedRectangle(
                pos=layout.pos,
                size=layout.size,
                radius=radius
            )

        # Привязка обновления фона
        def update_bg(instance, value):
            self.background_rect.pos = layout.pos
            self.background_rect.size = layout.size
            self.background_rect.radius = radius

        layout.bind(pos=update_bg, size=update_bg)

        # Сообщение
        message_label = Label(
            text=message,
            color=text_color,
            markup=True,
            font_size=adapt_value(18, 0.6),
            size_hint=(0.9, None),
            height=adapt_value(100),
            halign='center',
            valign='middle',
            pos_hint={'center_x': 0.5, 'top': 0.97},
            text_size=(Window.width * 0.85, None),
            line_height=1.2
        )
        message_label.bind(size=message_label.setter('text_size'))

        # Контейнер для таблицы
        table_container = BoxLayout(
            orientation='vertical',
            size_hint=(0.95, 0.7),
            pos_hint={"center_x": 0.5, "top": 0.75},
            spacing=adapt_value(10)
        )

        # ScrollView
        scroll_view = ScrollView(
            size_hint=(1, 1),
            bar_width=adapt_value(10),
            bar_color=(0.5, 0.5, 0.5, 0.7),
            bar_inactive_color=(0.3, 0.3, 0.3, 0)
        )

        # Таблица
        table_layout = GridLayout(
            cols=5,
            spacing=adapt_value(2),
            size_hint=(1, None),
            padding=adapt_value(5),
            row_default_height=adapt_value(40)
        )
        table_layout.bind(minimum_height=table_layout.setter('height'))

        # Адаптивные размеры
        base_font = adapt_value(14)
        row_height = adapt_value(35)

        # Заголовки таблицы
        headers = ["Фракция", "Ветераны", "Потери", "Уничтожено", "Боевой \n рейтинг"]
        for header in headers:
            lbl = Label(
                text=header,
                color=(1, 1, 1, 1),
                bold=True,
                font_size=base_font,
                size_hint_y=None,
                height=row_height,
                halign='center',
                valign='middle'
            )
            lbl.bind(
                size=lambda instance, _: setattr(instance.bg_rect, 'size', instance.size),
                pos=lambda instance, _: setattr(instance.bg_rect, 'pos', instance.pos)
            )

            with lbl.canvas.before:
                Color(0.15, 0.4, 0.7, 1)
                lbl.bg_rect = RoundedRectangle(pos=lbl.pos, size=lbl.size, radius=radius)

            table_layout.add_widget(lbl)

        # Данные таблицы
        for i, res in enumerate(results):
            row_color = (0.14, 0.14, 0.14, 1) if i % 2 == 0 else (0.16, 0.16, 0.16, 1)
            row_data = [
                res["faction"],
                f"{res['units_combat']:,}".replace(',', ' '),
                f"{res['units_destroyed']:,}".replace(',', ' '),
                f"{res['units_killed']:,}".replace(',', ' '),
                f"{res['army_efficiency_ratio']:.2f}"
            ]

            for value in row_data:
                lbl = Label(
                    text=value,
                    color=(0.92, 0.92, 0.92, 1),
                    font_size=base_font * 0.9,
                    size_hint_y=None,
                    height=row_height,
                    halign='center',
                    valign='middle'
                )
                lbl.bind(
                    size=lambda instance, _: setattr(instance.bg_rect, 'size', instance.size),
                    pos=lambda instance, _: setattr(instance.bg_rect, 'pos', instance.pos)
                )

                with lbl.canvas.before:
                    Color(*row_color)
                    lbl.bg_rect = RoundedRectangle(pos=lbl.pos, size=lbl.size, radius=radius)

                table_layout.add_widget(lbl)

        scroll_view.add_widget(table_layout)
        table_container.add_widget(scroll_view)

        # Кнопка выхода
        exit_btn = Button(
            text="ВЕРНУТЬСЯ В МЕНЮ",
            font_size=dp(16) if Window.width < 600 else dp(18),
            size_hint=(0.7, None),
            height=dp(45),
            pos_hint={"center_x": 0.5, "y": 0.02},
            background_color=(0.2, 0.5, 0.8, 1),
            background_normal=''
        )
        exit_btn.bind(on_release=self.exit_to_main_menu)

        # Добавляем элементы
        layout.add_widget(message_label)
        layout.add_widget(table_container)
        layout.add_widget(exit_btn)

        # Создаем попап
        popup = Popup(
            title="",
            content=layout,
            size_hint=(
                min(0.95, Window.width / 1000 + 0.6),
                min(0.95, Window.height / 1000 + 0.6)
            ),
            auto_dismiss=False,
            background='',  # Убираем стандартный фон
            background_color=[0, 0, 0, 0],  # Полная прозрачность
            separator_color=[0, 0, 0, 0],  # Убираем разделитель заголовка
            overlay_color=(0, 0, 0, 0.7))  # Затемнение фона приложения

        # Функция адаптации
        def adapt_layout(*args):
            table_layout.width = scroll_view.width
            message_label.text_size = (message_label.width * 0.95, None)
            table_layout.row_default_height = adapt_value(40)
            table_layout.spacing = adapt_value(2)
            scroll_view.bar_width = adapt_value(10)

        # Привязка к изменению размеров
        Window.bind(width=lambda *x: adapt_layout(), height=lambda *x: adapt_layout())
        Clock.schedule_once(adapt_layout)

        popup.open()
        self.popup = popup

    def exit_to_main_menu(self, instance):
        app = App.get_running_app()

        # Закрываем попап результатов
        if hasattr(self, 'popup') and self.popup:
            self.popup.dismiss()

        # === КРИТИЧЕСКИ ВАЖНЫЙ БЛОК: очистка и восстановление БД ===
        try:
            # 1. Очищаем игровые таблицы (сохраняя статистику в dossier)
            clear_tables(self.conn)

            # 2. Восстанавливаем дефолтные данные для новых игр
            restore_from_backup(self.conn)

            print("[DB] Игровые данные успешно сброшены. Готово к новой кампании.")
        except Exception as e:
            print(f"[DB ERROR] Ошибка при сбросе данных: {e}")
            import traceback
            traceback.print_exc()
            # Даже при ошибке БД продолжаем перезапуск приложения
        # =========================================================

        # Полная перезагрузка приложения для корректной инициализации
        app.restart_app()

