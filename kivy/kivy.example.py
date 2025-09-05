# Kivy Calculator App (single-file)
# --------------------------------------------------
# Cara menjalankan:
# 1) pip install kivy
# 2) python main.py
# --------------------------------------------------

from __future__ import annotations
import ast
from dataclasses import dataclass

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
ALLOWED_NODES = (ast.Expression, ast.BinOp, ast.UnaryOp, ast.Num, ast.Constant, ast.Pow)


def safe_eval(expr: str) -> float:
    """
    Safely evaluate a math expression containing numbers and + - * / % // ** parentheses.
    Does NOT allow variables or function calls.
    """
    # Parse to AST
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
        if isinstance(n, ast.Num):  # Py<3.8 compatibility
            return n.n  # type: ignore[attr-defined]
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
        raise ValueError("Ekspresi mengandung operasi yang tidak diizinkan")

    return _eval(node)


# ---------------------------
# Helpers to edit the display
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
    # Tampilkan tanpa .0 jika bilangan bulat
    if n == int(n):
        return str(int(n))
    # Batasi panjang agar tidak terlalu panjang
    return ("%f" % n).rstrip("0").rstrip(".")


def find_last_number_span(s: str) -> tuple[int, int]:
    """Return (start, end) index (end exclusive) of the last number segment in s.
    Number can include a leading sign and decimal point. If none, return (len(s), len(s)).
    """
    i = len(s) - 1
    if i < 0:
        return (0, 0)

    # Skip trailing spaces (shouldn't exist) or parentheses/operators
    # Find number end
    end = len(s)

    # Walk backwards through digits and decimal point
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

    # Handle optional leading sign directly before the number
    if i >= 0 and s[i] in ["-", "−", "+"]:
        # Only treat as sign if it's at start or preceded by an operator or '('
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

        # Optional: set a convenient starting window size
        try:
            Window.size = (360, 560)
        except Exception:
            pass

        self.display = TextInput(
            text="",
            readonly=True,
            halign="right",
            font_size=48,
            size_hint=(1, 0.25),
            background_color=(0.1, 0.1, 0.1, 1),
            foreground_color=(1, 1, 1, 1),
            cursor_blink=False,
        )
        self.add_widget(self.display)

        grid = GridLayout(cols=4, spacing=8, size_hint=(1, 0.75))
        self.add_widget(grid)

        # Define buttons row by row
        buttons = [
            ("C", self.clear), ("⌫", self.backspace), ("%", self.percent), ("÷", lambda *_: self.add_char("÷")),
            ("7", lambda *_: self.add_char("7")), ("8", lambda *_: self.add_char("8")), ("9", lambda *_: self.add_char("9")), ("×", lambda *_: self.add_char("×")),
            ("4", lambda *_: self.add_char("4")), ("5", lambda *_: self.add_char("5")), ("6", lambda *_: self.add_char("6")), ("−", lambda *_: self.add_char("−")),
            ("1", lambda *_: self.add_char("1")), ("2", lambda *_: self.add_char("2")), ("3", lambda *_: self.add_char("3")), ("+", lambda *_: self.add_char("+")),
            ("(", lambda *_: self.add_char("(")), (")", lambda *_: self.add_char(")")), ("±", self.toggle_sign), ("=", self.evaluate),
            ("0", lambda *_: self.add_char("0")), (".", lambda *_: self.add_char(".")),
        ]

        # Layout tweak: make '=' span full height of last column would require KV; keep simple
        for label, handler in buttons:
            btn = Button(text=label, font_size=24)
            btn.bind(on_press=handler)
            grid.add_widget(btn)

        # Ensure basic keyboard support (optional)
        Window.bind(on_key_down=self._on_key_down)

    # --------------
    # Button actions
    # --------------
    def add_char(self, ch: str):
        # Prevent two operators in a row (except minus for negative)
        s = self.display.text
        if not s and ch in ")×÷+%":
            return
        if s:
            last = s[-1]
            if is_operator(last) and is_operator(ch):
                # Allow '(' after operator and ')' after number
                if ch == "(" and last in "+−×÷*/%(":
                    pass
                elif ch == ")" and last not in "+−×÷*/%(":
                    pass
                elif ch in "+×÷%" and last not in ")":
                    return
        # Basic parenthesis balance: prevent starting with ')'
        if not s and ch == ")":
            return

        # Don't allow multiple dots in the current number
        if ch == ".":
            start, end = find_last_number_span(s)
            if "." in s[start:end]:
                return

        self.display.text += ch

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

        # Try to auto-close parentheses if obviously unbalanced
        if s.count("(") > s.count(")"):
            s = s + ")" * (s.count("(") - s.count(")"))

        expr = map_display_to_eval(s)
        try:
            result = safe_eval(expr)
            self.display.text = prettify_number(result)
        except Exception:
            self.display.text = "Error"

    # Keyboard support (basic)
    def _on_key_down(self, window, key, scancode, codepoint, modifiers):  # noqa: ARG002
        mapping = {
            13: self.evaluate,  # Enter
            271: self.evaluate,  # Numpad Enter
            8: self.backspace,  # Backspace
            27: self.clear,  # Esc
        }
        if key in mapping:
            mapping[key]()
            return True
        # Allow typing digits/operators
        if codepoint and (codepoint.isdigit() or codepoint in "+-*/()."):
            # Map ASCII '-' to pretty minus
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
