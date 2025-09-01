# nobles.py

from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.popup import Popup
from kivy.metrics import dp, sp
from kivy.core.window import Window
from kivy.uix.scrollview import ScrollView
from kivy.graphics import Color, RoundedRectangle

from nobles_generator import (
    get_all_nobles,
    check_coup_attempts,
    update_noble_loyalty_for_event,
    attempt_secret_service_action,
    get_player_faction,
    get_noble_traits,
    pay_greedy_noble
    # Убраны check_player_money и deduct_player_money
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
    """Создание виджета для отображения одного дворянина (без аватара)"""
    # Адаптивные размеры
    is_android = hasattr(Window, 'keyboard') # Простая проверка
    widget_height = dp(80) if not is_android else dp(70)
    font_large = sp(16) if not is_android else sp(14)
    font_medium = sp(14) if not is_android else sp(12)
    font_small = sp(12) if not is_android else sp(10)
    padding_inner = dp(8) if not is_android else dp(5)
    spacing_inner = dp(5) if not is_android else dp(3)

    layout = BoxLayout(
        orientation='horizontal',
        size_hint_y=None,
        height=widget_height,
        spacing=spacing_inner,
        padding=padding_inner
    )

    # Информация (без аватара)
    info_layout = BoxLayout(orientation='vertical', spacing=spacing_inner/2)
    name_label = Label(
        text=noble_data['name'],
        font_size=font_large,
        halign='left',
        size_hint_y=None,
        height=dp(25) if not is_android else dp(20)
    )

    # --- Изменено: Расчет и отображение процента посещаемости ---
    # Предполагаем, что noble_data['attendance_history'] - это строка вида "1,0,1,1" или список [1,0,1,1]
    attendance_history_raw = noble_data.get('attendance_history', '')
    attention_text = "Проявленное внимание: ?"
    attention_color = (1, 1, 1, 1) # Белый по умолчанию

    if isinstance(attendance_history_raw, str) and attendance_history_raw:
        try:
            # Преобразуем строку в список целых чисел
            history_list = [int(x) for x in attendance_history_raw.split(',') if x.isdigit()]
        except ValueError:
            history_list = []
    elif isinstance(attendance_history_raw, list):
        # Если уже список (например, из get_all_nobles), используем его
        history_list = [x for x in attendance_history_raw if isinstance(x, int)]
    else:
        history_list = []

    if history_list:
        total_events = len(history_list)
        attended_events = sum(history_list)
        if total_events > 0:
            attendance_percentage = int((attended_events / total_events) * 100)
            attention_text = f"Проявленное внимание: {attendance_percentage}%"
            # Цветовая индикация на основе процента
            if attendance_percentage < 30:
                attention_color = (1, 0, 0, 1) # Красный
            elif attendance_percentage < 60:
                attention_color = (1, 1, 0, 1) # Желтый
            else:
                attention_color = (0, 1, 0, 1) # Зеленый
        # Примечание: Если total_events == 0, останется текст с '?' из инициализации
    # Если history_list пуст, останется текст с '?' из инициализации

    attention_label = Label(
        text=attention_text,
        font_size=font_medium,
        halign='left',
        color=attention_color,
        size_hint_y=None,
        height=dp(25) if not is_android else dp(20)
    )
    # ---------------------------------------------------------------

    info_layout.add_widget(name_label)
    info_layout.add_widget(attention_label)
    layout.add_widget(info_layout)

    # Кнопка "Договориться" (только для продажных)
    noble_traits = get_noble_traits(noble_data['ideology'])
    if noble_traits['type'] == 'greed':
        deal_btn = Button(
            text="Договориться",
            size_hint=(None, None),
            size=(dp(110) if not is_android else dp(100), dp(40) if not is_android else dp(35)),
            font_size=font_small,
            background_color=(0.3, 0.7, 0.3, 1) # Зеленоватый
        )
        deal_btn.bind(on_release=lambda btn, nd=noble_data, cp=cash_player: show_deal_popup(conn, nd, cp))
        layout.add_widget(deal_btn)
    else:
        layout.add_widget(Label(size_hint=(None, None), size=(dp(110) if not is_android else dp(100), 1)))

    return layout

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
        text="Если Вы заплатите, я буду лоббировать Ваши интересы.",
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
                # Обновляем отображение (например, меняем статус или цвет)
                # В данном случае, предположим, что лояльность увеличивается или статус меняется
                # Для простоты, просто покажем сообщение. Обновление списка произойдет при перезагрузке.
                # Можно добавить обновление конкретного виджета, если нужно.
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

def show_secret_service_popup(conn, on_result_callback, cash_player, refresh_main_list_callback):
    """Показывает всплывающее окно для Тайной службы с выбором цели."""
    COST_SECRET_SERVICE = 20_000_000 # Константа стоимости

    # --- Проверка баланса ---
    cash_player.load_resources()
    current_money = cash_player.resources.get("Кроны", 0)
    if current_money < COST_SECRET_SERVICE:
        insufficient_funds_popup = Popup(
            title="Недостаточно средств",
            content=Label(
                text=f"Недостаточно Крон для операции Тайной Службы.\nСтоимость: {format_number(COST_SECRET_SERVICE)}\nУ вас: {format_number(current_money)}",
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

    # --- Получаем список нелояльных дворян (без аватара) ---
    try:
        cursor = conn.cursor()
        # Запрашиваем нужные поля, исключая avatar
        cursor.execute("""
            SELECT id, name, loyalty, status, ideology
            FROM nobles 
            WHERE status = 'active' AND loyalty < 60
            ORDER BY loyalty ASC
        """)
        disloyal_nobles = cursor.fetchall()
        # Преобразуем кортежи в словари для удобства
        disloyal_nobles_data = [
            {
                'id': row[0],
                'name': row[1],
                'loyalty': row[2],
                'status': row[3],
                'ideology': row[4]
            }
            for row in disloyal_nobles
        ]
    except Exception as e:
        print(f"[ERROR] Ошибка при получении списка нелояльных дворян: {e}")
        on_result_callback({'success': False, 'message': "Ошибка получения списка целей."})
        return

    if not disloyal_nobles_data:
        no_targets_popup = Popup(
            title="Нет целей",
            content=Label(
                text="Нет нелояльных дворян для устранения.",
                halign='center',
                valign='middle',
                text_size=(dp(250), None)
            ),
            size_hint=(0.8, 0.4)
        )
        no_targets_popup.content.bind(size=no_targets_popup.content.setter('text_size'))
        no_targets_popup.open()
        on_result_callback({'success': False, 'message': "Нет доступных целей для устранения."})
        return

    # --- Создаем попап для выбора цели ---
    content = BoxLayout(orientation='vertical', padding=dp(10), spacing=dp(10))

    title_label = Label(
        text="Тайная служба - Выбор цели",
        font_size=sp(18),
        bold=True,
        size_hint_y=None,
        height=dp(30)
    )
    info_label = Label(
        text=f"Стоимость операции: {format_number(COST_SECRET_SERVICE)} крон.\nВыберите цель для устранения:",
        halign='center',
        valign='middle',
        font_size=sp(14),
        size_hint_y=None,
        height=dp(50)
    )
    info_label.bind(size=info_label.setter('text_size'))

    # --- Список дворян для выбора (без аватара) ---
    nobles_list_layout = BoxLayout(orientation='vertical', spacing=dp(5))
    scroll_view = ScrollView(do_scroll_x=False, size_hint=(1, 1))
    scroll_view.add_widget(nobles_list_layout)

    # Создаем кнопки для каждого нелояльного дворянина
    for noble_data in disloyal_nobles_data:
        # noble_id, noble_name, noble_loyalty, noble_status = noble_row
        noble_layout = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(50), padding=dp(5))

        # Информация (без аватара)
        info_layout = BoxLayout(orientation='vertical')
        name_label = Label(text=noble_data['name'], halign='left', font_size=sp(14), size_hint_y=None, height=dp(20))
        loyalty_label = Label(text=f"Лояльность: {noble_data['loyalty']}%", halign='left', font_size=sp(12), size_hint_y=None, height=dp(15))
        info_layout.add_widget(name_label)
        info_layout.add_widget(loyalty_label)
        noble_layout.add_widget(info_layout)

        # Кнопка выбора
        select_btn = Button(
            text="Устранить",
            size_hint=(None, None),
            size=(dp(80), dp(40)),
            font_size=sp(12),
            background_color=(0.8, 0.2, 0.2, 1) # Красный
        )

        def make_select_handler(n_id, n_name):
            def on_select(instance):
                target_selection_popup.dismiss()
                deduction_success = cash_player.deduct_resources(COST_SECRET_SERVICE)
                if deduction_success:
                    # Выполняем действие устранения конкретного дворянина
                    result = attempt_secret_service_action(conn, get_player_faction(conn), target_noble_id=n_id)
                    on_result_callback(result)
                    # --- Обновляем основной список ---
                    if callable(refresh_main_list_callback):
                        refresh_main_list_callback()
                else:
                    on_result_callback({'success': False, 'message': "Ошибка списания средств."})
            return on_select

        select_btn.bind(on_release=make_select_handler(noble_data['id'], noble_data['name']))
        noble_layout.add_widget(select_btn)

        nobles_list_layout.add_widget(noble_layout)

    # Кнопка отмены внизу
    cancel_btn_layout = BoxLayout(size_hint_y=None, height=dp(50))
    cancel_btn = Button(text="Отмена", size_hint_x=0.5)
    cancel_btn_layout.add_widget(Label())
    cancel_btn_layout.add_widget(cancel_btn)
    cancel_btn_layout.add_widget(Label())

    content.add_widget(title_label)
    content.add_widget(info_label)
    content.add_widget(scroll_view)
    content.add_widget(cancel_btn_layout)

    target_selection_popup = Popup(
        title="Выбор цели",
        content=content,
        size_hint=(0.9, 0.8),
        auto_dismiss=False
    )
    cancel_btn.bind(on_release=target_selection_popup.dismiss)
    target_selection_popup.open()

# --- calculate_event_cost остается без изменений ---

def show_event_popup(conn, player_faction, season_index, on_event_applied_callback, refresh_callback, cash_player):
    """Показывает всплывающее окно для выбора и проведения мероприятия."""
    event_type = get_event_type_by_season(season_index)
    event_season = get_season_name_by_index(season_index)
    cost = calculate_event_cost(season_index)

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
                text_size=(dp(250), None)
            ),
            size_hint=(0.8, 0.4)
        )
        insufficient_funds_popup.content.bind(size=insufficient_funds_popup.content.setter('text_size'))
        insufficient_funds_popup.open()
        return
    # ------------------------------------

    content = BoxLayout(orientation='vertical', padding=dp(15), spacing=dp(15))

    title_label = Label(
        text=f"Организовать мероприятие:\n{event_type}",
        font_size=sp(18),
        bold=True,
        halign='center',
        valign='middle',
        size_hint_y=None,
        height=dp(50)
    )
    title_label.bind(size=title_label.setter('text_size'))

    info_label = Label(
        text=f"Сезон: {event_season}\nВся знать будет приглашена.\nСтоимость: {format_number(cost)} крон",
        halign='center',
        valign='middle',
        font_size=sp(15)
    )
    info_label.bind(size=info_label.setter('text_size'))

    btn_layout = BoxLayout(size_hint_y=None, height=dp(50), spacing=dp(10))

    confirm_btn = Button(text="Провести", background_color=(0.2, 0.6, 0.8, 1))
    cancel_btn = Button(text="Отмена")

    popup = Popup(
        title="Мероприятие",
        content=content,
        size_hint=(0.85, 0.65),
        auto_dismiss=False
    )

    def on_confirm(instance):
        popup.dismiss()
        # --- Списание средств ---
        success = cash_player.deduct_resources(cost)
        if success:
            try:
                # Применяем мероприятие ко всем активным дворянам
                cursor = conn.cursor()
                cursor.execute("SELECT id FROM nobles WHERE status = 'active'")
                active_nobles = cursor.fetchall()

                for noble_row in active_nobles:
                    noble_id = noble_row[0]
                    update_noble_loyalty_for_event(conn, noble_id, player_faction, event_type, event_season)

                on_event_applied_callback("Мероприятие проведено.")
                # --- Обновляем основной список ---
                if callable(refresh_callback):
                    refresh_callback()
                # -----------------------------
            except Exception as e:
                print(f"Ошибка при проведении мероприятия: {e}")
                on_event_applied_callback("Ошибка при проведении мероприятия.")
        else:
            on_event_applied_callback("Ошибка транзакции. Недостаточно средств.")
        # -----------------------------------------------

    def on_cancel(instance):
        popup.dismiss()

    confirm_btn.bind(on_release=on_confirm)
    cancel_btn.bind(on_release=on_cancel)

    btn_layout.add_widget(confirm_btn)
    btn_layout.add_widget(cancel_btn)

    content.add_widget(title_label)
    content.add_widget(info_label)
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

    layout = BoxLayout(orientation='vertical', padding=padding_outer, spacing=spacing_outer)

    # --- Заголовок ---
    title = Label(
        text="Дворяне",
        font_size=font_title,
        size_hint_y=None,
        height=dp(45) if not is_android else dp(40),
        bold=True,
        color=(0.95, 0.9, 0.7, 1)
    )
    layout.add_widget(title)

    # --- Информационная плашка ---
    info_label = Label(
        text="Для того чтобы понять лояльность дворян, нужно проводить мероприятия, будьте готовы к любым ситуациям...",
        font_size=font_info,
        size_hint_y=None,
        height=dp(30) if not is_android else dp(25),
        color=(0.8, 0.8, 0.8, 1),
        halign='center'
    )
    info_label.bind(size=info_label.setter('text_size'))
    layout.add_widget(info_label)

    # --- Функция обновления списка ---
    def refresh_nobles_list():
        # Удаляем всех дворян (оставляем title, info_label, buttons_layout, coup_label?, close_btn)
        while len(layout.children) > 3:
            if layout.children[2] not in (buttons_layout, close_btn):
                layout.remove_widget(layout.children[2])
            else:
                break

        # Добавляем дворян заново
        nobles_data = get_all_nobles(conn)
        for noble_data in reversed(nobles_data):
            widget = create_noble_widget(noble_data, conn, cash_player)
            layout.add_widget(widget, index=2)

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
        widget = create_noble_widget(noble_data, conn, cash_player)
        layout.add_widget(widget)

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
        f"Организовать\n{get_event_type_by_season(season_index)}",
        lambda btn: show_event_popup(conn, player_faction, season_index, on_event_result, refresh_nobles_list, cash_player),
        bg_color=(0.5, 0.7, 0.9, 1)
    )

    buttons_layout.add_widget(secret_service_btn)
    buttons_layout.add_widget(organize_event_btn)
    layout.add_widget(buttons_layout)

    # --- Проверка на переворот ---
    coup_occurred = check_coup_attempts(conn)
    if coup_occurred:
        coup_label = Label(
            text="Попытка переворота!",
            color=(1, 0, 0, 1),
            font_size=sp(16) if not is_android else sp(14),
            size_hint_y=None,
            height=dp(35) if not is_android else dp(30),
            bold=True
        )
        layout.add_widget(coup_label)

    # --- Кнопка закрытия ---
    close_btn = styled_btn(
        "Закрыть",
        lambda btn: popup.dismiss(),
        bg_color=(0.5, 0.5, 0.5, 1)
    )

    scroll_view = ScrollView(do_scroll_x=False, size_hint=(1, 1))
    scroll_view.add_widget(layout)

    popup_pos_hint = {'center_x': 0.5, 'center_y': 0.5} if is_android else {}
    popup = Popup(
        title="Знать",
        content=scroll_view,
        size_hint=(0.96, 0.96) if not is_android else (1, 1),
        pos_hint=popup_pos_hint
    )

    layout.add_widget(close_btn)
    popup.open()




# --- calculate_event_cost остается без изменений ---
def calculate_event_cost(season_index):
    """Рассчитывает стоимость мероприятия в зависимости от сезона."""
    base_cost = 5_000_000
    seasonal_multiplier = {0: 1.2, 1: 1.0, 2: 1.5, 3: 1.1}
    multiplier = seasonal_multiplier.get(season_index, 1.0)
    return int(base_cost * multiplier)
# -------------------------------------------------------------------------
