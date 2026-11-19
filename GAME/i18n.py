"""Presentation-only localization for LANDSCAPE_GO FG-1 GUI.

Canonical internal values (modes, filter identifiers, save formats, matrix IDs,
scoring, and rules) are never translated. No third-party dependencies.
"""
from __future__ import annotations

import json
from pathlib import Path
import tkinter as tk
from tkinter import ttk

LANGUAGES = ("en", "uk", "ru")
LANGUAGE_NAMES = {"English": "en", "Українська": "uk", "Русский": "ru"}
CHOICE_NAMES = {v: k for k, v in LANGUAGE_NAMES.items()}
SETTINGS_PATH = Path.home() / ".landscape_go_language.json"

# Each tuple is the original UI wording, international English, Ukrainian.
# Keep source identifiers, H_B/H_W, V/U, FG-1, scores and JSON keys immutable.
ROWS = (
    ("Оригинал · общая матрица", "Original · shared landscape", "Оригінал · спільний ландшафт"),
    ("Dual Priority · две матрицы", "Dual Priority · two landscapes", "Dual Priority · два ландшафти"),
    ("Монохромные · общая матрица", "Monochrome · shared landscape", "Монохромні · спільний ландшафт"),
    ("Все карты", "All landscapes", "Усі ландшафти"),
    ("Первичный баланс V=0", "Primary balance V=0", "Первинний баланс V=0"),
    ("Полная ничья U=0", "Full draw U=0", "Повна нічия U=0"),
    ("Пространственный фильтр", "Spatial filter", "Просторовий фільтр"),
    ("Dynamic: точный V", "Dynamic: exact V", "Dynamic: точне V"),
    ("Dynamic: граница V", "Dynamic: bounded V", "Dynamic: межі V"),
    ("Dynamic: V не решён", "Dynamic: V unresolved", "Dynamic: V не розв'язано"),
    ("Основной научный атлас", "Main scientific atlas", "Основний науковий атлас"),
    ("Знаковые ландшафты", "Signed landscapes", "Знакові ландшафти"),
    ("Полный научный архив (индекс)", "Full scientific archive (index)", "Повний науковий архів (індекс)"),
    ("Человек", "Human", "Людина"),
    ("Компьютер", "Computer", "Комп'ютер"),
    ("Рядом", "Side by side", "Поруч"),
    ("Друг над другом", "Stacked", "Одна над одною"),
    ("Числа высот H_B", "Height values H_B", "Значення висот H_B"),
    ("Числа высот H_W", "Height values H_W", "Значення висот H_W"),
    ("Рельеф + числа H_B", "Terrain + values H_B", "Рельєф + значення H_B"),
    ("Рельеф + числа H_W", "Terrain + values H_W", "Рельєф + значення H_W"),
    ("Не показывать", "Hide values", "Не показувати"),
    ("Карта чёрных H_B", "Black landscape H_B", "Ландшафт чорних H_B"),
    ("Карта белых H_W", "White landscape H_W", "Ландшафт білих H_W"),
    ("Числа двух полей", "Values on both boards", "Значення на обох дошках"),
    ("Рельеф + числа двух полей", "Terrain + values on both boards", "Рельєф + значення на обох дошках"),
    ("Общий рельеф H", "Shared terrain H", "Спільний рельєф H"),
    ("Чёрные H_B", "Black H_B", "Чорні H_B"),
    ("Белые H_W", "White H_W", "Білі H_W"),
    ("Язык", "Language", "Мова"),
    ("Режим игры", "Game mode", "Режим гри"),
    ("Размер поля", "Board size", "Розмір дошки"),
    ("Урок (1–5)", "Lesson (1–5)", "Урок (1–5)"),
    ("Экспериментальный урок (1–20)", "Experimental lesson (1–20)", "Експериментальний урок (1–20)"),
    ("Оригинальный урок (1–5)", "Original lesson (1–5)", "Початковий урок (1–5)"),
    ("Начать выбранный урок", "Start selected lesson", "Почати вибраний урок"),
    ("Или любая исходная матрица", "Or select a landscape", "Або виберіть ландшафт"),
    ("Начать выбранную матрицу", "Start selected landscape", "Почати вибраний ландшафт"),
    ("Игроки", "Players", "Гравці"),
    ("● Чёрные", "● Black", "● Чорні"),
    ("○ Белые", "○ White", "○ Білі"),
    ("● ЧЁРНЫЕ", "● BLACK", "● ЧОРНІ"),
    ("○ БЕЛЫЕ", "○ WHITE", "○ БІЛІ"),
    ("ЧЁРНЫЕ", "BLACK", "ЧОРНІ"),
    ("БЕЛЫЕ", "WHITE", "БІЛІ"),
    ("НИЧЬЯ", "DRAW", "НІЧИЯ"),
    ("Стиль компьютера", "Computer strategy", "Стратегія комп'ютера"),
    ("Подсветка высот", "Height overlay", "Відображення висот"),
    ("Две доски: расположение и размер", "Two boards: layout and size", "Дві дошки: розташування й розмір"),
    ("↶ Отмена", "↶ Undo", "↶ Скасувати"),
    ("Атлас / матрицы", "Atlas / landscapes", "Атлас / ландшафти"),
    ("Сохранить", "Save", "Зберегти"),
    ("Открыть", "Open", "Відкрити"),
    ("Правила проекта FG-1", "FG-1 project rules", "Правила проєкту FG-1"),
    ("Оригинальный рельеф / две матрицы · вечная заморозка захваченных клеток",
     "Original terrain / two landscapes · captured points freeze permanently",
     "Початковий рельєф / два ландшафти · захоплені точки назавжди заморожуються"),
    ("Счёт FG-1 · без территории и коми", "FG-1 score · no territory or komi",
     "Рахунок FG-1 · без території та комі"),
    ("● ЧЁРНЫЕ · H_B", "● BLACK · H_B", "● ЧОРНІ · H_B"),
    ("○ БЕЛЫЕ · H_W", "○ WHITE · H_W", "○ БІЛІ · H_W"),
    ("Выберите размер, урок или матрицу.", "Select a board size, lesson or landscape.",
     "Виберіть розмір дошки, урок або ландшафт."),
    ("Чёрные ходят первыми. Оригинал: общий рельеф;",
     "Black plays first. Original: shared terrain;",
     "Чорні ходять першими. Оригінал: спільний рельєф;"),
    ("Dual Priority: разные матрицы цветов.", "Dual Priority: separate landscapes for each color.",
     "Dual Priority: окремі ландшафти для кожного кольору."),
    ("Группы связаны по четырём сторонам.", "Groups connect orthogonally.",
     "Групи з'єднані за чотирма напрямками."),
    ("Суицид запрещён до снятия пленных.", "Suicide is forbidden before capture resolution.",
     "Самогубний хід заборонений до зняття полонених."),
    ("Захваченные клетки навсегда заморожены.", "Captured points are frozen permanently.",
     "Захоплені точки заморожуються назавжди."),
    ("Пас допускается только вынужденно.", "Passing is allowed only when forced.",
     "Пас дозволено лише за відсутності легальних ходів."),
    ("Нет территорий и коми.", "No territory scoring or komi.",
     "Немає підрахунку територій або комі."),
    ("Near-Zero в Dual — только экспериментальные",
     "Near-Zero in Dual indicates only experimental",
     "Near-Zero у Dual означає лише експериментальні"),
    ("результаты ботов, не точный minimax.",
     "bot outcomes, not exact minimax.",
     "результати ботів, а не точний мінімакс."),
    ("Фильтр Mono", "Monochrome filter", "Фільтр Mono"),
    (" карт", " landscapes", " ландшафтів"),
    ("Полный архив не установлен.", "Full archive is not installed.", "Повний архів не встановлено."),
    ("научный статус отдельный", "scientific status is separate", "науковий статус окремий"),
    ("исходных матриц", "source landscapes", "вихідних ландшафтів"),
    ("оригинальных матриц", "original landscapes", "оригінальних ландшафтів"),
    ("экспериментальных пар", "experimental pairs", "експериментальних пар"),
    ("уроков исходного маршрута", "lessons from original route", "уроків початкового маршруту"),
    ("minimax не доказан", "minimax not established", "мінімакс не доведений"),
    ("Ошибка выбора урока", "Lesson selection error", "Помилка вибору уроку"),
    ("Ошибка выбора матрицы", "Landscape selection error", "Помилка вибору ландшафту"),
    ("Нет карты в выбранном фильтре. Выберите другой фильтр.",
     "Landscape not found in the selected filter. Choose another filter.",
     "Ландшафт не знайдено у вибраному фільтрі. Оберіть інший фільтр."),
    ("Ошибка загрузки", "Loading error", "Помилка завантаження"),
    ("Сохранить партию", "Save game", "Зберегти партію"),
    ("Открыть сохранение", "Open saved game", "Відкрити збережену партію"),
    ("Партия завершена.", "Game finished.", "Партію завершено."),
    ("результат по U:", "outcome by U:", "результат за U:"),
    ("Ход ", "Move ", "Хід "),
    ("текущее V=", "current V=", "поточне V="),
    ("заморожено=", "frozen=", "заморожено="),
    ("не исход любой партии", "not the outcome of every game", "не результат будь-якої партії"),
    ("Чёрные:", "Black:", "Чорні:"),
    ("Белые:", "White:", "Білі:"),
    ("Разница V:", "Difference V:", "Різниця V:"),
    ("Камни: чёрные", "Stones: black", "Камені: чорні"),
    ("белые", "white", "білі"),
    ("чёрные", "black", "чорні"),
    ("бонус захватов: чёрные", "capture bonus: black", "бонус захоплень: чорні"),
    ("белые впереди на", "white leads by", "білі попереду на"),
    ("чёрные впереди на", "black leads by", "чорні попереду на"),
    (" очк.", " points", " очок"),
    ("равенство по первичному счёту V=0",
     "primary score tied at V=0", "рівність за первинним рахунком V=0"),
    ("ПРЕДВАРИТЕЛЬНО", "PROVISIONAL", "ПОПЕРЕДНЬО"),
    ("итоговый победитель определяется по U.", "the final winner is determined by U.",
     "остаточного переможця визначає U."),
    ("ИТОГ", "FINAL", "ПІДСУМОК"),
    ("НИЧЬЯ по полному U=0.", "DRAW by full U=0.", "НІЧИЯ за повним U=0."),
    ("победили", "won", "перемогли"),
    ("с разницей", "by a margin of", "з різницею"),
    ("по дополнительным критериям", "by secondary criteria", "за додатковими критеріями"),
    ("по V", "by V", "за V"),
    ("U при V=0", "U when V=0", "U за V=0"),
    ("Атлас и каталог ландшафтов LANDSCAPE_GO · просмотр",
     "LANDSCAPE_GO landscape atlas · preview",
     "Атлас ландшафтів LANDSCAPE_GO · перегляд"),
    ("Каталог числовых ландшафтов", "Numerical landscape catalog",
     "Каталог числових ландшафтів"),
    ("Предпросмотр без сброса партии. Для общей матрицы H_B = H_W показывается один рельеф.",
     "Preview without resetting the game. Shared H_B = H_W displays one landscape.",
     "Перегляд без скидання партії. Спільний H_B = H_W показує один ландшафт."),
    ("Режим:", "Mode:", "Режим:"),
    ("Размер:", "Size:", "Розмір:"),
    ("Поиск карты по ID:", "Find landscape by ID:", "Пошук ландшафту за ID:"),
    ("Просмотр:", "View:", "Перегляд:"),
    ("Легенда: красноватый — отрицательный, зелёный — положительный, бежевый — ноль.",
     "Legend: red = negative, green = positive, beige = zero.",
     "Легенда: червоний — від'ємне, зелений — додатне, бежевий — нуль."),
    ("Играть на выбранном ландшафте", "Play on selected landscape",
     "Грати на вибраному ландшафті"),
    ("Закрыть просмотр", "Close preview", "Закрити перегляд"),
    ("показано /", "shown /", "показано /"),
    ("поиск по полному индексу", "searching full index", "пошук за повним індексом"),
    ("Нет ландшафтов в выбранном фильтре.", "No landscapes match this filter.",
     "Немає ландшафтів за вибраним фільтром."),
    ("неизвестен", "unknown", "невідоме"),
    ("Границы из источника:", "Source bounds:", "Межі з джерела:"),
    ("Семейства:", "Families:", "Родини:"),
    ("Распределение высот:", "Height distribution:", "Розподіл висот:"),
    ("FG-1: глобальное V=", "FG-1: global V=", "FG-1: глобальне V="),
    ("полное U=", "full U=", "повне U="),
    ("Dual Priority: разные H_B и H_W; Near-Zero не доказательство minimax.",
     "Dual Priority: different H_B and H_W; Near-Zero does not prove minimax.",
     "Dual Priority: різні H_B та H_W; Near-Zero не доводить мінімакс."),
    ("Original: одна общая матрица; статус исследовательского V/U отдельный.",
     "Original: one shared landscape; research V/U status is separate.",
     "Original: один спільний ландшафт; статус дослідницьких V/U окремий."),
    ("Начать новую партию?", "Start a new game?", "Почати нову партію?"),
    ("Текущая партия будет заменена. Продолжить?",
     "The current game will be replaced. Continue?",
     "Поточну партію буде замінено. Продовжити?"),
    ("Наведите курсор: H_B / H_W / занятость узла",
     "Hover: H_B / H_W / point occupancy",
     "Наведіть курсор: H_B / H_W / зайнятість точки"),
    ("заморожен", "frozen", "заморожено"),
    ("занят чёрными", "occupied by black", "зайнято чорними"),
    ("занят белыми", "occupied by white", "зайнято білими"),
    ("свободен", "empty", "вільно"),
)
INDEX = {r[0]: {"en": r[1], "uk": r[2], "ru": r[0]} for r in ROWS}
INVERSE = {rendered: source for source, trans in INDEX.items()
           for rendered in trans.values()}
REPLACEMENTS = sorted(INDEX, key=len, reverse=True)


def read_language() -> str:
    try:
        lang = json.loads(SETTINGS_PATH.read_text(encoding="utf-8"))["language"]
        if lang in LANGUAGES:
            return lang
    except (OSError, ValueError, KeyError, TypeError):
        pass
    return "en"


_active = read_language()


def get_language() -> str:
    return _active


def set_language(code: str, persist: bool = True):
    global _active
    if code not in LANGUAGES:
        raise ValueError("Unsupported language code")
    _active = code
    if persist:
        try:
            SETTINGS_PATH.write_text(json.dumps({"language": code}), encoding="utf-8")
        except OSError:
            pass


def canonical(value: str) -> str:
    return INVERSE.get(value, value)


def tr(value: str, language: str | None = None) -> str:
    """Translate a canonical UI string; unknown scientific data is untouched."""
    if not isinstance(value, str):
        return value
    lang = get_language() if language is None else language
    if lang == "ru":
        return value
    if value in INDEX:
        return INDEX[value][lang]
    # Dynamic labels and legacy fragments are composed in Russian in the
    # engine-independent GUI, then translated for presentation only.
    result = value
    for old in REPLACEMENTS:
        if old in result:
            result = result.replace(old, INDEX[old][lang])
    return result


class LanguageVar(tk.StringVar):
    """Display the selected language but return a stable canonical internal value."""
    def __init__(self, master=None, value="", **kwargs):
        super().__init__(master=master, **kwargs)
        self._canonical = ""
        self._rendered = ""
        self.set(value)

    def set(self, value):
        self._canonical = canonical(str(value))
        self._rendered = tr(self._canonical)
        super().set(self._rendered)

    def get(self):
        shown = super().get()
        if shown != self._rendered:
            self._canonical = canonical(shown)
            self._rendered = shown
        return self._canonical

    def rendered(self):
        return super().get()

    def refresh(self):
        self.set(self.get())


def refresh_tree(root):
    """Relocalize an existing ttk widget tree without reconstructing Game/State."""
    def visit(w):
        try:
            keys = w.keys()
            if "text" in keys and not ("textvariable" in keys and w.cget("textvariable")):
                current = w.cget("text")
                if current != getattr(w, "_i18n_rendered_text", None):
                    w._i18n_canonical_text = canonical(current)
                original = getattr(w, "_i18n_canonical_text", current)
                rendered = tr(original)
                if rendered != current:
                    w.configure(text=rendered)
                w._i18n_rendered_text = rendered
            if isinstance(w, ttk.Combobox):
                current = tuple(w.cget("values"))
                if current != getattr(w, "_i18n_rendered_values", None):
                    w._i18n_canonical_values = tuple(canonical(x) for x in current)
                source = getattr(w, "_i18n_canonical_values", current)
                rendered = tuple(tr(x) for x in source)
                if rendered != current:
                    w.configure(values=rendered)
                w._i18n_rendered_values = rendered
        except tk.TclError:
            pass
        for child in w.winfo_children():
            visit(child)
    visit(root)
