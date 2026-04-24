import tkinter as tk
from tkinter import colorchooser
import math

# ===== БАЗОВЫЙ КЛАСС (Иерархия по требованию лабы) =====
class Shape:
    def __init__(self, x, y, w=50, h=50, color="black"):
        self.x = x
        self.y = y
        self.w = w
        self.h = h
        self.color = color
        self.selected = False

    def move(self, dx, dy, max_w, max_h):
        """Логика перемещения вынесена в базу для исключения дублирования"""
        new_x = self.x + dx
        new_y = self.y + dy
        # Проверка границ: ни одна часть не должна выйти за холст
        if 0 <= new_x and new_x + self.w <= max_w:
            self.x = new_x
        if 0 <= new_y and new_y + self.h <= max_h:
            self.y = new_y

    def resize(self, dw, dh, max_w, max_h):
        """Логика изменения размера вынесена в базу"""
        new_w = max(10, self.w + dw) # Мин. размер 10
        new_h = max(10, self.h + dh)
        # Проверка границ при растяжении
        if self.x + new_w <= max_w:
            self.w = new_w
        if self.y + new_h <= max_h:
            self.h = new_h

    def draw(self, canvas):
        pass

    def draw_frame(self, canvas):
        """Рамка выделения"""
        if self.selected:
            canvas.create_rectangle(self.x-2, self.y-2, self.x+self.w+2, self.y+self.h+2, 
                                     outline="red", dash=(4, 2))

    def contains(self, px, py):
        """Базовая проверка попадания в прямоугольную область"""
        return self.x <= px <= self.x + self.w and self.y <= py <= self.y + self.h


# ===== НАСЛЕДНИКИ =====

class Rectangle(Shape):
    def draw(self, canvas):
        canvas.create_rectangle(self.x, self.y, self.x + self.w, self.y + self.h, 
                                outline=self.color, width=2)
        self.draw_frame(canvas)

class Circle(Shape): # Эллипс в границах w и h
    def draw(self, canvas):
        canvas.create_oval(self.x, self.y, self.x + self.w, self.y + self.h, 
                           outline=self.color, width=2)
        self.draw_frame(canvas)
    
    def contains(self, px, py):
        # Более точная проверка для круга (из лр3)
        rx, ry = self.w/2, self.h/2
        cx, cy = self.x + rx, self.y + ry
        return ((px - cx)**2 / rx**2 + (py - cy)**2 / ry**2) <= 1

class Triangle(Shape):
    def draw(self, canvas):
        points = [self.x + self.w/2, self.y, 
                  self.x, self.y + self.h, 
                  self.x + self.w, self.y + self.h]
        canvas.create_polygon(points, outline=self.color, fill="", width=2)
        self.draw_frame(canvas)


# ===== КОНТЕЙНЕР ОБЪЕКТОВ (из ЛР 3) =====
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


# ===== ГЛАВНОЕ ОКНО (GUI) =====
class App:
    def __init__(self, root):
        self.root = root
        self.root.title("Лабораторная 4: Визуальный редактор")
        self.container = ShapeContainer()
        self.current_type = "rect" # Тип по умолчанию

        # Панель инструментов (Меню)
        self.toolbar = tk.Frame(root, bg="lightgray", pady=5)
        self.toolbar.pack(side=tk.TOP, fill=tk.X)

        tk.Button(self.toolbar, text="Квадрат", command=lambda: self.set_type("rect")).pack(side=tk.LEFT, padx=5)
        tk.Button(self.toolbar, text="Круг", command=lambda: self.set_type("circle")).pack(side=tk.LEFT, padx=5)
        tk.Button(self.toolbar, text="Треугольник", command=lambda: self.set_type("tri")).pack(side=tk.LEFT, padx=5)
        tk.Button(self.toolbar, text="Цвет", command=self.pick_color).pack(side=tk.LEFT, padx=15)

        # Холст
        self.canvas = tk.Canvas(root, width=800, height=600, bg="white")
        self.canvas.pack(fill=tk.BOTH, expand=True)

        # События
        self.canvas.bind("<Button-1>", self.on_click)
        self.root.bind("<Delete>", lambda e: self.delete_selected())
        self.root.bind("<KeyPress>", self.on_key)

    def set_type(self, t):
        self.current_type = t

    def pick_color(self):
        color = colorchooser.askcolor()[1]
        if color:
            for s in self.container.get_selected():
                s.color = color
            self.redraw()

    def on_click(self, event):
        ctrl = (event.state & 0x0004) != 0 # Проверка Ctrl для мультивыбора
        
        # Ищем, кликнули ли по фигуре (с конца списка, чтобы брать верхнюю)
        clicked_shape = None
        for s in reversed(self.container.shapes):
            if s.contains(event.x, event.y):
                clicked_shape = s
                break

        if clicked_shape:
            if not ctrl:
                self.container.clear_selection()
            clicked_shape.selected = True if not ctrl else not clicked_shape.selected
        else:
            if not ctrl:
                self.container.clear_selection()
                # Создаем новую фигуру при клике в пустоту
                self.create_shape(event.x, event.y)
        
        self.redraw()

    def create_shape(self, x, y):
        # Базовый размер 60x60
        if self.current_type == "rect":
            new_s = Rectangle(x, y, 60, 60)
        elif self.current_type == "circle":
            new_s = Circle(x, y, 60, 60)
        else:
            new_s = Triangle(x, y, 60, 60)
        
        self.container.add(new_s)

    def on_key(self, event):
        step = 5
        shift = (event.state & 0x0001) != 0 # Shift для изменения размера
        
        selected = self.container.get_selected()
        cw, ch = self.canvas.winfo_width(), self.canvas.winfo_height()

        for s in selected:
            if event.keysym == "Up":
                if shift: s.resize(0, -step, cw, ch)
                else: s.move(0, -step, cw, ch)
            elif event.keysym == "Down":
                if shift: s.resize(0, step, cw, ch)
                else: s.move(0, step, cw, ch)
            elif event.keysym == "Left":
                if shift: s.resize(-step, 0, cw, ch)
                else: s.move(-step, 0, cw, ch)
            elif event.keysym == "Right":
                if shift: s.resize(step, 0, cw, ch)
                else: s.move(step, 0, cw, ch)
        
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
