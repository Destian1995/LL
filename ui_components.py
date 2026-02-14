from kivy.graphics import Color, Rectangle, RoundedRectangle
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.image import Image
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.clock import Clock
from kivy.animation import Animation
from kivy.core.window import Window
from kivy.metrics import dp, sp


class TutorialHint(FloatLayout):
    """Виджет подсказки обучения со стрелкой, текстом и кнопкой 'Далее'"""

    def __init__(self, target_widget, arrow_source, message, arrow_direction='right',
                 on_complete=None, on_skip=None, on_next=None, **kwargs):
        super().__init__(**kwargs)
        self.target_widget = target_widget
        self.arrow_direction = arrow_direction
        self.on_complete = on_complete
        self.on_skip = on_skip
        self.on_next = on_next
        self.size_hint = (1, 1)
        self.pos_hint = {'x': 0, 'y': 0}
        self.spotlight_padding = dp(25)

        # Затемняющий фон
        with self.canvas.before:
            Color(0, 0, 0, 0.5)
            self.bg_rect = Rectangle(pos=self.pos, size=self.size)

        self.bind(pos=self._update_bg, size=self._update_bg)

        # Прямоугольники для эффекта фокуса
        with self.canvas.before:
            Color(0, 0, 0, 0.82)
            self.top_rect = Rectangle()
            self.left_rect = Rectangle()
            self.right_rect = Rectangle()
            self.bottom_rect = Rectangle()

        # Стрелка-указатель
        self.arrow = Image(
            source=arrow_source,
            size_hint=(None, None),
            size=(dp(60), dp(60)),
            allow_stretch=True,
            keep_ratio=True
        )

        # КОНТЕЙНЕР ДЛЯ ТЕКСТА (улучшенная версия)
        self.bubble = BoxLayout(
            orientation='vertical',
            size_hint=(None, None),
            width=dp(400),  # Увеличил ширину
            padding=(dp(28), dp(28), dp(28), dp(20)),  # Увеличил отступы
            spacing=dp(20)
        )

        # Метка с текстом
        self.label = Label(
            text=message,
            font_size=sp(20),
            color=(0.95, 1.0, 1.0, 1),
            halign='center',
            valign='middle',  # Изменил на middle для лучшего вертикального выравнивания
            markup=True,
            size_hint_y=None,
            text_size=(self.bubble.width - dp(56), None)  # Учитываем padding
        )

        # ВАЖНО: правильный расчет высоты на основе текста
        self.label.bind(
            texture_size=self._update_label_height
        )

        # Кнопка "Далее"
        self.next_btn = Button(
            text="Продолжить",
            size_hint=(None, None),
            size=(dp(160), dp(48)),  # Увеличил кнопку
            background_color=(0.3, 0.7, 0.3, 1),
            color=(1, 1, 1, 1),
            font_size=sp(18),
            bold=True,
            pos_hint={'center_x': 0.5}  # Центрирование внутри BoxLayout
        )
        self.next_btn.bind(on_release=self._on_next)

        # Кнопка пропуска (будет добавлена отдельно, не в пузырь)
        self.skip_btn = Button(
            text="Пропустить обучение",
            size_hint=(None, None),
            size=(dp(200), dp(40)),
            background_color=(0.6, 0.2, 0.2, 0.95),
            color=(1, 1, 1, 1),
            font_size=sp(16),
            bold=True
        )
        self.skip_btn.bind(on_release=self._on_skip)

        # Сборка пузыря
        self.bubble.add_widget(self.label)
        self.bubble.add_widget(self.next_btn)

        # Создаем фон для пузыря с закругленными углами
        with self.bubble.canvas.before:
            Color(0.15, 0.25, 0.45, 0.98)
            self.bubble_bg = RoundedRectangle(
                pos=self.bubble.pos,
                size=self.bubble.size,
                radius=[24]
            )

        # Обновляем фон при изменении позиции/размера пузыря
        self.bubble.bind(pos=self._update_bubble_bg, size=self._update_bubble_bg)

        # Добавляем виджеты
        self.add_widget(self.arrow)
        self.add_widget(self.bubble)
        self.add_widget(self.skip_btn)  # Кнопка пропуска отдельно от пузыря

        # Обновляем text_size при изменении ширины пузыря
        self.bubble.bind(width=self._update_label_text_size)

        # Позиционирование
        Clock.schedule_once(self._position_elements, 0.2)

        # Анимация появления
        self.opacity = 0
        Animation(opacity=1, duration=0.35).start(self)

    def _update_label_height(self, instance, texture_size):
        """Обновление высоты метки на основе размера текста"""
        instance.height = max(texture_size[1], dp(40))  # Минимальная высота 40dp

    def _update_label_text_size(self, instance, width):
        """Обновление text_size при изменении ширины пузыря"""
        self.label.text_size = (width - dp(56), None)  # Учитываем padding слева и справа

    def _update_bubble_bg(self, instance, value):
        """Обновление позиции и размера фона пузыря"""
        self.bubble_bg.pos = instance.pos
        self.bubble_bg.size = instance.size

    def _position_elements(self, dt):
        """Позиционирование элементов подсказки"""
        if not self.target_widget or not self.target_widget.parent:
            return

        # Получаем координаты целевого виджета
        target_x, target_y = self.target_widget.to_window(*self.target_widget.pos)
        target_w, target_h = self.target_widget.size

        win_x, win_y = self.to_widget(target_x, target_y, relative=True)

        # Рассчитываем координаты "дырки"
        hole_x = win_x - self.spotlight_padding
        hole_y = win_y - self.spotlight_padding
        hole_w = target_w + self.spotlight_padding * 2
        hole_h = target_h + self.spotlight_padding * 2

        # Обновляем прямоугольники затемнения
        window_w, window_h = Window.size

        self.top_rect.pos = (0, hole_y + hole_h)
        self.top_rect.size = (window_w, window_h - (hole_y + hole_h))

        self.left_rect.pos = (0, hole_y)
        self.left_rect.size = (hole_x, hole_h)

        self.right_rect.pos = (hole_x + hole_w, hole_y)
        self.right_rect.size = (window_w - (hole_x + hole_w), hole_h)

        self.bottom_rect.pos = (0, 0)
        self.bottom_rect.size = (window_w, hole_y)

        # Позиционируем стрелку и пузырь
        bubble_center_y = win_y + target_h / 2
        bubble_center_x = win_x + target_w / 2

        # Принудительно обновляем размер пузыря перед позиционированием
        self.bubble.width = dp(400)
        self.bubble.height = self.label.height + self.next_btn.height + dp(68)  # Учитываем padding и spacing

        if self.arrow_direction == 'right':
            # Стрелка слева от кнопки
            self.arrow.pos = (win_x - dp(95), bubble_center_y - dp(30))
            # Пузырь слева от кнопки
            self.bubble.pos = (
                win_x - self.bubble.width - dp(50),
                bubble_center_y - self.bubble.height / 2
            )
        else:  # down
            # Стрелка сверху кнопки
            self.arrow.pos = (bubble_center_x - dp(30), win_y - dp(95))
            # Пузырь сверху от кнопки
            self.bubble.pos = (
                bubble_center_x - self.bubble.width / 2,
                win_y - self.bubble.height - dp(50)
            )

        # Корректировка, чтобы пузырь не выходил за границы экрана
        self._ensure_bubble_on_screen()

        # Позиционируем кнопку пропуска
        self.skip_btn.pos = (Window.width / 2 - self.skip_btn.width / 2, dp(30))

    def _ensure_bubble_on_screen(self):
        """Корректировка позиции пузыря, чтобы он не выходил за границы экрана"""
        window_w, window_h = Window.size

        # По X
        if self.bubble.x < dp(10):
            self.bubble.x = dp(10)
        elif self.bubble.right > window_w - dp(10):
            self.bubble.x = window_w - self.bubble.width - dp(10)

        # По Y
        if self.bubble.y < dp(50):  # Учитываем место для кнопки пропуска
            self.bubble.y = dp(50)
        elif self.bubble.top > window_h - dp(10):
            self.bubble.y = window_h - self.bubble.height - dp(10)

    def _on_next(self, instance):
        """Обработчик нажатия кнопки 'Далее'"""
        anim = Animation(opacity=0, duration=0.25)
        anim.bind(on_complete=lambda *a: self._cleanup())
        anim.start(self)
        if self.on_next:
            Clock.schedule_once(lambda dt: self.on_next(), 0.3)

    def _on_skip(self, instance):
        """Обработчик пропуска обучения"""
        anim = Animation(opacity=0, duration=0.25)
        anim.bind(on_complete=lambda *a: self._cleanup())
        anim.start(self)
        if self.on_skip:
            Clock.schedule_once(lambda dt: self.on_skip(), 0.3)

    def _cleanup(self):
        """Очистка виджета"""
        if self.parent:
            self.parent.remove_widget(self)

    def _update_bg(self, *args):
        """Обновление фонового прямоугольника"""
        self.bg_rect.pos = self.pos
        self.bg_rect.size = self.size
