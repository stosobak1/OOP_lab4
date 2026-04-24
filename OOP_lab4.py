import tkinter as tk
from tkinter import colorchooser, Menu, messagebox

# =============================================================================
# БИЗНЕС-ЛОГИКА: ИЕРАРХИЯ КЛАССОВ ФИГУР
# =============================================================================

class Shape:
    """ Базовый класс для всех графических объектов """
    def __init__(self, x, y, width=60, height=60, color="black"):
        self.x = x
        self.y = y
        self.w = width
        self.h = height
        self.color = color
        self.selected = False

    def move(self, dx, dy, max_w, max_h):
        """ Перемещение объекта с жесткой проверкой границ холста """
        new_x = self.x + dx
        new_y = self.y + dy
        
        # Контроль выхода за рабочую область (лево/право)
        if 0 <= new_x and new_x + self.w <= max_w:
            self.x = new_x
        # Контроль выхода за рабочую область (верх/низ)
        if 0 <= new_y and new_y + self.h <= max_h:
            self.y = new_y

    def resize(self, dw, dh, max_w, max_h):
        """ Изменение размеров (ширины и высоты) с проверкой границ """
        new_w = max(5, self.w + dw)  # Минимальная ширина 5 пикселей
        new_h = max(5, self.h + dh)  # Минимальная высота 5 пикселей
        
        # Не даем растягивать фигуру за пределы холста
        if self.x + new_w <= max_w:
            self.w = new_w
        if self.y + new_h <= max_h:
            self.h = new_h

    def draw(self, canvas):
        """ Метод отрисовки, который каждый потомок реализует сам """
        pass

    def draw_selection_frame(self, canvas):
        """ Отрисовка рамки выделения для выбранных объектов """
        if self.selected:
            # Рисуем пунктирную рамку чуть больше самой фигуры
            canvas.create_rectangle(
                self.x - 3, self.y - 3, 
                self.x + self.w + 3, self.y + self.h + 3, 
                outline="red", dash=(4, 4), width=1
            )

    def contains(self, px, py):
        """ Проверка: находится ли точка (клик) внутри области фигуры """
        return self.x <= px <= self.x + self.w and self.y <= py <= self.y + self.h


class RectangleShape(Shape):
    def draw(self, canvas):
        canvas.create_rectangle(self.x, self.y, self.x + self.w, self.y + self.h, 
                                outline=self.color, width=2)
        self.draw_selection_frame(canvas)


class EllipseShape(Shape):
    def draw(self, canvas):
        canvas.create_oval(self.x, self.y, self.x + self.w, self.y + self.h, 
                           outline=self.color, width=2)
        self.draw_selection_frame(canvas)


class TriangleShape(Shape):
    def draw(self, canvas):
        # Треугольник вписывается в прямоугольную область (x, y, w, h)
        points = [
            self.x + self.w / 2, self.y,           # Верхняя точка
            self.x, self.y + self.h,               # Левая нижняя
            self.x + self.w, self.y + self.h       # Правая нижняя
        ]
        canvas.create_polygon(points, outline=self.color, fill="", width=2)
        self.draw_selection_frame(canvas)


class LineShape(Shape):
    def draw(self, canvas):
        # Отрезок рисуется из угла в угол воображаемого прямоугольника
        canvas.create_line(self.x, self.y, self.x + self.w, self.y + self.h, 
                           fill=self.color, width=2)
        self.draw_selection_frame(canvas)


# =============================================================================
# КОНТЕЙНЕР ОБЪЕКТОВ (ЛОГИКА ХРАНЕНИЯ)
# =============================================================================

class ShapeContainer:
    def __init__(self):
        self.shapes = []

    def add_shape(self, shape):
        self.shapes.append(shape)

    def clear_selection(self):
        for s in self.shapes:
            s.selected = False

    def get_selected_shapes(self):
        return [s for s in self.shapes if s.selected]

    def delete_selected(self):
        self.shapes = [s for s in self.shapes if not s.selected]

    def clear_all(self):
        self.shapes = []


# =============================================================================
# ГЛАВНОЕ ОКНО ПРИЛОЖЕНИЯ (GUI)
# =============================================================================

class VisualEditorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Профессиональный векторный редактор (Лаб. №4)")
        self.root.geometry("1000x750")

        self.container = ShapeContainer()
        self.current_tool = "rect"
        
        # Текущие настройки для создания новых фигур
        self.target_width = 80
        self.target_height = 60
        
        # Координаты для Drag-and-Drop
        self.drag_last_x = 0
        self.drag_last_y = 0

        self.init_interface()

    def init_interface(self):
        """ Создание всех элементов управления """
        # --- 1. ВЕРХНЕЕ МЕНЮ ---
        self.menu_bar = Menu(self.root)
        
        file_menu = Menu(self.menu_bar, tearoff=0)
        file_menu.add_command(label="Гайд по управлению", command=self.show_help_guide)
        file_menu.add_command(label="Очистить холст", command=self.action_clear_canvas)
        file_menu.add_separator()
        file_menu.add_command(label="Выход", command=self.root.quit)
        self.menu_bar.add_cascade(label="Файл", menu=file_menu)

        func_menu = Menu(self.menu_bar, tearoff=0)
        func_menu.add_command(label="Изменить цвет (Palette)", command=self.action_pick_color)
        func_menu.add_command(label="Удалить выбранное (Del)", command=self.action_delete)
        self.menu_bar.add_cascade(label="Функции", menu=func_menu)
        
        self.root.config(menu=self.menu_bar)

        # --- 2. ПАНЕЛЬ ИНСТРУМЕНТОВ ---
        self.toolbar = tk.Frame(self.root, bd=1, relief=tk.RAISED, bg="#e1e1e1")
        self.toolbar.pack(side=tk.TOP, fill=tk.X)

        # Группа кнопок выбора фигур
        tk.Label(self.toolbar, text="Объекты:", bg="#e1e1e1", font=("Arial", 9, "bold")).pack(side=tk.LEFT, padx=5)
        for tool_id, name in [("rect", "Прямоуг."), ("ellipse", "Эллипс"), ("tri", "Треуг."), ("line", "Линия")]:
            btn = tk.Button(self.toolbar, text=name, command=lambda t=tool_id: self.set_active_tool(t))
            btn.pack(side=tk.LEFT, padx=2, pady=5)

        # Разделитель
        tk.Frame(self.toolbar, width=2, bd=1, relief=tk.SUNKEN).pack(side=tk.LEFT, fill=tk.Y, padx=10, pady=5)

        # Ползунки размерности (X и Y отдельно)
        tk.Label(self.toolbar, text="Ширина (X):", bg="#e1e1e1").pack(side=tk.LEFT, padx=2)
        self.scale_w = tk.Scale(self.toolbar, from_=5, to=400, orient=tk.HORIZONTAL, length=120, command=self.on_width_scale_move)
        self.scale_w.set(self.target_width)
        self.scale_w.pack(side=tk.LEFT, padx=5)

        tk.Label(self.toolbar, text="Высота (Y):", bg="#e1e1e1").pack(side=tk.LEFT, padx=2)
        self.scale_h = tk.Scale(self.toolbar, from_=5, to=400, orient=tk.HORIZONTAL, length=120, command=self.on_height_scale_move)
        self.scale_h.set(self.target_height)
        self.scale_h.pack(side=tk.LEFT, padx=5)

        # Кнопки быстрых действий
        tk.Button(self.toolbar, text="Цвет", command=self.action_pick_color, bg="#d0d0d0").pack(side=tk.LEFT, padx=15)
        tk.Button(self.toolbar, text="Удалить", command=self.action_delete, fg="white", bg="#a04040").pack(side=tk.RIGHT, padx=10)

        # --- 3. ХОЛСТ (РАБОЧАЯ ОБЛАСТЬ) ---
        self.canvas = tk.Canvas(self.root, bg="white", highlightthickness=1, highlightbackground="#999")
        self.canvas.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # --- 4. СОБЫТИЯ И БИНДИНГИ ---
        self.canvas.bind("<Button-1>", self.handle_mouse_press)      # Нажатие
        self.canvas.bind("<B1-Motion>", self.handle_mouse_drag)      # Перетаскивание
        self.root.bind("<KeyPress>", self.handle_key_press)          # Клавиатура
        self.root.bind("<Delete>", lambda e: self.action_delete())   # Del

    # --- МЕТОДЫ УПРАВЛЕНИЯ ---

    def show_help_guide(self):
        """ Тот самый мини-гайд по управлению """
        guide_text = (
            "ИНСТРУКЦИЯ ПО ЭКСПЛУАТАЦИИ:\n\n"
            "• Клик по пустому месту — создать фигуру (используются размеры с ползунков).\n"
            "• Клик по фигуре — выбрать её (появится красная рамка).\n"
            "• Ctrl + Клик — мультивыбор нескольких объектов.\n"
            "• Зажать и тянуть — свободное перемещение выбранных объектов.\n\n"
            "КЛАВИАТУРА:\n"
            "• Стрелки [↑][↓][←][→] — перемещение объектов.\n"
            "• Shift + [←][→] — изменить ШИРИНУ объекта.\n"
            "• Shift + [↑][↓] — изменить ВЫСОТУ объекта.\n"
            "• [Delete] — удалить выбранное.\n\n"
            "ПОЛЗУНКИ:\n"
            "• Меняют размер создаваемой фигуры ИЛИ мгновенно меняют размер всех выбранных."
        )
        messagebox.showinfo("Гайд по редактору", guide_text)

    def set_active_tool(self, tool):
        self.current_tool = tool

    def on_width_scale_move(self, val):
        """ Реакция на изменение ползунка ширины """
        self.target_width = int(val)
        cw, ch = self.canvas.winfo_width(), self.canvas.winfo_height()
        # Если есть выделенные — меняем их ширину, сохраняя их высоту
        for s in self.container.get_selected_shapes():
            diff = self.target_width - s.w
            s.resize(diff, 0, cw, ch)
        self.refresh_canvas()

    def on_height_scale_move(self, val):
        """ Реакция на изменение ползунка высоты """
        self.target_height = int(val)
        cw, ch = self.canvas.winfo_width(), self.canvas.winfo_height()
        # Если есть выделенные — меняем их высоту, сохраняя их ширину
        for s in self.container.get_selected_shapes():
            diff = self.target_height - s.h
            s.resize(0, diff, cw, ch)
        self.refresh_canvas()

    def handle_mouse_press(self, event):
        """ Обработка первого клика мыши """
        ctrl_held = (event.state & 0x0004) != 0
        self.drag_last_x, self.drag_last_y = event.x, event.y
        
        # Ищем объект под курсором (в обратном порядке, чтобы брать верхний)
        found_shape = None
        for s in reversed(self.container.shapes):
            if s.contains(event.x, event.y):
                found_shape = s
                break

        if found_shape:
            # Если не зажат Ctrl и кликаем по новому объекту — сбрасываем старое выделение
            if not ctrl_held and not found_shape.selected:
                self.container.clear_selection()
            
            # Переключаем состояние выделения
            if ctrl_held:
                found_shape.selected = not found_shape.selected
            else:
                found_shape.selected = True
            
            # СИНХРОНИЗАЦИЯ: обновляем ползунки под размеры выбранной фигуры
            # (если выбрана одна фигура)
            selected_list = self.container.get_selected_shapes()
            if len(selected_list) == 1:
                # Временно отключаем команды ползунков, чтобы не вызвать рекурсию
                self.scale_w.set(selected_list[0].w)
                self.scale_h.set(selected_list[0].h)
        else:
            # Клик в пустоту
            if not ctrl_held:
                self.container.clear_selection()
                self.add_new_shape_at(event.x, event.y)
        
        self.refresh_canvas()

    def handle_mouse_drag(self, event):
        """ Перемещение объектов при зажатой левой кнопке мыши """
        dx = event.x - self.drag_last_x
        dy = event.y - self.drag_last_y
        
        cw, ch = self.canvas.winfo_width(), self.canvas.winfo_height()
        # Двигаем всю группу выделенных объектов
        for s in self.container.get_selected_shapes():
            s.move(dx, dy, cw, ch)
            
        self.drag_last_x, self.drag_last_y = event.x, event.y
        self.refresh_canvas()

    def handle_key_press(self, event):
        """ Управление с клавиатуры по стандартам Windows """
        step = 5
        shift_held = (event.state & 0x0001) != 0
        cw, ch = self.canvas.winfo_width(), self.canvas.winfo_height()
        selected = self.container.get_selected_shapes()

        for s in selected:
            if event.keysym == "Up":
                if shift_held: s.resize(0, -step, cw, ch) # Уменьшить высоту
                else: s.move(0, -step, cw, ch)            # Двигать вверх
            elif event.keysym == "Down":
                if shift_held: s.resize(0, step, cw, ch)  # Увеличить высоту
                else: s.move(0, step, cw, ch)             # Двигать вниз
            elif event.keysym == "Left":
                if shift_held: s.resize(-step, 0, cw, ch) # Уменьшить ширину
                else: s.move(-step, 0, cw, ch)            # Двигать влево
            elif event.keysym == "Right":
                if shift_held: s.resize(step, 0, cw, ch)  # Увеличить ширину
                else: s.move(step, 0, cw, ch)             # Двигать вправо
        
        # Обновляем ползунки, если размер изменился кнопками
        if selected and shift_held:
            self.scale_w.set(selected[-1].w)
            self.scale_h.set(selected[-1].h)
            
        self.refresh_canvas()

    def add_new_shape_at(self, x, y):
        """ Создание объекта на основе текущих настроек тулбара """
        w, h = self.target_width, self.target_height
        cw, ch = self.canvas.winfo_width(), self.canvas.winfo_height()
        
        # Корректируем X/Y, чтобы объект не создавался "за кадром"
        if x + w > cw: x = cw - w
        if y + h > ch: y = ch - h
        if x < 0: x = 0
        if y < 0: y = 0

        if self.current_tool == "rect":
            new_s = RectangleShape(x, y, w, h)
        elif self.current_tool == "ellipse":
            new_s = EllipseShape(x, y, w, h)
        elif self.current_tool == "tri":
            new_s = TriangleShape(x, y, w, h)
        elif self.current_tool == "line":
            new_s = LineShape(x, y, w, h)
        
        self.container.add_shape(new_s)

    def action_pick_color(self):
        """ Стандартный диалог выбора цвета Windows """
        selected = self.container.get_selected_shapes()
        if not selected:
            messagebox.showwarning("Внимание", "Сначала выберите фигуры для окрашивания!")
            return
            
        color_tuple = colorchooser.askcolor(title="Выберите цвет контура")
        if color_tuple[1]: # Если не нажали 'Отмена'
            for s in selected:
                s.color = color_tuple[1]
            self.refresh_canvas()

    def action_delete(self):
        self.container.delete_selected()
        self.refresh_canvas()

    def action_clear_canvas(self):
        if messagebox.askyesno("Подтверждение", "Вы уверены, что хотите удалить ВСЕ объекты?"):
            self.container.clear_all()
            self.refresh_canvas()

    def refresh_canvas(self):
        """ Полная перерисовка всех объектов из контейнера """
        self.canvas.delete("all")
        for shape in self.container.shapes:
            shape.draw(self.canvas)


# =============================================================================
# ТОЧКА ВХОДА
# =============================================================================

if __name__ == "__main__":
    root = tk.Tk()
    # Установка иконки или стилей при необходимости
    editor = VisualEditorApp(root)
    root.mainloop()
