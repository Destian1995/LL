
# nobles.py
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.popup import Popup
from kivy.metrics import dp, sp
from kivy.core.window import Window
from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout # Добавлено для таблиц
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
    base_cost = 2_000_000
    seasonal_multiplier = {0: 1.9, 1: 0.4, 2: 4.5, 3: 9.1}
    multiplier = seasonal_multiplier.get(season_index, 1.0)
    return int(base_cost * multiplier)

def show_deal_popup(conn, noble_data, cash_player): # Добавлен cash_player
    """Показывает всплывающее окно с требованием продажного дворянина."""
    noble_traits = get_noble_traits(noble_data['ideology'])
    if noble_traits['type'] != 'greed':
        return
    demand = noble_traits['demand']
    # --- Проверка баланса ---
    cash_player.load_resources() # Обновляем ресурсы перед проверкой
    current_money = cash_player.resources.get("Кроны", 0)
    if current_money < demand:
        insufficient_funds_popup = Popup(
            title="Недостаточно средств",
            content=Label(
                text=f"Недостаточно Крон для сделки.\nСтоимость: {format_number(demand)}\nУ вас: {format_number(current_money)}",
                halign='center',
                valign='middle',
                text_size=(dp(250), None)
            ),
            size_hint=(0.8, 0.4)
        )
        insufficient_funds_popup.content.bind(size=insufficient_funds_popup.content.setter('text_size'))
        insufficient_funds_popup.open()
        return
    # -------------------------------------------------------
    content = BoxLayout(orientation='vertical', padding=dp(15), spacing=dp(15))
    title_label = Label(
        text=f"{noble_data['name']}",
        font_size=sp(18),
        bold=True,
        size_hint_y=None,
        height=dp(30)
    )
    demand_label = Label(
        text=f"Моя лояльность стоит:\n{format_number(demand)} крон",
        font_size=sp(16),
        halign='center',
        valign='middle'
    )
    demand_label.bind(size=demand_label.setter('text_size'))
    info_label = Label(
        text="Если Вы заплатите, я буду продвигать Ваши интересы.",
        font_size=sp(14),
        color=(0.8, 0.8, 0.8, 1),
        halign='center',
        valign='middle'
    )
    info_label.bind(size=info_label.setter('text_size'))
    btn_layout = BoxLayout(size_hint_y=None, height=dp(50), spacing=dp(10))
    confirm_btn = Button(text="Заплатить", background_color=(0.3, 0.7, 0.3, 1))
    cancel_btn = Button(text="Отмена")
    popup = Popup(
        title="Сделка",
        content=content,
        size_hint=(0.85, 0.6),
        auto_dismiss=False
    )
    def on_confirm(instance):
        popup.dismiss()
        # --- Списание средств ---
        success = cash_player.deduct_resources(demand)
        if success:
            # Списание прошло успешно, теперь оплачиваем дворянина
            pay_success = pay_greedy_noble(conn, noble_data['id'], demand)
            if pay_success:
                success_popup = Popup(
                    title="Успех",
                    content=Label(text=f"Вы заплатили {format_number(demand)} крон. {noble_data['name']} теперь лоялен.", halign='center'),
                    size_hint=(0.8, 0.4)
                )
                success_popup.open()
            else:
                error_popup = Popup(
                    title="Ошибка",
                    content=Label(text="Произошла ошибка при оформлении сделки.", halign='center'),
                    size_hint=(0.8, 0.4)
                )
                error_popup.open()
        else:
            error_popup = Popup(
                title="Ошибка",
                content=Label(text="Недостаточно средств или ошибка транзакции.", halign='center'),
                size_hint=(0.8, 0.4)
            )
            error_popup.open()
        # -----------------------------------------------
    def on_cancel(instance):
        popup.dismiss()
    confirm_btn.bind(on_release=on_confirm)
    cancel_btn.bind(on_release=on_cancel)
    btn_layout.add_widget(confirm_btn)
    btn_layout.add_widget(cancel_btn)
    content.add_widget(title_label)
    content.add_widget(demand_label)
    content.add_widget(info_label)
    content.add_widget(btn_layout)
    popup.open()

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
        icon = "✓"
    else:
        title = "Ошибка"
        title_color = (0.9, 0.2, 0.2, 1)  # Красный
        icon = "✗"
    # Заголовок с иконкой
    title_label = Label(
        text=f"[b]{icon} {title}[/b]",
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


def show_secret_service_popup(conn, on_result_callback, cash_player, refresh_main_list_callback):
    """Показывает всплывающее окно для Тайной службы с выбором цели (табличный формат)."""
    COST_SECRET_SERVICE = 20_000_000  # Константа стоимости

    # --- Проверка баланса ---
    cash_player.load_resources()
    current_money = cash_player.resources.get("Кроны", 0)
    if current_money < COST_SECRET_SERVICE:
        insufficient_funds_popup = Popup(
            title="Недостаточно средств",
            content=Label(
                text=f"Не хватает крон, для доступа к засекреченной информации.\n"
                     f"Стоимость: {format_number(COST_SECRET_SERVICE)}\n"
                     f"У вас: {format_number(current_money)}",
                halign='center',
                valign='middle',
                text_size=(dp(250), None)
            ),
            size_hint=(0.8, 0.4)
        )
        insufficient_funds_popup.content.bind(size=insufficient_funds_popup.content.setter('text_size'))
        insufficient_funds_popup.open()
        return
    # ------------------------------------

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

            # --- Лояльность и Взгляды открываются только после 3 мероприятий ---
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
        show_secret_service_result_popup({'success': False, 'message': "Ошибка получения списка целей."})
        return

    if not nobles_data:
        no_targets_popup = Popup(
            title="Нет целей",
            content=Label(
                text="Нет активных дворян для устранения.",
                halign='center',
                valign='middle',
                text_size=(dp(250), None)
            ),
            size_hint=(0.8, 0.4)
        )
        no_targets_popup.content.bind(size=no_targets_popup.content.setter('text_size'))
        no_targets_popup.open()
        show_secret_service_result_popup({'success': False, 'message': "Нет доступных целей для устранения."})
        return

    # --- Адаптивные размеры ---
    is_android = hasattr(Window, 'keyboard')
    padding_main = dp(10) if not is_android else dp(5)
    spacing_main = dp(10) if not is_android else dp(7)
    font_title = sp(18) if not is_android else sp(16)
    font_info = sp(14) if not is_android else sp(12)
    font_header = sp(13) if not is_android else sp(11)
    font_noble_name = sp(14) if not is_android else sp(12)
    font_noble_loyalty = sp(12) if not is_android else sp(10)
    btn_height = dp(35) if not is_android else dp(30)
    btn_font_size = sp(11) if not is_android else sp(9)
    noble_item_height = dp(50) if not is_android else dp(45)

    # --- Создаем попап ---
    content = BoxLayout(orientation='vertical', padding=padding_main, spacing=spacing_main)
    title_label = Label(
        text="Санкция на физическое устранение (20 млн. крон)",
        font_size=font_title,
        bold=True,
        size_hint_y=None,
        height=dp(35) if not is_android else dp(30)
    )

    # --- Таблица дворян ---
    scroll_view = ScrollView(do_scroll_x=False, size_hint=(1, 1))
    table_layout = GridLayout(cols=4, spacing=dp(1) if not is_android else dp(0.5), size_hint_y=None)
    table_layout.bind(minimum_height=table_layout.setter('height'))

    header_names = ["Имя", "Лояльность", "Взгляды", ""]
    for header_text in header_names:
        header_label = Label(
            text=f"[b]{header_text}[/b]",
            font_size=font_header,
            markup=True,
            halign='center',
            valign='middle',
            size_hint_y=None,
            height=dp(30) if not is_android else dp(25),
            color=(0.8, 0.9, 1, 1)
        )
        header_label.bind(size=header_label.setter('text_size'))
        table_layout.add_widget(header_label)

    # --- Строки дворян ---
    for noble_data in nobles_data:
        display_name = get_noble_display_name_with_sympathies(noble_data)
        name_label = Label(
            text=display_name,
            halign='left',
            valign='middle',
            font_size=font_noble_name,
            size_hint_y=None,
            height=noble_item_height
        )
        name_label.bind(size=name_label.setter('text_size'))

        # Лояльность
        if noble_data['show_loyalty'] and noble_data['calculated_loyalty'] is not None:
            loyalty = noble_data['calculated_loyalty']
            if loyalty < 30:
                loyalty_color = (1, 0, 0, 1)
            elif loyalty < 60:
                loyalty_color = (1, 1, 0, 1)
            else:
                loyalty_color = (0, 1, 0, 1)
            loyalty_text = f"{loyalty}%"
        else:
            loyalty_color = (0.7, 0.7, 0.7, 1)
            loyalty_text = "?"

        loyalty_label = Label(
            text=loyalty_text,
            halign='center',
            valign='middle',
            font_size=font_noble_loyalty,
            size_hint_y=None,
            height=noble_item_height,
            color=loyalty_color
        )
        loyalty_label.bind(size=loyalty_label.setter('text_size'))

        # Взгляды
        if noble_data['show_views']:
            noble_traits = get_noble_traits(noble_data['ideology'])
            ideology_to_text = {
                'Борьба': "Борьба",
                'Смирение': "Смирение",
                'Любит Эльфы': "Любит Эльфов",
                'Любит Элины': "Любит Элинов",
                'Любит Люди': "Любит Людей",
                'Любит Вампиры': "Любит Вампиров",
                'Любит Адепты': "Любит Адептов",
            }
            if noble_traits['type'] == 'greed':
                views_text = "Продажный"
            else:
                views_text = ideology_to_text.get(noble_traits['value'], noble_traits['value'])
        else:
            views_text = "?"

        views_label = Label(
            text=views_text,
            halign='center',
            valign='middle',
            font_size=font_noble_loyalty,
            size_hint_y=None,
            height=noble_item_height,
            color=(0.9, 0.9, 0.9, 1)
        )
        views_label.bind(size=views_label.setter('text_size'))

        # Кнопка устранения
        select_btn = Button(
            text="Устранить",
            size_hint_y=None,
            height=btn_height,
            font_size=btn_font_size,
            background_color=(0.8, 0.2, 0.2, 1)
        )

        def make_select_handler(n_id, n_name, n_loyalty):
            def on_select(instance):
                target_selection_popup.dismiss()
                deduction_success = cash_player.deduct_resources(COST_SECRET_SERVICE)
                if deduction_success:
                    result = attempt_secret_service_action(conn, get_player_faction(conn), target_noble_id=n_id)
                    show_secret_service_result_popup(result)
                    if callable(refresh_main_list_callback):
                        refresh_main_list_callback()
                else:
                    show_secret_service_result_popup({'success': False, 'message': "Ошибка списания средств."})
            return on_select

        select_btn.bind(on_release=make_select_handler(noble_data['id'], noble_data['name'], noble_data['loyalty']))

        # Добавляем в таблицу
        table_layout.add_widget(name_label)
        table_layout.add_widget(loyalty_label)
        table_layout.add_widget(views_label)
        table_layout.add_widget(select_btn)

    scroll_view.add_widget(table_layout)

    # Кнопка отмены
    cancel_btn_layout = BoxLayout(size_hint_y=None, height=dp(50) if not is_android else dp(45))
    cancel_btn = Button(
        text="Отмена",
        size_hint_x=0.5,
        height=dp(45) if not is_android else dp(40),
        font_size=sp(14) if not is_android else sp(12)
    )
    cancel_btn_layout.add_widget(Label())
    cancel_btn_layout.add_widget(cancel_btn)
    cancel_btn_layout.add_widget(Label())

    content.add_widget(title_label)
    content.add_widget(scroll_view)
    content.add_widget(cancel_btn_layout)

    target_selection_popup = Popup(
        title="Выбор цели",
        content=content,
        size_hint=(0.95, 0.85) if not is_android else (1, 1),
        pos_hint={} if not is_android else {'center_x': 0.5, 'center_y': 0.5},
        auto_dismiss=False
    )

    cancel_btn.bind(on_release=target_selection_popup.dismiss)
    target_selection_popup.open()

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
    title_height = dp(60) if not is_android else dp(55)
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
    # --- Улучшенный заголовок с визуальным оформлением ---
    # --- Тип мероприятия с акцентом ---
    event_type_label = Label(
        text=f"[b]{event_type}[/b]",
        font_size=font_subtitle,
        halign='center',
        valign='middle',
        size_hint_y=None,
        height=dp(30) if not is_android else dp(25),
        markup=True,
        color=(0.7, 0.9, 1, 1)  # Голубой цвет
    )
    event_type_label.bind(size=event_type_label.setter('text_size'))
    # --- Информационная панель с красивым оформлением ---
    info_box = BoxLayout(orientation='vertical', size_hint_y=None, height=info_height, spacing=dp(5))
    season_label = Label(
        text=f"Сезон: [b]{event_season}[/b]",
        font_size=font_info,
        halign='center',
        valign='middle',
        markup=True,
        color=(0.8, 0.8, 1, 1)  # Светло-синий
    )
    season_label.bind(size=season_label.setter('text_size'))
    guests_label = Label(
        text="Вся знать будет приглашена",
        font_size=font_info - sp(1),
        halign='center',
        valign='middle',
        color=(0.7, 0.9, 0.7, 1)  # Светло-зеленый
    )
    guests_label.bind(size=guests_label.setter('text_size'))
    cost_label = Label(
        text=f"Стоимость: [b]{format_number(cost)}[/b] крон",
        font_size=font_info,
        halign='center',
        valign='middle',
        markup=True,
        color=(1, 0.8, 0.6, 1)  # Персиковый
    )
    cost_label.bind(size=cost_label.setter('text_size'))
    info_box.add_widget(season_label)
    info_box.add_widget(guests_label)
    info_box.add_widget(cost_label)
    # --- Кнопки с улучшенным дизайном ---
    btn_layout = BoxLayout(size_hint_y=None, height=btn_layout_height, spacing=dp(15) if not is_android else dp(10))
    confirm_btn = Button(
        text="Провести",
        font_size=font_btn,
        size_hint_y=None,
        height=btn_height,
        background_color=(0.2, 0.7, 0.4, 1),  # Зеленоватый
        background_normal=''
    )
    cancel_btn = Button(
        text="Отмена",
        font_size=font_btn,
        size_hint_y=None,
        height=btn_height,
        background_color=(0.6, 0.6, 0.6, 1),  # Серый
        background_normal=''
    )
    # Адаптивные размеры попапа
    popup_size_hint = (0.85, 0.7) if not is_android else (0.95, 0.75)
    popup_pos_hint = {} if not is_android else {'center_x': 0.5, 'center_y': 0.5}
    popup = Popup(
        title="Мероприятие",
        content=content,
        size_hint=popup_size_hint,
        pos_hint=popup_pos_hint,
        auto_dismiss=False
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
                # Отображаем красивый результат
                show_result_popup(
                    title="Успех!",
                    message="Мероприятие прошло",
                    is_success=True
                )
                if callable(refresh_callback):
                    refresh_callback()
            except Exception as e:
                print(f"Ошибка при проведении мероприятия: {e}")
                show_result_popup(
                    title="Ошибка",
                    message="Произошла ошибка при проведении мероприятия.",
                    is_success=False
                )
        else:
            show_result_popup(
                title="Ошибка",
                message="Недостаточно средств для проведения мероприятия.",
                is_success=False
            )
        # -----------------------------------------------
    def on_cancel(instance):
        popup.dismiss()
    confirm_btn.bind(on_release=on_confirm)
    cancel_btn.bind(on_release=on_cancel)
    btn_layout.add_widget(confirm_btn)
    btn_layout.add_widget(cancel_btn)
    # Добавляем все элементы в контент
    content.add_widget(event_type_label)
    content.add_widget(info_box)
    content.add_widget(btn_layout)
    popup.open()

def show_nobles_window(conn, faction, class_faction):
    """Открытие окна с дворянами"""
    cash_player = CalculateCash(faction, class_faction)
    player_faction = get_player_faction(conn)
    season_index = get_current_season_index(conn)

    # --- Главный layout ---
    is_android = hasattr(Window, 'keyboard')
    padding_outer = dp(10) if not is_android else dp(5)
    spacing_outer = dp(10) if not is_android else dp(7)
    font_title = sp(20) if not is_android else sp(18)
    font_info = sp(12) if not is_android else sp(10)
    font_header = sp(14) if not is_android else sp(12)

    layout = BoxLayout(orientation='vertical', padding=padding_outer, spacing=spacing_outer)

    # --- Заголовки таблицы ---
    headers_layout = GridLayout(cols=3, size_hint_y=None, height=dp(35) if not is_android else dp(30))

    name_header = Label(
        text="[b]Имя[/b]",
        font_size=font_header,
        markup=True,
        halign='left',
        valign='middle',
        color=(0.8, 0.9, 1, 1)  # Светло-голубой
    )
    name_header.bind(size=name_header.setter('text_size'))

    attention_header = Label(
        text="[b]Уровень внимания[/b]",
        font_size=font_header,
        markup=True,
        halign='center',
        valign='middle',
        color=(0.8, 0.9, 1, 1)  # Светло-голубой
    )
    attention_header.bind(size=attention_header.setter('text_size'))

    action_header = Label(
        text="[b]Действия[/b]",
        font_size=font_header,
        markup=True,
        halign='center',
        valign='middle',
        color=(0.8, 0.9, 1, 1)  # Светло-голубой
    )
    action_header.bind(size=action_header.setter('text_size'))

    headers_layout.add_widget(name_header)
    headers_layout.add_widget(attention_header)
    headers_layout.add_widget(action_header)
    layout.add_widget(headers_layout)

    # --- Контейнер для списка дворян ---
    nobles_container = BoxLayout(orientation='vertical', size_hint_y=1)
    layout.add_widget(nobles_container)

    # --- Функция обновления списка ---
    def refresh_nobles_list():
        # Очищаем только контейнер с дворянами
        nobles_container.clear_widgets()

        # Добавляем дворян заново в контейнер
        nobles_data = get_all_nobles(conn)
        for noble_data in nobles_data:  # Убран reversed, чтобы сохранить порядок
            widget = create_noble_widget_with_deal(noble_data, conn, cash_player, refresh_nobles_list)
            nobles_container.add_widget(widget)

    # --- Callbacks ---
    def on_secret_service_result(result):
        message_popup = Popup(
            title="Результат" if result['success'] else "Ошибка",
            content=Label(text=result['message'], halign='center', text_size=(dp(250), None)),
            size_hint=(0.85, 0.5)
        )
        message_popup.content.bind(size=message_popup.content.setter('text_size'))
        message_popup.open()
        if result['success']:
            refresh_nobles_list()

    def on_event_result(message):
        message_popup = Popup(
            title="Результат",
            content=Label(text=message, halign='center', text_size=(dp(250), None)),
            size_hint=(0.85, 0.4)
        )
        message_popup.content.bind(size=message_popup.content.setter('text_size'))
        message_popup.open()
        if "проведено" in message:
            refresh_nobles_list()

    # --- Первичное заполнение дворянами ---
    nobles_data = get_all_nobles(conn)
    for noble_data in nobles_data:
        widget = create_noble_widget_with_deal(noble_data, conn, cash_player, refresh_nobles_list)
        nobles_container.add_widget(widget)

    # --- Кнопка с мягким стилем ---
    def styled_btn(text, on_release_callback, bg_color=(0.6, 0.2, 0.2, 1)):
        btn = Button(
            text=text,
            font_size=sp(14),
            size_hint_y=None,
            height=dp(50),
            background_normal='',
            background_color=(0, 0, 0, 0),
            color=(1, 1, 1, 1)
        )
        with btn.canvas.before:
            from kivy.graphics import Color, RoundedRectangle
            Color(*bg_color)
            btn.bg = RoundedRectangle(radius=[dp(12)])
        def update_bg(instance, value):
            btn.bg.pos = instance.pos
            btn.bg.size = instance.size
        btn.bind(pos=update_bg, size=update_bg)
        btn.bind(on_release=on_release_callback)
        return btn

    # --- Кнопки действий ---
    buttons_layout = BoxLayout(
        size_hint_y=None,
        height=dp(55),
        spacing=dp(10)
    )

    secret_service_btn = styled_btn(
        "Тайная служба\n(20 млн)",
        lambda btn: show_secret_service_popup(conn, on_secret_service_result, cash_player, refresh_nobles_list),
        bg_color=(0.8, 0.5, 0.5, 1)
    )

    organize_event_btn = styled_btn(
        f'Провести мероприятие: ' f'\n"{get_event_type_by_season(season_index)}"',
        lambda btn: show_event_popup(conn, player_faction, season_index, refresh_nobles_list, cash_player),
        bg_color=(0.5, 0.7, 0.9, 1)
    )

    buttons_layout.add_widget(secret_service_btn)
    buttons_layout.add_widget(organize_event_btn)
    layout.add_widget(buttons_layout)
    layout._buttons_layout = buttons_layout

    # --- Кнопка закрытия ---
    close_btn = styled_btn(
        "Закрыть",
        lambda btn: popup.dismiss(),
        bg_color=(0.5, 0.5, 0.5, 1)
    )
    layout.add_widget(close_btn)
    layout._close_btn = close_btn

    scroll_view = ScrollView(do_scroll_x=False, size_hint=(1, 1))
    scroll_view.add_widget(layout)

    popup_pos_hint = {'center_x': 0.5, 'center_y': 0.5} if is_android else {}
    popup = Popup(
        title="Парламент",
        content=scroll_view,
        size_hint=(0.96, 0.96) if not is_android else (1, 1),
        pos_hint=popup_pos_hint
    )

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

def show_result_popup(title, message, is_success=True):
    """Отображает красивый popup с результатом действия."""
    is_android = hasattr(Window, 'keyboard')
    # Адаптивные размеры
    font_title = sp(18) if not is_android else sp(16)
    font_message = sp(15) if not is_android else sp(13)
    padding_main = dp(20) if not is_android else dp(15)
    spacing_main = dp(10) if not is_android else dp(8)
    content = BoxLayout(orientation='vertical', padding=padding_main, spacing=spacing_main)
    title_label = Label(
        text=f"[b]{title}[/b]",
        font_size=font_title,
        markup=True,
        halign='center',
        valign='middle',
        size_hint_y=None,
        height=dp(40) if not is_android else dp(35),
        color=(0.2, 0.8, 0.2, 1) if is_success else (0.9, 0.2, 0.2, 1)
    )
    title_label.bind(size=title_label.setter('text_size'))
    message_label = Label(
        text=message,
        font_size=font_message,
        halign='center',
        valign='middle',
        markup=True,
        color=(0.9, 0.9, 0.9, 1)
    )
    message_label.bind(size=message_label.setter('text_size'))
    content.add_widget(title_label)
    content.add_widget(message_label)
    popup = Popup(
        title="",
        content=content,
        size_hint=(0.85, 0.4) if not is_android else (0.9, 0.45),
        pos_hint={'center_x': 0.5, 'center_y': 0.5},
        auto_dismiss=True
    )
    popup.open()

# -------------------------------------------------------------------------