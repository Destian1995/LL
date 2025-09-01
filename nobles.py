# nobles.py
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.popup import Popup
from kivy.uix.image import Image
from kivy.metrics import dp, sp
from kivy.core.window import Window
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

def create_noble_widget(noble_data, conn):
    """Создание виджета для отображения одного дворянина"""
    # Адаптивные размеры
    is_android = hasattr(Window, 'keyboard') # Простая проверка
    avatar_size = dp(80) if not is_android else dp(70)
    widget_height = dp(110) if not is_android else dp(100)
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

    # Аватарка
    img = Image(
        source=noble_data['avatar'],
        size_hint=(None, None),
        size=(avatar_size, avatar_size),
        allow_stretch=True,
        keep_ratio=True
    )
    layout.add_widget(img)

    # Информация
    info_layout = BoxLayout(orientation='vertical', spacing=spacing_inner/2)
    name_label = Label(
        text=noble_data['name'],
        font_size=font_large,
        halign='left',
        text_size=(dp(140) if not is_android else dp(120), None),
        size_hint_y=None,
        height=dp(25) if not is_android else dp(20)
    )

    # Отображаем % посещений или предпочтения
    # known_loyalty в nobles_generator.py теперь отражает % посещений
    attendance_text = f"Посещения: {noble_data['known_loyalty']}"
    # Цвет для процента посещений
    known_loyalty_value = noble_data['known_loyalty']
    if isinstance(known_loyalty_value, int):
        if known_loyalty_value < 30:
            attendance_color = (1, 0, 0, 1) # Красный
        elif known_loyalty_value < 60:
            attendance_color = (1, 1, 0, 1) # Желтый
        else:
            attendance_color = (0, 1, 0, 1) # Зеленый
    else:
        attendance_color = (1, 1, 1, 1) # Белый для '?'

    attendance_label = Label(
        text=attendance_text,
        font_size=font_medium,
        halign='left',
        color=attendance_color,
        size_hint_y=None,
        height=dp(25) if not is_android else dp(20)
    )

    # Плейсхолдер для предпочтений (будет заполнен позже)
    preference_label = Label(
        text="", # Изначально пусто
        font_size=font_small,
        halign='left',
        color=(0.8, 0.8, 0.8, 1),
        size_hint_y=None,
        height=dp(20) if not is_android else dp(18)
    )

    # Сохраняем ссылки на labels для обновления
    noble_data['attendance_label'] = attendance_label
    noble_data['preference_label'] = preference_label

    info_layout.add_widget(name_label)
    info_layout.add_widget(attendance_label)
    info_layout.add_widget(preference_label)
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
        deal_btn.bind(on_release=lambda btn: show_deal_popup(conn, noble_data, cash_player)) # Передаем cash_player
        layout.add_widget(deal_btn)
    else:
        # Добавляем пустой виджет для выравнивания
        layout.add_widget(Label(size_hint=(None, None), size=(dp(110) if not is_android else dp(100), 1)))

    return layout

def show_deal_popup(conn, noble_data, cash_player): # Добавлен cash_player
    """Показывает всплывающее окно с требованием продажного дворянина."""
    noble_traits = get_noble_traits(noble_data['ideology'])
    if noble_traits['type'] != 'greed':
        return

    demand = noble_traits['demand']

    # --- Обновлено: Использование CalculateCash для проверки баланса ---
    cash_player.load_resources() # Обновляем ресурсы перед проверкой
    current_money = cash_player.resources.get("Кроны", 0)
    if current_money < demand:
        # Создаем и открываем попап с сообщением о нехватке средств
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
        return # Прерываем открытие основного попапа сделки
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
        # --- Обновлено: Использование CalculateCash для списания ---
        # Пытаемся списать деньги
        success = cash_player.deduct_resources(demand)
        if success:
            # Списание прошло успешно, теперь оплачиваем дворянина
            # pay_greedy_noble может использовать старую логику или быть адаптирована
            # если она также должна использовать CalculateCash, её нужно передать туда
            pay_success = pay_greedy_noble(conn, noble_data['id'], demand)
            if pay_success:
                # Обновляем отображение
                if 'preference_label' in noble_data:
                    noble_data['preference_label'].text = "Продажный (оплачен)"
                    noble_data['preference_label'].color = (0.3, 0.7, 0.3, 1) # Зеленый
                # Можно показать сообщение об успехе
                success_popup = Popup(
                    title="Успех",
                    content=Label(text=f"Вы заплатили {format_number(demand)} крон. {noble_data['name']} теперь лоялен.", halign='center'),
                    size_hint=(0.8, 0.4)
                )
                success_popup.open()
            else:
                # Ошибка при оплате дворянина (например, БД)
                error_popup = Popup(
                    title="Ошибка",
                    content=Label(text="Произошла ошибка при оформлении сделки.", halign='center'),
                    size_hint=(0.8, 0.4)
                )
                error_popup.open()
        else:
            # Недостаточно средств (или ошибка списания)
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

def show_secret_service_popup(conn, on_result_callback, cash_player): # Добавлен cash_player
    """Показывает всплывающее окно для Тайной службы."""
    COST_SECRET_SERVICE = 20_000_000 # Константа стоимости

    # --- Обновлено: Использование CalculateCash для проверки баланса ---
    cash_player.load_resources() # Обновляем ресурсы перед проверкой
    current_money = cash_player.resources.get("Кроны", 0)
    if current_money < COST_SECRET_SERVICE:
        # Создаем и открываем попап с сообщением о нехватке средств
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
        # Вызываем callback с ошибкой
        on_result_callback({'success': False, 'message': "Недостаточно средств для операции Тайной Службы."})
        return # Прерываем открытие основного попапа
    # ------------------------------------

    content = BoxLayout(orientation='vertical', padding=dp(15), spacing=dp(15))

    title_label = Label(
        text="Тайная служба",
        font_size=sp(18),
        bold=True,
        size_hint_y=None,
        height=dp(30)
    )

    info_label = Label(
        text="Санкция на физическое устранение нелояльных дворян. Стоимость 20 млн. крон.\nВероятность успеха: от 55% до 70%. \nПри провале есть риск падения лояльности среди остальных.",
        halign='center',
        valign='middle',
        font_size=sp(15)
    )
    info_label.bind(size=info_label.setter('text_size'))

    btn_layout = BoxLayout(size_hint_y=None, height=dp(50), spacing=dp(10))

    confirm_btn = Button(text="Устранить", background_color=(0.8, 0.2, 0.2, 1))
    cancel_btn = Button(text="Отмена")

    popup = Popup(
        title="Тайная служба",
        content=content,
        size_hint=(0.85, 0.6),
        auto_dismiss=False
    )

    def on_confirm(instance):
        popup.dismiss()
        # --- Обновлено: Использование CalculateCash для списания ---
        # Пытаемся списать деньги
        success = cash_player.deduct_resources(COST_SECRET_SERVICE)
        if success:
            # Списание прошло успешно, выполняем действие
            result = attempt_secret_service_action(conn, get_player_faction(conn))
            on_result_callback(result)
        else:
            # Недостаточно средств или ошибка
            on_result_callback({'success': False, 'message': "Ошибка транзакции. Недостаточно средств или внутренняя ошибка."})
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

# --- Добавьте вспомогательную функцию для расчета стоимости мероприятия ---
def calculate_event_cost(season_index):
    """Рассчитывает стоимость мероприятия в зависимости от сезона."""
    # Примерные стоимости, замените на реальные значения
    base_cost = 5_000_000
    seasonal_multiplier = {0: 1.2, 1: 1.0, 2: 1.5, 3: 1.1} # Зима, Весна, Лето, Осень
    multiplier = seasonal_multiplier.get(season_index, 1.0)
    return int(base_cost * multiplier)
# -------------------------------------------------------------------------

def show_event_popup(conn, player_faction, season_index, on_event_applied_callback, refresh_callback, cash_player): # Добавлен cash_player
    """Показывает всплывающее окно для выбора и проведения мероприятия."""
    event_type = get_event_type_by_season(season_index)
    event_season = get_season_name_by_index(season_index)
    cost = calculate_event_cost(season_index) # Рассчитываем стоимость

    # --- Обновлено: Использование CalculateCash для проверки баланса ---
    cash_player.load_resources() # Обновляем ресурсы перед проверкой
    current_money = cash_player.resources.get("Кроны", 0)
    if current_money < cost:
        # Создаем и открываем попап с сообщением о нехватке средств
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
        on_event_applied_callback("Недостаточно средств для проведения мероприятия.")
        return # Прерываем открытие основного попапа
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
        # --- Обновлено: Использование CalculateCash для списания ---
        # Пытаемся списать деньги
        success = cash_player.deduct_resources(cost)
        if success:
            # Списание прошло успешно, применяем мероприятие
            try:
                # Применяем мероприятие ко всем активным дворянам
                cursor = conn.cursor()
                cursor.execute("SELECT id FROM nobles WHERE status = 'active'")
                active_nobles = cursor.fetchall()

                for noble_row in active_nobles:
                    noble_id = noble_row[0]
                    update_noble_loyalty_for_event(conn, noble_id, player_faction, event_type, event_season)

                on_event_applied_callback("Мероприятие проведено.")
                # Обновляем основной список после мероприятия
                refresh_callback()
            except Exception as e:
                # Обработка ошибки выполнения мероприятия
                print(f"Ошибка при проведении мероприятия: {e}")
                on_event_applied_callback("Ошибка при проведении мероприятия.")
        else:
            # Недостаточно средств или ошибка
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
    # Создаём экземпляр класса CalculateCash
    cash_player = CalculateCash(faction, class_faction)

    player_faction = get_player_faction(conn)
    season_index = get_current_season_index(conn)

    def on_secret_service_result(result):
        # Показываем результат
        message_popup = Popup(
            title="Результат" if result['success'] else "Ошибка",
            content=Label(text=result['message'], halign='center', text_size=(dp(250), None)),
            size_hint=(0.85, 0.5)
        )
        message_popup.content.bind(size=message_popup.content.setter('text_size'))
        message_popup.open()
        if result['success']:
            refresh_nobles_list() # Обновляем список, если кто-то был устранен

    def on_event_result(message):
        message_popup = Popup(
            title="Результат",
            content=Label(text=message, halign='center', text_size=(dp(250), None)),
            size_hint=(0.85, 0.4)
        )
        message_popup.content.bind(size=message_popup.content.setter('text_size'))
        message_popup.open()
        # Список обновится через refresh_callback в show_event_popup

    def refresh_nobles_list():
        # Очищаем layout, кроме заголовка, кнопок и кнопки закрытия
        # Предполагаем порядок: [close_btn, buttons_layout, title, ...noble_widgets...]
        while len(layout.children) > 3:
            layout.remove_widget(layout.children[-1]) # Удаляем первый добавленный виджет (в конце списка)

        nobles_data = get_all_nobles(conn)
        # Добавляем виджеты в обратном порядке, чтобы они шли сверху вниз
        for noble_data in reversed(nobles_data):
            widget = create_noble_widget(noble_data, conn)
            layout.add_widget(widget, index=len(layout.children)-2) # Вставляем перед buttons_layout

    nobles_data = get_all_nobles(conn)

    # Адаптивный макет
    is_android = hasattr(Window, 'keyboard')
    padding_outer = dp(10) if not is_android else dp(5)
    spacing_outer = dp(10) if not is_android else dp(7)
    font_title = sp(20) if not is_android else sp(18)

    layout = BoxLayout(orientation='vertical', padding=padding_outer, spacing=spacing_outer)

    title = Label(
        text="Дворяне",
        font_size=font_title,
        size_hint_y=None,
        height=dp(45) if not is_android else dp(40),
        bold=True
    )
    layout.add_widget(title)

    # Добавляем виджеты дворян
    for noble_data in nobles_data:
        widget = create_noble_widget(noble_data, conn)
        layout.add_widget(widget)

    # Общие кнопки
    buttons_layout = BoxLayout(
        size_hint_y=None,
        height=dp(55) if not is_android else dp(50),
        spacing=dp(10) if not is_android else dp(7)
    )

    secret_service_btn = Button(
        text="Тайная служба\n(20 млн)",
        background_color=(0.8, 0.2, 0.2, 1),
        font_size=sp(14) if not is_android else sp(12)
    )
    # Передаем cash_player в show_secret_service_popup
    secret_service_btn.bind(on_release=lambda btn: show_secret_service_popup(conn, on_secret_service_result, cash_player))

    organize_event_btn = Button(
        text=f"Организовать\n{get_event_type_by_season(season_index)}",
        background_color=(0.2, 0.6, 0.8, 1),
        font_size=sp(14) if not is_android else sp(12)
    )
    # Передаем cash_player в show_event_popup
    organize_event_btn.bind(on_release=lambda btn: show_event_popup(
        conn, player_faction, season_index, on_event_result, refresh_nobles_list, cash_player))

    buttons_layout.add_widget(secret_service_btn)
    buttons_layout.add_widget(organize_event_btn)
    layout.add_widget(buttons_layout)

    # Проверка на переворот
    coup_occurred = check_coup_attempts(conn)
    if coup_occurred:
        coup_label = Label(
            text="⚠️ Попытка переворота!",
            color=(1, 0, 0, 1),
            font_size=sp(16) if not is_android else sp(14),
            size_hint_y=None,
            height=dp(35) if not is_android else dp(30),
            bold=True
        )
        layout.add_widget(coup_label)

    # Кнопка закрытия
    close_btn = Button(
        text="Закрыть",
        size_hint_y=None,
        height=dp(50) if not is_android else dp(45),
        font_size=sp(16) if not is_android else sp(14)
    )
    # Обернем layout в ScrollView для лучшей адаптации на маленьких экранах
    from kivy.uix.scrollview import ScrollView
    scroll_view = ScrollView(do_scroll_x=False, size_hint=(1, 1))
    scroll_view.add_widget(layout)

    popup_pos_hint = {'center_x': 0.5, 'center_y': 0.5} if is_android else {}
    popup = Popup(
        title="Знать",
        content=scroll_view,
        size_hint=(0.96, 0.96) if not is_android else (1, 1),
        pos_hint=popup_pos_hint
    )
    close_btn.bind(on_release=popup.dismiss)
    layout.add_widget(close_btn)

    popup.open()
