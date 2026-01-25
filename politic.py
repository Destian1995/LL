
from db_lerdon_connect import *


from economic import format_number
# Глобальная блокировка для работы с БД
db_lock = threading.Lock()
from nobles import show_nobles_window
from diversion import show_diversion_window

translation_dict = {
    "Север": "arkadia",
    "Эльфы": "celestia",
    "Адепты": "eteria",
    "Вампиры": "giperion",
    "Элины": "halidon",
}

# Словарь для перевода названий файлов в русскоязычные названия фракций
faction_names = {
    "arkadia_in_city": "Север",
    "celestia_in_city": "Эльфы",
    "eteria_in_city": "Адепты",
    "giperion_in_city": "Вампиры",
    "halidon_in_city": "Элины"
}

faction_names_build = {
    "arkadia_buildings_city": "Север",
    "celestia_buildings_city": "Эльфы",
    "eteria_buildings_city": "Адепты",
    "giperion_buildings_city": "Вампиры",
    "halidon_buildings_city": "Элины"
}

def transform_filename(file_path):
    path_parts = file_path.split('/')
    for i, part in enumerate(path_parts):
        for ru_name, en_name in translation_dict.items():
            if ru_name in part:
                path_parts[i] = part.replace(ru_name, en_name)
    return '/'.join(path_parts)


reverse_translation_dict = {v: k for k, v in translation_dict.items()}

def all_factions(cursor):
    """
    Выгружает список активных фракций из таблицы diplomacies.
    Возвращает уникальный список фракций, у которых статус в relationship не равен "уничтожена".
    :param cursor: Курсор для работы с базой данных
    :return: Список активных фракций
    """
    try:
        # Запрос для получения всех уникальных фракций, кроме тех, что имеют статус "уничтожена"
        query = """
            SELECT DISTINCT faction 
            FROM (
                SELECT faction1 AS faction, relationship FROM diplomacies
                UNION
                SELECT faction2 AS faction, relationship FROM diplomacies
            ) AS all_factions
            WHERE relationship != 'уничтожена' AND faction != 'Мятежники'
        """
        cursor.execute(query)
        factions = [row[0] for row in cursor.fetchall()]
        return factions
    except sqlite3.Error as e:
        print(f"Ошибка при получении списка активных фракций: {e}")
        return []

# Функция для расчета базового размера шрифта
def calculate_font_size():
    """Рассчитывает базовый размер шрифта на основе высоты окна."""
    base_height = 720  # Базовая высота окна для нормального размера шрифта
    default_font_size = 16  # Базовый размер шрифта
    scale_factor = Window.height / base_height  # Коэффициент масштабирования
    return max(8, int(default_font_size * scale_factor))  # Минимальный размер шрифта — 8

def get_relation_level(conn, f1, f2):
    cursor = conn.cursor()
    cursor.execute("""
        SELECT relationship FROM relations 
        WHERE (faction1=? AND faction2=?) OR (faction1=? AND faction2=?)
    """, (f1, f2, f2, f1))
    row = cursor.fetchone()
    return int(row[0]) if row else 0


def calculate_coefficient(rel):
    rel = int(rel)
    if rel < 15:
        return 0
    if 15 <= rel < 25:
        return 0.1
    if 25 <= rel < 35:
        return 0.4
    if 35 <= rel < 54:
        return 0.95
    if 54 <= rel < 65:
        return 1.5
    if 65 <= rel < 75:
        return 2
    if 75 <= rel < 90:
        return 3.1
    if 90 <= rel <= 100:
        return 4
    return 0








# Кастомная кнопка с анимациями и эффектами
class StyledButton(ButtonBehavior, BoxLayout):
    def __init__(self, text, font_size, button_color, text_color, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        self.size_hint = (1, None)
        self.height = font_size * 3  # Высота кнопки зависит от размера шрифта
        self.padding = [font_size // 2, font_size // 4]  # Отступы внутри кнопки
        self.normal_color = button_color
        self.hover_color = [c * 0.9 for c in button_color]  # Темнее при наведении
        self.pressed_color = [c * 0.8 for c in button_color]  # Еще темнее при нажатии
        self.current_color = self.normal_color

        with self.canvas.before:
            self.color = Color(*self.current_color)
            self.rect = RoundedRectangle(size=self.size, pos=self.pos, radius=[font_size // 2])

        self.bind(pos=self.update_rect, size=self.update_rect)

        self.label = Label(
            text=text,
            font_size=font_size * 1.2,
            color=text_color,
            bold=True,
            halign='center',
            valign='middle'
        )
        self.label.bind(size=self.label.setter('text_size'))
        self.add_widget(self.label)

        self.bind(on_press=self.on_press_effect, on_release=self.on_release_effect)
        self.bind(on_touch_move=self.on_hover, on_touch_up=self.on_leave)

    def update_rect(self, *args):
        self.rect.pos = self.pos
        self.rect.size = self.size

    def on_press_effect(self, instance):
        """Эффект затемнения при нажатии"""
        anim = Animation(current_color=self.pressed_color, duration=0.1)
        anim.start(self)
        self.update_color()

    def on_release_effect(self, instance):
        """Возвращаем цвет после нажатия"""
        anim = Animation(current_color=self.normal_color, duration=0.1)
        anim.start(self)
        self.update_color()

    def on_hover(self, instance, touch):
        """Эффект при наведении"""
        if self.collide_point(*touch.pos):
            anim = Animation(current_color=self.hover_color, duration=0.1)
            anim.start(self)
            self.update_color()

    def on_leave(self, instance, touch):
        """Возвращаем цвет, если курсор ушел с кнопки"""
        if not self.collide_point(*touch.pos):
            anim = Animation(current_color=self.normal_color, duration=0.1)
            anim.start(self)
            self.update_color()

    def update_color(self):
        """Обновляет цвет фона"""
        self.canvas.before.clear()
        with self.canvas.before:
            Color(*self.current_color)
            self.rect = RoundedRectangle(size=self.size, pos=self.pos, radius=[self.height // 4])



def calculate_peace_army_points(conn, faction):
    """
    Вычисляет общую силу армии фракции по новой логике:
    - Класс 1: базовая сила
    - Герои (класс 2 и 3): усиливают класс 1 умножением
    - Прочие юниты (класс 4+): просто добавляются к общей силе
    """
    cursor = conn.cursor()
    factions_data = {}

    try:
        cursor.execute("""
            SELECT g.unit_name, g.unit_count, u.attack, u.defense, u.durability, u.unit_class 
            FROM garrisons g
            JOIN units u ON g.unit_name = u.unit_name
            WHERE u.faction = ?
        """, (faction,))
        units_data = cursor.fetchall()

        # Инициализируем данные для текущей фракции
        factions_data[faction] = {
            "class_1": {"count": 0, "total_stats": 0},
            "heroes": {"total_stats": 0},   # классы 2 и 3
            "others": {"total_stats": 0}    # классы 4 и выше
        }

        for unit_name, unit_count, attack, defense, durability, unit_class in units_data:
            stats_sum = attack + defense + durability

            if unit_class == "1":
                factions_data[faction]["class_1"]["count"] += unit_count
                factions_data[faction]["class_1"]["total_stats"] += stats_sum * unit_count
            elif unit_class in ("2", "3"):
                factions_data[faction]["heroes"]["total_stats"] += stats_sum * unit_count
            else:
                factions_data[faction]["others"]["total_stats"] += stats_sum * unit_count

        # Рассчитываем силу армии
        data = factions_data[faction]
        class_1_count = data["class_1"]["count"]
        base_stats = data["class_1"]["total_stats"]
        hero_bonus = data["heroes"]["total_stats"]
        others_stats = data["others"]["total_stats"]

        total_strength = 0

        if class_1_count > 0:
            total_strength += base_stats + hero_bonus * class_1_count

        total_strength += others_stats

        return total_strength

    except Exception as e:
        print(f"Ошибка при вычислении очков армии: {e}")
        return 0



# =================================
def show_peace_form(player_faction, conn):
    """Окно формы для предложения о заключении мира (с использованием StyledButton)."""
    # Рассчитываем базовый размер шрифта
    font_size = calculate_font_size()
    button_height = font_size * 3   # Высота кнопок внутри StyledButton
    input_height = font_size * 2.5
    padding = font_size // 2
    spacing = font_size // 4
    cursor = conn.cursor()

    try:
        # Получаем текущие "военные" отношения
        cursor.execute(
            "SELECT faction2, relationship FROM diplomacies WHERE faction1 = ?",
            (player_faction,)
        )
        relations = {f: status for f, status in cursor.fetchall()}

        # Берем все активные фракции и фильтруем только те, с кем в "войне"
        cursor2 = conn.cursor()
        active_factions = all_factions(cursor2)
        available_factions = [f for f in active_factions if relations.get(f) == "война"]

        # Если нет фракций для мира
        if not available_factions:
            popup_content = BoxLayout(
                orientation='vertical',
                padding=padding,
                spacing=spacing
            )
            message_label = Label(
                text="Мы сейчас ни с кем не воюем",
                size_hint=(1, None),
                height=font_size * 2,
                font_size=font_size,
                color=(0, 1, 0, 1),  # Зеленый
                halign='center'
            )
            popup_content.add_widget(message_label)

            close_button = StyledButton(
                text="Закрыть",
                font_size=font_size * 1.2,
                button_color=[0.80, 0.20, 0.20, 1],  # Красный
                text_color=[1, 1, 1, 1]
            )
            close_button.bind(on_release=lambda _: popup.dismiss())
            popup_content.add_widget(close_button)

            popup = Popup(
                title="Заключение мира",
                content=popup_content,
                size_hint=(0.7, 0.3),
                auto_dismiss=False
            )
            popup.open()
            return

        # --- Основная форма ---
        content = BoxLayout(
            orientation='vertical',
            padding=padding,
            spacing=spacing
        )

        # Заголовок
        title = Label(
            text="Предложение о заключении мира",
            size_hint=(1, None),
            height=button_height,
            font_size=font_size * 1.5,
            color=(1, 1, 1, 1),
            bold=True,
            halign='center'
        )
        title.bind(size=lambda lbl, sz: lbl.setter('text_size')(lbl, (sz[0], None)))
        content.add_widget(title)

        # Спиннер для выбора фракции
        factions_spinner = Spinner(
            text="С какой фракцией?",
            values=available_factions,
            size_hint=(1, None),
            height=input_height,
            font_size=font_size,
            background_color=(0.2, 0.6, 1, 1),
            color=(1, 1, 1, 1),
            background_normal='',
            background_down=''
        )
        content.add_widget(factions_spinner)

        # Сообщения пользователю
        message_label = Label(
            text="",
            size_hint=(1, None),
            height=font_size * 2,
            font_size=font_size,
            color=(0, 1, 0, 1),
            halign='center'
        )
        content.add_widget(message_label)

        # Функция для вывода предупреждений
        def show_warning(text, color=(1, 0, 0, 1)):
            message_label.text = text
            message_label.color = color

        # Функция для отправки предложения
        def send_proposal(instance):
            target_faction = factions_spinner.text
            if target_faction == "С какой фракцией?":
                show_warning("Пожалуйста, выберите фракцию!", color=(1, 0, 0, 1))
                return

            # Вычисляем очки армий
            player_points = calculate_peace_army_points(conn, player_faction)
            enemy_points = calculate_peace_army_points(conn, target_faction)

            if player_points == 0 and enemy_points > 0:
                show_warning("Обойдешься. Сейчас я отыграюсь по полной.", color=(1, 0, 0, 1))
                return

            # Если у противника нет армии
            if enemy_points == 0 and player_points >= enemy_points:
                response = "Мы согласны на мир! Нам пока и воевать то нечем..."
                cursor.execute(
                    "UPDATE diplomacies SET relationship = ? WHERE faction1 = ? AND faction2 = ?",
                    ("нейтралитет", player_faction, target_faction)
                )
                cursor.execute(
                    "UPDATE diplomacies SET relationship = ? WHERE faction1 = ? AND faction2 = ?",
                    ("нейтралитет", target_faction, player_faction)
                )
                conn.commit()
                show_warning(response, color=(0, 1, 0, 1))
                return

            # Если превосходство игрока
            if player_points > enemy_points:
                superiority_percentage = ((player_points - enemy_points) / max(enemy_points, 1)) * 100
                if superiority_percentage >= 70:
                    response = "Ваша милость наконец соизволила нас пощадить.."
                elif 50 <= superiority_percentage < 70:
                    response = "Мы уже сдаемся, что Вам еще надо?..."
                elif 20 <= superiority_percentage < 50:
                    response = "У нас не осталось тех кто готов сопротивляться..."
                elif 5 <= superiority_percentage < 20:
                    response = "Это геноцид...мы врят ли когда-то сможем воевать..."
                else:
                    response = "В следующий раз мы будем лучше готовы"

                cursor.execute(
                    "UPDATE diplomacies SET relationship = ? WHERE faction1 = ? AND faction2 = ?",
                    ("нейтралитет", player_faction, target_faction)
                )
                cursor.execute(
                    "UPDATE diplomacies SET relationship = ? WHERE faction1 = ? AND faction2 = ?",
                    ("нейтралитет", target_faction, player_faction)
                )
                conn.commit()
                show_warning(response, color=(0, 1, 0, 1))

            # Если превосходство врага
            elif player_points < enemy_points:
                inferiority_percentage = ((enemy_points - player_points) / max(player_points, 1)) * 100
                if inferiority_percentage <= 15:
                    response = "Может Вы и правы, но мы еще готовы продолжать сопротивление..."
                    show_warning(response, color=(1, 1, 0, 1))
                else:
                    response = "Уже сдаетесь?! Мы еще не закончили Вас бить!"
                    show_warning(response, color=(1, 0, 0, 1))
            else:
                response = "Сейчас передохнем и в рыло дадим"
                show_warning(response, color=(1, 0, 0, 1))

        # --- Кнопочная панель ---
        button_layout = BoxLayout(
            orientation='horizontal',
            size_hint=(1, None),
            height=button_height,
            spacing=font_size // 2
        )

        send_button = StyledButton(
            text="Отправить предложение",
            font_size=font_size * 1.2,
            button_color=[0.20, 0.60, 0.86, 1],  # Синий
            text_color=[1, 1, 1, 1]
        )
        send_button.bind(on_release=send_proposal)

        back_button = StyledButton(
            text="Назад",
            font_size=font_size * 1.2,
            button_color=[0.90, 0.49, 0.13, 1],  # Оранжево-красный
            text_color=[1, 1, 1, 1]
        )
        back_button.bind(on_release=lambda _: popup.dismiss())

        button_layout.add_widget(send_button)
        button_layout.add_widget(back_button)

        content.add_widget(button_layout)

        # --- Собираем и показываем Popup ---
        popup = Popup(
            title="Заключение мира",
            content=content,
            size_hint=(0.7, 0.5),
            auto_dismiss=False
        )
        popup.open()

    except Exception as e:
        print(f"Ошибка при работе с дипломатией: {e}")


# Словарь фраз для каждой фракции
alliance_phrases = {
    "Эльфы": "Природа восторжествует!",
    "Север": "Светлого неба!",
    "Адепты": "Да хранит нас Бог!",
    "Элины": "Огонь пустыни защитит Вас!",
    "Вампиры": "Теплокровных оставьте нам..."
}



def show_popup_message(title, message):
    """
    Показывает всплывающее окно с заданным заголовком и сообщением.

    :param title: Заголовок окна.
    :param message: Текст сообщения.
    """
    popup_content = BoxLayout(orientation='vertical', padding=10, spacing=10)
    popup_content.add_widget(Label(text=message, color=(1, 1, 1, 1), halign='center'))
    close_button = Button(text="Закрыть", size_hint=(1, 0.3))
    popup = Popup(title=title, content=popup_content, size_hint=(0.6, 0.4), auto_dismiss=False)
    close_button.bind(on_release=popup.dismiss)
    popup_content.add_widget(close_button)
    popup.open()




#-------------------------------------

def calculate_army_strength(conn):
    """Рассчитывает силу армий для каждой фракции по новой логике."""

    army_strength = {}

    try:
        cursor = conn.cursor()

        # Получаем все юниты из таблицы garrisons и их характеристики из units
        cursor.execute("""
            SELECT g.unit_name, g.unit_count, u.faction, u.attack, u.defense, u.durability, u.unit_class 
            FROM garrisons g
            JOIN units u ON g.unit_name = u.unit_name
        """)
        garrison_data = cursor.fetchall()

        # Собираем данные по фракциям
        factions_data = {}

        for row in garrison_data:
            unit_name, unit_count, faction, attack, defense, durability, unit_class = row

            if not faction:
                continue

            key = faction
            if key not in factions_data:
                factions_data[key] = {
                    "class_1": {"count": 0, "total_stats": 0},
                    "heroes": {"total_stats": 0},  # герои класса 2 и 3
                    "others": {"total_stats": 0}   # юниты класса 4 и 5
                }

            stats_sum = attack + defense + durability

            if unit_class == "1":
                factions_data[key]["class_1"]["count"] += unit_count
                factions_data[key]["class_1"]["total_stats"] += stats_sum * unit_count
            elif unit_class in ("2", "3"):
                factions_data[key]["heroes"]["total_stats"] += stats_sum * unit_count
            else:  # класс 4 и выше
                factions_data[key]["others"]["total_stats"] += stats_sum * unit_count

        # Применяем новую формулу
        for faction, data in factions_data.items():
            class_1_count = data["class_1"]["count"]
            base_stats = data["class_1"]["total_stats"]
            hero_bonus = data["heroes"]["total_stats"]
            others_stats = data["others"]["total_stats"]

            total_strength = 0

            if class_1_count > 0:
                total_strength += base_stats + hero_bonus * class_1_count

            total_strength += others_stats

            army_strength[faction] = total_strength

    except Exception as e:
        print(f"Ошибка при работе с базой данных: {e}")
        return {}

    # Возвращаем два словаря: один с числовыми значениями, другой с отформатированными строками
    formatted_army_strength = {faction: format_number(strength) for faction, strength in army_strength.items()}
    return army_strength, formatted_army_strength


def create_army_rating_table(conn):
    """Создает таблицу рейтинга армий с улучшенным дизайном."""
    army_strength, formatted_army_strength = calculate_army_strength(conn)
    if not army_strength:
        return GridLayout()

    max_strength = max(army_strength.values(), default=1)

    # Макет таблицы
    layout = GridLayout(
        cols=3,
        size_hint_y=None,
        spacing=dp(10),
        padding=[dp(10), dp(5), dp(10), dp(5)],
        row_default_height=dp(50),
        row_force_default=True
    )
    layout.bind(minimum_height=layout.setter('height'))

    # Цвета
    header_color = (0.1, 0.5, 0.9, 1)  # Темно-синий
    row_colors = [
        (1, 1, 1, 1),       # Белый
        (0.8, 0.9, 1, 1),   # Светло-голубой
        (0.6, 0.8, 1, 1),   # Голубой
        (0.4, 0.7, 1, 1),   # Сине-зеленый
        (0.2, 0.6, 1, 1)    # Темно-синий
    ]

    def create_label(text, color, halign="left", valign="middle", bold=False):
        lbl = Label(
            text=text,
            color=(0, 0, 0, 1),
            font_size=sp(14),
            size_hint_y=None,
            height=dp(50),
            halign=halign,
            valign=valign,
            bold=bold
        )
        lbl.bind(size=lbl.setter('text_size'))
        with lbl.canvas.before:
            Color(*color)
            lbl.rect = RoundedRectangle(pos=lbl.pos, size=lbl.size, radius=[dp(8)])
        lbl.bind(
            pos=lambda _, value: setattr(lbl.rect, 'pos', value),
            size=lambda _, value: setattr(lbl.rect, 'size', value)
        )
        return lbl

    # Заголовки
    layout.add_widget(create_label("Раса", header_color, halign="center", valign="middle", bold=True))
    layout.add_widget(create_label("Рейтинг", header_color, halign="center", valign="middle", bold=True))
    layout.add_widget(create_label("Могущество", header_color, halign="center", valign="middle", bold=True))

    sorted_factions = sorted(army_strength.items(), key=lambda x: x[1], reverse=True)

    for rank, (faction, strength) in enumerate(sorted_factions):
        rating = (strength / max_strength) * 100
        faction_name = faction_names.get(faction, faction)
        color = row_colors[rank % len(row_colors)]

        # Добавляем ячейки
        layout.add_widget(create_label(f"  {faction_name}", color, halign="left", valign="middle"))
        layout.add_widget(create_label(f"{rating:.1f}%", color, halign="center", valign="middle"))
        layout.add_widget(create_label(formatted_army_strength[faction], color, halign="right", valign="middle"))

    return layout

def show_ratings_popup(conn):
    """Открывает всплывающее окно с рейтингом армий."""
    table_layout = create_army_rating_table(conn)

    scroll_view = ScrollView(
        size_hint=(1, 1),
        bar_width=dp(6),
        scroll_type=['bars', 'content']
    )
    scroll_view.add_widget(table_layout)

    popup = Popup(
        title="Рейтинг армий",
        content=scroll_view,
        size_hint=(0.9, 0.8),
        pos_hint={'center_x': 0.5, 'center_y': 0.5},
        background_color=(0.1, 0.1, 0.1, 0.95),
        separator_color=(0.2, 0.6, 1, 1),
        title_color=(1, 1, 1, 1),
        title_size=sp(20)
    )
    popup.open()


#------------------------------------------------------------------
def start_politic_mode(faction, game_area, class_faction, conn):
    """Инициализация политического режима для выбранной фракции"""

    from kivy.metrics import dp, sp
    from kivy.uix.widget import Widget

    is_android = platform == 'android'

    politics_layout = BoxLayout(
        orientation='horizontal',
        size_hint=(1, None),
        height=dp(70) if is_android else 60,
        pos_hint={'x': -0.34, 'y': 0},
        spacing=dp(10) if is_android else 10,
        padding=[dp(10), dp(5), dp(10), dp(5)] if is_android else [10, 5, 10, 5]
    )

    # Добавляем пустое пространство слева
    politics_layout.add_widget(Widget(size_hint_x=None, width=dp(20)))

    def styled_btn(text, callback):
        btn = Button(
            text=text,
            size_hint_x=None,
            width=dp(120) if is_android else 100,
            size_hint_y=None,
            height=dp(60) if is_android else 50,
            background_color=(0, 0, 0, 0),
            color=(1, 1, 1, 1),
            font_size=sp(18) if is_android else 16,
            bold=True
        )

        with btn.canvas.before:
            Color(0.2, 0.6, 1, 1)
            btn.rect = RoundedRectangle(pos=btn.pos, size=btn.size, radius=[15])

        def update_rect(instance, value):
            instance.rect.pos = instance.pos
            instance.rect.size = instance.size

        btn.bind(pos=update_rect, size=update_rect)
        btn.bind(on_release=callback)
        return btn

    btn_army = styled_btn("Сила армий", lambda btn: show_ratings_popup(conn))
    btn_nobles = styled_btn("Совет", lambda btn: show_nobles_window(conn, faction, class_faction))
    btn_diversion = styled_btn("Диверсия", lambda btn: show_diversion_window(conn, faction, class_faction))

    politics_layout.add_widget(btn_army)
    politics_layout.add_widget(btn_nobles)
    politics_layout.add_widget(btn_diversion)

    game_area.add_widget(politics_layout)