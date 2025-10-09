from kivy.uix.checkbox import CheckBox

from db_lerdon_connect import *
from heroes import open_artifacts_popup
from create_artifacts import workshop

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


def save_building_change(faction_name, city, building_type, delta, conn):
    """
    Обновляет количество зданий для указанного города в базе данных.
    delta — изменение (например, +1 или -1).
    """

    cursor = conn.cursor()

    try:
        # Проверяем, существует ли запись для данного города и типа здания
        cursor.execute('''
            SELECT count 
            FROM buildings 
            WHERE city_name = ? AND faction = ? AND building_type = ?
        ''', (city, faction_name, building_type))
        row = cursor.fetchone()

        if row:
            # Обновляем существующую запись
            new_count = row[0] + delta
            if new_count < 0:
                new_count = 0  # Предотвращаем отрицательные значения
            cursor.execute('''
                UPDATE buildings 
                SET count = ? 
                WHERE city_name = ? AND faction = ? AND building_type = ?
            ''', (new_count, city, faction_name, building_type))
        else:
            # Добавляем новую запись
            cursor.execute('''
                INSERT INTO buildings (city_name, faction, building_type, count)
                VALUES (?, ?, ?, ?)
            ''', (city, faction_name, building_type, delta))

        conn.commit()
    except sqlite3.Error as e:
        print(f"Ошибка при сохранении изменений в зданиях: {e}")



class Faction:
    def __init__(self, name, conn):
        self.faction = name
        self.conn = conn
        self.cursor = self.conn.cursor()
        self.resources = self.load_resources_from_db()  # Загрузка ресурсов
        self.buildings = self.load_buildings()  # Загрузка зданий
        self.trade_agreements = self.load_trade_agreements()
        self.city_count = 0
        self.cities = self.load_cities()  # Загрузка городов
        self.hospitals = 0
        self.factories = 0
        self.taxes = 0
        self.food_info = 0
        self.work_peoples = 0
        self.money_info = 0
        self.born_peoples = 0
        self.money_up = 0
        self.taxes_info = 0
        self.food_peoples = 0
        self.tax_effects = 0
        self.clear_up_peoples = 0
        self.current_consumption = 0
        self.turn = 0
        self.last_turn_loaded = -1  # Последний загруженный номер хода
        self.raw_material_price_history = []  # История цен на еду
        self.current_tax_rate = 0  # Начальная ставка налога — по умолчанию 0%
        self.turns = 0  # Счетчик ходов
        self.tax_set = False  # Флаг, установлен ли налог
        self.custom_tax_rate = 0  # Новый атрибут для хранения пользовательской ставки налога
        self.auto_build_enabled = False
        self.auto_build_ratio = (1, 1)  # По умолчанию 1:1
        self.load_auto_build_settings()
        self.cities_buildings = {city['name']: {'Больница': 0, 'Фабрика': 0} for city in self.cities}

        self.resources = {
            'Кроны': self.money,
            'Рабочие': self.free_peoples,
            'Кристаллы': self.raw_material,
            'Население': self.population,
            'Потребление': self.current_consumption,
            'Лимит армии': self.max_army_limit
        }
        self.economic_params = {
            "Люди": {"tax_rate": 0.07},
            "Эльфы": {"tax_rate": 0.03},
            "Вампиры": {"tax_rate": 0.02},
            "Адепты": {"tax_rate": 0.017},
            "Элины": {"tax_rate": 0.01},
        }

        self.is_first_run = True  # Флаг для первого запуска
        self.generate_raw_material_price()  # Генерация начальной цены на еду

    def load_data(self, table, columns, condition=None, params=None):
        """
        Универсальный метод для загрузки данных из таблицы базы данных.
        :param table: Имя таблицы.
        :param columns: Список колонок для выборки.
        :param condition: Условие WHERE (строка).
        :param params: Параметры для условия.
        :return: Список кортежей с данными.
        """
        try:
            query = f"SELECT {', '.join(columns)} FROM {table}"
            if condition:
                query += f" WHERE {condition}"
            self.cursor.execute(query, params or ())
            return self.cursor.fetchall()
        except sqlite3.Error as e:
            return []

    def load_resources(self):
        """Загружает ресурсы из таблицы resources."""
        rows = self.load_data("resources", ["resource_type", "amount"], "faction = ?", (self.faction,))
        resources = {"Рабочие": 0, "Кроны": 0, "Кристаллы": 0, "Население": 0}
        for resource_type, amount in rows:
            resources[resource_type] = amount
        return resources

    def load_auto_build_settings(self):
        conn = self.conn
        cursor = conn.cursor()
        cursor.execute('''
            SELECT enabled, hospitals_ratio, factories_ratio 
            FROM auto_build_settings 
            WHERE faction = ?
        ''', (self.faction,))
        result = cursor.fetchone()

        if result:
            self.auto_build_enabled = bool(result[0])
            # Сохраняем пропорцию как кортеж целых чисел
            self.auto_build_ratio = (result[1], result[2])
        else:
            self.auto_build_ratio = (1, 1)  # Значение по умолчанию

    def save_auto_build_settings(self):
        conn = self.conn
        cursor = conn.cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO auto_build_settings 
            (faction, enabled, hospitals_ratio, factories_ratio)
            VALUES (?, ?, ?, ?)
        ''', (self.faction, int(self.auto_build_enabled),
              self.auto_build_ratio[0], self.auto_build_ratio[1]))
        conn.commit()


    def city_has_space(self, city_name):
        current = self.cities_buildings.get(city_name, {"Больница": 0, "Фабрика": 0})
        return current["Больница"] + current["Фабрика"] < 500

    # Основной метод автоматического строительства
    def auto_build(self):
        """
        Рассчитывает количество возможных зданий на основе текущих ресурсов
        и передает результат в методы build_factory и build_hospital.
        Учитывает лимит в 500 зданий на город и минимальное количество крон (200).
        """
        if not self.auto_build_enabled:
            return

        # Проверяем, достаточно ли денег для строительства
        if self.money < 200:
            print("Недостаточно крон для авто-строительства. Минимум требуется 200 крон.")
            return
        print("Проверка доступных городов перед загрузкой:", self.cities)
        # Загружаем актуальные данные о городах и зданиях
        self.load_cities()
        self.load_buildings()

        # Получаем соотношение из настроек авто-строительства
        hospitals_ratio, factories_ratio = self.auto_build_ratio
        total_per_cycle = hospitals_ratio + factories_ratio

        if total_per_cycle == 0:
            return

        # Определяем стоимость одного цикла строительства
        hospital_cost = 300
        factory_cost = 200
        cost_per_cycle = hospitals_ratio * hospital_cost + factories_ratio * factory_cost

        if cost_per_cycle == 0:
            return

        # Проверяем доступные ресурсы
        max_cycles_by_money = self.money // cost_per_cycle
        if max_cycles_by_money == 0:
            return

        # Проверяем доступное место в городах
        available_cities = []
        print("Проверка доступных городов после загрузки:", self.cities)
        for city in self.cities:
            city_name = city['name']
            current_buildings = self.cities_buildings.get(city_name, {"Больница": 0, "Фабрика": 0})
            total_current = current_buildings["Больница"] + current_buildings["Фабрика"]
            space_left = 500 - total_current
            available_cities.extend([city_name] * (space_left // total_per_cycle))

        # Если доступных городов нет, завершаем выполнение
        if not available_cities:
            print("Нет доступных городов для строительства.")
            return

        max_cycles_by_cities = len(available_cities) // total_per_cycle
        max_full_cycles = min(max_cycles_by_money, max_cycles_by_cities)

        if max_full_cycles == 0:
            print("Недостаточно ресурсов или места в городах для строительства.")
            return

        # Рассчитываем общее количество зданий
        total_hospitals = hospitals_ratio * max_full_cycles
        total_factories = factories_ratio * max_full_cycles
        total_cost = max_full_cycles * cost_per_cycle

        # Списываем средства
        if not self.cash_build(total_cost):
            print("Не удалось списать средства для строительства.")
            return

        # Распределяем здания по городам
        try:
            selected_cities = random.sample(available_cities, max_full_cycles * total_per_cycle)
        except ValueError:
            print("Ошибка при выборе городов. Возможно, недостаточно доступных городов.")
            return

        try:
            # Группируем здания по городам
            city_buildings = {}
            for i in range(total_hospitals):
                city = selected_cities[i]
                if self.city_has_space(city):  # Проверяем, есть ли место в городе
                    if city not in city_buildings:
                        city_buildings[city] = {"Больница": 0, "Фабрика": 0}
                    city_buildings[city]["Больница"] += 1

            for i in range(total_hospitals, total_hospitals + total_factories):
                city = selected_cities[i]
                if self.city_has_space(city):  # Проверяем, есть ли место в городе
                    if city not in city_buildings:
                        city_buildings[city] = {"Больница": 0, "Фабрика": 0}
                    city_buildings[city]["Фабрика"] += 1

            # Строим здания за один вызов для каждого города
            for city, buildings in city_buildings.items():
                if buildings["Больница"] > 0:
                    self.build_hospital(city, quantity=buildings["Больница"])
                if buildings["Фабрика"] > 0:
                    self.build_factory(city, quantity=buildings["Фабрика"])

        except Exception as e:
            print(f"Ошибка в авто-строительстве: {e}")

    def load_buildings(self):
        """
        Загружает данные о зданиях для текущей фракции из таблицы buildings.
        """
        try:
            self.cursor.execute('''
                SELECT city_name, building_type, count 
                FROM buildings 
                WHERE faction = ?
            ''', (self.faction,))
            rows = self.cursor.fetchall()

            # Сброс текущих данных о зданиях
            self.cities_buildings = {}
            total_hospitals = 0
            total_factories = 0

            for row in rows:
                city_name, building_type, count = row
                if city_name not in self.cities_buildings:
                    self.cities_buildings[city_name] = {"Больница": 0, "Фабрика": 0}

                # Обновление данных для конкретного города
                if building_type == "Больница":
                    self.cities_buildings[city_name]["Больница"] += count
                    total_hospitals += count
                elif building_type == "Фабрика":
                    self.cities_buildings[city_name]["Фабрика"] += count
                    total_factories += count

            # Обновление глобальных показателей
            self.hospitals = total_hospitals
            self.factories = total_factories

        except sqlite3.Error as e:
            print(f"Ошибка при загрузке зданий: {e}")

    def load_trade_agreements(self):
        """Загружает данные о торговых соглашениях для текущей фракции из таблицы trade_agreements."""
        rows = self.load_data(
            "trade_agreements",
            ["initiator_faction", "target_faction", "initiator_type_resource",
             "initiator_summ_resource", "target_type_resource", "target_summ_resource"],
            "initiator_faction = ? OR target_faction = ?",
            (self.faction, self.faction)
        )
        trade_agreements = []
        for row in rows:
            trade_agreements.append({
                "initiator_faction": row[0],
                "target_faction": row[1],
                "initiator_type_resource": row[2],
                "initiator_summ_resource": row[3],
                "target_type_resource": row[4],
                "target_summ_resource": row[5]
            })
        return trade_agreements

    def load_cities(self):
        """
        Загружает список городов для текущей фракции из таблицы cities.
        Не перезаписывает существующие данные о зданиях в городах.
        """

        rows = self.load_data("cities", ["name", "coordinates"], "faction = ?", (self.faction,))
        print(f"[DEBUG ROWS CITY!]:{rows}")
        cities = []
        self.city_count = 0

        for row in rows:
            name, coordinates = row
            try:
                coordinates = coordinates.strip('[]')
                x, y = map(int, coordinates.split(','))
            except ValueError:
                print(f"Ошибка при разборе координат для города {name}: {coordinates}")
                x, y = 0, 0

            cities.append({"name": name, "x": x, "y": y})

            # Не перезаписываем, если уже есть данные о зданиях
            if name not in self.cities_buildings:
                self.cities_buildings[name] = {'Больница': 0, 'Фабрика': 0}

            self.city_count += 1
        self.cities = cities
        return cities

    def build_factory(self, city, quantity=1):
        """Увеличить количество фабрик в указанном городе на заданное количество."""
        if city not in self.cities_buildings:
            self.cities_buildings[city] = {'Больница': 0, 'Фабрика': 0}
        self.cities_buildings[city]['Фабрика'] += quantity  # Обновляем локальные данные
        save_building_change(self.faction, city, "Фабрика", quantity, self.conn)  # Передаем изменение
        self.load_buildings()  # Пересчитываем общие показатели

    def build_hospital(self, city, quantity=1):
        """Увеличить количество больниц в указанном городе на заданное количество."""
        if city not in self.cities_buildings:
            self.cities_buildings[city] = {'Больница': 0, 'Фабрика': 0}
        self.cities_buildings[city]['Больница'] += quantity
        save_building_change(self.faction, city, "Больница", quantity, self.conn)
        self.load_buildings()  # Пересчитываем общие показатели

    def cash_build(self, money):
        """Списывает деньги, если их хватает, и возвращает True, иначе False."""
        if self.money >= money:
            self.money -= money
            self.save_resources_to_db()
            return True
        else:
            return False

    def get_income_per_person(self):
        """Получение дохода с одного человека для данной фракции."""
        if self.tax_set and self.custom_tax_rate is not None:
            return self.custom_tax_rate
        params = self.economic_params[self.faction]
        return params["tax_rate"]

    def calculate_tax_income(self):
        """Расчет дохода от налогов с учетом установленной ставки."""
        if not self.tax_set:
            print("Налог не установлен. Прироста от налогов нет.")
            self.taxes = 0
        else:
            # Используем пользовательскую ставку налога или базовую, если пользовательская не задана
            tax_rate = self.custom_tax_rate if self.custom_tax_rate is not None else self.get_base_tax_rate()
            self.taxes = self.population * tax_rate  # Применяем базовую налоговую ставку
        return self.taxes

    def set_taxes(self, new_tax_rate):
        """
        Установка нового уровня налогов и обновление ресурсов.
        """
        self.custom_tax_rate = self.get_base_tax_rate() * new_tax_rate
        self.tax_set = True
        self.calculate_tax_income()

    def tax_effect(self, tax_rate):
        """
        Рассчитывает процентное изменение населения на основе ставки налога.
        :param tax_rate: Текущая ставка налога (в процентах).
        :return: Процент изменения населения (положительное или отрицательное значение).
        """
        if tax_rate >= 90:
            return -89  # Критическая убыль населения (-89%)
        elif 80 <= tax_rate < 90:
            return -51  # Значительная убыль населения (-51%)
        elif 65 <= tax_rate < 80:
            return -37  # Умеренная убыль населения (-37%)
        elif 45 <= tax_rate < 65:
            return -21  # Умеренная убыль населения (-21%)
        elif 35 <= tax_rate < 45:
            return -8  # Небольшая убыль населения (-8%)
        elif 25 <= tax_rate < 35:
            return 0  # Нейтральный эффект (0%)
        elif 16 <= tax_rate < 25:
            return 11  # Небольшой рост (5%)
        elif 10 <= tax_rate < 16:
            return 20  # Небольшой рост населения (+11%)
        elif 1 <= tax_rate < 10:
            return 32  # Небольшой рост населения (+18%)
        else:
            return 54  # Существенный рост населения (+34%)

    def apply_tax_effect(self, tax_rate):
        """
        Применяет эффект налогов на население в виде процентного изменения.
        :param tax_rate: Текущая ставка налога (в процентах).
        :return: Абсолютное изменение населения.
        """
        # Получаем процентное изменение населения
        percentage_change = self.tax_effect(tax_rate)

        # Загружаем текущее население из базы данных
        try:
            self.cursor.execute('''
                SELECT amount
                FROM resources
                WHERE faction = ? AND resource_type = "Население"
            ''', (self.faction,))
            row = self.cursor.fetchone()
            current_population = row[0] if row else 0
        except sqlite3.Error as e:
            print(f"Ошибка при загрузке данных о населении: {e}")
            current_population = 0

        # Рассчитываем абсолютное изменение населения
        population_change = int(current_population * (percentage_change / 100))

        # Применяем эффект налогов
        self.tax_effects = population_change
        return self.tax_effects

    def calculate_base_tax_rate(self, tax_rate):
        """Формула расчёта базовой налоговой ставки для текущей фракции."""
        params = self.economic_params[self.faction]
        base_tax_rate = params["tax_rate"]  # Базовая ставка налога для текущей фракции

        # Формируем корректировочный коэффициент на основе введённой ставки
        multiplier = tax_rate
        # Возвращаем корректированную налоговую ставку
        return base_tax_rate * multiplier

    def get_base_tax_rate(self):
        """Получение базовой налоговой ставки для текущей фракции."""
        return self.economic_params[self.faction]["tax_rate"]

    def show_popup(self, title, message):
        """Отображает всплывающее окно с сообщением."""
        popup = Popup(title=title, content=Label(text=message), size_hint=(0.6, 0.4))
        popup.open()

    def load_available_buildings_from_db(self):
        """
        Загружает список доступных зданий для текущей фракции из базы данных.
        """
        try:
            self.cursor.execute('''
                SELECT DISTINCT building_type
                FROM buildings
                WHERE faction = ?
            ''', (self.faction,))
            rows = self.cursor.fetchall()
            return [row[0] for row in rows]  # Возвращаем список типов зданий
        except sqlite3.Error as e:
            print(f"Ошибка при загрузке зданий: {e}")
            return []

    def update_cash(self):
        """
        Обновляет ресурсы и сохраняет их в БД.
        """
        self.load_resources()
        self.resources['Кроны'] = self.money
        self.resources['Рабочие'] = self.free_peoples
        self.resources['Кристаллы'] = self.raw_material
        self.resources['Население'] = self.population
        self.resources['Потребление'] = self.current_consumption
        self.resources['Лимит армии'] = self.max_army_limit
        self.save_resources_to_db()
        return self.resources

    def check_resource_availability(self, resource_type, required_amount):
        """
        Проверяет, достаточно ли у фракции ресурсов для выполнения сделки.

        :param resource_type: Тип ресурса (например, "Кристаллы", "Кроны", "Рабочие", "Население").
        :param required_amount: Требуемое количество ресурсов.
        :return: True, если ресурсов достаточно, иначе False.
        """
        # Убедимся, что required_amount является числом и не отрицательным
        if not isinstance(required_amount, (int, float)) or required_amount < 0:
            print(f"Некорректное требуемое количество ресурсов: {required_amount}")
            return False

        # Получаем текущее значение ресурса из словаря self.resources
        current_amount = self.resources.get(resource_type, 0)

        # Если значение None или некорректное, считаем его равным 0
        if current_amount is None or not isinstance(current_amount, (int, float)):
            current_amount = 0

        # Проверяем, достаточно ли ресурсов
        if current_amount >= required_amount:
            return True
        else:
            print(f"Недостаточно ресурсов типа '{resource_type}': "
                  f"требуется {required_amount}, доступно {current_amount}")
            return False

    def update_resource_deals(self, resource_type='', amount=''):
        """
        Обновляет количество ресурсов фракции на указанное значение.

        :param resource_type: Тип ресурса (например, "Кристаллы", "Кроны", "Рабочие", "Население").
        :param amount: Изменение количества ресурсов (положительное или отрицательное).
        """
        if resource_type == "Кристаллы":
            self.resources['Кристаллы'] += amount
        elif resource_type == "Кроны":
            self.resources['Кроны'] += amount
        elif resource_type == "Население":
            self.resources['Население'] += amount
        elif resource_type == "Рабочие":
            self.resources['Рабочие'] += amount
        else:
            raise ValueError(f"Неизвестный тип ресурса: {resource_type}")

    def update_trade_resources_from_db(self):
        try:
            # Проверяем все неподтвержденные сделки (agree = 0)
            self.cursor.execute('''
                SELECT id, initiator, target_faction 
                FROM trade_agreements 
                WHERE (initiator = ? OR target_faction = ?) AND agree = 0
            ''', (self.faction, self.faction))

            rejected_rows = self.cursor.fetchall()

            # Выводим сообщение о том, что сделка была отклонена
            for row in rejected_rows:
                trade_id, initiator, target_faction = row

                if initiator == self.faction:
                    show_message("Отказ", f"{target_faction} отказались от сделки.")
                elif target_faction == self.faction:
                    show_message("Отказ", f"{initiator} отказались от сделки.")

            # Удаляем все неподтвержденные сделки
            self.cursor.execute('''
                DELETE FROM trade_agreements 
                WHERE (initiator = ? OR target_faction = ?) AND agree = 0
            ''', (self.faction, self.faction))

            # Извлекаем все подтвержденные сделки
            self.cursor.execute('''
                SELECT id, initiator, target_faction, initiator_type_resource, 
                       initiator_summ_resource, target_type_resource, target_summ_resource
                FROM trade_agreements 
                WHERE (initiator = ? OR target_faction = ?) AND agree = 1
            ''', (self.faction, self.faction))

            rows = self.cursor.fetchall()
            completed_trades = []  # Список завершенных сделок

            for row in rows:
                trade_id, initiator, target_faction, initiator_type_resource, \
                    initiator_summ_resource, target_type_resource, target_summ_resource = row

                # Проверяем, была ли сделка одобрена
                show_message(f"{initiator_type_resource}", f" {target_faction} одобрили сделку!")

                if initiator == self.faction:
                    # Проверяем наличие ресурсов только если они должны быть отданы
                    if initiator_summ_resource and initiator_type_resource:
                        if not self.check_resource_availability(initiator_type_resource, initiator_summ_resource):
                            print(f"Недостаточно ресурсов для выполнения сделки с фракцией {initiator}.")
                            continue

                        # Отнимаем ресурс, который отдает инициатор
                        self.update_resource_deals(initiator_type_resource, -initiator_summ_resource)

                    # Добавляем ресурс, который получает инициатор (если есть что получать)
                    if target_summ_resource and target_type_resource:
                        self.update_resource_deals(target_type_resource, target_summ_resource)

                elif target_faction == self.faction:
                    # Проверяем наличие ресурсов только если они должны быть отданы
                    if target_summ_resource and target_type_resource:
                        if not self.check_resource_availability(target_type_resource, target_summ_resource):
                            print(f"Недостаточно ресурсов для выполнения сделки с фракцией {initiator}.")
                            continue

                        # Отнимаем ресурс, который отдает целевая фракция
                        self.update_resource_deals(target_type_resource, -target_summ_resource)

                    # Добавляем ресурс, который получает целевая фракция (если есть что получать)
                    if initiator_summ_resource and initiator_type_resource:
                        self.update_resource_deals(initiator_type_resource, initiator_summ_resource)
                        print(f"Сделка успешно выполнена: {trade_id}")

                # Добавляем сделку в список завершенных
                completed_trades.append(trade_id)

            # Удаляем завершенные сделки
            for trade_id in completed_trades:
                self.cursor.execute('''
                    DELETE FROM trade_agreements 
                    WHERE id = ?
                ''', (trade_id,))

            self.save_resources_to_db()

        except sqlite3.Error as e:
            print(f"Ошибка при обновлении ресурсов на основе торговых соглашений: {e}")

    def load_resources_from_db(self):
        """
        Загружает текущие ресурсы фракции из таблицы resources.
        """
        try:
            self.cursor.execute('''
                SELECT resource_type, amount
                FROM resources
                WHERE faction = ?
            ''', (self.faction,))
            rows = self.cursor.fetchall()

            # Инициализация ресурсов по умолчанию
            self.money = 0
            self.free_peoples = 0
            self.raw_material = 0
            self.population = 0

            # Обновление ресурсов на основе данных из базы данных
            for resource_type, amount in rows:
                if resource_type == "Кроны":
                    self.money = amount
                elif resource_type == "Рабочие":
                    self.free_peoples = amount
                elif resource_type == "Кристаллы":
                    self.raw_material = amount
                elif resource_type == "Население":
                    self.population = amount

        except sqlite3.Error as e:
            print(f"Ошибка при загрузке ресурсов: {e}")

    def save_resources_to_db(self):
        """
        Сохраняет текущие ресурсы фракции в таблицу resources.
        Обновляет только существующие записи, не добавляет новые.
        """
        try:
            for resource_type, amount in self.resources.items():
                # Проверяем, существует ли запись
                self.cursor.execute('''
                    SELECT amount
                    FROM resources
                    WHERE faction = ? AND resource_type = ?
                ''', (self.faction, resource_type))
                existing_record = self.cursor.fetchone()

                if existing_record:
                    # Обновляем существующую запись
                    self.cursor.execute('''
                        UPDATE resources
                        SET amount = ?
                        WHERE faction = ? AND resource_type = ?
                    ''', (amount, self.faction, resource_type))
                else:
                    pass

            # Сохраняем изменения в базе данных
            self.conn.commit()
        except sqlite3.Error as e:
            print(f"Ошибка при сохранении ресурсов: {e}")

    @property
    def max_army_limit(self):
        """
        Динамически рассчитывает максимальный лимит армии
        на основе базового значения и бонуса от городов.
        """
        base_limit = 400_000
        city_bonus = 100_000 * self.city_count
        return base_limit + city_bonus

    def load_relations(self):
        """
        Загружает текущие отношения из таблицы relations в базе данных.
        Возвращает словарь, где ключи — названия фракций, а значения — уровни отношений.
        """
        try:
            self.cursor.execute('''
                SELECT faction2, relationship
                FROM relations
                WHERE faction1 = ?
            ''', (self.faction,))
            rows = self.cursor.fetchall()

            # Преобразуем результат в словарь, преобразуя значения в числа
            relations = {faction2: int(relationship) for faction2, relationship in rows}
            return relations

        except sqlite3.Error as e:
            print(f"Ошибка при загрузке отношений из таблицы relations: {e}")
            return {}

    def load_political_system(self):
        """
        Загружает текущую политическую систему фракции из базы данных.
        """
        try:
            query = "SELECT system FROM political_systems WHERE faction = ?"
            self.cursor.execute(query, (self.faction,))
            result = self.cursor.fetchone()
            return result[0] if result else "Смирение"  # По умолчанию "Смирение"
        except sqlite3.Error as e:
            print(f"Ошибка при загрузке политической системы: {e}")
            return "Смирение"

    def apply_player_bonuses(self):
        bonuses = {}
        try:
            system = self.load_political_system()
            if system == "Смирение":
                crowns_bonus = int(self.money_up * 10.50)
                if crowns_bonus > 0:
                    self.money += crowns_bonus
                    bonuses["Кроны"] = crowns_bonus
            elif system == "Борьба":
                raw_material_bonus = int(self.food_info * 4.00)
                if raw_material_bonus > 0:
                    self.raw_material += raw_material_bonus
                    bonuses["Кристаллы"] = raw_material_bonus

            if self.turn % 3 == 0:
                self.update_relations_based_on_political_system()

            return bonuses
        except Exception as e:
            print(f"Ошибка при применении бонусов игроку: {e}")
            return {}

    def load_political_system_for_faction(self, faction):
        """
        Загружает политическую систему указанной фракции.
        """
        try:
            query = "SELECT system FROM political_systems WHERE faction = ?"
            self.cursor.execute(query, (faction,))
            result = self.cursor.fetchone()
            return result[0] if result else "Смирение"  # По умолчанию "Смирение"
        except sqlite3.Error as e:
            print(f"Ошибка при загрузке политической системы для фракции {faction}: {e}")
            return "Смирение"

    def update_relations_based_on_political_system(self):
        """
        Изменяет отношения на основе политической системы каждые 4 хода.
        """
        current_system = self.load_political_system()
        all_factions = self.load_relations()

        for faction, relation_level in all_factions.items():
            other_system = self.load_political_system_for_faction(faction)

            if current_system == other_system:
                # Улучшаем отношения на +3%
                new_relation = min(relation_level + 3, 100)
                print(f"Улучшение отношений с {faction}: {relation_level} -> {new_relation}")
            else:
                # Ухудшаем отношения на -7%
                new_relation = max(relation_level - 7, 0)
                print(f"Ухудшение отношений с {faction}: {relation_level} -> {new_relation}")

            # Обновляем уровень отношений в базе данных
            self.update_relation_in_db(faction, new_relation)

    def update_relation_in_db(self, faction, new_relation):
        """
        Обновляет уровень отношений в базе данных.
        """
        try:
            print(f"Обновляем отношения для {faction}: новое значение = {new_relation}")
            query = """
                UPDATE relations
                SET relationship = ?
                WHERE faction1 = ? AND faction2 = ?
            """
            self.cursor.execute(query, (new_relation, self.faction, faction))
            self.conn.commit()
            print(f"Отношения успешно обновлены для {faction}.")
        except sqlite3.Error as e:
            print(f"Ошибка при обновлении отношений для фракции {faction}: {e}")

    def calculate_and_deduct_consumption(self):
        """
        Метод для расчета потребления Кристаллы гарнизонами текущей фракции
        и вычета суммарного потребления из self.raw_material.
        Также проверяет лимиты потребления и при необходимости сокращает армию,
        уменьшая количество юнитов на 15% от их числа.
        """
        try:
            self.current_consumption = 0
            # Шаг 1: Выгрузка всех гарнизонов
            self.cursor.execute("SELECT city_name, unit_name, unit_count FROM garrisons")
            garrisons = self.cursor.fetchall()

            # Шаг 2: Для каждого гарнизона получаем данные юнита
            faction_units = {}
            for garrison in garrisons:
                city_name, unit_name, unit_count = garrison

                if unit_name not in faction_units:
                    self.cursor.execute("SELECT consumption, faction FROM units WHERE unit_name = ?", (unit_name,))
                    unit_data = self.cursor.fetchone()
                    if unit_data:
                        consumption, unit_faction = unit_data
                        faction_units[unit_name] = {'consumption': consumption, 'faction': unit_faction}
                    else:
                        continue

                if faction_units[unit_name]['faction'] == self.faction:
                    self.current_consumption += faction_units[unit_name]['consumption'] * unit_count

            starving_units = []
            if self.current_consumption > self.max_army_limit:
                excess_consumption = self.current_consumption - self.max_army_limit

                for garrison in garrisons:
                    city_name, unit_name, unit_count = garrison

                    if unit_count <= 0 or faction_units[unit_name]['faction'] != self.faction:
                        continue

                    reduction = max(1, int(unit_count * 0.15))

                    self.cursor.execute("""
                        UPDATE garrisons
                        SET unit_count = unit_count - ?
                        WHERE city_name = ? AND unit_name = ?
                    """, (reduction, city_name, unit_name))

                    new_unit_count = unit_count - reduction
                    starving_units.append((unit_name, reduction))

                    if new_unit_count <= 0:
                        self.cursor.execute("DELETE FROM garrisons WHERE city_name = ? AND unit_name = ?",
                                            (city_name, unit_name))
                    else:
                        self.current_consumption -= faction_units[unit_name]['consumption'] * reduction
                        excess_consumption -= faction_units[unit_name]['consumption'] * reduction

                    if excess_consumption <= 0:
                        break

            # Шаг 3: Обновляем досье
            total_starved = sum(reduction for _, reduction in starving_units)

            if total_starved > 0:
                try:
                    self.cursor.execute("SELECT avg_soldiers_starving FROM dossier WHERE faction = ?", (self.faction,))
                    result = self.cursor.fetchone()

                    if result and result[0] is not None:
                        new_avg = (result[0] + total_starved) / 2
                    else:
                        new_avg = total_starved

                    # Округление в меньшую сторону
                    new_avg = math.floor(new_avg)

                    self.cursor.execute("""
                        INSERT INTO dossier (faction, avg_soldiers_starving, last_data)
                        VALUES (?, ?, datetime('now'))
                        ON CONFLICT(faction) DO UPDATE SET
                            avg_soldiers_starving = ?,
                            last_data = datetime('now')
                    """, (self.faction, new_avg, new_avg))

                except Exception as e:
                    print(f"[Ошибка] Не удалось обновить досье: {e}")
                    self.conn.rollback()

            # Шаг 4: Вывод сообщения о голодании
            if starving_units:
                message = "Армия голодает и будет сокращаться:\n"
                for unit_name, reduction in starving_units:
                    message += f"- {unit_name}: умерло {reduction} юнитов\n"
                show_message("Голод в армии", message)
                print(f"Армия сокращена до допустимого лимита.")

            # Шаг 5: Обновление ресурсов
            self.raw_material -= self.current_consumption
            print(f"Общее потребление Кристаллы: {self.current_consumption}")
            print(f"Остаток Кристаллы у фракции: {self.raw_material}")

            self.resources['Потребление'] = self.current_consumption
            self.save_resources_to_db()

            self.conn.commit()

        except Exception as e:
            print(f"[Ошибка] Произошла ошибка: {e}")
            self.conn.rollback()
            self.resources['Потребление'] = self.current_consumption

    def update_average_net_profit(self, coins_profit, raw_profit):
        """
        Обновляет или создает запись в таблице results для колонок Average_Net_Profit_Coins и Average_Net_Profit_Raw.
        :param coins_profit: Текущая прибыль по кронам
        :param raw_profit: Текущая прибыль по Кристаллы
        """
        try:
            # Проверяем существование записи для фракции
            self.cursor.execute('''
                SELECT Average_Net_Profit_Coins, Average_Net_Profit_Raw 
                FROM results 
                WHERE faction = ?
            ''', (self.faction,))
            row = self.cursor.fetchone()

            if row:
                current_coins_profit, current_raw_profit = row

                # Рассчитываем новые средние значения
                new_coins_profit = round((current_coins_profit + coins_profit) / 2, 2)
                new_raw_profit = round((current_raw_profit + raw_profit) / 2, 2)

                # Обновляем существующую запись
                self.cursor.execute('''
                    UPDATE results 
                    SET Average_Net_Profit_Coins = ?, Average_Net_Profit_Raw = ?
                    WHERE faction = ?
                ''', (new_coins_profit, new_raw_profit, self.faction))
            else:
                # Создаем новую запись
                self.cursor.execute('''
                    INSERT INTO results (faction, Average_Net_Profit_Coins, Average_Net_Profit_Raw)
                    VALUES (?, ?, ?)
                ''', (self.faction, round(coins_profit, 2), round(raw_profit, 2)))

            self.conn.commit()
        except sqlite3.Error as e:
            print(f"Ошибка при обновлении средней чистой прибыли: {e}")

    def update_resources(self):
        """
        Обновление текущих ресурсов с учетом данных из базы данных.
        Все расчеты выполняются на основе таблиц в базе данных.
        """
        print('-----------------ХОДИТ ИГРОК-----------', self.faction.upper)
        # Обновляем данные о зданиях из таблицы buildings
        self.turn += 1
        # Строим
        self.auto_build()
        # Сохраняем предыдущие значения ресурсов
        previous_money = self.money
        previous_raw_material = self.raw_material
        # Генерируем новую цену на Кристаллы
        self.generate_raw_material_price()
        # Обновляем ресурсы на основе торговых соглашений
        self.update_trade_resources_from_db()


        # Коэффициенты для каждой фракции
        faction_coefficients = {
            'Люди': {'money_loss': 150, 'food_loss': 0.4},
            'Эльфы': {'money_loss': 180, 'food_loss': 0.1},
            'Вампиры': {'money_loss': 210, 'food_loss': 0.09},
            'Адепты': {'money_loss': 240, 'food_loss': 0.05},
            'Элины': {'money_loss': 270, 'food_loss': 0.04},
        }

        # Получение коэффициентов для текущей фракции
        faction = self.faction
        if faction not in faction_coefficients:
            raise ValueError(f"Фракция '{faction}' не найдена.")
        coeffs = faction_coefficients[faction]

        # Обновление ресурсов с учетом коэффициентов
        self.born_peoples = int(self.hospitals * 500)
        self.work_peoples = int(self.factories * 200)
        self.clear_up_peoples = self.born_peoples - (self.work_peoples - self.tax_effects*2.5)
        # Загружаем текущие значения ресурсов из базы данных
        self.load_resources_from_db()
        # Выполняем расчеты
        self.free_peoples += self.clear_up_peoples
        self.money += int(self.calculate_tax_income() - (self.hospitals * coeffs['money_loss']))
        self.money_info = int(self.hospitals * coeffs['money_loss'])
        self.money_up = int(self.calculate_tax_income() - (self.hospitals * coeffs['money_loss']))
        self.taxes_info = int(self.calculate_tax_income())

        # Учитываем, что одна фабрика может прокормить 10000 людей
        base_raw_material_production = (self.factories * 10000) - (self.population * coeffs['food_loss'])
        city_bonus_raw_material = base_raw_material_production * (0.05 * self.city_count)  # Бонус 5% за каждый город
        self.raw_material += int(base_raw_material_production + city_bonus_raw_material)

        self.food_info = (
                int((self.factories * 10000) - (self.population * coeffs['food_loss'])) - self.current_consumption)
        self.food_peoples = int(self.population * coeffs['food_loss'])

        # Проверяем условия для роста населения
        if self.raw_material > 0:
            self.population += int(self.clear_up_peoples)
        else:
            # Логика убыли населения при недостатке Кристаллы
            if self.population > 100:
                loss = int(self.population * 0.45)  # 45% от населения
                self.population -= loss
            else:
                loss = min(self.population, 50)  # Обнуление по 50, но не ниже 0
                self.population -= loss
            self.free_peoples = 0  # Все рабочие обнуляются, так как Кристаллы нет

        # Проверка, чтобы ресурсы не опускались ниже 0 и не превышали максимальные значения
        self.resources.update({
            "Кроны": max(min(int(self.money), 10_000_000_000), 0),  # Не более 10 млрд
            "Рабочие": max(min(int(self.free_peoples), 10_000_000), 0),  # Не более 10 млн
            "Кристаллы": max(min(int(self.raw_material), 10_000_000_000), 0),  # Не более 10 млрд
            "Население": max(min(int(self.population), 100_000_000), 0),  # Не более 100 млн
            "Потребление": self.current_consumption,  # Используем рассчитанное значение
            "Лимит армии": self.max_army_limit
        })

        # Рассчитываем чистую прибыль
        net_profit_coins = round(self.money - previous_money, 2)
        net_profit_raw = round(self.raw_material - previous_raw_material, 2)
        # Обновляем средние значения чистой прибыли в таблице results
        self.update_average_net_profit(net_profit_coins, net_profit_raw)
        # Списываем потребление войсками
        self.calculate_and_deduct_consumption()
        # Сохраняем обновленные ресурсы в базу данных
        self.save_resources_to_db()
        print(f"Ресурсы обновлены: {self.resources}, Больницы: {self.hospitals}, Фабрики: {self.factories}")
        # Профит от бонусов
        profit_details = {
            "Кроны": net_profit_coins,
            "Кристаллы": net_profit_raw,
        }
        # Оставляем только положительные значения
        profit_details = {k: v for k, v in profit_details.items() if v > 0}

        return profit_details

    def get_resource_now(self, resource_type):
        """
        Возвращает текущее значение указанного ресурса.
        :param resource_type: Тип ресурса (например, "Кроны").
        :return: Значение ресурса.
        """
        return self.resources.get(resource_type, 0)

    def update_resource_now(self, resource_type, new_amount):
        if resource_type == 'Кроны':
            self.money = new_amount
        elif resource_type == 'Рабочие':
            self.free_peoples = new_amount
        elif resource_type == 'Кристаллы':
            self.raw_material = new_amount
        elif resource_type == 'Население':
            self.population = new_amount

    def get_resources(self):
        """Получение текущих ресурсов с форматированием чисел."""
        formatted_resources = {}

        for resource, value in self.resources.items():
            formatted_resources[resource] = format_number(value)

        return formatted_resources

    def get_city_count(self):
        """
        Возвращает текущее количество городов для фракции.
        :return: Количество городов (целое число).
        """
        try:
            # Выполняем запрос к таблице cities для подсчета городов фракции
            self.cursor.execute('''
                SELECT COUNT(*)
                FROM cities
                WHERE faction = ?
            ''', (self.faction,))

            # Получаем результат запроса
            row = self.cursor.fetchone()
            if row and isinstance(row[0], int):  # Проверяем, что результат корректен
                return row[0]  # Возвращаем количество городов
            else:
                return 0  # Если записей нет или результат некорректен, возвращаем 0
        except sqlite3.Error as e:
            print(f"Ошибка при получении количества городов: {e}")
            return 0

    def check_all_relations_high(self):
        """
        Проверяет, превышают ли все отношения текущей фракции с НЕУНИЧТОЖЕННЫМИ фракциями 95%.
        :return: True, если все активные отношения > 95%, иначе False.
        """
        try:
            # Добавляем JOIN с таблицей diplomacies для фильтрации уничтоженных фракций
            self.cursor.execute('''
                SELECT r.faction2, r.relationship
                FROM relations r
                JOIN diplomacies d ON r.faction2 = d.faction2
                WHERE r.faction1 = ?
                  AND d.relationship != 'уничтожена'  -- исключаем уничтоженные фракции
                  AND r.faction2 != r.faction1        -- исключаем саму себя
            ''', (self.faction,))
            rows = self.cursor.fetchall()

            if not rows:
                print("Нет активных фракций для проверки отношений.")
                return False

            # Проверяем каждое отношение
            for faction2, relationship in rows:
                if int(relationship) <= 95:
                    print(f"Отношение с {faction2} <= 95% ({relationship}%)")
                    return False  # Если хотя бы одно отношение <= 95, игра не завершается

            print("Все активные отношения > 95%. Условие завершения игры выполнено.")
            return True

        except sqlite3.Error as e:
            print(f"Ошибка при проверке отношений: {e}")
            return False

    def check_remaining_factions(self):
        """
        Проверяет, остались ли активные фракции (не уничтоженные и не 'Мятежники') в таблице relations.
        :return: True, если есть активные фракции, кроме Мятежников, False, если все (кроме Мятежников) уничтожены/отсутствуют.
        """
        try:
            # Используем JOIN для проверки статуса фракции [[6]]
            self.cursor.execute('''
                SELECT DISTINCT r.faction2 
                FROM relations r
                JOIN diplomacies f ON r.faction2 = f.faction2 
                WHERE r.faction1 = ?
                  AND f.relationship != 'уничтожена'  -- фильтруем уничтоженные [[2]]
                  AND r.faction2 != r.faction1   -- исключаем текущую фракцию
                  AND r.faction2 != 'Мятежники'      -- исключаем Мятежников
            ''', (self.faction,))

            rows = self.cursor.fetchall()
            remaining_factions = {faction2 for (faction2,) in rows}

            if not remaining_factions:
                print("Все фракции уничтожены или отсутствуют.")
                return False

            return True

        except sqlite3.Error as e:
            print(f"Ошибка проверки фракций: {e}")
            return False

    def end_game(self):
        """
        Проверяет условия завершения игры:
        - Нулевое население.
        - Отсутствие городов.
        - Все отношения > 95%.
        - Остались ли другие фракции.
        :return: Кортеж (bool, str), где:
            - bool: True, если игра продолжается, False, если игра завершена.
            - str: Сообщение с описанием условий завершения игры.
        """
        try:
            # Проверяем, что население и количество городов корректны
            population_valid = isinstance(self.population, int) and self.population >= 0
            city_count_valid = isinstance(self.get_city_count(), int) and self.get_city_count() >= 0

            if not population_valid and self.raw_material >= 0:
                message = "Слишком мало больниц было построено на текущем этапе, население накрыла неизвестная болезнь..."
                print(message)
                return False, message

            if not population_valid or not city_count_valid:
                message = "Города опустели, уровень налогов распугал всех граждан..."
                print(message)
                return False, message

            # Условия завершения игры
            if self.population == 0 and self.raw_material <= 0:
                message = "Города опустели из-за отсутствия еды...."
                print(message)
                return False, message

            if self.get_city_count() == 0:
                message = "Противник завоевал все города"
                print(message)
                return False, message

            # Проверка все отношения > 95%
            if self.check_all_relations_high():
                message = "Мир во всем мире"
                print(message)
                return False, message

            # Проверка остались ли другие фракции
            if not self.check_remaining_factions():
                message = "Все фракции были уничтожены"
                print(message)
                return False, message

            # Если ни одно из условий не выполнено, игра продолжается
            return True, "Игра продолжается."

        except Exception as e:
            message = f"Ошибка при проверке завершения игры: {e}"
            print(message)
            return False, message

    def buildings_info_fraction(self):
        if self.faction == 'Люди':
            return 150
        if self.faction == 'Эльфы':
            return 180
        if self.faction == 'Вампиры':
            return 210
        if self.faction == 'Адепты':
            return 240
        if self.faction == 'Элины':
            return 270

    def update_economic_efficiency(self, efficiency_value):
        """
        Обновляет или создает запись в таблице results для колонки Average_Deal_Ratio эффективность торговых сделок.
        :param efficiency_value: Новое значение эффективности для обработки.
        """
        try:
            # Проверяем существование записи для фракции
            self.cursor.execute('''
                SELECT Average_Deal_Ratio
                FROM results 
                WHERE faction = ?
            ''', (self.faction,))
            row = self.cursor.fetchone()

            if row:
                # Если запись существует - обновляем среднее значение
                current_efficiency = row[0]
                # Округляем результат до двух знаков после запятой
                new_efficiency = round((current_efficiency + efficiency_value) / 2, 2)
                self.cursor.execute('''
                    UPDATE results 
                    SET Average_Deal_Ratio = ? 
                    WHERE faction = ?
                ''', (new_efficiency, self.faction))
            else:
                # Если записи нет - создаем новую
                # Округляем входное значение до двух знаков после запятой
                self.cursor.execute('''
                    INSERT INTO results (faction, Average_Deal_Ratio)
                    VALUES (?, ?)
                ''', (self.faction, round(efficiency_value, 2)))

            self.conn.commit()
        except sqlite3.Error as e:
            print(f"Ошибка при обновлении экономической эффективности: {e}")

    def initialize_raw_material_prices(self):
        """Инициализация истории цен на Кристаллы"""
        for _ in range(25):  # Генерируем 25 случайных цен
            self.generate_raw_material_price()

    def generate_raw_material_price(self):
        """
        Генерация случайной цены на Кристаллы.
        Цена генерируется только при изменении номера хода.
        """
        # Загрузка номера хода из таблицы turn
        try:
            self.cursor.execute('''
                SELECT turn_count 
                FROM turn
                ORDER BY turn_count DESC
                LIMIT 1
            ''')
            row = self.cursor.fetchone()
            if row:
                current_turn = row[0]  # Текущий номер хода
            else:
                current_turn = 1  # Если записей нет, начинаем с нуля
        except sqlite3.Error as e:
            print(f"Ошибка при загрузке номера хода: {e}")
            current_turn = 1  # В случае ошибки устанавливаем значение по умолчанию

        # Проверка, был ли уже загружен текущий ход
        if current_turn == self.last_turn_loaded:
            return  # Цена уже сгенерирована для этого хода

        # Генерация новой цены
        if current_turn == 1:  # Если это первый ход
            self.current_raw_material_price = random.randint(736, 9720)
            self.raw_material_price_history.append(self.current_raw_material_price)
        else:
            # Генерация новой цены на основе текущей
            self.current_raw_material_price = self.raw_material_price_history[-1] + random.randint(-345, 475)
            self.current_raw_material_price = max(
                736, min(9720, self.current_raw_material_price)  # Ограничиваем диапазон
            )
            self.raw_material_price_history.append(self.current_raw_material_price)

        # Ограничение длины истории цен до 25 элементов
        if len(self.raw_material_price_history) > 25:
            self.raw_material_price_history.pop(0)

        # Обновляем значение последнего загруженного хода
        self.last_turn_loaded = current_turn

    def trade_raw_material(self, action, quantity):
        """
        Торговля Кристаллым через таблицу resources.
        :param action: Действие ('buy' для покупки, 'sell' для продажи).
        :param quantity: Количество лотов (1 лот = 10,000 единиц Кристаллы).
        """
        # Преобразуем количество лотов в единицы Кристаллы
        total_quantity = quantity * 10000
        total_cost = self.current_raw_material_price * quantity

        if action == 'buy':  # Покупка Кристаллы
            # Проверяем, достаточно ли денег для покупки
            if self.money >= total_cost:
                # Обновляем ресурсы
                self.money -= total_cost
                self.raw_material += total_quantity
                # Сохраняем изменения в базе данных
                self.save_resources_to_db()
                return True  # Операция успешна
            else:
                show_message("Недостаточно денег", "У вас недостаточно денег для покупки Кристаллы.")
                return False

        elif action == 'sell':  # Продажа Кристаллы
            # Проверяем, достаточно ли Кристаллы для продажи
            if self.raw_material >= total_quantity:
                # Обновляем ресурсы
                self.money += total_cost
                self.raw_material -= total_quantity
                # Сохраняем изменения в базе данных
                self.save_resources_to_db()
                return True  # Операция успешна
            else:
                show_message("Недостаточно Кристаллы", "У вас недостаточно Кристаллы для продажи.")
                return False

        return False  # Операция не удалась

    def get_raw_material_price_history(self):
        """Получение табличного представления истории цен на Кристаллы"""
        history = []
        for i, price in enumerate(self.raw_material_price_history):
            # Вместо строки создаем кортеж (номер хода, цена)
            history.append((f"Ход {i + 1}", price))
        return history

    def get_available_raw_material_lots(self) -> int:
        """Возвращает количество доступных для торговли лотов Кристаллы"""
        return self.raw_material // 10000

def show_message(title, message):
    # === Оценка высоты текста ===
    lines = message.count('\n') + 1
    text_height = max(dp(100), dp(lines * 25))  # минимум 100dp, дальше по строкам
    popup_height = text_height + dp(110)        # + кнопка и отступы

    # === Стилизованный Label с переносом текста и выравниванием по центру ===
    label = Label(
        text=message,
        size_hint_y=None,
        height=text_height,
        text_size=(None, None),
        halign='center',
        valign='middle',
        font_size='16sp',
        padding=(dp(10), dp(10))
    )

    # Обновляем текстуру после изменения размера
    def update_label_width(instance, width):
        instance.text_size = (instance.width * 0.9, None)
        instance.texture_update()

    label.bind(width=update_label_width)

    # === Кнопка "Закрыть" с минимальной высотой и стилем ===
    close_btn = Button(
        text="Закрыть",
        size_hint=(1, None),
        height=dp(48),
        background_color=(0.2, 0.6, 0.8, 1),
        background_normal='',
        font_size='16sp'
    )

    # === Основной макет ===
    layout = BoxLayout(orientation='vertical', padding=dp(10), spacing=dp(10))
    layout.add_widget(label)
    layout.add_widget(close_btn)

    # === Всплывающее окно ===
    popup = Popup(
        title=title,
        content=layout,
        size_hint=(0.7, None),
        height=popup_height,
        auto_dismiss=False
    )
    close_btn.bind(on_release=popup.dismiss)

    popup.open()

# Логика для отображения сообщения об ошибке средств
def show_error_message(message):
    error_popup = Popup(title="Ошибка", content=Label(text=message), size_hint=(0.5, 0.5))
    error_popup.open()


def open_build_popup(faction):
    def rebuild_popup(*args):
        build_popup.dismiss()
        open_build_popup(faction)

    build_popup = Popup(
        title="Состояние государства",
        size_hint=(0.9, 0.85),
        title_size=sp(20),
        title_align='center',
        title_color=(1, 1, 1, 1),
        background_color=(0.1, 0.1, 0.1, 0.95),
        separator_color=(0.3, 0.3, 0.3, 1),
        auto_dismiss=False
    )

    main_layout = BoxLayout(
        orientation='vertical',
        spacing=dp(12),
        padding=[dp(16), dp(16), dp(16), dp(16)]
    )

    scroll_view = ScrollView(
        size_hint=(1, 1),
        do_scroll_x=False,
        do_scroll_y=True
    )

    screen_w, _ = Window.size
    cols_count = 1 if screen_w < dp(600) else 2

    stats_grid = GridLayout(
        cols=cols_count,
        size_hint_y=None,
        spacing=dp(12),
        row_force_default=True,
        row_default_height=dp(80)
    )
    stats_grid.bind(minimum_height=stats_grid.setter('height'))

    # Адаптивный шрифт
    def calculate_font_size():
        w, _ = Window.size
        base = 14 + (w - dp(360)) / (dp(720)) * 4
        return sp(max(14, min(18, base)))

    adaptive_font = calculate_font_size()

    # 1) Объединённый блок «Постройки за ход» — увеличили высоту до dp(120)
    build_card = BoxLayout(
        orientation='vertical',
        padding=[dp(12), dp(8), dp(12), dp(8)],
        spacing=dp(4),
        size_hint_y=None,
        height=dp(120)
    )
    with build_card.canvas.before:
        Color(0.2, 0.2, 0.2, 1)
        build_card.bg_rect = RoundedRectangle(
            pos=build_card.pos,
            size=build_card.size,
            radius=[12]
        )
    def update_build_rect(instance, val):
        instance.bg_rect.pos = instance.pos
        instance.bg_rect.size = instance.size
    build_card.bind(pos=update_build_rect, size=update_build_rect)

    # Подпись для больницы
    hosp_label = Label(
        text=f"1 больница: +500 раб./-{faction.buildings_info_fraction()} крон",
        font_size=adaptive_font,
        color=(1, 1, 1, 1),
        size_hint_y=None,
        height=dp(28),
        halign='left',
        valign='middle'
    )
    hosp_label.bind(size=lambda inst, val: setattr(inst, 'text_size', (inst.width, inst.height)))
    build_card.add_widget(hosp_label)

    # Подпись для фабрики
    fact_label = Label(
        text="1 фабрика: +1000 крист./-200 рабочих",
        font_size=adaptive_font,
        color=(1, 1, 1, 1),
        size_hint_y=None,
        height=dp(28),
        halign='left',
        valign='middle'
    )
    fact_label.bind(size=lambda inst, val: setattr(inst, 'text_size', (inst.width, inst.height)))
    build_card.add_widget(fact_label)

    stats_grid.add_widget(build_card)

    # 2) Оставшиеся данные статистики
    stats_data = [
        ("Количество больниц:", format_number(faction.hospitals)),
        ("Количество фабрик:", format_number(faction.factories)),
        ("Рабочих на фабриках:", format_number(faction.work_peoples)),
        ("Прирост рабочих:", format_number(faction.clear_up_peoples)),
        ("Расход денег больницами:", format_number(faction.money_info)),
        ("Прирост кристаллов:", format_number(faction.food_info)),
        ("Чистый прирост денег:", format_number(faction.money_up)),
        ("Доход от налогов:", format_number(faction.taxes_info)),
        ("Эффект от налогов:",
         format_number(faction.apply_tax_effect(int(faction.current_tax_rate[:-1]))) if faction.tax_set else "–")
    ]

    for label_text, value in stats_data:
        card = BoxLayout(
            orientation='vertical',
            padding=[dp(12), dp(8), dp(12), dp(8)],
            spacing=dp(4),
            size_hint_y=None,
            height=dp(80)
        )
        with card.canvas.before:
            Color(0.2, 0.2, 0.2, 1)
            card.bg_rect = RoundedRectangle(
                pos=card.pos,
                size=card.size,
                radius=[12]
            )
        def update_card_rect(instance, val):
            instance.bg_rect.pos = instance.pos
            instance.bg_rect.size = instance.size
        card.bind(pos=update_card_rect, size=update_card_rect)

        lbl = Label(
            text=label_text,
            font_size=adaptive_font,
            color=(1, 1, 1, 1),
            bold=True,
            size_hint_y=None,
            height=dp(24),
            halign='left',
            valign='middle'
        )
        lbl.bind(size=lambda inst, val: setattr(inst, 'text_size', (inst.width, inst.height)))
        card.add_widget(lbl)

        if isinstance(value, (int, float)):
            val_color = (0, 1, 0, 1) if value >= 0 else (1, 0, 0, 1)
            val_text = str(value)
        else:
            val_color = (1, 1, 1, 1)
            val_text = str(value)

        val = Label(
            text=val_text,
            font_size=adaptive_font,
            color=val_color,
            bold=True,
            size_hint_y=None,
            height=dp(28),
            halign='right',
            valign='middle'
        )
        val.bind(size=lambda inst, val: setattr(inst, 'text_size', (inst.width, inst.height)))
        card.add_widget(val)

        stats_grid.add_widget(card)

    scroll_view.add_widget(stats_grid)
    main_layout.add_widget(scroll_view)

    btn_box = BoxLayout(
        orientation='horizontal',
        spacing=dp(12),
        size_hint=(1, None),
        height=dp(50)
    )

    btn_close = Button(
        text="Закрыть",
        size_hint=(1, 1),
        background_normal='',
        background_color=(0.7, 0.2, 0.2, 1),
        font_size=adaptive_font,
        bold=True,
        color=(1, 1, 1, 1)
    )
    btn_close.bind(on_release=lambda x: build_popup.dismiss())

    btn_box.add_widget(btn_close)
    main_layout.add_widget(btn_box)

    build_popup.content = main_layout
    build_popup.open()


# ---------------------------------------------------------------


def open_trade_popup(game_instance):
    game_instance.get_resources()
    game_instance.generate_raw_material_price()

    # === ПОЛЕ ВВОДА (вверху) ===
    input_box = BoxLayout(orientation='vertical', spacing=dp(5), size_hint=(1, None), height=dp(120))

    # === ГОРИЗОНТАЛЬНЫЙ LAYOUT ДЛЯ "ПРОДАТЬ ВСЁ" И ИНФОРМАЦИИ О ЛОТАХ ===
    top_row_layout = BoxLayout(
        orientation='horizontal',
        size_hint=(1, None),
        height=dp(40),
        spacing=dp(10)
    )

    # === ГАЛОЧКА "ПРОДАТЬ ВСЁ" ===
    sell_all_checkbox = CheckBox(size_hint=(None, None), size=(dp(30), dp(30)), active=False)
    sell_all_label = Label(
        text="Продать всё",
        font_size=sp(16),
        color=(1, 1, 1, 1),
        halign="left",
        size_hint_x=None,
        width=dp(120)
    )

    # Добавляем галочку и лейбл в левую часть
    left_layout = BoxLayout(
        orientation='horizontal',
        size_hint_x=None,
        width=dp(160),
        spacing=dp(5)
    )
    left_layout.add_widget(sell_all_checkbox)
    left_layout.add_widget(sell_all_label)

    # === ИНФОРМАЦИЯ О ДОСТУПНЫХ ЛОТАХ ===
    available_lots_label = Label(
        text=f"Доступно: {game_instance.get_available_raw_material_lots()} лотов",
        font_size=sp(14),
        color=(0.8, 0.8, 0.8, 1),
        halign="left"
    )

    # Собираем верхнюю строку
    top_row_layout.add_widget(left_layout)
    top_row_layout.add_widget(available_lots_label)
    top_row_layout.add_widget(Widget())  # Заполнитель справа

    input_box.add_widget(top_row_layout)

    # === ЛОГИКА БЛОКИРОВКИ ПОЛЯ ВВОДА ===
    def toggle_input(*args):
        quantity_input.disabled = sell_all_checkbox.active
        if sell_all_checkbox.active:
            quantity_input.text = ""
            quantity_input.hint_text = "Продажа всех лотов"
        else:
            quantity_input.hint_text = "Введите количество лотов, например: 3"

    sell_all_checkbox.bind(active=toggle_input)

    trade_layout = BoxLayout(
        orientation='vertical',
        padding=dp(16),
        spacing=dp(12)
    )

    quantity_input = TextInput(
        hint_text="Введите количество лотов, например: 3",
        font_size=sp(16),
        multiline=False,
        input_filter='int',
        size_hint=(1, None),
        height=dp(40),
        padding=[dp(10), dp(8)],
        background_color=(0.9, 0.9, 0.9, 1),
        foreground_color=(0, 0, 0, 1),
        cursor_color=(0, 0, 0, 1)
    )
    input_box.add_widget(quantity_input)
    trade_layout.add_widget(input_box)

    # === ТЕКУЩАЯ ЦЕНА (между полем ввода и кнопками) ===
    current_price = game_instance.current_raw_material_price
    prev_price = game_instance.raw_material_price_history[-2] if len(game_instance.raw_material_price_history) > 1 else current_price
    arrow_color = (0, 1, 0, 1) if current_price > prev_price else \
        (1, 0, 0, 1) if current_price < prev_price else (0.8, 0.8, 0.8, 1)

    current_price_label = Label(
        text=f"[b]Текущая цена на Кристаллы:[/b] {current_price}",
        markup=True,
        font_size=sp(25),
        color=arrow_color,
        halign="center",
        valign="middle"
    )
    current_price_label.bind(size=current_price_label.setter('text_size'))
    trade_layout.add_widget(current_price_label)

    # === КНОПКИ ===
    button_layout = BoxLayout(spacing=dp(16), size_hint=(1, None), height=dp(60))

    buy_btn = Button(
        text="Купить",
        font_size=sp(16),
        bold=True,
        background_color=(0, 0.6, 0.2, 1),
        color=(1, 1, 1, 1),
        size_hint=(0.5, 1),
        background_normal='',
        background_down=''
    )

    sell_btn = Button(
        text="Продать",
        font_size=sp(16),
        bold=True,
        background_color=(0.7, 0.1, 0.1, 1),
        color=(1, 1, 1, 1),
        size_hint=(0.5, 1),
        background_normal='',
        background_down=''
    )

    button_layout.add_widget(buy_btn)
    button_layout.add_widget(sell_btn)
    trade_layout.add_widget(button_layout)

    # === ПОПАП ===
    popup = Popup(title="Рынок Кристаллы", content=trade_layout, size_hint=(0.95, 0.8))

    def on_press_wrapper(action):
        def handler(instance):
            handle_trade(game_instance, action, quantity_input.text, popup, sell_all=sell_all_checkbox.active)
        return handler

    buy_btn.bind(on_release=on_press_wrapper('buy'))
    sell_btn.bind(on_release=on_press_wrapper('sell'))

    # === АНИМАЦИЯ МИГАНИЯ ===
    def start_blinking(*args):
        anim = Animation(background_color=(0.7, 0.7, 0.7, 1), duration=0.5) + \
               Animation(background_color=(0.9, 0.9, 0.9, 1), duration=0.5)
        anim.repeat = True
        anim.start(quantity_input)

    def stop_blinking(*args):
        Animation.stop_all(quantity_input)

    popup.bind(on_open=start_blinking)
    popup.bind(on_dismiss=stop_blinking)

    popup.open()


def handle_trade(game_instance, action, quantity, trade_popup, sell_all=False):
    """Обработка торговли (покупка/продажа Кристаллы)"""
    try:
        price_per_lot = game_instance.current_raw_material_price  # Цена за 1 лот

        if action == 'sell' and sell_all:
            # Продажа всех доступных лотов
            available_lots = game_instance.get_available_raw_material_lots()
            if available_lots <= 0:
                raise ValueError("Нет доступных лотов для продажи.")
            quantity = available_lots
        else:
            # Обычная логика
            if not quantity or int(quantity) <= 0:
                raise ValueError("Не было введено количество лотов. Пожалуйста, введите количество лотов.")
            quantity = int(quantity)

        # Проверяем, что количество Кристаллы для продажи не превышает доступное
        if action == 'sell' and quantity * 10000 > game_instance.resources["Кристаллы"]:
            raise ValueError("Недостаточно Кристаллы для продажи.")

        result = game_instance.trade_raw_material(action, quantity)
        if result:  # Если торговля прошла успешно
            economic_efficiency = round(price_per_lot / 10000, 2)
            game_instance.update_economic_efficiency(economic_efficiency)

            if action == 'buy':
                total_cost = price_per_lot * quantity
                show_message("Успех", f"Куплено {format_number(quantity)} лотов Кристаллов за {format_number(total_cost)} крон.")
            elif action == 'sell':
                profit = price_per_lot * quantity
                show_message("Успех", f"Получено: {format_number(profit)} крон\n(Соотношение: {economic_efficiency} крон/ед. Кристалла)")
        else:
            show_message("Ошибка", "Не удалось завершить операцию.")
    except ValueError as e:
        show_message("Ошибка", str(e))

    trade_popup.dismiss()

# -----------------------------------
def open_tax_popup(faction):
    # Проверка платформы
    is_android = platform == 'android'

    # Размеры popup в зависимости от платформы
    popup_size_hint = (0.9, 0.7) if is_android else (0.8, 0.6)

    tax_popup = Popup(
        title="Управление налогами",
        size_hint=popup_size_hint,
        background_color=(0.05, 0.05, 0.05, 0.95),
        title_color=(0.8, 0.8, 0.8, 1),
        separator_color=(0.3, 0.3, 0.3, 1),
        title_size=sp(28) if is_android else sp(24),
        title_align='center'
    )

    main_layout = FloatLayout()


    try:
        current_tax_rate = int(faction.current_tax_rate.strip('%')) \
            if isinstance(faction.current_tax_rate, str) else int(faction.current_tax_rate)
    except:
        current_tax_rate = 0

    # === Метка с текущим уровнем налогов ===
    tax_label = Label(
        text=f"Налог: {current_tax_rate}%",
        color=(0.7, 0.9, 0.7, 1),
        font_size=sp(32) if is_android else sp(28),
        bold=True,
        pos_hint={'center_x': 0.5, 'top': 0.92},
        size_hint=(0.9, None),
        halign="center"
    )
    main_layout.add_widget(tax_label)

    # === Ползунок управления налогом ===
    tax_slider = Slider(
        min=0,
        max=100,
        value=current_tax_rate,
        step=1,
        orientation='horizontal',
        pos_hint={'center_x': 0.5, 'center_y': 0.65},
        size_hint=(0.95, 0.12) if is_android else (0.9, 0.15),
        background_width=dp(10),
        cursor_size=(dp(40), dp(40)),
        value_track=False
    )

    def update_tax_label(instance, value):
        tax_label.text = f"Налог: {int(value)}%"
        r = value / 100
        g = 1 - r
        tax_label.color = (r, g, 0, 1)
        Animation(font_size=sp(36), duration=0.1).start(tax_label)
        Animation(font_size=sp(32), duration=0.2).start(tax_label)

    tax_slider.bind(value=update_tax_label)
    main_layout.add_widget(tax_slider)

    # === Кнопка "Применить" ===
    set_tax_button = Button(
        text="Применить",
        pos_hint={'center_x': 0.5, 'y': 0.08},
        size_hint=(0.8, 0.15) if is_android else (0.6, 0.15),
        background_color=(0, 0, 0, 0),
        color=(0.8, 0.8, 0.8, 1),
        font_size=sp(24) if is_android else sp(20),
        bold=True
    )

    with set_tax_button.canvas.before:
        Color(0.3, 0.3, 0.3, 0.5)
        set_tax_button.rect = RoundedRectangle(
            size=set_tax_button.size,
            pos=set_tax_button.pos,
            radius=[dp(15)]
        )

    def update_rect(instance, value):
        instance.rect.pos = instance.pos
        instance.rect.size = instance.size

    set_tax_button.bind(pos=update_rect, size=update_rect)

    def set_tax(instance):
        tax_rate = int(tax_slider.value)
        faction.current_tax_rate = f"{tax_rate}%"
        faction.set_taxes(tax_rate)
        faction.apply_tax_effect(tax_rate)
        tax_popup.dismiss()

    set_tax_button.bind(on_release=set_tax)
    main_layout.add_widget(set_tax_button)

    # === Закрытие попапа по нажатию вне виджета ===
    def dismiss_on_outside(instance, touch):
        if not main_layout.collide_point(*touch.pos):
            tax_popup.dismiss()

    tax_popup.bind(on_touch_down=dismiss_on_outside)

    tax_popup.content = main_layout
    tax_popup.open()

def open_auto_build_popup(faction):
    auto_popup = Popup(
        title="Министерство развития",
        size_hint=(0.8, 0.8),
        background_color=(0.1, 0.1, 0.1, 0.95),
        title_color=(1, 1, 0.7, 1),
        title_size='24sp',
    )

    main_layout = BoxLayout(orientation='vertical', spacing=20, padding=25)

    # Шапка
    header = BoxLayout(size_hint=(1, 0.15), spacing=20)
    left_label = Label(text="[b]Больницы[/b]", markup=True, color=(1, 0.4, 0.4, 1), font_size='20sp')
    right_label = Label(text="[b]Фабрики[/b]", markup=True, color=(0.4, 1, 0.4, 1), font_size='20sp')
    header.add_widget(left_label)
    header.add_widget(right_label)

    # Панель управления
    controls = BoxLayout(orientation='horizontal', size_hint=(1, 0.2), spacing=15)
    left_btn = Button(text="<<", font_size='18sp', background_normal='', background_color=(0.5, 0.1, 0.1, 1))
    slider = Slider(min=0, max=8, value=4, step=1, cursor_size=(24, 24))
    right_btn = Button(text=">>", font_size='18sp', background_normal='', background_color=(0.1, 0.5, 0.1, 1))
    controls.add_widget(left_btn)
    controls.add_widget(slider)
    controls.add_widget(right_btn)

    # Индикатор
    ratio_layout = BoxLayout(size_hint=(1, 0.2))
    ratio_display = Label(text="1:1", font_size='28sp', color=(1, 1, 0.5, 1))
    ratio_layout.add_widget(ratio_display)

    # Описание
    description = Label(
        text="Соотношение больниц и фабрик для строительства",
        color=(0.8, 0.8, 0.8, 1),
        font_size='16sp',
        size_hint=(1, 0.2),
        halign='center',
        valign='middle'
    )
    description.bind(size=description.setter('text_size'))

    # Кнопки
    buttons_layout = BoxLayout(size_hint=(1, 0.2), spacing=15)

    def styled_button(text, color):
        btn = Button(text=text, font_size='18sp', background_normal='', background_color=color)
        with btn.canvas.before:
            Color(*color)
            btn.rect = RoundedRectangle(size=btn.size, pos=btn.pos, radius=[12])
            btn.bind(pos=lambda i, v: setattr(btn.rect, 'pos', v))
            btn.bind(size=lambda i, v: setattr(btn.rect, 'size', v))
        return btn

    save_btn = styled_button("Сохранить", (0.2, 0.6, 0.2, 1))
    cancel_btn = styled_button("Отмена", (0.6, 0.2, 0.2, 1))
    buttons_layout.add_widget(save_btn)
    buttons_layout.add_widget(cancel_btn)

    # Добавление элементов
    main_layout.add_widget(header)
    main_layout.add_widget(controls)
    main_layout.add_widget(ratio_layout)
    main_layout.add_widget(description)
    main_layout.add_widget(buttons_layout)

    # Соотношения
    RATIOS = [(5, 2), (3, 2), (3, 1), (2, 1), (1, 1), (1, 2), (1, 3), (2, 3), (2, 5)]

    def update_display(instance, value):
        idx = int(value)
        ratio = RATIOS[idx]
        ratio_display.text = f"{ratio[0]}:{ratio[1]}"
        description.text = f"Строить: {ratio[0]} больниц и {ratio[1]} фабрик за ход"
        if ratio[0] > ratio[1]:
            ratio_display.color = (1, 0.4, 0.4, 1)
        elif ratio[1] > ratio[0]:
            ratio_display.color = (0.4, 1, 0.4, 1)
        else:
            ratio_display.color = (1, 1, 0.6, 1)

    if hasattr(faction, 'auto_build_ratio') and faction.auto_build_ratio in RATIOS:
        saved_index = RATIOS.index(faction.auto_build_ratio)
        slider.value = saved_index
        update_display(slider, saved_index)

    slider.bind(value=update_display)
    left_btn.bind(on_release=lambda _: setattr(slider, 'value', max(slider.value - 1, 0)))
    right_btn.bind(on_release=lambda _: setattr(slider, 'value', min(slider.value + 1, 8)))

    def save_settings(instance):
        idx = int(slider.value)
        faction.auto_build_ratio = RATIOS[idx]
        faction.auto_build_enabled = True
        faction.save_auto_build_settings()
        auto_popup.dismiss()
        show_message("Сохранено", "Как прикажете!")

    save_btn.bind(on_release=save_settings)
    cancel_btn.bind(on_release=auto_popup.dismiss)

    auto_popup.content = main_layout
    auto_popup.open()


def open_development_popup(faction):
    from kivy.uix.tabbedpanel import TabbedPanel, TabbedPanelItem
    from kivy.uix.scrollview import ScrollView
    from kivy.uix.gridlayout import GridLayout
    from kivy.uix.boxlayout import BoxLayout
    from kivy.uix.button import Button
    from kivy.uix.label import Label
    from kivy.graphics import Color, RoundedRectangle
    from kivy.metrics import dp, sp
    from kivy.animation import Animation
    from kivy.core.window import Window

    # === Создание всплывающего окна ===
    dev_popup = Popup(
        title="Развитие",
        size_hint=(0.9, 0.85),
        title_size=sp(20),
        title_align='center',
        title_color=(0.9, 0.9, 0.9, 1),
        background_color=(0.08, 0.08, 0.08, 0.98),  # Темнее
        separator_color=(0.3, 0.3, 0.3, 1),
        auto_dismiss=False
    )

    # === Создание TabbedPanel с улучшенным дизайном ===
    tab_panel = TabbedPanel(
        do_default_tab=False,
        tab_width=dp(140),
        tab_height=dp(50),
        background_color=(0.15, 0.15, 0.15, 1)
    )

    # Установка стиля для вкладок
    with tab_panel.canvas.before:
        Color(0.2, 0.2, 0.2, 1)
        tab_panel.bg_rect = RoundedRectangle(
            pos=tab_panel.pos,
            size=tab_panel.size,
            radius=[10]
        )
        def update_bg_rect(instance, val):
            instance.bg_rect.pos = instance.pos
            instance.bg_rect.size = instance.size
        tab_panel.bind(pos=update_bg_rect, size=update_bg_rect)

    # === Вкладка "Строительство" ===
    build_tab = TabbedPanelItem(text="Строительство")
    # Настройка стиля вкладки
    build_tab.background_normal = ''
    build_tab.background_down = ''
    build_tab.background_color = (0.3, 0.3, 0.3, 1)
    build_tab.color = (0.9, 0.9, 0.9, 1)
    build_tab.font_size = sp(16)

    # Контент для вкладки "Строительство" - сразу открываем настройки
    build_content = BoxLayout(orientation='vertical', spacing=dp(12), padding=dp(16))

    # Шапка
    header = BoxLayout(size_hint=(1, 0.15), spacing=20)
    left_label = Label(text="[b]Больницы[/b]", markup=True, color=(1, 0.4, 0.4, 1), font_size='20sp')
    right_label = Label(text="[b]Фабрики[/b]", markup=True, color=(0.4, 1, 0.4, 1), font_size='20sp')
    header.add_widget(left_label)
    header.add_widget(right_label)
    build_content.add_widget(header)

    # Панель управления
    controls = BoxLayout(orientation='horizontal', size_hint=(1, 0.2), spacing=15)
    left_btn = Button(text="<<", font_size='18sp', background_normal='', background_color=(0.3, 0.1, 0.1, 1))
    slider = Slider(min=0, max=8, value=4, step=1, cursor_size=(24, 24))
    right_btn = Button(text=">>", font_size='18sp', background_normal='', background_color=(0.1, 0.3, 0.1, 1))
    controls.add_widget(left_btn)
    controls.add_widget(slider)
    controls.add_widget(right_btn)
    build_content.add_widget(controls)

    # Индикатор
    ratio_layout = BoxLayout(size_hint=(1, 0.2))
    ratio_display = Label(text="1:1", font_size='28sp', color=(1, 1, 0.5, 1))
    ratio_layout.add_widget(ratio_display)
    build_content.add_widget(ratio_layout)

    # Описание
    description = Label(
        text="Соотношение больниц и фабрик для строительства",
        color=(0.8, 0.8, 0.8, 1),
        font_size='16sp',
        size_hint=(1, 0.2),
        halign='center',
        valign='middle'
    )
    description.bind(size=description.setter('text_size'))
    build_content.add_widget(description)

    # Кнопки
    buttons_layout = BoxLayout(size_hint=(1, 0.2), spacing=15)

    def styled_button(text, color):
        btn = Button(text=text, font_size='18sp', background_normal='', background_color=color)
        with btn.canvas.before:
            Color(*color)
            btn.rect = RoundedRectangle(size=btn.size, pos=btn.pos, radius=[12])
            btn.bind(pos=lambda i, v: setattr(btn.rect, 'pos', v))
            btn.bind(size=lambda i, v: setattr(btn.rect, 'size', v))
        return btn

    save_btn = styled_button("Сохранить", (0.2, 0.6, 0.2, 1))
    cancel_btn = styled_button("Закрыть", (0.6, 0.2, 0.2, 1))  # Переименовали
    buttons_layout.add_widget(save_btn)
    buttons_layout.add_widget(cancel_btn)
    build_content.add_widget(buttons_layout)

    # Соотношения
    RATIOS = [(5, 2), (3, 2), (3, 1), (2, 1), (1, 1), (1, 2), (1, 3), (2, 3), (2, 5)]

    def update_display(instance, value):
        idx = int(value)
        ratio = RATIOS[idx]
        ratio_display.text = f"{ratio[0]}:{ratio[1]}"
        description.text = f"Строить: {ratio[0]} больниц и {ratio[1]} фабрик за ход"
        if ratio[0] > ratio[1]:
            ratio_display.color = (1, 0.4, 0.4, 1)
        elif ratio[1] > ratio[0]:
            ratio_display.color = (0.4, 1, 0.4, 1)
        else:
            ratio_display.color = (1, 1, 0.6, 1)

    if hasattr(faction, 'auto_build_ratio') and faction.auto_build_ratio in RATIOS:
        saved_index = RATIOS.index(faction.auto_build_ratio)
        slider.value = saved_index
        update_display(slider, saved_index)

    slider.bind(value=update_display)
    left_btn.bind(on_release=lambda _: setattr(slider, 'value', max(slider.value - 1, 0)))
    right_btn.bind(on_release=lambda _: setattr(slider, 'value', min(slider.value + 1, 8)))

    def save_settings(instance):
        idx = int(slider.value)
        faction.auto_build_ratio = RATIOS[idx]
        faction.auto_build_enabled = True
        faction.save_auto_build_settings()
        show_message("Сохранено", "Как прикажете!")
        dev_popup.dismiss()  # Закрываем после сохранения

    save_btn.bind(on_release=save_settings)
    cancel_btn.bind(on_release=lambda x: dev_popup.dismiss())

    build_scroll = ScrollView(size_hint=(1, 1), do_scroll_x=False, do_scroll_y=True)
    build_scroll.add_widget(build_content)
    build_tab.content = build_scroll

    # === Вкладка "Статистика" ===
    stat_tab = TabbedPanelItem(text="Статистика")
    # Настройка стиля вкладки
    stat_tab.background_normal = ''
    stat_tab.background_down = ''
    stat_tab.background_color = (0.3, 0.3, 0.3, 1)
    stat_tab.color = (0.9, 0.9, 0.9, 1)
    stat_tab.font_size = sp(16)

    # Контент для вкладки "Статистика"
    stat_content = BoxLayout(orientation='vertical', spacing=dp(12), padding=dp(16))
    stat_scroll = ScrollView(size_hint=(1, 1), do_scroll_x=False, do_scroll_y=True)

    screen_w, _ = Window.size
    cols_count = 1 if screen_w < dp(600) else 2

    stats_grid = GridLayout(
        cols=cols_count,
        size_hint_y=None,
        spacing=dp(12),
        row_force_default=True,
        row_default_height=dp(80)
    )
    stats_grid.bind(minimum_height=stats_grid.setter('height'))

    # Адаптивный шрифт
    def calculate_font_size():
        w, _ = Window.size
        base = 14 + (w - dp(360)) / (dp(720)) * 4
        return sp(max(14, min(18, base)))

    adaptive_font = calculate_font_size()

    # Данные статистики
    stats_data = [
        ("Количество больниц:", format_number(faction.hospitals)),
        ("Количество фабрик:", format_number(faction.factories)),
        ("Рабочих на фабриках:", format_number(faction.work_peoples)),
        ("Прирост рабочих:", format_number(faction.clear_up_peoples)),
        ("Расход денег больницами:", format_number(faction.money_info)),
        ("Прирост кристаллов:", format_number(faction.food_info)),
        ("Чистый прирост денег:", format_number(faction.money_up)),
        ("Доход от налогов:", format_number(faction.taxes_info)),
        ("Эффект от налогов:",
         format_number(faction.apply_tax_effect(int(faction.current_tax_rate[:-1]))) if faction.tax_set else "–")
    ]

    for label_text, value in stats_data:
        card = BoxLayout(
            orientation='vertical',
            padding=[dp(12), dp(8), dp(12), dp(8)],
            spacing=dp(4),
            size_hint_y=None,
            height=dp(80)
        )
        with card.canvas.before:
            Color(0.2, 0.2, 0.2, 1)
            card.bg_rect = RoundedRectangle(
                pos=card.pos,
                size=card.size,
                radius=[12]
            )
        def update_stat_card_rect(instance, val):
            instance.bg_rect.pos = instance.pos
            instance.bg_rect.size = instance.size
        card.bind(pos=update_stat_card_rect, size=update_stat_card_rect)

        lbl = Label(
            text=label_text,
            font_size=adaptive_font,
            color=(0.9, 0.9, 0.9, 1),  # Ярче
            bold=True,
            size_hint_y=None,
            height=dp(24),
            halign='left',
            valign='middle'
        )
        lbl.bind(size=lambda inst, val: setattr(inst, 'text_size', (inst.width, inst.height)))
        card.add_widget(lbl)

        if isinstance(value, (int, float)):
            val_color = (0, 1, 0, 1) if value >= 0 else (1, 0, 0, 1)
            val_text = str(value)
        else:
            val_color = (0.9, 0.9, 0.9, 1)  # Ярче
            val_text = str(value)

        val = Label(
            text=val_text,
            font_size=adaptive_font,
            color=val_color,
            bold=True,
            size_hint_y=None,
            height=dp(28),
            halign='right',
            valign='middle'
        )
        val.bind(size=lambda inst, val: setattr(inst, 'text_size', (inst.width, inst.height)))
        card.add_widget(val)

        stats_grid.add_widget(card)

    stat_scroll.add_widget(stats_grid)
    stat_tab.content = stat_scroll

    # === Добавление вкладок в TabbedPanel ===
    tab_panel.add_widget(build_tab)
    tab_panel.add_widget(stat_tab)

    # === Основной макет — без кнопки "Закрыть" внизу ===
    main_layout = BoxLayout(orientation='vertical', spacing=dp(12), padding=dp(16))
    main_layout.add_widget(tab_panel)

    # Убрали кнопку "Закрыть" внизу
    # btn_box = BoxLayout(...)
    # main_layout.add_widget(btn_box)

    dev_popup.content = main_layout
    dev_popup.open()


#--------------------------
def start_economy_mode(faction, game_area, db_conn, season_manager):
    """Инициализация экономического режима для выбранной фракции"""

    from kivy.metrics import dp, sp
    from kivy.uix.widget import Widget

    is_android = platform == 'android'

    economy_layout = BoxLayout(
        orientation='horizontal',
        size_hint=(1, None),
        height=dp(70) if is_android else 60,
        pos_hint={'x': -0.34, 'y': 0},
        spacing=dp(10) if is_android else 10,
        padding=[dp(10), dp(5), dp(10), dp(5)] if is_android else [10, 5, 10, 5]
    )

    # Добавляем пустое пространство слева
    economy_layout.add_widget(Widget(size_hint_x=None, width=dp(20)))

    def create_styled_button(text, on_press_callback):
        button = Button(
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

        with button.canvas.before:
            Color(0.2, 0.8, 0.2, 1)
            button.rect = RoundedRectangle(pos=button.pos, size=button.size, radius=[15])

        def update_rect(instance, value):
            instance.rect.pos = instance.pos
            instance.rect.size = instance.size

        button.bind(pos=update_rect, size=update_rect)
        button.bind(on_release=on_press_callback)
        return button

    dev_btn = create_styled_button("Развитие", lambda x: open_development_popup(faction))
    trade_btn = create_styled_button("Рынок", lambda x: open_trade_popup(faction))
    tax_btn = create_styled_button("Налоги", lambda x: open_tax_popup(faction))
    economy_layout.add_widget(create_styled_button("Мастерская", lambda x: workshop(faction, db_conn)))
    economy_layout.add_widget(create_styled_button("Артефакты", lambda x: open_artifacts_popup(faction, season_manager)))
    economy_layout.add_widget(dev_btn)
    economy_layout.add_widget(trade_btn)
    economy_layout.add_widget(tax_btn)

    game_area.add_widget(economy_layout)