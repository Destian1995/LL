from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.popup import Popup
from kivy.metrics import dp, sp
from kivy.core.window import Window
from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout
from kivy.graphics import Color, RoundedRectangle
from kivy.clock import Clock

# --- КОНФИГУРАЦИЯ СТИЛЕЙ (THEME) ---
class UIStyles:
    # Цветовая палитра "Королевство"
    COLOR_BG = (0.05, 0.05, 0.1, 1)       # Темно-синий фон
    COLOR_CARD = (0.15, 0.15, 0.25, 1)    # Фон карточки
    COLOR_GOLD = (0.8, 0.65, 0.2, 1)      # Золото
    COLOR_TEXT = (0.9, 0.9, 0.9, 1)       # Белый текст
    COLOR_TEXT_DIM = (0.6, 0.6, 0.6, 1)   # Тусклый текст
    COLOR_SUCCESS = (0.2, 0.8, 0.4, 1)    # Зеленый
    COLOR_DANGER = (0.8, 0.2, 0.2, 1)     # Красный
    COLOR_ACTION = (0.3, 0.5, 0.8, 1)     # Синяя кнопка

    # Размеры
    BTN_HEIGHT = dp(50)
    CARD_HEIGHT = dp(70)
    PADDING = dp(10)
    RADIUS = dp(10)

    @staticmethod
    def is_android():
        return hasattr(Window, 'keyboard')

    @staticmethod
    def get_font_size(base_size):
        """Адаптивный шрифт"""
        if UIStyles.is_android():
            return base_size * 0.9
        return base_size

# --- КАСТОМНЫЕ ВИДЖЕТЫ ---

class StyledButton(Button):
    """Кнопка со скругленными углами и эффектом нажатия"""
    def __init__(self, color=UIStyles.COLOR_ACTION, **kwargs):
        super().__init__(**kwargs)
        self.background_color = (0, 0, 0, 0)
        self.background_normal = ''
        self.color = UIStyles.COLOR_TEXT
        self._color = color
        self._original_color = color

        with self.canvas.before:
            self._bg_color = Color(*self._color)
            self._bg_rect = RoundedRectangle(pos=self.pos, size=self.size, radius=[UIStyles.RADIUS])

        self.bind(pos=self._update_rect, size=self._update_rect)
        self.bind(on_press=self._on_press, on_release=self._on_release)

    def _update_rect(self, instance, value):
        self._bg_rect.pos = instance.pos
        self._bg_rect.size = instance.size

    def _on_press(self, instance):
        self._bg_color.rgba = (self._color[0]*0.7, self._color[1]*0.7, self._color[2]*0.7, 1)

    def _on_release(self, instance):
        self._bg_color.rgba = self._original_color

class NobleCard(BoxLayout):
    """Карточка дворянина"""
    def __init__(self, noble_data, conn, cash_player, refresh_callback, **kwargs):
        super().__init__(orientation='horizontal', size_hint_y=None, height=UIStyles.CARD_HEIGHT, padding=UIStyles.PADDING, spacing=dp(5), **kwargs)

        # Фон карточки
        with self.canvas.before:
            Color(*UIStyles.COLOR_CARD)
            self.rect = RoundedRectangle(pos=self.pos, size=self.size, radius=[UIStyles.RADIUS])
        self.bind(pos=self._update_rect, size=self._update_rect)

        # 1. Имя и статус
        info_layout = BoxLayout(orientation='vertical', size_hint_x=0.6)
        name_label = Label(
            text=noble_data['name'],
            font_size=sp(UIStyles.get_font_size(16)),
            halign='left',
            valign='middle',
            color=UIStyles.COLOR_TEXT,
            markup=True
        )
        name_label.bind(size=name_label.setter('text_size'))

        # Статус (лояльность или внимание)
        status_text = self._get_status_text(noble_data)
        status_label = Label(
            text=status_text,
            font_size=sp(UIStyles.get_font_size(12)),
            halign='left',
            valign='middle',
            color=UIStyles.COLOR_TEXT_DIM,
            markup=True
        )
        status_label.bind(size=status_label.setter('text_size'))

        info_layout.add_widget(name_label)
        info_layout.add_widget(status_label)

        # 2. Кнопка действия
        btn_layout = BoxLayout(size_hint_x=0.4)
        action_btn = self._create_action_button(noble_data, conn, cash_player, refresh_callback)
        btn_layout.add_widget(action_btn)

        self.add_widget(info_layout)
        self.add_widget(btn_layout)

    def _update_rect(self, instance, value):
        self.rect.pos = instance.pos
        self.rect.size = instance.size

    def _get_status_text(self, noble_data):
        # Логика отображения статуса (упрощенная для примера)
        attendance = noble_data.get('attendance_history', '')
        if attendance:
            try:
                history = [int(x) for x in str(attendance).split(',') if x.isdigit()]
                if history:
                    percent = int((sum(history) / len(history)) * 100)
                    color = "[color=ff0000]" if percent < 30 else "[color=ffff00]" if percent < 60 else "[color=00ff00]"
                    return f"{color}Внимание: {percent}%[/color]"
            except: pass
        return "[color=aaaaaa]Статус неизвестен[/color]"

    def _create_action_button(self, noble_data, conn, cash_player, refresh_callback):
        try:
            ideology = json.loads(noble_data['ideology']) if isinstance(noble_data['ideology'], str) else noble_data['ideology']
            if isinstance(ideology, dict) and ideology.get('type') == 'greed':
                btn = StyledButton(text="Договориться", color=UIStyles.COLOR_GOLD)
                btn.bind(on_release=lambda inst: self._handle_deal(conn, noble_data, cash_player, refresh_callback))
                return btn
        except: pass

        label = Label(text="Нет действий", color=UIStyles.COLOR_TEXT_DIM, halign='center', valign='middle')
        label.bind(size=label.setter('text_size'))
        return label

    def _handle_deal(self, conn, noble_data, cash_player, refresh_callback):
        show_deal_popup(conn, noble_data, cash_player)
        Clock.schedule_once(lambda dt: refresh_callback(), 0.5)

# --- ОБНОВЛЕННЫЕ ФУНКЦИИ ИНТЕРФЕЙСА ---

def show_nobles_window(conn, faction, class_faction):
    """Главное окно списка дворян с новым дизайном"""
    cash_player = CalculateCash(faction, class_faction)
    player_faction = get_player_faction(conn)
    season_index = get_current_season_index(conn)

    # Основной контейнер
    main_layout = BoxLayout(orientation='vertical', padding=UIStyles.PADDING, spacing=dp(10))
    main_layout.canvas.before.add(Color(*UIStyles.COLOR_BG))
    main_layout.canvas.before.add(RoundedRectangle(pos=main_layout.pos, size=main_layout.size, radius=[dp(15)]))

    # Заголовок
    header = Label(
        text="[b]Совет Дворян[/b]",
        font_size=sp(UIStyles.get_font_size(24)),
        color=UIStyles.COLOR_GOLD,
        markup=True,
        size_hint_y=None,
        height=dp(50)
    )
    main_layout.add_widget(header)

    # Список дворян (ScrollView)
    scroll_view = ScrollView(do_scroll_x=False, size_hint_y=1)
    nobles_list = BoxLayout(orientation='vertical', size_hint_y=None, spacing=dp(5))
    nobles_list.bind(minimum_height=nobles_list.setter('height'))
    scroll_view.add_widget(nobles_list)
    main_layout.add_widget(scroll_view)

    # Панель действий внизу
    actions_layout = BoxLayout(size_hint_y=None, height=UIStyles.BTN_HEIGHT + dp(10), spacing=dp(10))

    btn_secret = StyledButton(text="Тайная служба", color=UIStyles.COLOR_DANGER)
    btn_secret.bind(on_release=lambda inst: show_secret_service_popup(conn, lambda res: None, cash_player, lambda: refresh_list()))

    btn_event = StyledButton(text="Мероприятие", color=UIStyles.COLOR_ACTION)
    btn_event.bind(on_release=lambda inst: show_event_popup(conn, player_faction, season_index, lambda: refresh_list(), cash_player))

    actions_layout.add_widget(btn_secret)
    actions_layout.add_widget(btn_event)
    main_layout.add_widget(actions_layout)

    # Кнопка закрытия
    btn_close = StyledButton(text="Закрыть", color=(0.5, 0.5, 0.5, 1), size_hint_y=None, height=UIStyles.BTN_HEIGHT)
    btn_close.bind(on_release=lambda inst: popup.dismiss())
    main_layout.add_widget(btn_close)

    # Функция обновления списка
    def refresh_list():
        nobles_list.clear_widgets()
        for noble in get_all_nobles(conn):
            nobles_list.add_widget(NobleCard(noble, conn, cash_player, refresh_list))

    # Первоначальное заполнение
    refresh_list()

    # Popup контейнер
    popup = Popup(
        title="",
        content=main_layout,
        size_hint=(0.95, 0.9) if not UIStyles.is_android() else (1, 1),
        pos_hint={'center_x': 0.5, 'center_y': 0.5},
        background_color=(0, 0, 0, 0.5), # Затемнение фона
        separator_height=0
    )
    popup.open()

def show_deal_popup(conn, noble_data, cash_player):
    """Красивое окно сделки"""
    noble_traits = get_noble_traits(noble_data['ideology'])
    if noble_traits['type'] != 'greed':
        return

    demand = noble_traits['demand']
    cash_player.load_resources()
    current_money = cash_player.resources.get("Кроны", 0)

    if current_money < demand:
        # Упрощенный popup ошибки
        show_result_popup("Ошибка", "Недостаточно крон!", False)
        return

    content = BoxLayout(orientation='vertical', padding=dp(20), spacing=dp(15))

    # Заголовок сделки
    title = Label(
        text=f"[color={UIStyles.COLOR_GOLD[0]}, {UIStyles.COLOR_GOLD[1]}, {UIStyles.COLOR_GOLD[2]}, 1]{noble_data['name']}[/color]",
        font_size=sp(20),
        markup=True,
        halign='center',
        size_hint_y=None,
        height=dp(40)
    )

    # Сумма
    cost_label = Label(
        text=f"Требуется: [b]{format_number(demand)} крон[/b]",
        font_size=sp(18),
        markup=True,
        halign='center',
        color=UIStyles.COLOR_TEXT
    )

    # Кнопки
    btn_layout = BoxLayout(size_hint_y=None, height=UIStyles.BTN_HEIGHT, spacing=dp(15))
    btn_pay = StyledButton(text="Заплатить", color=UIStyles.COLOR_SUCCESS)
    btn_cancel = StyledButton(text="Отмена", color=(0.5, 0.5, 0.5, 1))

    def do_pay(*args):
        if cash_player.deduct_resources(demand):
            if pay_greedy_noble(conn, noble_data['id'], demand):
                show_result_popup("Успех", "Дворянин теперь лоялен вам!", True)
                popup.dismiss()
            else:
                show_result_popup("Ошибка", "Сбой транзакции", False)
        else:
            show_result_popup("Ошибка", "Недостаточно средств", False)

    btn_pay.bind(on_release=do_pay)
    btn_cancel.bind(on_release=lambda *args: popup.dismiss())

    btn_layout.add_widget(btn_pay)
    btn_layout.add_widget(btn_cancel)

    content.add_widget(title)
    content.add_widget(cost_label)
    content.add_widget(Label()) # Распорка
    content.add_widget(btn_layout)

    popup = Popup(
        title="Предложение",
        content=content,
        size_hint=(0.8, 0.5),
        pos_hint={'center_x': 0.5, 'center_y': 0.5},
        background_color=(0, 0, 0, 0.7)
    )
    popup.open()

def show_result_popup(title, message, is_success=True):
    """Универсальное окно результата"""
    content = BoxLayout(orientation='vertical', padding=dp(20), spacing=dp(10))

    color = UIStyles.COLOR_SUCCESS if is_success else UIStyles.COLOR_DANGER
    icon = "✓" if is_success else "✗"

    lbl_title = Label(
        text=f"[b]{icon} {title}[/b]",
        font_size=sp(20),
        markup=True,
        color=color,
        size_hint_y=None,
        height=dp(40)
    )

    lbl_msg = Label(
        text=message,
        font_size=sp(16),
        halign='center',
        valign='middle',
        color=UIStyles.COLOR_TEXT
    )
    lbl_msg.bind(size=lbl_msg.setter('text_size'))

    btn = StyledButton(text="Принять", color=UIStyles.COLOR_ACTION)
    btn.bind(on_release=lambda *args: popup.dismiss())

    content.add_widget(lbl_title)
    content.add_widget(lbl_msg)
    content.add_widget(btn)

    popup = Popup(
        title="",
        content=content,
        size_hint=(0.7, 0.4),
        pos_hint={'center_x': 0.5, 'center_y': 0.5},
        background_color=(0, 0, 0, 0.5),
        separator_height=0
    )
    popup.open()

from nobles_generator import (
    get_all_nobles,
    update_noble_loyalty_for_event,
    attempt_secret_service_action,
    get_player_faction,
    get_noble_traits,
    pay_greedy_noble,
    show_secret_service_result_popup,
    get_noble_display_name_with_sympathies
)
def format_number(number):
    """Форматирует число с добавлением приставок (тыс., млн., млрд., трлн.)"""
    if not isinstance(number, (int, float)):
        return str(number)
    if number == 0:
        return "0"
    absolute = abs(number)
    sign = -1 if number < 0 else 1
    if absolute >= 1_000_000_000_000:  # 1e36
        return f"{sign * absolute / 1e12:.1f} трлн."
    elif absolute >= 1_000_000_000:  # 1e9
        return f"{sign * absolute / 1e9:.1f} млрд."
    elif absolute >= 1_000_000:  # 1e6
        return f"{sign * absolute / 1e6:.1f} млн."
    elif absolute >= 1_000:  # 1e3
        return f"{sign * absolute / 1e3:.1f} тыс."
    else:
        return f"{number}"
class CalculateCash:
    def __init__(self, faction, class_faction):
        """
        Инициализация класса PoliticalCash.
        :param faction: Название фракции.
        :param class_faction: Экземпляр класса Faction (экономический модуль).
        """
        self.faction = faction
        self.class_faction = class_faction  # Экономический модуль
        self.resources = self.load_resources()  # Загрузка начальных ресурсов
    def load_resources(self):
        """
        Загружает текущие ресурсы фракции через экономический модуль.
        """
        try:
            resources = {
                "Кроны": self.class_faction.get_resource_now("Кроны"),
                "Рабочие": self.class_faction.get_resource_now("Рабочие")
            }
            print(f"[DEBUG] Загружены ресурсы для фракции '{self.faction}': {resources}")
            return resources
        except Exception as e:
            print(f"Ошибка при загрузке ресурсов: {e}")
            return {"Кроны": 0, "Рабочие": 0}
    def deduct_resources(self, crowns, workers=0):
        """
        Списывает ресурсы через экономический модуль.
        :param crowns: Количество крон для списания.
        :param workers: Количество рабочих для списания (по умолчанию 0).
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
            if workers > 0:
                self.class_faction.update_resource_now("Рабочие", current_workers - workers)
            # Обновляем внутренний словарь ресурсов
            self.resources["Кроны"] = current_crowns - crowns
            if workers > 0:
                self.resources["Рабочие"] = current_workers - workers
            return True
        except Exception as e:
            print(f"Ошибка при списании ресурсов: {e}")
            return False


# --- Функции для работы с мероприятиями ---
def get_current_season_index(conn):
    """Получает индекс текущего сезона из БД."""
    cursor = conn.cursor()
    cursor.execute("SELECT season_index FROM season WHERE id = 1")
    result = cursor.fetchone()
    return result[0] if result else 0


def get_season_name_by_index(index):
    """Получает название сезона по его индексу."""
    season_names = ['Зима', 'Весна', 'Лето', 'Осень']
    return season_names[index] if 0 <= index < len(season_names) else 'Зима'


def get_event_type_by_season(season_index):
    """Получает тип мероприятия по индексу сезона."""
    events = {0: 'Бал', 1: 'Королевский совет', 2: 'Королевская охота', 3: 'Рыцарский турнир'}
    return events.get(season_index, 'Неизвестное мероприятие')


# --- Функции интерфейса ---
def create_noble_widget(noble_data, conn, cash_player):
    """Создание виджета для отображения одного дворянина (табличный формат)"""
    # Адаптивные размеры
    is_android = hasattr(Window, 'keyboard') # Простая проверка
    widget_height = dp(60) if not is_android else dp(55)
    font_large = sp(16) if not is_android else sp(14)
    font_medium = sp(14) if not is_android else sp(12)
    font_small = sp(12) if not is_android else sp(10)
    padding_inner = dp(8) if not is_android else dp(5)
    spacing_inner = dp(5) if not is_android else dp(3)

    # --- Используем GridLayout для табличного формата ---
    layout = GridLayout(cols=2, size_hint_y=None, height=widget_height, padding=padding_inner, spacing=spacing_inner)
    display_name = get_noble_display_name_with_sympathies(noble_data)
    # Имя
    name_label = Label(
        text=display_name,
        font_size=font_large,
        halign='left',
        valign='middle',
        text_size=(None, None) # Позволить обрезать длинные имена
    )
    name_label.bind(size=name_label.setter('text_size'))

    # --- Расчет и отображение процента посещаемости ---
    attendance_history_raw = noble_data.get('attendance_history', '')
    attention_text = "?"
    attention_color = (1, 1, 1, 1) # Белый по умолчанию
    if isinstance(attendance_history_raw, str) and attendance_history_raw:
        try:
            history_list = [int(x) for x in attendance_history_raw.split(',') if x.isdigit()]
        except ValueError:
            history_list = []
    elif isinstance(attendance_history_raw, list):
        history_list = [x for x in attendance_history_raw if isinstance(x, int)]
    else:
        history_list = []

    if history_list:
        total_events = len(history_list)
        attended_events = sum(history_list)
        if total_events > 0:
            attendance_percentage = int((attended_events / total_events) * 100)
            attention_text = f"{attendance_percentage}%"
            # Цветовая индикация на основе процента
            if attendance_percentage < 30:
                attention_color = (1, 0, 0, 1) # Красный
            elif attendance_percentage < 60:
                attention_color = (1, 1, 0, 1) # Желтый
            else:
                attention_color = (0, 1, 0, 1) # Зеленый

    attention_label = Label(
        text=attention_text,
        font_size=font_medium,
        halign='center', # Центрируем внутри ячейки
        valign='middle',
        color=attention_color,
        text_size=(None, None)
    )
    attention_label.bind(size=attention_label.setter('text_size'))

    layout.add_widget(name_label)
    layout.add_widget(attention_label)
    return layout

# --- calculate_event_cost остается без изменений ---
def calculate_event_cost(season_index):
    """Рассчитывает стоимость мероприятия в зависимости от сезона."""
    base_cost = 2_000
    seasonal_multiplier = {0: 1.9, 1: 0.4, 2: 4.5, 3: 9.1}
    multiplier = seasonal_multiplier.get(season_index, 1.0)
    return int(base_cost * multiplier)



def show_event_result_popup(message):
    """Показывает красивое всплывающее окно с результатом мероприятия."""
    # --- Адаптивные размеры ---
    is_android = hasattr(Window, 'keyboard')
    padding_main = dp(15) if not is_android else dp(10)
    spacing_main = dp(10) if not is_android else dp(7)
    font_title = sp(18) if not is_android else sp(16)
    font_message = sp(15) if not is_android else sp(13)
    btn_height = dp(45) if not is_android else dp(40)
    font_btn = sp(14) if not is_android else sp(12)
    content = BoxLayout(orientation='vertical', padding=padding_main, spacing=spacing_main)
    # Определяем тип сообщения и цвета
    if "проведено" in message.lower():
        title = "Успех!"
        title_color = (0.2, 0.8, 0.2, 1)  # Зеленый
    else:
        title = "Ошибка"
        title_color = (0.9, 0.2, 0.2, 1)  # Красный
    # Заголовок с иконкой
    title_label = Label(
        text=f"[b]{title}[/b]",
        font_size=font_title,
        markup=True,
        halign='center',
        valign='middle',
        size_hint_y=None,
        height=dp(40) if not is_android else dp(35),
        color=title_color
    )
    title_label.bind(size=title_label.setter('text_size'))
    # Сообщение
    message_label = Label(
        text=message,
        font_size=font_message,
        halign='center',
        valign='middle',
        text_size=(dp(280) if not is_android else dp(250), None)
    )
    message_label.bind(size=message_label.setter('text_size'))
    # Кнопка закрытия
    close_btn = Button(
        text="Закрыть",
        font_size=font_btn,
        size_hint_y=None,
        height=btn_height,
        background_color=(0.5, 0.5, 0.7, 1) if "проведено" in message.lower() else (0.7, 0.5, 0.5, 1),
        background_normal=''
    )
    # Адаптивные размеры попапа
    popup_size_hint = (0.8, 0.5) if not is_android else (0.9, 0.45)
    popup_pos_hint = {} if not is_android else {'center_x': 0.5, 'center_y': 0.5}
    popup = Popup(
        title="",
        content=content,
        size_hint=popup_size_hint,
        pos_hint=popup_pos_hint,
        auto_dismiss=False
    )
    def on_close(instance):
        popup.dismiss()
    close_btn.bind(on_release=on_close)
    content.add_widget(title_label)
    content.add_widget(message_label)
    content.add_widget(close_btn)
    popup.open()

def get_events_count_from_history(conn):
    """Получает количество проведённых мероприятий из истории посещений всех активных дворян."""
    cursor = conn.cursor()
    cursor.execute("SELECT attendance_history FROM nobles WHERE status = 'active'")
    all_histories = cursor.fetchall()

    all_lengths = []
    for history_row in all_histories:
        history_str = history_row[0] if history_row[0] else ""
        if history_str:
            try:
                history_list = [x for x in history_str.split(',') if x.isdigit()]
                all_lengths.append(len(history_list))
            except Exception:
                continue  # Игнорируем некорректные данные
        else:
            all_lengths.append(0)

    # Возвращаем максимальную длину истории, что соответствует количеству проведённых мероприятий
    return max(all_lengths) if all_lengths else 0


# --- Обновлённая функция show_secret_service_popup ---
def show_secret_service_popup(conn, on_result_callback, cash_player, refresh_main_list_callback):
    """Показывает всплывающее окно для Тайной службы с выбором цели (карточный формат)."""
    COST_SECRET_SERVICE = 140_000

    # --- Проверка баланса ---
    cash_player.load_resources()
    current_money = cash_player.resources.get("Кроны", 0)
    if current_money < COST_SECRET_SERVICE:
        show_result_popup("Ошибка", f"Недостаточно средств. Нужно {format_number(COST_SECRET_SERVICE)}", False)
        return

    # --- Получаем количество проведённых мероприятий ---
    events_count = get_events_count_from_history(conn)

    # --- Получаем список всех активных дворян ---
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, name, loyalty, status, ideology, attendance_history
            FROM nobles
            WHERE status = 'active'
            ORDER BY name ASC
        """)
        all_active_nobles = cursor.fetchall()
        nobles_data = []
        for row in all_active_nobles:
            noble_dict = {
                'id': row[0],
                'name': row[1],
                'loyalty': row[2],
                'status': row[3],
                'ideology': row[4],
                'attendance_history': row[5]
            }
            if events_count >= 3:
                noble_dict['show_loyalty'] = True
                noble_dict['show_views'] = True
                noble_dict['calculated_loyalty'] = int(noble_dict['loyalty']) if noble_dict['loyalty'] is not None else None
            else:
                noble_dict['show_loyalty'] = False
                noble_dict['show_views'] = False
                noble_dict['calculated_loyalty'] = None
            nobles_data.append(noble_dict)
    except Exception as e:
        print(f"[ERROR] Ошибка при получении списка активных дворян: {e}")
        show_result_popup("Ошибка", "Ошибка получения списка целей.", False)
        return

    if not nobles_data:
        show_result_popup("Ошибка", "Нет доступных целей для устранения.", False)
        return

    # --- Основной контейнер ---
    main_layout = BoxLayout(orientation='vertical', padding=UIStyles.PADDING, spacing=dp(10))
    main_layout.canvas.before.add(Color(*UIStyles.COLOR_BG))
    main_layout.canvas.before.add(RoundedRectangle(pos=main_layout.pos, size=main_layout.size, radius=[dp(15)]))

    # --- Заголовок ---
    header = Label(
        text="[b]Тайная служба[/b]",
        font_size=sp(UIStyles.get_font_size(22)),
        color=UIStyles.COLOR_DANGER,
        markup=True,
        size_hint_y=None,
        height=dp(50),
        halign='center'
    )
    main_layout.add_widget(header)

    # --- Информация о стоимости ---
    cost_info = Label(
        text=f"Стоимость санкции: [b]{format_number(COST_SECRET_SERVICE)} крон[/b]",
        font_size=sp(UIStyles.get_font_size(14)),
        color=UIStyles.COLOR_TEXT_DIM,
        markup=True,
        size_hint_y=None,
        height=dp(30),
        halign='center'
    )
    main_layout.add_widget(cost_info)

    # --- Список целей (ScrollView) ---
    scroll_view = ScrollView(do_scroll_x=False, size_hint_y=1)
    nobles_list = BoxLayout(orientation='vertical', size_hint_y=None, spacing=dp(5))
    nobles_list.bind(minimum_height=nobles_list.setter('height'))
    scroll_view.add_widget(nobles_list)
    main_layout.add_widget(scroll_view)

    # --- Кнопки внизу ---
    btn_layout = BoxLayout(size_hint_y=None, height=UIStyles.BTN_HEIGHT + dp(10), spacing=dp(10))
    btn_cancel = StyledButton(text="Отмена", color=(0.5, 0.5, 0.5, 1))
    # Кнопка будет привязана после создания popup
    btn_layout.add_widget(btn_cancel)
    main_layout.add_widget(btn_layout)

    # --- Popup контейнер (СОЗДАЕМ ЗДЕСЬ, ДО refresh_list) ---
    popup = Popup(
        title="",
        content=main_layout,
        size_hint=(0.95, 0.9) if not UIStyles.is_android() else (1, 1),
        pos_hint={'center_x': 0.5, 'center_y': 0.5},
        background_color=(0, 0, 0, 0.7),
        separator_height=0
    )

    # Привязываем кнопку отмены теперь, когда popup существует
    btn_cancel.bind(on_release=lambda *args: popup.dismiss())

    # --- Функция обновления списка ---
    def refresh_list():
        nobles_list.clear_widgets()
        for noble_data in nobles_data:
            # Передаем popup в карточку
            card = SecretServiceCard(noble_data, conn, cash_player, popup, refresh_main_list_callback, events_count)
            nobles_list.add_widget(card)

    # --- Первоначальное заполнение ---
    refresh_list()

    popup.open()


# --- Карточка цели для Тайной службы ---
class SecretServiceCard(BoxLayout):
    """Карточка цели для Тайной службы"""

    def __init__(self, noble_data, conn, cash_player, popup_ref, refresh_callback, events_count, **kwargs):
        super().__init__(
            orientation='horizontal',
            size_hint_y=None,
            height=dp(85),
            padding=UIStyles.PADDING,
            spacing=dp(5),
            **kwargs
        )

        self.noble_data = noble_data
        self.conn = conn
        self.cash_player = cash_player
        self.popup_ref = popup_ref  # Ссылка на попап
        self.refresh_callback = refresh_callback
        self.events_count = events_count
        self.COST_SECRET_SERVICE = 140_000

        # Фон карточки
        with self.canvas.before:
            Color(*UIStyles.COLOR_CARD)
            self.rect = RoundedRectangle(pos=self.pos, size=self.size, radius=[UIStyles.RADIUS])
        self.bind(pos=self._update_rect, size=self._update_rect)

        # 1. Информация о дворянине (левая часть)
        info_layout = BoxLayout(orientation='vertical', size_hint_x=0.65, spacing=dp(2))

        # Имя
        name_label = Label(
            text=noble_data['name'],
            font_size=sp(UIStyles.get_font_size(15)),
            halign='left',
            valign='middle',
            color=UIStyles.COLOR_TEXT,
            markup=True
        )
        name_label.bind(size=name_label.setter('text_size'))

        # Статус
        status_text = self._get_status_text()
        status_label = Label(
            text=status_text,
            font_size=sp(UIStyles.get_font_size(11)),
            halign='left',
            valign='middle',
            color=UIStyles.COLOR_TEXT_DIM,
            markup=True
        )
        status_label.bind(size=status_label.setter('text_size'))

        info_layout.add_widget(name_label)
        info_layout.add_widget(status_label)

        # 2. Кнопка устранения (правая часть)
        btn_layout = BoxLayout(size_hint_x=0.35)
        action_btn = StyledButton(text="Устранить", color=UIStyles.COLOR_DANGER)
        action_btn.bind(on_release=lambda inst: self._handle_elimination())
        btn_layout.add_widget(action_btn)

        self.add_widget(info_layout)
        self.add_widget(btn_layout)

    def _update_rect(self, instance, value):
        self.rect.pos = instance.pos
        self.rect.size = instance.size

    def _get_status_text(self):
        """Формирует строку статуса с лояльностью и взглядами"""
        parts = []

        # Лояльность
        if self.noble_data['show_loyalty'] and self.noble_data['calculated_loyalty'] is not None:
            loyalty = self.noble_data['calculated_loyalty']
            if loyalty < 30:
                color = "ff0000"
            elif loyalty < 60:
                color = "ffff00"
            else:
                color = "00ff00"
            parts.append(f"[color={color}]Лояльность: {loyalty}%[/color]")
        else:
            parts.append("[color=aaaaaa]Лояльность: ?[/color]")

        # Взгляды
        if self.noble_data['show_views']:
            try:
                noble_traits = get_noble_traits(self.noble_data['ideology'])
                ideology_to_text = {
                    'Борьба': "Борьба",
                    'Смирение': "Смирение",
                    'Любит Эльфы': "Эльфы",
                    'Любит Элины': "Элины",
                    'Любит Север': "Люди",
                    'Любит Вампиры': "Вампиры",
                    'Любит Адепты': "Адепты",
                }
                if noble_traits['type'] == 'greed':
                    views = "Продажный"
                else:
                    views = ideology_to_text.get(noble_traits['value'], noble_traits['value'])
                parts.append(f"[color=cccccc]{views}[/color]")
            except:
                parts.append("[color=aaaaaa]Взгляды: ?[/color]")
        else:
            parts.append("[color=aaaaaa]Взгляды: скрыто[/color]")

        return "  |  ".join(parts)

    def _handle_elimination(self):
        """Обработка кнопки устранения"""
        self.cash_player.load_resources()
        current_money = self.cash_player.resources.get("Кроны", 0)

        if current_money < self.COST_SECRET_SERVICE:
            show_result_popup("Ошибка", "Недостаточно средств.", False)
            return

        # Подтверждение
        confirm_content = BoxLayout(orientation='vertical', padding=dp(20), spacing=dp(15))
        confirm_popup = Popup(
            title="Подтверждение",
            content=confirm_content,
            size_hint=(0.8, 0.4),
            pos_hint={'center_x': 0.5, 'center_y': 0.5},
            background_color=(0, 0, 0, 0.7),
            separator_height=0
        )

        title = Label(
            text=f"[b]Устранить {self.noble_data['name']}?[/b]",
            font_size=sp(UIStyles.get_font_size(16)),
            markup=True,
            color=UIStyles.COLOR_DANGER,
            size_hint_y=None,
            height=dp(40),
            halign='center'
        )
        cost = Label(
            text=f"Стоимость: {format_number(self.COST_SECRET_SERVICE)} крон",
            font_size=sp(UIStyles.get_font_size(13)),
            color=UIStyles.COLOR_TEXT,
            halign='center'
        )
        btn_layout = BoxLayout(size_hint_y=None, height=UIStyles.BTN_HEIGHT, spacing=dp(10))

        def do_eliminate(*args):
            confirm_popup.dismiss()
            deduction_success = self.cash_player.deduct_resources(self.COST_SECRET_SERVICE)
            if deduction_success:
                result = attempt_secret_service_action(
                    self.conn,
                    get_player_faction(self.conn),
                    target_noble_id=self.noble_data['id']
                )
                show_secret_service_result_popup(result)
                if callable(self.refresh_callback):
                    Clock.schedule_once(lambda dt: self.refresh_callback(), 0.5)
                # Закрываем главное окно тайной службы
                if self.popup_ref:
                    self.popup_ref.dismiss()
            else:
                show_result_popup("Ошибка", "Ошибка списания средств.", False)

        btn_confirm = StyledButton(text="Подтвердить", color=UIStyles.COLOR_DANGER)
        btn_confirm.bind(on_release=do_eliminate)

        btn_cancel = StyledButton(text="Отмена", color=(0.5, 0.5, 0.5, 1))
        btn_cancel.bind(on_release=lambda *args: confirm_popup.dismiss())

        btn_layout.add_widget(btn_confirm)
        btn_layout.add_widget(btn_cancel)

        confirm_content.add_widget(title)
        confirm_content.add_widget(cost)
        confirm_content.add_widget(Label())
        confirm_content.add_widget(btn_layout)

        confirm_popup.open()

def show_toast_notification(message, is_success=True, duration=1.5):
    """Показывает всплывающее уведомление без кнопок, которое исчезает автоматически."""

    # --- Адаптивные размеры ---
    is_android = hasattr(Window, 'keyboard')
    padding_main = dp(20) if not is_android else dp(15)
    font_message = sp(16) if not is_android else sp(14)

    # --- Цвета в зависимости от результата ---
    color = UIStyles.COLOR_SUCCESS if is_success else UIStyles.COLOR_DANGER
    icon = "✓" if is_success else "✗"

    # --- Контент уведомления ---
    content = BoxLayout(
        orientation='vertical',
        padding=padding_main,
        size_hint_y=None,
        height=dp(80) if not is_android else dp(70)
    )

    # Добавляем фон карточки
    with content.canvas.before:
        Color(*UIStyles.COLOR_CARD)
        content.rect = RoundedRectangle(pos=content.pos, size=content.size, radius=[UIStyles.RADIUS])

    def update_rect(instance, value):
        content.rect.pos = instance.pos
        content.rect.size = instance.size

    content.bind(pos=update_rect, size=update_rect)

    # Текст уведомления
    message_label = Label(
        text=f"[b]{icon} {message}[/b]",
        font_size=font_message,
        markup=True,
        halign='center',
        valign='middle',
        color=UIStyles.COLOR_TEXT
    )
    message_label.bind(size=message_label.setter('text_size'))

    content.add_widget(message_label)

    # --- Popup без кнопок ---
    toast_popup = Popup(
        title="",
        content=content,
        size_hint=(0.7, None),
        height=dp(80) if not is_android else dp(70),
        pos_hint={'center_x': 0.5, 'center_y': 0.5},
        background_color=(0, 0, 0, 0),  # Прозрачный фон popup
        separator_height=0,
        auto_dismiss=False
    )

    # --- Автоматическое закрытие через Clock ---
    def close_toast(dt):
        try:
            # Проверяем через приватный атрибут _is_open
            if toast_popup._is_open:
                toast_popup.dismiss()
        except:
            # Если попап уже закрыт - игнорируем ошибку
            pass

    toast_popup.open()
    Clock.schedule_once(close_toast, duration)


def show_event_popup(conn, player_faction, season_index, refresh_callback, cash_player):
    """Показывает всплывающее окно для выбора и проведения мероприятия."""
    event_type = get_event_type_by_season(season_index)
    event_season = get_season_name_by_index(season_index)
    cost = calculate_event_cost(season_index)

    # --- Адаптивные размеры ---
    is_android = hasattr(Window, 'keyboard')
    padding_main = dp(15) if not is_android else dp(10)
    spacing_main = dp(15) if not is_android else dp(10)
    font_title = sp(18) if not is_android else sp(16)
    font_subtitle = sp(16) if not is_android else sp(14)
    font_info = sp(15) if not is_android else sp(13)
    font_btn = sp(14) if not is_android else sp(12)
    btn_height = dp(50) if not is_android else dp(45)
    info_height = dp(80) if not is_android else dp(70)
    btn_layout_height = dp(50) if not is_android else dp(45)

    # --- Проверка баланса ---
    cash_player.load_resources()
    current_money = cash_player.resources.get("Кроны", 0)
    if current_money < cost:
        insufficient_funds_popup = Popup(
            title="Недостаточно средств",
            content=Label(
                text=f"Недостаточно Крон для проведения мероприятия.\nСтоимость: {format_number(cost)}\nУ вас: {format_number(current_money)}",
                halign='center',
                valign='middle',
                text_size=(dp(250), None),
                font_size=sp(14) if not is_android else sp(12)
            ),
            size_hint=(0.85, 0.45) if not is_android else (0.9, 0.4)
        )
        insufficient_funds_popup.content.bind(size=insufficient_funds_popup.content.setter('text_size'))
        insufficient_funds_popup.open()
        return

    # ------------------------------------
    content = BoxLayout(orientation='vertical', padding=padding_main, spacing=spacing_main)

    # --- Тип мероприятия с акцентом ---
    event_type_label = Label(
        text=f"[b]{event_type}[/b]",
        font_size=font_subtitle,
        halign='center',
        valign='middle',
        size_hint_y=None,
        height=dp(30) if not is_android else dp(25),
        markup=True,
        color=(0.7, 0.9, 1, 1)
    )
    event_type_label.bind(size=event_type_label.setter('text_size'))

    # --- Информационная панель ---
    info_box = BoxLayout(orientation='vertical', size_hint_y=None, height=info_height, spacing=dp(5))
    season_label = Label(
        text=f"Сезон: [b]{event_season}[/b]",
        font_size=font_info,
        halign='center',
        valign='middle',
        markup=True,
        color=(0.8, 0.8, 1, 1)
    )
    season_label.bind(size=season_label.setter('text_size'))

    guests_label = Label(
        text="Вся знать будет приглашена",
        font_size=font_info - sp(1),
        halign='center',
        valign='middle',
        color=(0.7, 0.9, 0.7, 1)
    )
    guests_label.bind(size=guests_label.setter('text_size'))

    cost_label = Label(
        text=f"Стоимость: [b]{format_number(cost)}[/b] крон",
        font_size=font_info,
        halign='center',
        valign='middle',
        markup=True,
        color=(1, 0.8, 0.6, 1)
    )
    cost_label.bind(size=cost_label.setter('text_size'))

    info_box.add_widget(season_label)
    info_box.add_widget(guests_label)
    info_box.add_widget(cost_label)

    # --- Кнопки с улучшенным дизайном ---
    btn_layout = BoxLayout(size_hint_y=None, height=btn_layout_height, spacing=dp(15) if not is_android else dp(10))

    confirm_btn = StyledButton(text="Провести", color=UIStyles.COLOR_SUCCESS)
    cancel_btn = StyledButton(text="Отмена", color=(0.5, 0.5, 0.5, 1))

    # Адаптивные размеры попапа
    popup_size_hint = (0.85, 0.7) if not is_android else (0.95, 0.75)
    popup_pos_hint = {} if not is_android else {'center_x': 0.5, 'center_y': 0.5}

    popup = Popup(
        title="Мероприятие",
        content=content,
        size_hint=popup_size_hint,
        pos_hint=popup_pos_hint,
        auto_dismiss=False,
        background_color=(0, 0, 0, 0.7),
        separator_height=0
    )

    def on_confirm(instance):
        popup.dismiss()
        success = cash_player.deduct_resources(cost)

        if success:
            try:
                cursor = conn.cursor()
                cursor.execute("SELECT id FROM nobles WHERE status = 'active'")
                active_nobles = cursor.fetchall()
                for noble_row in active_nobles:
                    noble_id = noble_row[0]
                    update_noble_loyalty_for_event(conn, noble_id, player_faction, event_type, event_season)

                #  Показываем тост-уведомление вместо обычного popup
                show_toast_notification("Мероприятие проведено!", is_success=True, duration=1.5)

                if callable(refresh_callback):
                    Clock.schedule_once(lambda dt: refresh_callback(), 0.5)

            except Exception as e:
                print(f"Ошибка при проведении мероприятия: {e}")
                show_toast_notification("Ошибка проведения мероприятия", is_success=False, duration=2)
        else:
            show_toast_notification("Недостаточно средств", is_success=False, duration=2)

    def on_cancel(instance):
        popup.dismiss()

    confirm_btn.bind(on_release=on_confirm)
    cancel_btn.bind(on_release=on_cancel)

    btn_layout.add_widget(confirm_btn)
    btn_layout.add_widget(cancel_btn)

    content.add_widget(event_type_label)
    content.add_widget(info_box)
    content.add_widget(btn_layout)

    popup.open()


def create_noble_widget_with_deal(noble_data, conn, cash_player, refresh_callback):
    """Создание виджета для отображения одного дворянина с кнопкой 'Договориться'"""
    # Адаптивные размеры
    global json
    is_android = hasattr(Window, 'keyboard') # Простая проверка
    widget_height = dp(60) if not is_android else dp(55)
    font_large = sp(16) if not is_android else sp(14)
    font_medium = sp(14) if not is_android else sp(12)
    font_small = sp(12) if not is_android else sp(10)
    padding_inner = dp(8) if not is_android else dp(5)
    spacing_inner = dp(5) if not is_android else dp(3)

    # --- Используем GridLayout для табличного формата ---
    layout = GridLayout(cols=3, size_hint_y=None, height=widget_height, padding=padding_inner, spacing=spacing_inner)

    # Имя
    name_label = Label(
        text=noble_data['name'],
        font_size=font_large,
        halign='left',
        valign='middle',
        text_size=(None, None) # Позволить обрезать длинные имена
    )
    name_label.bind(size=name_label.setter('text_size'))

    # --- Расчет и отображение процента посещаемости ---
    attendance_history_raw = noble_data.get('attendance_history', '')
    attention_text = "?"
    attention_color = (1, 1, 1, 1) # Белый по умолчанию
    if isinstance(attendance_history_raw, str) and attendance_history_raw:
        try:
            history_list = [int(x) for x in attendance_history_raw.split(',') if x.isdigit()]
        except ValueError:
            history_list = []
    elif isinstance(attendance_history_raw, list):
        history_list = [x for x in attendance_history_raw if isinstance(x, int)]
    else:
        history_list = []

    if history_list:
        total_events = len(history_list)
        attended_events = sum(history_list)
        if total_events > 0:
            attendance_percentage = int((attended_events / total_events) * 100)
            attention_text = f"{attendance_percentage}%"
            # Цветовая индикация на основе процента
            if attendance_percentage < 30:
                attention_color = (1, 0, 0, 1) # Красный
            elif attendance_percentage < 60:
                attention_color = (1, 1, 0, 1) # Желтый
            else:
                attention_color = (0, 1, 0, 1) # Зеленый

    attention_label = Label(
        text=attention_text,
        font_size=font_medium,
        halign='center', # Центрируем внутри ячейки
        valign='middle',
        color=attention_color,
        text_size=(None, None)
    )
    attention_label.bind(size=attention_label.setter('text_size'))

    # --- Кнопка "Договориться" ---
    try:
        import json
        ideology_data = json.loads(noble_data['ideology']) if isinstance(noble_data['ideology'], str) else noble_data['ideology']
        if isinstance(ideology_data, dict) and ideology_data.get('type') == 'greed':
            deal_btn = Button(
                text="Договориться",
                font_size=font_small,
                size_hint_y=None,
                height=dp(30) if not is_android else dp(25),
                background_color=(0.3, 0.7, 0.3, 1)  # Зеленый
            )
            def on_deal(instance):
                show_deal_popup(conn, noble_data, cash_player)
                # После закрытия popup обновляем список
                from kivy.clock import Clock
                Clock.schedule_once(lambda dt: refresh_callback(), 0.1)

            deal_btn.bind(on_release=on_deal)
        else:
            deal_btn = Label(
                text="-",
                font_size=font_small,
                halign='center',
                valign='middle',
                color=(0.7, 0.7, 0.7, 1)
            )
            deal_btn.bind(size=deal_btn.setter('text_size'))
    except (json.JSONDecodeError, TypeError):
        deal_btn = Label(
            text="-",
            font_size=font_small,
            halign='center',
            valign='middle',
            color=(0.7, 0.7, 0.7, 1)
        )
        deal_btn.bind(size=deal_btn.setter('text_size'))

    layout.add_widget(name_label)
    layout.add_widget(attention_label)
    layout.add_widget(deal_btn)

    return layout


# -------------------------------------------------------------------------