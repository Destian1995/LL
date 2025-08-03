from db_lerdon_connect import *
def format_number(number):
    """Форматирует число с добавлением приставок (тыс., млн., млрд., трлн., квадр., квинт., секст., септил., октил., нонил., децил., андец.)"""
    if not isinstance(number, (int, float)):
        return str(number)
    if number == 0:
        return "0"

    absolute = abs(number)
    sign = -1 if number < 0 else 1

    if absolute >= 1_000_000_000_000_000_000_000_000_000_000_000_000:  # 1e36
        return f"{sign * absolute / 1e36:.1f} андец."
    elif absolute >= 1_000_000_000_000_000_000_000_000_000_000_000:  # 1e33
        return f"{sign * absolute / 1e33:.1f} децил."
    elif absolute >= 1_000_000_000_000_000_000_000_000_000_000:  # 1e30
        return f"{sign * absolute / 1e30:.1f} нонил."
    elif absolute >= 1_000_000_000_000_000_000_000_000_000:  # 1e27
        return f"{sign * absolute / 1e27:.1f} октил."
    elif absolute >= 1_000_000_000_000_000_000_000_000:  # 1e24
        return f"{sign * absolute / 1e24:.1f} септил."
    elif absolute >= 1_000_000_000_000_000_000_000:  # 1e21
        return f"{sign * absolute / 1e21:.1f} секст."
    elif absolute >= 1_000_000_000_000_000_000:  # 1e18
        return f"{sign * absolute / 1e18:.1f} квинт."
    elif absolute >= 1_000_000_000_000_000:  # 1e15
        return f"{sign * absolute / 1e15:.1f} квадр."
    elif absolute >= 1_000_000_000_000:  # 1e12
        return f"{sign * absolute / 1e12:.1f} трлн."
    elif absolute >= 1_000_000_000:  # 1e9
        return f"{sign * absolute / 1e9:.1f} млрд."
    elif absolute >= 1_000_000:  # 1e6
        return f"{sign * absolute / 1e6:.1f} млн."
    elif absolute >= 1_000:  # 1e3
        return f"{sign * absolute / 1e3:.1f} тыс."
    else:
        return f"{number}"

# --- Вспомогательные функции ---

def load_artifacts_from_db(faction):
    """Загружает список артефактов из таблицы artifacts."""
    artifacts = []
    try:
        cursor = faction.conn.cursor()
        # Добавлено поле cost в SELECT
        cursor.execute('''
            SELECT id, name, attack, defense, health, army_consumption,
                   crystal_bonus, coins_bonus, workers_bonus,
                   season_name, season_bonus_multiplier, image_url, cost, artifact_type
            FROM artifacts
        ''')
        rows = cursor.fetchall()
        for row in rows:
            artifact = {
                "id": row[0],
                "name": row[1],
                "attack": row[2] if row[2] is not None else 0,
                "defense": row[3] if row[3] is not None else 0,
                "health": row[4] if row[4] is not None else 0,
                "army_consumption": row[5] if row[5] is not None else 0,
                "crystal_bonus": row[6] if row[6] is not None else 0,
                "coins_bonus": row[7] if row[7] is not None else 0,
                "workers_bonus": row[8] if row[8] is not None else 0,
                "season_name": row[9] if row[9] is not None else "", # Может быть пустой строкой
                "season_bonus_multiplier": row[10] if row[10] is not None else 1.0,
                "image_url": row[11] if row[11] is not None else "files/pict/artifacts/default.png",
                "cost": row[12] if row[12] is not None else 0,
                "artifact_type": row[13] if row[13] is not None else -1
            }
            #print(f'Загруженный артефакт:{artifact}')
            stats = [
                artifact['attack'], artifact['defense'], artifact['health'],
                artifact['army_consumption'], artifact['crystal_bonus'],
                artifact['coins_bonus'], artifact['workers_bonus']
            ]
            if any(stat != 0 for stat in stats):
                artifacts.append(artifact)
    except sqlite3.Error as e:
        print(f"Ошибка при загрузке артефактов: {e}")
    return artifacts

def load_hero_equipment_from_db(faction):
    """
    Загружает текущую экипировку героя.
    Предполагается существование таблицы hero_equipment
    с полями: faction_name, slot_type, artifact_id.
    slot_type: 'weapon', 'boots', 'armor', 'helmet', 'accessory'
    """
    equipment = {}
    try:
        cursor = faction.conn.cursor()
        cursor.execute('''
            SELECT slot_type, artifact_id
            FROM hero_equipment
            WHERE faction_name = ?
        ''', (faction.faction,))
        rows = cursor.fetchall()
        for slot_type, artifact_id in rows:
            equipment[slot_type] = artifact_id
    except sqlite3.Error as e:
        print(f"Ошибка при загрузке экипировки героя: {e}")
    return equipment

def save_hero_equipment_to_db(faction, slot_type, artifact_id):
    """
    Сохраняет/обновляет экипировку героя в БД.
    """
    try:
        cursor = faction.conn.cursor()
        if artifact_id is None:
            # Удаление записи, если artifact_id None
            cursor.execute('''
                 DELETE FROM hero_equipment
                 WHERE faction_name = ? AND slot_type = ?
             ''', (faction.faction, slot_type))
        else:
            # Используем INSERT OR REPLACE для обновления или вставки
            cursor.execute('''
                INSERT OR REPLACE INTO hero_equipment (faction_name, slot_type, artifact_id)
                VALUES (?, ?, ?)
            ''', (faction.faction, slot_type, artifact_id))
        faction.conn.commit()
    except sqlite3.Error as e:
        print(f"Ошибка при сохранении экипировки героя: {e}")
        faction.conn.rollback()

def load_hero_image_from_db(faction):
    """
    Загружает изображение героя из таблицы garrisons, предварительно проверив faction героя через таблицу units.
    """
    try:
        cursor = faction.conn.cursor()

        # Сначала определяем faction героя через таблицу units и сравниваем с faction игрока
        cursor.execute('''
            SELECT DISTINCT g.unit_image FROM garrisons g
            LEFT JOIN units u ON g.unit_name = u.unit_name
            WHERE u.faction = ? AND u.unit_class = "3"
            LIMIT 1
        ''', (faction.faction,))  # Добавлена запятая здесь
        row = cursor.fetchone()
        print('Изображение героя:', row)
        if row and row[0]:
            return row[0]
        else:
            return "files/pict/garrisons/default_hero.png"

    except sqlite3.Error as e:
        print(f"Ошибка при загрузке изображения героя: {e}")
        return "files/pict/garrisons/default_hero.png"

def format_artifact_description(artifact):
    """
    Формирует строку описания артефакта на основе его характеристик.
    """
    stat_map = {
        'attack': 'Атака',
        'defense': 'Защита',
        'health': 'Здоровье',
        'army_consumption': 'Содержание армии',
        'crystal_bonus': 'Бонус кристаллов',
        'coins_bonus': 'Бонус монет',
        'workers_bonus': 'Рабочие'
    }
    stats = []
    for key, label in stat_map.items():
        value = artifact.get(key, 0)
        if value and value != 0:
            # Учитываем множитель сезона, если он не равен 1.0
            multiplier = artifact.get('season_bonus_multiplier', 1.0)
            if multiplier != 1.0:
                effective_value = value * multiplier
                # Округляем до целого, если результат целый, иначе до 1 знака после запятой
                if effective_value.is_integer():
                    effective_value = int(effective_value)
                else:
                    effective_value = round(effective_value, 1)
                stats.append(f"{label} +{effective_value}%")
            else:
                stats.append(f"{label} +{value}%")

    if not stats:
        return None  # Пропустить артефакт, если все характеристики нулевые

    # Формируем суффикс для времени действия бонуса
    season = artifact.get('season_name')
    if season:
        suffix = f"Сезон артефакта: {season}"
    else:
        suffix = "Всегда"

    return f"{', '.join(stats)} {suffix}"

def create_artifact_button_style(btn):
    """Создает стиль для строки артефакта."""
    with btn.canvas.before:
        Color(0.2, 0.2, 0.2, 1) # Темно-серый фон
        btn.rect = RoundedRectangle(pos=btn.pos, size=btn.size, radius=[10])
    def update_rect(instance, value):
        instance.rect.pos = instance.pos
        instance.rect.size = instance.size
    btn.bind(pos=update_rect, size=update_rect)
    return btn

# --- Основная функция открытия попапа ---
def open_artifacts_popup(faction):
    """
    Открывает Popup с артефактами и экипировкой героя.
    :param faction: Экземпляр класса Faction
    """
    # --- Загрузка данных ---
    artifacts_list = load_artifacts_from_db(faction)
    hero_equipment = load_hero_equipment_from_db(faction)
    hero_image_path = load_hero_image_from_db(faction)

    # --- Создание Popup ---
    popup_layout = BoxLayout(orientation='horizontal', padding=dp(10), spacing=dp(10))

    # --- Левая часть: Список артефактов ---
    left_panel = BoxLayout(orientation='vertical', size_hint=(0.5, 1))

    # --- Фильтры ---
    # --- Контейнер для фильтров ---
    filters_container = BoxLayout(orientation='vertical', size_hint_y=None, height=dp(120), spacing=dp(5))
    # Инициализируем состояния фильтров
    filter_states = {
        'season_influence': 'all', # 'all', 'has_influence', 'no_influence'
        'artifact_type': 'all',   # 'all', 'weapon', 'boots', 'armor', 'helmet', 'accessory'
        'cost_sort': 'all'       # 'all',
    }

    # --- Функция для обновления отображаемого списка артефактов ---
    def update_artifact_list(*args):
        """Обновляет список артефактов на основе текущих фильтров."""
        # Очистка текущего списка
        artifacts_list_layout.clear_widgets()

        # Применение фильтров
        filtered_artifacts = []
        for artifact in artifacts_list:
            # Фильтр по влиянию сезона
            season_ok = True
            if filter_states['season_influence'] == 'has_influence':
                # Считаем, что сезон влияет, если поле season_name не пустое и не None
                season_name = artifact.get('season_name')
                season_ok = season_name is not None and season_name != ""
            elif filter_states['season_influence'] == 'no_influence':
                # Считаем, что сезон НЕ влияет, если поле season_name пустое или None
                season_name = artifact.get('season_name')
                season_ok = season_name is None or season_name == ""

            # Фильтр по типу артефакта
            type_ok = True
            if filter_states['artifact_type'] != 'all':
                # Предположим, у артефакта есть поле 'slot_type'
                type_ok = artifact.get('artifact_type') == filter_states['artifact_type']

            # Фильтр по стоимости
            cost_ok = True
            if filter_states['cost_sort'] == 'asc':
                filtered_artifacts.sort(key=lambda art: art.get('cost', 0))
            elif filter_states['cost_sort'] == 'desc':
                filtered_artifacts.sort(key=lambda art: art.get('cost', 0), reverse=True)


            if season_ok and type_ok and cost_ok:
                filtered_artifacts.append(artifact)

        # --- Заполнение таблицы отфильтрованными артефактами ---
        for artifact in filtered_artifacts:
            description = format_artifact_description(artifact)
            if not description:  # Пропустить, если описание пустое (все бонусы 0)
                continue
            # --- Контейнер строки артефакта ---
            artifact_row_container = BoxLayout(
                orientation='horizontal',
                size_hint_y=None,
                height=dp(90),
                padding=(dp(5), dp(5)),
                spacing=dp(10)
            )

            # --- Контейнер информации об артефакте ---
            artifact_info_container = BoxLayout(
                orientation='vertical',
                size_hint_x=0.75
            )
            name_label = Label(
                text=artifact['name'],
                halign='left',
                valign='middle',
                font_size='16sp',
                bold=True,
                size_hint_y=None,
                height=dp(25)
            )
            name_label.bind(size=name_label.setter('text_size'))
            stats_label = Label(
                text=description,
                halign='left',
                valign='top',
                font_size='14sp',
                bold=True,
                color=(0.8, 0.8, 0.8, 1),
                size_hint_y=None,
                height=dp(50)
            )
            stats_label.bind(size=stats_label.setter('text_size'))
            artifact_info_container.add_widget(name_label)
            artifact_info_container.add_widget(stats_label)

            # --- Кнопка "Купить" ---
            # Получаем стоимость артефакта (по ключу 'cost'), если ключа нет, используем 0 по умолчанию
            cost = artifact.get('cost', 0)
            # Форматируем число стоимости
            formatted_cost = format_number(cost)  # <-- Теперь правильно: передаем число в format_number
            buy_button = Button(
                text=f"Купить\n({formatted_cost})",
                size_hint_x=None,
                width=dp(90),
                height=dp(60),
            )

            style_buy_button(buy_button) # Предполагается, что эта функция определена в вашем коде

            def make_buy_handler(art_data):
                def on_buy(instance):
                    print(f"Покупка артефакта: {art_data['name']} (ID: {art_data['id']})")
                    slot_equipped = False
                    # 0 - Оружие, 1 - Головные уборы, 2 - Сапоги, 3 - Туловище, 4 - Аксессуары
                    for slot_type in ['0', '2', '3', '1', '4']:
                        if slot_type not in hero_equipment or hero_equipment[slot_type] is None:
                            save_hero_equipment_to_db(faction, slot_type, art_data['id'])
                            hero_equipment[slot_type] = art_data['id']
                            update_equipment_slot(slot_type, art_data)
                            print(f"Артефакт {art_data['name']} экипирован в {slot_type}")
                            slot_equipped = True
                            break
                    if not slot_equipped:
                        print(f"Нет свободных слотов для артефакта {art_data['name']}")
                return on_buy

            buy_button.bind(on_release=make_buy_handler(artifact))

            # --- Добавление виджетов в строку ---
            artifact_row_container.add_widget(artifact_info_container)
            button_wrapper = BoxLayout(size_hint_x=None, width=dp(90), padding=(0, dp(15), 0, dp(15)))
            button_wrapper.add_widget(buy_button)
            artifact_row_container.add_widget(button_wrapper)

            # --- Добавить строку в таблицу ---
            artifacts_list_layout.add_widget(artifact_row_container)
            # artifact_widgets[artifact['id']] = artifact_row_container # Можно сохранить, если нужно

        # Обновляем высоту контейнера
        artifacts_list_layout.height = len(artifacts_list_layout.children) * dp(90) + (len(artifacts_list_layout.children) - 1) * dp(5) if artifacts_list_layout.children else dp(1)

    # --- Виджеты фильтров ---
    # 1. Фильтр по сезону
    season_filter_layout = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(30))
    season_filter_layout.add_widget(Label(text="Сезон:", size_hint_x=None, width=dp(60), halign='left'))
    season_spinner = Spinner(
        text='Все',
        values=('Все', 'Есть влияние', 'Нет влияния'),
        size_hint=(1, None),
        height=dp(30)
    )
    def on_season_spinner_select(spinner, text):
        mapping = {'Все': 'all', 'Есть влияние': 'has_influence', 'Нет влияния': 'no_influence'}
        filter_states['season_influence'] = mapping.get(text, 'all')
        update_artifact_list()
    season_spinner.bind(text=on_season_spinner_select)
    season_filter_layout.add_widget(season_spinner)
    filters_container.add_widget(season_filter_layout)

    # 2. Фильтр по типу
    type_filter_layout = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(30))
    type_filter_layout.add_widget(Label(text="Тип:", size_hint_x=None, width=dp(60), halign='left'))
    type_spinner = Spinner(
        text='Все',
        values=('Все', 'Оружие', 'Сапоги', 'Туловище', 'Голова', 'Аксессуар'),
        size_hint=(1, None),
        height=dp(30)
    )

    def on_type_spinner_select(spinner, text):
        # Используем числовые значения для фильтрации, соответствующие artifact_type в БД
        # 0 - Оружие, 1 - Головные уборы, 2 - Сапоги, 3 - Туловище, 4 - Аксессуары
        mapping = {
            'Все': 'all',
            'Оружие': 0,
            'Голова': 1,
            'Сапоги': 2,
            'Туловище': 3,
            'Аксессуар': 4
        }
        # filter_states['artifact_type'] должен быть числом или 'all'
        selected_value = mapping.get(text, 'all')
        filter_states['artifact_type'] = selected_value
        update_artifact_list()
    type_spinner.bind(text=on_type_spinner_select)
    type_filter_layout.add_widget(type_spinner)
    filters_container.add_widget(type_filter_layout)

    # 3. Фильтр по стоимости (изменен на сортировку)
    cost_filter_layout = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(30))
    cost_filter_layout.add_widget(Label(text="Цена:", size_hint_x=None, width=dp(60), halign='left'))
    # Изменяем значения спиннера для сортировки
    cost_spinner = Spinner(
        text='Все',
        values=('Все', 'По возрастанию', 'По убыванию'), # <-- ИЗМЕНЕНЫ значения
        size_hint=(1, None),
        height=dp(30)
    )
    def on_cost_spinner_select(spinner, text):
        # Используем 'asc' и 'desc' для сортировки
        mapping = {'Все': 'all', 'По возрастанию': 'asc', 'По убыванию': 'desc'}
        filter_states['cost_sort'] = mapping.get(text, 'all') # ИЗМЕНЕНО с cost_range на cost_sort
        update_artifact_list()
    cost_spinner.bind(text=on_cost_spinner_select)
    cost_filter_layout.add_widget(cost_spinner)
    filters_container.add_widget(cost_filter_layout)

    # Добавляем контейнер с фильтрами на левую панель
    left_panel.add_widget(filters_container)

    # --- Заголовок списка артефактов ---
    left_panel.add_widget(Label(text="Артефакты", size_hint_y=None, height=dp(40), bold=True, font_size='18sp'))

    # --- Список артефактов (ScrollView) ---
    scroll_view = ScrollView(do_scroll_x=False)
    artifacts_list_layout = BoxLayout(orientation='vertical', size_hint_y=None, spacing=dp(5))
    # Привязка высоты
    artifacts_list_layout.bind(minimum_height=artifacts_list_layout.setter('height'))
    scroll_view.add_widget(artifacts_list_layout)
    left_panel.add_widget(scroll_view)
    # --- Создание виджетов для артефактов ---
    artifact_widgets = {}
    equipment_slots = {}  # Ссылки на виджеты слотов будут храниться здесь

    # --- Функция для стилизации кнопки "Купить" ---
    def style_buy_button(button):
        """Применяет стиль к кнопке 'Купить'."""
        # Пример стиля, вы можете настроить его по своему вкусу
        button.background_color = (0.2, 0.6, 0.8, 1)  # Сине-зеленый
        button.color = (1, 1, 1, 1)  # Белый текст
        button.bold = True
        # Можно также изменить background_normal и background_down для картинок
        return button

    # --- Заполнение таблицы артефактами ---
    for artifact in artifacts_list:
        description = format_artifact_description(artifact)
        if not description:  # Пропустить, если описание пустое (все бонусы 0)
            continue

        # --- Контейнер строки артефакта ---
        artifact_row_container = BoxLayout(
            orientation='horizontal',
            size_hint_y=None,
            # height будет рассчитана динамически или установлена фиксированная
            height=dp(90),  # Увеличил высоту для лучшего размещения
            padding=(dp(5), dp(5)),
            spacing=dp(10)  # Увеличил отступ между информацией и кнопкой
        )
        # Применяем общий стиль к строке, если нужно
        # artifact_row_container = create_artifact_button_style(artifact_row_container)

        # --- Контейнер информации об артефакте ---
        artifact_info_container = BoxLayout(
            orientation='vertical',
            size_hint_x=0.75  # Занимает 75% ширины строки
        )

        # Название артефакта
        name_label = Label(
            text=artifact['name'],
            halign='left',
            valign='middle',
            font_size='16sp',
            bold=True,
            size_hint_y=None,
            height=dp(25)
        )
        name_label.bind(size=name_label.setter('text_size'))

        # Характеристики артефакта
        stats_label = Label(
            text=description,
            halign='left',
            valign='top',
            font_size='14sp',  # <-- Увеличенный размер шрифта
            bold=True,  # <-- Сделан жирным
            color=(0.8, 0.8, 0.8, 1),
            size_hint_y=None,
            height=dp(50)  # <-- Возможно, стоит немного увеличить высоту, чтобы текст помещался
        )
        stats_label.bind(size=stats_label.setter('text_size'))

        artifact_info_container.add_widget(name_label)
        artifact_info_container.add_widget(stats_label)

        # --- Кнопка "Купить" ---
        # Получаем стоимость артефакта (по ключу 'cost'), если ключа нет, используем 0 по умолчанию
        cost = artifact.get('cost', 0)
        # Форматируем число стоимости
        formatted_cost = format_number(cost)  # <-- Теперь правильно: передаем число в format_number
        buy_button = Button(
            text=f"Купить\n({formatted_cost})",
            size_hint_x=None,
            width=dp(90),
            height=dp(60),
        )
        # Применяем стиль к кнопке
        style_buy_button(buy_button)

        # Обработчик нажатия кнопки "Купить"
        def make_buy_handler(art_data):
            def on_buy(instance):
                """Обработчик нажатия кнопки 'Купить'."""
                print(f"Покупка артефакта: {art_data['name']} (ID: {art_data['id']})")
                # --- Здесь должна быть логика покупки ---
                # Например: проверка денег, вызов save_hero_equipment_to_db или другой функции

                # Для примера, просто экипируем в первый свободный подходящий слот
                # Предположим, артефакт имеет поле 'slot_type' или мы определяем его по имени
                # Если такого поля нет, нужно определить логику определения слота
                # Например, можно передать slot_type как аргумент или определить его внутри on_buy

                # Простая логика: экипируем в первый свободный слот из списка
                slot_equipped = False
                # 0 - Оружие, 1 - Головные уборы, 2 - Сапоги, 3 - Туловище, 4 - Аксессуары
                for slot_type in ['0', '2', '3', '1', '4']:
                    if slot_type not in hero_equipment or hero_equipment[slot_type] is None:
                        save_hero_equipment_to_db(faction, slot_type, art_data['id'])
                        hero_equipment[slot_type] = art_data['id']
                        # Обновляем виджет слота
                        update_equipment_slot(slot_type, art_data)
                        print(f"Артефакт {art_data['name']} экипирован в {slot_type}")
                        slot_equipped = True
                        break  # Экипировали и вышли

                if not slot_equipped:
                    print(f"Нет свободных слотов для артефакта {art_data['name']}")

                # --- Конец логики покупки ---

            return on_buy

        buy_button.bind(on_release=make_buy_handler(artifact))

        # --- Добавление виджетов в строку ---
        artifact_row_container.add_widget(artifact_info_container)
        # Добавляем виджет с кнопкой, чтобы центрировать кнопку по вертикали
        button_wrapper = BoxLayout(size_hint_x=None, width=dp(90), padding=(0, dp(15), 0, dp(15)))
        button_wrapper.add_widget(buy_button)
        artifact_row_container.add_widget(button_wrapper)

        # --- Добавить строку в таблицу ---
        artifacts_list_layout.add_widget(artifact_row_container)
        artifact_widgets[artifact['id']] = artifact_row_container  # Сохраняем ссылку

    # --- Обновление ScrollView ---
    artifacts_list_layout.bind(minimum_height=artifacts_list_layout.setter('height'))


    # --- Правая часть: Герой и экипировка ---
    right_panel = FloatLayout(size_hint=(0.5, 1))

    # --- Загрузка изображения героя ---
    try:
        hero_image_width = dp(450)
        hero_image_height = dp(450)
        hero_image = Image(source=hero_image_path, size_hint=(None, None), size=(hero_image_width, hero_image_height))
        hero_image_size = (hero_image_width, hero_image_height)

        hero_image.pos_hint = {'center_x': 0.5, 'center_y': 0.5}
        right_panel.add_widget(hero_image)
    except Exception as e:
        print(f"Ошибка загрузки изображения героя {hero_image_path}: {e}")
        # Создаем placeholder, если изображение не загрузилось
        hero_placeholder = Label(
            text="[b]Изображение\nГероя[/b]",
            markup=True,
            halign='center',
            valign='middle'
        )
        hero_placeholder.size_hint = (None, None)
        hero_placeholder.size = (dp(450), dp(450))
        # Устанавливаем центр, учитывая возможную задержку в получении размеров right_panel
        hero_placeholder.center = (dp(100), dp(100))  # Значение по умолчанию

        # Попробуем обновить позицию позже, если right_panel уже готов
        def set_placeholder_center(*args):
            if hasattr(right_panel, 'center_x') and hasattr(right_panel, 'center_y'):
                hero_placeholder.center_x = right_panel.center_x
                hero_placeholder.center_y = right_panel.center_y

        right_panel.bind(parent=set_placeholder_center)  # Привязываем к родителю, как пример
        right_panel.add_widget(hero_placeholder)
        # hero_image = hero_placeholder # Не нужно, если мы не используем hero_image ниже

    slot_size = (dp(90), dp(90))

    # --- Функция обновления слота экипировки ---
    def update_equipment_slot(slot_type, artifact_data=None):
        """Обновляет виджет слота экипировки."""
        if slot_type in equipment_slots:
            slot_widget = equipment_slots[slot_type]
            slot_widget.clear_widgets()
            if artifact_data:
                try:
                    img_source = artifact_data.get('image_url')
                    if not img_source:
                        img_source = "files/pict/artifacts/default.png"  # Путь по умолчанию
                    slot_image = Image(source=img_source, allow_stretch=True, keep_ratio=True)
                    slot_widget.add_widget(slot_image)
                except Exception as e:
                    print(f"Ошибка загрузки изображения для слота {slot_type}: {e}")
                    # Если изображение не загрузилось, показываем знак вопроса
                    slot_widget.add_widget(Label(text="?", font_size='20sp'))
            else:
                # Если слот пуст, показываем тип слота
                slot_widget.add_widget(Label(text=f"[{slot_type[:3].upper()}]", markup=True, font_size='10sp'))

    # --- Создание слотов экипировки ---
    for slot_type in ['0', '2', '3', '1', '4']:
        # Создаем виджет кнопки для слота
        slot_widget = Button(
            size_hint=(None, None),
            size=slot_size,
            pos=(0, 0),  # Позиция будет установлена позже
            background_color=(0.3, 0.3, 0.3, 1),  # Серый фон по умолчанию
            background_normal='',  # Убираем стандартный фон
            # text=f"[{slot_type[:3].upper()}]" # Можно добавить текст по умолчанию
        )
        # Добавляем скругленные углы
        with slot_widget.canvas.before:
            from kivy.graphics import Color, RoundedRectangle
            Color(0.4, 0.4, 0.4, 1)  # Цвет рамки/фона
            slot_widget.rect = RoundedRectangle(pos=slot_widget.pos, size=slot_widget.size, radius=[8])

        # Обновляем позицию и размер прямоугольника при изменении виджета
        def update_slot_rect(instance, value):
            instance.rect.pos = instance.pos
            instance.rect.size = instance.size

        slot_widget.bind(pos=update_slot_rect, size=update_slot_rect)

        # --- Добавление подписи слота ---
        # Словарь для сопоставления типа слота с его подписью
        # 0 - Оружие, 1 - Головные уборы, 2 - Сапоги, 3 - Туловище, 4 - Аксессуары
        slot_labels = {
            '0': 'Оружие',
            '2': 'Сапоги',
            '3': 'Туловище',
            '1': 'Голова',
            '4': 'Аксессуар'
        }
        # Создаем Label с подписью
        slot_label = Label(
            text=slot_labels.get(slot_type, slot_type),  # Получаем подпись или используем тип слота по умолчанию
            color=(1, 1, 1, 1),  # Белый цвет текста
            font_size='10sp',  # Размер шрифта
            halign='center',
            valign='middle'
        )
        slot_label.bind(size=slot_label.setter('text_size'))  # Позволяет выравнивание текста
        # Добавляем Label в slot_widget
        slot_widget.add_widget(slot_label)

        # Инициализация слота текущим артефактом (если есть)
        artifact_id_in_slot = hero_equipment.get(slot_type)
        artifact_data_in_slot = next((a for a in artifacts_list if a['id'] == artifact_id_in_slot),
                                     None) if artifact_id_in_slot else None
        update_equipment_slot(slot_type, artifact_data_in_slot)

        # Добавляем виджет слота на правую панель
        right_panel.add_widget(slot_widget)
        # Сохраняем ссылку на слот для последующего обновления
        equipment_slots[slot_type] = slot_widget

    # --- Сборка основного макета ---
    popup_layout.add_widget(left_panel)
    popup_layout.add_widget(right_panel)

    # --- Создание и открытие Popup ---
    artifacts_popup = Popup(
        title="Артефакты и Герой",
        content=popup_layout,
        size_hint=(0.95, 0.95),
        title_align='center',
        separator_color=(0.5, 0.3, 0.7, 1)  # Фиолетовый разделитель
    )

    # --- Функция позиционирования слотов ---
    def position_slots(dt):
        """Позиционирует слоты экипировки относительно центра правой панели."""
        # Проверка, готова ли панель (имеет размеры)
        if not right_panel or not hasattr(right_panel, 'width') or right_panel.width == 0:
            return  # Ждем, пока панель не будет готова
        right_panel_width = right_panel.width
        right_panel_height = right_panel.height
        right_panel_x = right_panel.x
        right_panel_y = right_panel.y
        center_x = right_panel_x + right_panel_width / 2
        center_y = right_panel_y + right_panel_height / 2

        # --- Скорректированные позиции ---
        # Добавляем небольшой отступ (например, dp(10)) между героем и слотом.
        half_hero_width = hero_image_size[0] / 2
        half_slot_width = slot_size[0] / 2
        min_distance_from_center = half_hero_width + half_slot_width + dp(10)  # Минимальное расстояние до центра слота

        # Можно использовать это расстояние или немного больше для esthetics
        distance_horizontal = max(dp(200),
                                  min_distance_from_center)  # Убедимся, что не меньше dp(200) или рассчитанного значения
        distance_vertical = max(dp(200), min_distance_from_center)  # То же для вертикали
        distance_above_head = distance_vertical + dp(80)  # Аксессуар немного выше, чем шлем
        # 0 - Оружие, 1 - Головные уборы, 2 - Сапоги, 3 - Туловище, 4 - Аксессуары
        slot_positions = {
            # Слева от героя (Оружие)
            '0': (center_x - distance_horizontal, center_y - slot_size[1] / 2),
            # Снизу от героя (Сапоги)
            '2': (center_x - slot_size[0] / 2, center_y - distance_vertical),
            # Справа от героя (Туловище)
            '3': (center_x + distance_horizontal - slot_size[0], center_y - slot_size[1] / 2),
            # Сверху от героя (Голова)
            '1': (center_x - slot_size[0] / 2, center_y + distance_vertical - slot_size[1]),
            # Сверху справа от героя (Аксессуар)
            '4': (center_x + distance_horizontal - slot_size[0], center_y + distance_above_head - slot_size[1]),
        }
        # -------------------------------

        # Установка позиций для каждого слота
        for slot_type, pos in slot_positions.items():
            if slot_type in equipment_slots:
                equipment_slots[slot_type].pos = pos

    # Планируем позиционирование слотов
    # Приоритет -1 для выполнения как можно раньше после открытия
    Clock.schedule_once(position_slots, -1)
    # Также привязываем к событию on_open попапа на случай, если позиционирование не сработает сразу
    artifacts_popup.bind(on_open=lambda *args: Clock.schedule_once(position_slots, 0.1))

    # --- Открытие Popup ---
    artifacts_popup.open()