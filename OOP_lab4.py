import tkinter as tk
from tkinter import colorchooser

# ===== БАЗОВЫЙ КЛАСС =====
class Shape:
    def __init__(self, x, y, size=60, color="black"):
        self.x = x
        self.y = y
        self.w = size
        self.h = size
        self.color = color
        self.selected = False

    def move(self, dx, dy, max_w, max_h):
        """Перемещение с проверкой границ"""
        new_x = self.x + dx
        new_y = self.y + dy
        if 0 <= new_x and new_x + self.w <= max_w:
            self.x = new_x
        if 0 <= new_y and new_y + self.h <= max_h:
            self.y = new_y

    def set_size(self, new_size, max_w, max_h):
        """Изменение размера с проверкой границ"""
        # Проверяем, не выйдет ли объект за границы при новом размере
        if self.x + new_size <= max_w and self.y + new_size <= max_h:
            self.w = new_size
            self.h = new_size

    def draw(self, canvas):
        pass

    def draw_frame(self, canvas):
        if self.selected:
            canvas.create_rectangle(self.x-2, self.y-2, self.x+self.w+2, self.y+self.h+2, 
                                     outline="red", dash=(4, 2))

    def contains(self, px, py):
        return self.x <= px <= self.x + self.w and self.y <= py <= self.y + self.h

# ===== НАСЛЕДНИКИ =====
class Rectangle(Shape):
    def draw(self, canvas):
        canvas.create_rectangle(self.x, self.y, self.x + self.w, self.y + self.h, 
                                outline=self.color, width=2)
        self.draw_frame(canvas)

class Circle(Shape):
    def draw(self, canvas):
        canvas.create_oval(self.x, self.y, self.x + self.w, self.y + self.h, 
                           outline=self.color, width=2)
        self.draw_frame(canvas)

class Triangle(Shape):
    def draw(self, canvas):
        points = [self.x + self.w/2, self.y, self.x, self.y + self.h, self.x + self.w, self.y + self.h]
        canvas.create_polygon(points, outline=self.color, fill="", width=2)
        self.draw_frame(canvas)

# ===== КОНТЕЙНЕР ОБЪЕКТОВ =====
class ShapeContainer:
    def __init__(self):
        self.shapes = []

    def add(self, shape):
        self.shapes.append(shape)

    def draw_all(self, canvas):
        for shape in self.shapes:
            shape.draw(canvas)

    def clear_selection(self):
        for shape in self.shapes:
            shape.selected = False

    def get_selected(self):
        return [s for s in self.shapes if s.selected]

    def delete_selected(self):
        self.shapes = [s for s in self.shapes if not s.selected]

# ===== ГЛАВНОЕ ОКНО =====
class App:
    def __init__(self, root):
        self.root = root
        self.root.title("Visual Editor 4.0")
        
        self.container = ShapeContainer()
        self.current_type = "rect"
        self.current_size = 60
        
        # Переменные для Drag-and-Drop
        self.last_x = 0
        self.last_y = 0

        self.setup_ui()

    def setup_ui(self):
        # Панель инструментов
        toolbar = tk.Frame(self.root, bg="#f0f0f0", pady=5)
        toolbar.pack(side=tk.TOP, fill=tk.X)

        # Выбор типа
        tk.Label(toolbar, text="Тип:").pack(side=tk.LEFT, padx=5)
        for t, n in [("rect", "Квадрат"), ("circle", "Круг"), ("tri", "Треугольник")]:
            tk.Button(toolbar, text=n, command=lambda arg=t: self.set_type(arg)).pack(side=tk.LEFT, padx=2)

        # Ползунок размера
        tk.Label(toolbar, text="Размер:").pack(side=tk.LEFT, padx=(20, 5))
        self.size_scale = tk.Scale(toolbar, from_=10, to=200, orient=tk.HORIZONTAL, 
                                   command=self.on_scale_change)
        self.size_scale.set(self.current_size)
        self.size_scale.pack(side=tk.LEFT)

        tk.Button(toolbar, text="Цвет", command=self.pick_color).pack(side=tk.LEFT, padx=10)
        tk.Button(toolbar, text="Удалить", command=self.delete_selected).pack(side=tk.RIGHT, padx=10)

        # Холст
        self.canvas = tk.Canvas(self.root, width=800, height=600, bg="white")
        self.canvas.pack(fill=tk.BOTH, expand=True)

        # Привязки событий
        self.canvas.bind("<Button-1>", self.on_press)      # Нажали кнопку
        self.canvas.bind("<B1-Motion>", self.on_drag)      # Ведем мышью
        self.root.bind("<Delete>", lambda e: self.delete_selected())
        self.root.bind("<KeyPress>", self.on_key)

    def set_type(self, t):
        self.current_type = t

    def on_scale_change(self, val):
        self.current_size = int(val)
        cw, ch = self.canvas.winfo_width(), self.canvas.winfo_height()
        # Если есть выделенные - меняем им размер сразу
        for s in self.container.get_selected():
            s.set_size(self.current_size, cw, ch)
        self.redraw()

    def pick_color(self):
        color = colorchooser.askcolor()[1]
        if color:
            for s in self.container.get_selected():
                s.color = color
            self.redraw()

    def on_press(self, event):
        ctrl = (event.state & 0x0004) != 0
        self.last_x, self.last_y = event.x, event.y
        
        clicked_shape = None
        for s in reversed(self.container.shapes):
            if s.contains(event.x, event.y):
                clicked_shape = s
                break

        if clicked_shape:
            if not ctrl and not clicked_shape.selected:
                self.container.clear_selection()
            
            if ctrl:
                clicked_shape.selected = not clicked_shape.selected
            else:
                clicked_shape.selected = True
            
            # При выделении одного объекта, подтягиваем ползунок под его размер
            if len(self.container.get_selected()) == 1:
                self.size_scale.set(clicked_shape.w)
        else:
            if not ctrl:
                self.container.clear_selection()
                self.create_shape(event.x, event.y)
        
        self.redraw()

    def on_drag(self, event):
        """Перемещение объектов мышкой"""
        dx = event.x - self.last_x
        dy = event.y - self.last_y
        
        cw, ch = self.canvas.winfo_width(), self.canvas.winfo_height()
        for s in self.container.get_selected():
            s.move(dx, dy, cw, ch)
            
        self.last_x, self.last_y = event.x, event.y
        self.redraw()

    def create_shape(self, x, y):
        # Используем текущий размер из ползунка
        args = (x, y, self.current_size)
        if self.current_type == "rect": new_s = Rectangle(*args)
        elif self.current_type == "circle": new_s = Circle(*args)
        else: new_s = Triangle(*args)
        
        # Проверка, чтобы не создалась за краем
        cw, ch = self.canvas.winfo_width(), self.canvas.winfo_height()
        if x + self.current_size > cw: new_s.x = cw - self.current_size
        if y + self.current_size > ch: new_s.y = ch - self.current_size
        
        self.container.add(new_s)

    def on_key(self, event):
        step = 5
        shift = (event.state & 0x0001) != 0
        selected = self.container.get_selected()
        cw, ch = self.canvas.winfo_width(), self.canvas.winfo_height()

        for s in selected:
            if event.keysym == "Up": s.move(0, -step, cw, ch)
            elif event.keysym == "Down": s.move(0, step, cw, ch)
            elif event.keysym == "Left": s.move(-step, 0, cw, ch)
            elif event.keysym == "Right": s.move(step, 0, cw, ch)
        self.redraw()

    def delete_selected(self):
        self.container.delete_selected()
        self.redraw()

    def redraw(self):
        self.canvas.delete("all")
        self.container.draw_all(self.canvas)

if __name__ == "__main__":
    root = tk.Tk()
    app = App(root)
    root.mainloop()
