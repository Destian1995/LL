# army.py
from lerdon_libraries import *
from db_lerdon_connect import *

from economic import format_number


PRIMARY_COLOR = get_color_from_hex('#2E7D32')
SECONDARY_COLOR = get_color_from_hex('#388E3C')
BACKGROUND_COLOR = get_color_from_hex('#212121')
TEXT_COLOR = get_color_from_hex('#FFFFFF')
INPUT_BACKGROUND = get_color_from_hex('#FFFFFF')

class ArmyButton(Button):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.background_normal = ''
        self.background_color = (0,0,0,0)
        self.color = TEXT_COLOR
        self.font_size = dp(18)
        self.bold = True
        self.size_hint = (1, None)
        self.height = dp(60)
        self.padding = (dp(20), dp(10))

        with self.canvas.before:
            Color(*PRIMARY_COLOR)
            self.rect = RoundedRectangle(
                radius=[dp(15)],
                pos=self.pos,
                size=self.size
            )

        self.bind(pos=self.update_rect, size=self.update_rect)

    def update_rect(self, *args):
        self.rect.pos = self.pos
        self.rect.size = self.size

    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos):
            Animation(background_color=(*SECONDARY_COLOR, 1), d=0.1).start(self)
        return super().on_touch_down(touch)

    def on_touch_up(self, touch):
        Animation(background_color=(*PRIMARY_COLOR, 1), d=0.2).start(self)
        return super().on_touch_up(touch)

class ArmyCash:
    def __init__(self, faction, class_faction, conn):
        """
        Инициализация класса ArmyCash.
        :param faction: Название фракции.
        :param class_faction: Экземпляр класса Faction (экономический модуль).
        """
        self.faction = faction
        self.class_faction = class_faction  # Экономический модуль
        self.conn = conn  # Подключение к
        self.cursor = self.conn.cursor()
        self.resources = self.load_resources()  # Загрузка начальных ресурсов

    def load_resources(self):
        """
        Загружает текущие ресурсы фракции из базы данных.
        """
        try:
            rows = self.load_data("resources", ["resource_type", "amount"], "faction = ?", (self.faction,))
            resources = {"Кроны": 0, "Рабочие": 0}
            for resource_type, amount in rows:
                if resource_type in resources:
                    resources[resource_type] = amount

            # Отладочный вывод: загруженные ресурсы
            print(f"[DEBUG] Загружены ресурсы для фракции '{self.faction}': {resources}")
            return resources
        except sqlite3.Error as e:
            print(f"Ошибка при загрузке ресурсов: {e}")
            return {"Кроны": 0, "Рабочие": 0}

    def load_data(self, table, columns, condition=None, params=None):
        """
        Универсальный метод для загрузки данных из таблицы базы данных.
        """
        try:
            query = f"SELECT {', '.join(columns)} FROM {table}"
            if condition:
                query += f" WHERE {condition}"
            self.cursor.execute(query, params or ())
            result = self.cursor.fetchall()

            # Отладочный вывод: SQL-запрос и результат
            print(f"[DEBUG] SQL-запрос: {query}, параметры: {params}")
            print(f"[DEBUG] Результат запроса: {result}")

            return result
        except sqlite3.Error as e:
            print(f"Ошибка при загрузке данных из таблицы {table}: {e}")
            return []

    def deduct_resources(self, crowns, workers):
        """
        Списывает ресурсы через экономический модуль.

        :param crowns: Количество крон для списания.
        :param workers: Количество рабочих для списания.
        :return: True, если ресурсы успешно списаны; False, если недостаточно ресурсов.
        """
        try:
            # Проверяем доступность ресурсов через экономический модуль
            current_crowns = self.class_faction.get_resource_now("Кроны")
            current_workers = self.class_faction.get_resource_now("Рабочие")

            print(f"[DEBUG] Текущие ресурсы: Кроны={current_crowns}, Рабочие={current_workers}")

            if current_crowns < crowns or current_workers < workers:
                print("[DEBUG] Недостаточно ресурсов для списания.")
                return False

            # Списываем ресурсы через экономический модуль
            self.class_faction.update_resource_now("Кроны", current_crowns - crowns)
            self.class_faction.update_resource_now("Рабочие", current_workers - workers)

            return True

        except Exception as e:
            print(f"Ошибка при списании ресурсов: {e}")
            return False

    def hire_unit(self, unit_name, unit_cost, quantity, unit_stats, unit_image):
        """
        Нанимает юнит (оружие), если ресурсов достаточно и соблюдены правила найма по классам.

        :param unit_name: Название юнита.
        :param unit_cost: Стоимость юнита в виде кортежа (кроны, рабочие).
        :param quantity: Количество нанимаемых юнитов.
        :param unit_stats: Характеристики юнита (должен быть словарём).
        :param unit_image: Путь к изображению юнита.
        :return: True, если найм успешен; False в противном случае.
        """
        crowns, workers = unit_cost
        required_crowns = int(crowns) * int(quantity)
        required_workers = int(workers) * int(quantity)

        # Проверка наличия ресурсов
        if not self.deduct_resources(required_crowns, required_workers):
            self.show_message(
                title="Ошибка найма",
                message=f"Нанять юнитов невозможно: недостаточно ресурсов.\n"
                        f"Необходимые: {format_number(required_crowns)} крон и {format_number(required_workers)} рабочих."
            )
            return False

        # Проверка типа unit_stats
        if not isinstance(unit_stats, dict):
            print("[ERROR] unit_stats должен быть словарём!")
            return False

        # Получаем класс юнита
        try:
            unit_class_str = unit_stats.get("Класс юнита", "")
            unit_class = int(unit_class_str.split()[0])  # Например, "1 класс" -> 1
        except (ValueError, KeyError, IndexError):
            print(f"[ERROR] Не удалось определить класс юнита. Получено значение: '{unit_class_str}'")
            return False

        # --- 🛡️ Основная проверка ограничений по классу ---
        if unit_class == 1:
            # Класс 1 — можно нанимать всегда, без дополнительных проверок
            pass

        elif unit_class in [2, 3, 4]:
            # Проверяем, есть ли уже юнит этого класса в armies или garrisons
            try:
                # Проверка в armies
                self.cursor.execute("""
                    SELECT 1
                    FROM armies
                    WHERE faction = ? AND unit_class = ?
                    LIMIT 1
                """, (self.faction, str(unit_class)))  # <-- Теперь сравниваем с числом как строкой

                exists_in_armies = self.cursor.fetchone()

                # Проверка в garrisons через units
                self.cursor.execute("""
                    SELECT 1
                    FROM garrisons g
                    JOIN units u ON g.unit_name = u.unit_name
                    WHERE u.faction = ? AND u.unit_class = ?
                    LIMIT 1
                """, (self.faction, str(unit_class)))  # <-- То же самое

                exists_in_garrisons = self.cursor.fetchone()

                if exists_in_armies or exists_in_garrisons:
                    self.show_message(
                        title="Ошибка найма",
                        message=f"Герой {unit_class} класса уже существует у вашей фракции.\n"
                                f"Одновременно можно иметь только одного героя такого класса."
                    )
                    return False

                # Герои: только один
                if quantity > 1:
                    self.show_message(
                        title="Ошибка найма",
                        message=f"Можно нанять только одного героя {unit_class} класса."
                    )
                    return False

            except sqlite3.Error as e:
                print(f"[ERROR] Ошибка при проверке существующего героя: {e}")
                return False

        else:
            self.show_message(
                title="Ошибка найма",
                message="Неизвестный класс юнита."
            )
            return False

        # Добавление юнитов в базу данных
        self.add_or_update_army_unit(unit_name, quantity, unit_stats, unit_image)

        # Отображение сообщения об успехе
        self.show_message(
            title="Успех",
            message=f"{unit_name} нанят!\n"
                    f"Потрачено: {format_number(required_crowns)} крон и {format_number(required_workers)} рабочих."
        )

        return True

    def add_or_update_army_unit(self, unit_name, quantity, unit_stats, unit_image):
        """
        Добавляет или обновляет данные о юните в базе данных.
        """
        self.cursor.execute("""
            SELECT quantity, total_attack, total_defense, total_durability, unit_image
            FROM armies
            WHERE faction = ? AND unit_type = ?
        """, (self.faction, unit_name))
        result = self.cursor.fetchone()

        if result:
            # Если юнит уже существует, обновляем его данные
            current_quantity, total_attack, total_defense, total_durability, _ = result
            new_quantity = current_quantity + quantity
            self.cursor.execute("""
                UPDATE armies
                SET quantity = ?, total_attack = ?, total_defense = ?, total_durability = ?, unit_image = ?
                WHERE faction = ? AND unit_type = ?
            """, (
                new_quantity,
                total_attack + unit_stats["Урон"] * quantity,
                total_defense + unit_stats["Защита"] * quantity,
                total_durability + unit_stats["Живучесть"] * quantity,
                unit_image,  # Обновляем изображение
                self.faction,
                unit_name
            ))
        else:
            # Если юнит новый, добавляем его в базу
            self.cursor.execute("""
                INSERT INTO armies (faction, unit_type, quantity, total_attack, total_defense, total_durability, unit_class, unit_image)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                self.faction,
                unit_name,
                quantity,
                unit_stats["Урон"] * quantity,
                unit_stats["Защита"] * quantity,
                unit_stats["Живучесть"] * quantity,
                unit_stats["Класс юнита"],
                unit_image  # Добавляем изображение
            ))

        self.conn.commit()

    def hire_weapons(self, weapon_name, unit_cost, quantity):
        """
        Обновляет или создает запись в таблице weapons.
        :param unit_cost: кортеж, содержащий стоимость оружия в кронах и рабочих.
        """
        crowns, workers = unit_cost
        required_crowns = int(crowns) * int(quantity)
        required_workers = int(workers) * int(quantity)


        # Проверка наличия ресурсов
        if not self.deduct_resources(required_crowns, required_workers):
            self.show_message(
                title="Ошибка найма",
                message=f"Нанять юнитов невозможно: недостаточно ресурсов.\n"
                        f"Необходимые: {format_number(required_crowns)} крон и {format_number(required_workers)} рабочих."
            )
            return False
        return True

    def update_weapon_in_db(self, faction, weapon_name, quantity, damage, koef):
        """
        Обновляет или создает запись в таблице weapons.
        :param faction: Название фракции.
        :param weapon_name: Название оружия.
        :param quantity: Количество единиц оружия.
        :param damage: Урон оружия.
        :param koef: Коэффициент преодоления ПВО.
        """
        try:
            # Проверяем, существует ли запись для данного оружия
            self.cursor.execute('''
                SELECT quantity
                FROM weapons
                WHERE faction = ? AND weapon_name = ?
            ''', (faction, weapon_name))
            result = self.cursor.fetchone()

            if result:
                # Если запись существует, обновляем количество
                current_quantity = result[0]
                new_quantity = current_quantity + quantity
                self.cursor.execute('''
                    UPDATE weapons
                    SET quantity = ?, damage = ?, koef = ?
                    WHERE faction = ? AND weapon_name = ?
                ''', (new_quantity, damage, koef, faction, weapon_name))
            else:
                # Если запись отсутствует, создаем новую
                self.cursor.execute('''
                    INSERT INTO weapons (faction, weapon_name, quantity, damage, koef)
                    VALUES (?, ?, ?, ?, ?)
                ''', (faction, weapon_name, quantity, damage, koef))

            self.conn.commit()
            print(f"[DEBUG] Данные оружия '{weapon_name}' успешно обновлены в таблице weapons.")

        except sqlite3.Error as e:
            print(f"Ошибка при обновлении таблицы weapons: {e}")

    def show_message(self, title, message):
        screen_width, _ = Window.size
        scale_factor = screen_width / 360

        font_size = min(max(int(15 * scale_factor), 12), 18)
        padding = int(15 * scale_factor)
        spacing = int(5 * scale_factor)  # ← Уменьшен
        label_height = int(80 * scale_factor)  # ← Уменьшен
        button_height = int(30 * scale_factor)

        content_layout = BoxLayout(
            orientation='vertical',
            padding=[padding, padding / 2, padding, padding / 2],  # ← Скорректированы
            spacing=spacing
        )

        message_label = Label(
            text=message,
            color=(1, 1, 1, 1),
            font_size=sp(font_size),
            size_hint_y=None,
            height=label_height,
            halign='center',
            valign='middle'
        )
        message_label.bind(size=message_label.setter('text_size'))

        close_button = Button(
            text="Закрыть",
            font_size=sp(font_size),
            size_hint_y=None,
            height=button_height,
            background_color=(0.2, 0.6, 1, 1),
            background_normal=''
        )

        content_layout.add_widget(message_label)
        content_layout.add_widget(close_button)

        total_height = label_height + button_height + spacing + padding  # ← Новый расчет
        popup = Popup(
            title=title,
            content=content_layout,
            size_hint=(0.75, None),
            height=total_height,  # ← Динамическая высота
            auto_dismiss=False,
            title_size=sp(font_size + 1),
            title_align='center',
            separator_color=(0.2, 0.6, 1, 1)
        )

        close_button.bind(on_release=popup.dismiss)
        popup.open()


def load_unit_data(faction, conn):
    """Загружает данные о юнитах для выбранной фракции из базы данных."""
    cursor = conn.cursor()
    cursor.execute("""
        SELECT unit_name, consumption, cost_money, cost_time, image_path, attack, defense, durability, unit_class
        FROM units WHERE faction = ?
    """, (faction,))
    rows = cursor.fetchall()

    unit_data = {}
    for row in rows:
        unit_name, consumption, cost_money, cost_time, image_path, attack, defense, durability, unit_class = row
        unit_data[unit_name] = {
            "cost": [cost_money, cost_time],
            "image": image_path,
            "stats": {
                "Урон": attack,
                "Защита": defense,
                "Живучесть": durability,
                "Класс юнита": unit_class,
                "Потребление сырья": consumption
            }
        }
    return unit_data


def start_army_mode(faction, game_area, class_faction, conn):
    army_hire = ArmyCash(faction, class_faction, conn)
    faction_colors = {
        "Люди": (0.2, 0.4, 0.9, 0.8),
        "Эльфы": (0.2, 0.7, 0.3, 0.8),
        "Вампиры": (0.5, 0.2, 0.6, 0.8),
        "Адепты": (0, 0, 0, 0.8),
        "Полукровки": (0.6, 0.5, 0.1, 0.8),
    }
    bg_color = faction_colors.get(faction, (0.15, 0.15, 0.15, 1))
    main_box = BoxLayout(
        orientation='horizontal',
        size_hint=(1, 1),
        padding=dp(10),
        spacing=dp(5)
    )
    left_space = BoxLayout(size_hint=(0.3, 1))
    right_container = FloatLayout(size_hint=(1, 1))

    # Карусель
    carousel = Carousel(
        direction='right',
        size_hint=(1, 1),
        loop=True,
        scroll_distance=30,
        pos_hint={'top': 1.1, 'right': 1.06}
    )

    # Загрузка и сортировка юнитов
    unit_data = load_unit_data(faction, conn)
    sorted_units = sorted(
        unit_data.items(),
        key=lambda x: int(x[1]['stats']['Класс юнита'].split()[0])
    )

    # Создание слайдов
    for unit_name, unit_info in sorted_units:
        slide = BoxLayout(
            orientation='vertical',
            size_hint=(0.8, 0.8),
            spacing=dp(1),
            padding=dp(1)
        )
        card = BoxLayout(
            orientation='vertical',
            size_hint=(1, 1),
            spacing=dp(1),
            padding=dp(20)
        )

        # Фон карточки
        with card.canvas.before:
            Color(rgba=bg_color)
            shadow_rect = RoundedRectangle(size=card.size, radius=[dp(25)])
            Color(rgba=(0.05, 0.05, 0.05, 0))
            rect = RoundedRectangle(size=card.size, radius=[dp(20)])

        def update_bg(instance, rect=rect, shadow_rect=shadow_rect):
            rect.pos = instance.pos
            rect.size = instance.size
            shadow_rect.pos = (instance.x - dp(2), instance.y - dp(2))
            shadow_rect.size = instance.size

        card.bind(pos=update_bg, size=update_bg)

        # Заголовок
        header = BoxLayout(
            size_hint=(1, 0.12),
            orientation='horizontal',
            padding=[dp(150), dp(5), dp(5), dp(5)],
        )
        title = Label(
            text=unit_name,
            font_size='18sp',
            bold=True,
            color=TEXT_COLOR,
            halign='left',
            valign='middle',
            text_size=(None, None),
            size_hint=(None, None),
            width=dp(1)
        )
        title.bind(texture_size=lambda inst, ts: setattr(inst, 'width', ts[0] + dp(5)))
        header.add_widget(title)

        # Тело карточки: сначала иконки‑статы, потом изображение
        body = BoxLayout(orientation='horizontal', size_hint=(1, 0.6), spacing=dp(3))

        # Контейнер для иконок‑стат
        stats_icons = {
            'Урон': 'files/pict/hire/sword.png',
            'Защита': 'files/pict/hire/shield.png',
            'Живучесть': 'files/pict/hire/health.png',
            'Класс': 'files/pict/hire/class.png',
            'Потребление': 'files/pict/hire/consumption.png',
        }
        stats_container = BoxLayout(orientation='vertical', size_hint=(0.4, 1), spacing=dp(5))
        for stat_name, icon_src in stats_icons.items():
            stat_line = BoxLayout(orientation='horizontal', size_hint=(1, None), height=dp(20), spacing=dp(5))
            stat_line.add_widget(Image(
                source=icon_src,
                size_hint=(None, None),
                size=(dp(24), dp(24)),
                allow_stretch=True,
                keep_ratio=True
            ))

            # выбираем правильный ключ в unit_info['stats']
            if stat_name == 'Класс':
                key = 'Класс юнита'
            elif stat_name == 'Потребление':
                key = 'Потребление сырья'
            else:
                key = stat_name

            value = unit_info['stats'].get(key, '')
            if key in ('Урон', 'Защита', 'Живучесть', 'Потребление сырья'):
                value = format_number(value)

            stat_line.add_widget(Label(
                text=str(value),
                font_size='16sp',
                bold=True,
                color=TEXT_COLOR,
                halign='left',
                valign='middle'
            ))
            stats_container.add_widget(stat_line)

        # Контейнер для изображения
        img_container = BoxLayout(orientation='vertical', size_hint=(0.6, 1), padding=[0, dp(10), 0, 0])
        img = Image(
            source=unit_info['image'],
            size_hint=(1, 1),
            keep_ratio=True,
            allow_stretch=True,
            mipmap=True
        )
        img_container.add_widget(img)

        # Добавляем в тело сначала stats, потом картинку
        body.add_widget(stats_container)
        body.add_widget(img_container)

        # Стоимость
        cost_container = BoxLayout(
            orientation='horizontal',
            size_hint=(1, 0.2),
            spacing=dp(10),
            padding=[dp(15), 0, dp(15), 0]
        )
        price_label = Label(
            text="Цена:  ",
            font_size='16sp',
            bold=True,
            color=TEXT_COLOR,
            halign='right',
            size_hint=(0.3, 1)
        )
        cost_values = BoxLayout(orientation='vertical', size_hint=(0.7, 1), spacing=dp(5))
        cost_money, cost_time = unit_info['cost']

        money_stat = BoxLayout(orientation='horizontal', size_hint=(1, 0.5), spacing=dp(5))
        money_icon = Label(
            text="[color=#FFFFFF]Кроны[/color]",
            markup=True,
            font_size='14sp',
            halign='left',
            size_hint=(0.2, 1)
        )
        money_value = Label(
            text=f"{format_number(cost_money)}",
            font_size='16sp',
            bold=True,
            color=TEXT_COLOR,
            size_hint=(0.8, 1),
            halign='left'
        )
        money_stat.add_widget(money_icon)
        money_stat.add_widget(money_value)

        time_stat = BoxLayout(orientation='horizontal', size_hint=(1, 0.5), spacing=dp(5))
        time_icon = Label(
            text="[color=#FFFFFF]Рабочие[/color]",
            markup=True,
            font_size='14sp',
            halign='left',
            size_hint=(0.2, 1)
        )
        time_value = Label(
            text=f"{format_number(cost_time)}",
            font_size='16sp',
            bold=True,
            color=TEXT_COLOR,
            size_hint=(0.8, 1),
            halign='left'
        )
        time_stat.add_widget(time_icon)
        time_stat.add_widget(time_value)

        cost_values.add_widget(money_stat)
        cost_values.add_widget(time_stat)
        cost_container.add_widget(price_label)
        cost_container.add_widget(cost_values)

        # Контроллеры найма
        unit_class = int(unit_info['stats']['Класс юнита'].split()[0])
        control_panel = BoxLayout(
            size_hint=(1, 0.18),
            orientation='horizontal',
            spacing=dp(10),
            padding=[dp(5), dp(10), dp(5), dp(5)]
        )
        btn_hire = Button(
            text='НАБРАТЬ',
            font_size='16sp',
            bold=True,
            background_color=PRIMARY_COLOR,
            color=TEXT_COLOR,
            size_hint=(0.4, 1)
        )

        # Если первый класс — добавляем поле ввода
        if unit_class == 1:
            input_qty = TextInput(
                hint_text='Количество',
                input_filter='int',
                font_size='14sp',
                size_hint=(0.6, 1),
                background_color=INPUT_BACKGROUND,
                halign='center',
                multiline=False
            )
            btn_hire.bind(
                on_release=lambda inst, name=unit_name, cost=unit_info['cost'],
                                  input_box=input_qty, stats=unit_info['stats'], image=unit_info["image"]:
                broadcast_units(name, cost, input_box, army_hire, image, stats)
            )
            control_panel.add_widget(input_qty)
        else:
            btn_hire = Button(
                text='НАНЯТЬ',
                font_size='16sp',
                bold=True,
                background_color=PRIMARY_COLOR,
                color=TEXT_COLOR,
                size_hint=(0.4,1)
            )
            btn_hire.bind(
                on_release=lambda inst, name=unit_name, cost=unit_info['cost'],
                                  stats=unit_info['stats'], image=unit_info["image"]:
                broadcast_units(name, cost, None, army_hire, image, stats)
            )

        control_panel.add_widget(btn_hire)

        # Вставляем контроллеры в карточку и в карусель
        card.add_widget(control_panel)
        carousel.add_widget(slide)
        card.add_widget(body)
        card.add_widget(header)
        card.add_widget(cost_container)
        slide.add_widget(card)

    # Добавляем стрелки прокрутки
    arrow_size = dp(60)
    arrow_right = Image(
        source='files/pict/right.png',
        size_hint=(None, None),
        size=(arrow_size, arrow_size),
        pos_hint={'center_y': 0.5, 'right': 1.27},
        allow_stretch=True,
        keep_ratio=True,
        mipmap=True
    )

    def on_arrow_right(instance, touch):
        if instance.collide_point(*touch.pos):
            carousel.load_next()
            animate_arrow_click(arrow_right)

    arrow_right.bind(on_touch_down=on_arrow_right)

    right_container.add_widget(carousel)
    right_container.add_widget(arrow_right)

    # Анимация для стрелок
    def animate_arrow_click(arrow):
        anim = (
                Animation(size=(dp(65), dp(65)), duration=0.1, t='in_out_elastic') +
                Animation(size=(dp(60), dp(60)), duration=0.2, t='in_out_elastic')
        )
        anim.start(arrow)

    # Мигание правой стрелки
    def blink_arrow(instance, duration=0.5):
        anim = Animation(opacity=0.3, duration=duration) + Animation(opacity=1.0, duration=duration)
        anim.repeat = True
        anim.start(instance)

    blink_arrow(arrow_right)

    # Сборка интерфейса
    main_box.add_widget(left_space)
    main_box.add_widget(right_container)

    float_layout = FloatLayout(size_hint=(1, 1))
    float_layout.add_widget(main_box)

    # Кнопка закрытия
    close_icon = Image(
        source='files/pict/close.png',
        size_hint=(None, None),
        size=(dp(60), dp(60)),
        pos_hint={'top': 0.85, 'right': 1.18},
        allow_stretch=True,
        keep_ratio=True,
        mipmap=True,
        color=(1, 1, 1, 0.9)
    )

    def on_close_press(instance, touch):
        if instance.collide_point(*touch.pos):
            game_area.clear_widgets()
            animate_arrow_click(instance)

    close_icon.bind(on_touch_down=on_close_press)
    float_layout.add_widget(close_icon)

    game_area.add_widget(float_layout)


def broadcast_units(unit_name, unit_cost, quantity_input, army_hire, image, unit_stats):
    try:
        # Если input передан — берём оттуда, иначе — один юнит
        if quantity_input is not None:
            qty_text = quantity_input.text.strip()
            quantity = int(qty_text) if qty_text else 0
        else:
            quantity = 1

        if quantity <= 0:
            raise ValueError("Количество должно быть положительным числом")

        army_hire.hire_unit(
            unit_name=unit_name,
            unit_cost=unit_cost,
            quantity=quantity,
            unit_stats=unit_stats,
            unit_image=image
        )

    except ValueError as e:
        show_army_message(
            title="Ошибка",
            message=f"[color=#FF0000]{str(e) or 'Введите корректное число!'}[/color]"
        )

def show_army_message(title, message):
    popup = Popup(
        title=title,
        content=Label(
            text=message,
            markup=True,
            font_size=dp(18),
            color=TEXT_COLOR),
        size_hint=(None, None),
        size=(dp(300), dp(200)),
        background_color=BACKGROUND_COLOR)
    popup.open()

def set_font_size(relative_size):
    """Вычисляет размер шрифта относительно размера окна"""
    from kivy.core.window import Window
    return Window.width * relative_size

#---------------------------------------------------------------
class StyledButton(Button):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        with self.canvas.before:
            Color(0.2, 0.6, 0.8, 1)  # Основной цвет кнопки
            self.rect = RoundedRectangle(radius=[20], size=self.size, pos=self.pos)
        self.bind(pos=self.update_rect, size=self.update_rect)

    def update_rect(self, *args):
        self.rect.pos = self.pos
        self.rect.size = self.size
        # Фиксируем радиус закругления
        self.rect.radius = [20]

    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos):
            # Сохраняем радиус при анимации
            self.rect.size = (self.size[0] - 5, self.size[1] - 5)
            self.rect.radius = [20]  # Форсируем обновление радиуса
        return super().on_touch_down(touch)

    def on_touch_up(self, touch):
        if self.collide_point(*touch.pos):
            self.rect.size = self.size
            self.rect.radius = [20]  # Форсируем обновление радиуса
        return super().on_touch_up(touch)