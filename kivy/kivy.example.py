# Kivy Calculator App dengan Trigonometri (pakai derajat)
# --------------------------------------------------
# Cara menjalankan:
# 1) pip install kivy
# 2) python main.py
# --------------------------------------------------

from __future__ import annotations
import ast
import math

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.core.window import Window

# ---------------------------
# Safe expression evaluator
# ---------------------------

ALLOWED_BINOPS = (ast.Add, ast.Sub, ast.Mult, ast.Div, ast.Pow, ast.Mod, ast.FloorDiv)
ALLOWED_UNARYOPS = (ast.UAdd, ast.USub)
ALLOWED_FUNCS = {
    "sin": lambda x: math.sin(math.radians(x)),
    "cos": lambda x: math.cos(math.radians(x)),
    "tan": lambda x: math.tan(math.radians(x)),
    "sqrt": math.sqrt,
    "log": math.log10,
}


def safe_eval(expr: str) -> float:
    """Safely evaluate expression with math functions."""
    try:
        node = ast.parse(expr, mode="eval")
    except SyntaxError as e:
        raise ValueError("Sintaks tidak valid") from e

    def _eval(n: ast.AST) -> float:
        if isinstance(n, ast.Expression):
            return _eval(n.body)
        if isinstance(n, ast.Constant):
            if isinstance(n.value, (int, float)):
                return n.value
            raise ValueError("Hanya angka yang diizinkan")
        if isinstance(n, ast.Num):
            return n.n
        if isinstance(n, ast.UnaryOp) and isinstance(n.op, ALLOWED_UNARYOPS):
            val = _eval(n.operand)
            return +val if isinstance(n.op, ast.UAdd) else -val
        if isinstance(n, ast.BinOp) and isinstance(n.op, ALLOWED_BINOPS):
            left = _eval(n.left)
            right = _eval(n.right)
            if isinstance(n.op, ast.Add):
                return left + right
            if isinstance(n.op, ast.Sub):
                return left - right
            if isinstance(n.op, ast.Mult):
                return left * right
            if isinstance(n.op, ast.Div):
                return left / right
            if isinstance(n.op, ast.FloorDiv):
                return left // right
            if isinstance(n.op, ast.Mod):
                return left % right
            if isinstance(n.op, ast.Pow):
                return left ** right
        if isinstance(n, ast.Call) and isinstance(n.func, ast.Name):
            fname = n.func.id
            if fname in ALLOWED_FUNCS:
                args = [_eval(arg) for arg in n.args]
                return ALLOWED_FUNCS[fname](*args)
        raise ValueError("Ekspresi mengandung operasi/fungsi yang tidak diizinkan")

    return _eval(node)


# ---------------------------
# Helpers
# ---------------------------

def is_operator(ch: str) -> bool:
    return ch in "+−×÷*/%()"


def map_display_to_eval(s: str) -> str:
    return (
        s.replace("×", "*")
        .replace("÷", "/")
        .replace("−", "-")
    )


def prettify_number(n: float) -> str:
    if n == int(n):
        return str(int(n))
    return ("%f" % n).rstrip("0").rstrip(".")


def find_last_number_span(s: str) -> tuple[int, int]:
    i = len(s) - 1
    if i < 0:
        return (0, 0)
    end = len(s)
    seen_dot = False
    while i >= 0:
        c = s[i]
        if c.isdigit():
            i -= 1
            continue
        if c == "." and not seen_dot:
            seen_dot = True
            i -= 1
            continue
        break
    if i >= 0 and s[i] in ["-", "−", "+"]:
        if i == 0 or s[i - 1] in "+−×÷*/%(":
            i -= 1
    start = i + 1
    return (start, end)


# ---------------------------
# UI
# ---------------------------

class Calculator(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(orientation="vertical", spacing=8, padding=10, **kwargs)
        try:
            Window.size = (400, 600)
        except Exception:
            pass

        self.display = TextInput(
            text="",
            readonly=True,
            halign="right",
            font_size=42,
            size_hint=(1, 0.25),
            background_color=(0.1, 0.1, 0.1, 1),
            foreground_color=(1, 1, 1, 1),
            cursor_blink=False,
        )
        self.add_widget(self.display)

        grid = GridLayout(cols=4, spacing=6, size_hint=(1, 0.75))
        self.add_widget(grid)

        buttons = [
            ("C", self.clear), ("⌫", self.backspace), ("%", self.percent), ("÷", lambda *_: self.add_char("÷")),
            ("sin", lambda *_: self.add_func("sin")), ("cos", lambda *_: self.add_func("cos")), ("tan", lambda *_: self.add_func("tan")), ("×", lambda *_: self.add_char("×")),
            ("sqrt", lambda *_: self.add_func("sqrt")), ("log", lambda *_: self.add_func("log")), ("(", lambda *_: self.add_char("(")), (")", lambda *_: self.add_char(")")),
            ("7", lambda *_: self.add_char("7")), ("8", lambda *_: self.add_char("8")), ("9", lambda *_: self.add_char("9")), ("−", lambda *_: self.add_char("−")),
            ("4", lambda *_: self.add_char("4")), ("5", lambda *_: self.add_char("5")), ("6", lambda *_: self.add_char("6")), ("+", lambda *_: self.add_char("+")),
            ("1", lambda *_: self.add_char("1")), ("2", lambda *_: self.add_char("2")), ("3", lambda *_: self.add_char("3")), ("=", self.evaluate),
            ("0", lambda *_: self.add_char("0")), (".", lambda *_: self.add_char(".")), ("±", self.toggle_sign),
        ]

        for label, handler in buttons:
            btn = Button(text=label, font_size=20)
            btn.bind(on_press=handler)
            grid.add_widget(btn)

        Window.bind(on_key_down=self._on_key_down)

    def add_char(self, ch: str):
        s = self.display.text
        if not s and ch in ")×÷+%":
            return
        if s:
            last = s[-1]
            if is_operator(last) and is_operator(ch):
                if ch == "(" and last in "+−×÷*/%(":
                    pass
                elif ch == ")" and last not in "+−×÷*/%(":
                    pass
                elif ch in "+×÷%" and last not in ")":
                    return
        if not s and ch == ")":
            return
        if ch == ".":
            start, end = find_last_number_span(s)
            if "." in s[start:end]:
                return
        self.display.text += ch

    def add_func(self, func: str):
        self.display.text += f"{func}("

    def clear(self, *_):
        self.display.text = ""

    def backspace(self, *_):
        s = self.display.text
        if s:
            self.display.text = s[:-1]

    def toggle_sign(self, *_):
        s = self.display.text
        if not s:
            return
        start, end = find_last_number_span(s)
        if start == end:
            return
        segment = s[start:end]
        if segment.startswith("-") or segment.startswith("−"):
            segment = segment[1:]
        else:
            segment = "-" + segment
        self.display.text = s[:start] + segment + s[end:]

    def percent(self, *_):
        s = self.display.text
        if not s:
            return
        start, end = find_last_number_span(s)
        if start == end:
            return
        segment = s[start:end]
        try:
            val = float(segment)
        except ValueError:
            return
        val = val / 100.0
        new_seg = prettify_number(val)
        self.display.text = s[:start] + new_seg + s[end:]

    def evaluate(self, *_):
        s = self.display.text
        if not s:
            return
        if s.count("(") > s.count(")"):
            s = s + ")" * (s.count("(") - s.count(")"))
        expr = map_display_to_eval(s)
        try:
            result = safe_eval(expr)
            self.display.text = prettify_number(result)
        except Exception:
            self.display.text = "Error"

    def _on_key_down(self, window, key, scancode, codepoint, modifiers):
        mapping = {13: self.evaluate, 271: self.evaluate, 8: self.backspace, 27: self.clear}
        if key in mapping:
            mapping[key]()
            return True
        if codepoint and (codepoint.isdigit() or codepoint in "+-*/()."):
            ch = "−" if codepoint == "-" else codepoint
            self.add_char(ch)
            return True
        return False


class CalculatorApp(App):
    def build(self):
        self.title = "Kivy Calculator"
        return Calculator()


if __name__ == "__main__":
    CalculatorApp().run()
