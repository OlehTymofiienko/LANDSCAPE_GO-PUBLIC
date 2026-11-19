"""Browse numerical landscapes without modifying the current FG-1 game.

This is a GUI-only feature. It does not load research atlases into gameplay.
"""
from __future__ import annotations

import tkinter as tk
from collections import Counter
from tkinter import ttk, messagebox

from .engine import LETTERS, sources, make_source_pair
from .monochrome import MONO_SIZES, filtered_monochrome
from .science_full import full_page, full_count
from .i18n import LanguageVar, canonical, tr, refresh_tree

MONO_MODE = 'Монохромные · общая матрица'
ORIGINAL_MODE = 'Оригинал · общая матрица'
DUAL_MODE = 'Dual Priority · две матрицы'
OVERLAY_OPTIONS = (
    'Числа высот H_B',
    'Числа высот H_W',
    'Рельеф + числа H_B',
    'Рельеф + числа H_W',
    'Не показывать',
    'Карта чёрных H_B',
    'Карта белых H_W',
)


def overlay_spec(value):
    """Return (height layer, colored background); None means hide all heights."""
    if value == 'Не показывать':
        return None, False
    if value in ('Числа высот H_W', 'Рельеф + числа H_W',
                 'Карта белых H_W'):
        return 1, value != 'Числа высот H_W'
    if value in ('Числа высот H_B', 'Рельеф + числа H_B',
                 'Карта чёрных H_B'):
        return 0, value != 'Числа высот H_B'
    return 0, False


def height_text(value):
    return f'+{value}' if value > 0 else str(value)


def signed_cell_color(value):
    if value < 0:
        return '#F1D7D2'
    if value > 0:
        return '#D5E9D2'
    return '#F1E7CA'


def matrix_stats(values):
    counts = Counter(values)
    return '  ·  '.join(f'{height_text(v)}: {counts[v]}' for v in sorted(counts))


def square_rows(values, n):
    if len(values) != n * n:
        raise ValueError(f'Matrix must contain {n*n} cells')
    return [values[i*n:(i+1)*n] for i in range(n)]


class LandscapeCatalogBrowser:
    """Read-only catalog preview. Only Start changes the main game.

    Sizes 3..19 exist in Original/Dual; Monochrome is limited to 3 and 4.
    The two player maps are only shown separately for truly dual landscapes.
    """
    def __init__(self, app, mono_filter_labels):
        self.app = app
        self.mono_filter_labels = dict(mono_filter_labels)
        self.window = tk.Toplevel(app.root)
        self.window.title('Атлас и каталог ландшафтов LANDSCAPE_GO · просмотр')
        self.window.geometry('1030x760')
        self.window.minsize(820, 580)
        self.mode_var = LanguageVar(value=app.mode_var.get())
        self.size_var = LanguageVar(value=app.n_var.get())
        self.filter_var = LanguageVar(value=app.mono_filter_var.get() if app.is_mono() else 'Все карты')
        self.search_var = LanguageVar(value='')
        self.layer_var = LanguageVar(value='Общий рельеф H')
        self.summary_var = LanguageVar(value='')
        self.details_var = LanguageVar(value='')
        self.rows = []
        self.visible = []
        self.current_id = None
        self.current_pair = None

        outer = ttk.Frame(self.window, padding=10)
        outer.pack(fill='both', expand=True)
        ttk.Label(outer, text='Каталог числовых ландшафтов',
                  font=('Segoe UI', 15, 'bold')).pack(anchor='w')
        ttk.Label(outer, text='Предпросмотр без сброса партии. Для общей матрицы H_B = H_W показывается один рельеф.').pack(anchor='w', pady=(0, 8))
        tools = ttk.Frame(outer)
        tools.pack(fill='x', pady=(0, 8))
        ttk.Label(tools, text='Режим:').pack(side='left')
        self.mode_cb = ttk.Combobox(tools, textvariable=self.mode_var,
                                    values=[ORIGINAL_MODE, DUAL_MODE, MONO_MODE],
                                    state='readonly', width=34)
        self.mode_cb.pack(side='left', padx=(5, 12))
        self.mode_cb.bind('<<ComboboxSelected>>', self._on_mode)
        ttk.Label(tools, text='Размер:').pack(side='left')
        self.size_cb = ttk.Combobox(tools, textvariable=self.size_var, width=5,
                                    state='readonly')
        self.size_cb.pack(side='left', padx=(5, 12))
        self.size_cb.bind('<<ComboboxSelected>>', self._on_size)
        self.filter_cb = ttk.Combobox(tools, textvariable=self.filter_var,
                                      width=24, state='readonly')
        self.filter_cb.pack(side='left', padx=2, fill='x', expand=True)
        self.filter_cb.bind('<<ComboboxSelected>>', self._load_catalog)

        body = ttk.Frame(outer)
        body.pack(fill='both', expand=True)
        left = ttk.Frame(body, width=235)
        left.pack(side='left', fill='y', padx=(0, 12))
        ttk.Label(left, text='Поиск карты по ID:').pack(anchor='w')
        entry = ttk.Entry(left, textvariable=self.search_var)
        entry.pack(fill='x', pady=(3, 7))
        ttk.Label(left, textvariable=self.summary_var, wraplength=235).pack(anchor='w', pady=(0, 6))
        listframe = ttk.Frame(left)
        listframe.pack(fill='both', expand=True)
        self.listbox = tk.Listbox(listframe, exportselection=False, font=('Consolas', 10))
        self.listbox.pack(side='left', fill='both', expand=True)
        scroll = ttk.Scrollbar(listframe, orient='vertical', command=self.listbox.yview)
        scroll.pack(side='right', fill='y')
        self.listbox.configure(yscrollcommand=scroll.set)
        self.listbox.bind('<<ListboxSelect>>', self._select)
        self.search_var.trace_add('write', lambda *_: self._filter_list())

        right = ttk.Frame(body)
        right.pack(side='left', fill='both', expand=True)
        bar = ttk.Frame(right)
        bar.pack(fill='x')
        ttk.Label(bar, text='Просмотр:').pack(side='left')
        self.layer_cb = ttk.Combobox(bar, textvariable=self.layer_var,
                                     values=['Общий рельеф H'], width=24, state='disabled')
        self.layer_cb.pack(side='left', padx=8)
        self.layer_cb.bind('<<ComboboxSelected>>', lambda event: self._draw())
        self.canvas = tk.Canvas(right, bg='#FBF4E9', highlightthickness=1,
                                highlightbackground='#BCA686')
        self.canvas.pack(fill='both', expand=True, pady=(6, 5))
        self.canvas.bind('<Configure>', lambda event: self._draw())
        ttk.Label(right, textvariable=self.details_var, wraplength=700,
                  justify='left').pack(anchor='w')
        ttk.Label(right, text='Легенда: красноватый — отрицательный, зелёный — положительный, бежевый — ноль.',
                  foreground='#555').pack(anchor='w', pady=(4, 0))

        actions = ttk.Frame(outer)
        actions.pack(fill='x', pady=(10, 0))
        ttk.Button(actions, text='Играть на выбранном ландшафте',
                   command=self.start_selected).pack(side='left')
        ttk.Button(actions, text='Закрыть просмотр', command=self.window.destroy).pack(side='right')
        self._on_mode()
        refresh_tree(self.window)

    def refresh_language(self):
        for v in vars(self).values():
            if isinstance(v, LanguageVar):
                v.refresh()
        refresh_tree(self.window)
        self._filter_list()

    def _on_mode(self, event=None):
        sizes = MONO_SIZES if self.mode_var.get() == MONO_MODE else range(3, 20)
        self.size_cb['values'] = tuple(str(n) for n in sizes)
        if int(self.size_var.get()) not in sizes:
            self.size_var.set(str(sizes[0]))
        self.filter_cb['values'] = (tuple(self.mono_filter_labels)
                                    if self.mode_var.get() == MONO_MODE
                                    else ('Все карты',))
        if self.filter_var.get() not in [canonical(v) for v in self.filter_cb['values']]:
            self.filter_var.set('Все карты')
        self._load_catalog()

    def _on_size(self, event=None):
        self._load_catalog()

    def _load_catalog(self, event=None):
        n = int(self.size_var.get())
        try:
            if self.mode_var.get() == MONO_MODE:
                category = self.mono_filter_labels[self.filter_var.get()]
                self.rows = filtered_monochrome(n, category)
            else:
                self.rows = sources(n)
        except (ValueError, KeyError) as exc:
            self.rows = []
            self.summary_var.set(str(exc))
        self._filter_list()
        refresh_tree(self.window)

    def _filter_list(self):
        needle = self.search_var.get().strip().casefold()
        is_full = (self.mode_var.get() == MONO_MODE and
                   self.mono_filter_labels.get(self.filter_var.get()) == 'full')
        if is_full:
            self.visible = full_page(int(self.size_var.get()), limit=120, query=needle)
        else:
            self.visible = [row for row in self.rows if needle in row['id'].casefold()]
        self.listbox.delete(0, 'end')
        for row in self.visible:
            self.listbox.insert('end', row['id'])
        n = int(self.size_var.get())
        total = full_count(n) if is_full else len(self.rows)
        self.summary_var.set(f'{n}×{n} · {len(self.visible)} показано / {total} карт'
                             + (' · поиск по полному индексу' if is_full else ''))
        preferred = (self.app.source_var.get()
                     if self.app.mode_var.get() == self.mode_var.get()
                     and self.app.n_var.get() == self.size_var.get()
                     else None)
        idx = next((i for i, row in enumerate(self.visible)
                    if row['id'] == preferred), 0)
        self.listbox.selection_clear(0, 'end')
        if self.visible:
            self.listbox.selection_set(idx)
            self.listbox.see(idx)
            self._select()
        else:
            self.current_pair = None
            self.current_id = None
            self.details_var.set('Нет ландшафтов в выбранном фильтре.')
            self.canvas.delete('all')

    def _select(self, event=None):
        selection = self.listbox.curselection()
        if not selection:
            return
        row = self.visible[selection[0]]
        n = int(self.size_var.get())
        self.current_id = row['id']
        if self.mode_var.get() == DUAL_MODE:
            game = make_source_pair(n, self.current_id)
            self.current_pair = (game['black'], game['white'])
            self.layer_cb['values'] = ('Чёрные H_B', 'Белые H_W')
            self.layer_cb.configure(state='readonly')
            if self.layer_var.get() not in [canonical(v) for v in self.layer_cb['values']]:
                self.layer_var.set('Чёрные H_B')
        else:
            flat = [value for line in row['matrix'] for value in line]
            self.current_pair = (flat, flat)
            self.layer_cb['values'] = ('Общий рельеф H',)
            self.layer_cb.configure(state='disabled')
            self.layer_var.set('Общий рельеф H')
        height_layer = (self.current_pair[1]
                        if self.layer_var.get() == 'Белые H_W'
                        else self.current_pair[0])
        if self.mode_var.get() == MONO_MODE:
            v_status = str(row['V']) if row.get('V') is not None else 'неизвестен'
            u_status = str(row['U']) if row.get('U') is not None else 'неизвестен'
            label = f'FG-1: глобальное V={v_status}; полное U={u_status}.'
            bound = row.get('global_bounds') or {}
            if isinstance(bound.get('lower'), int) and isinstance(bound.get('upper'), int):
                label += f' Границы из источника: [{bound["lower"]},{bound["upper"]}].'
            if row.get('source_groups'):
                label += ' Семейства: '+', '.join(row['source_groups'])+'.'
        elif self.mode_var.get() == DUAL_MODE:
            label = 'Dual Priority: разные H_B и H_W; Near-Zero не доказательство minimax.'
        else:
            label = 'Original: одна общая матрица; статус исследовательского V/U отдельный.'
        self.details_var.set(f'{self.current_id} · {label}\n'
                             f'Распределение высот: {matrix_stats(height_layer)}')
        self._draw()
        refresh_tree(self.window)

    def _draw(self):
        canvas = self.canvas
        canvas.delete('all')
        if self.current_pair is None:
            return
        n = int(self.size_var.get())
        values = (self.current_pair[1]
                  if self.layer_var.get() == 'Белые H_W'
                  else self.current_pair[0])
        if len(values) != n*n:
            raise ValueError('Catalog preview matrix dimension mismatch')
        w = max(200, canvas.winfo_width())
        h = max(200, canvas.winfo_height())
        cell = min((w-58)/n, (h-58)/n)
        x0 = (w-cell*n)/2
        y0 = (h-cell*n)/2
        font_size = max(8, min(16, int(cell*.42)))
        for y in range(n):
            canvas.create_text(x0-15, y0+(y+.5)*cell, text=str(y+1),
                               fill='#62492D', font=('Segoe UI', max(8, font_size-2)))
        for x in range(n):
            canvas.create_text(x0+(x+.5)*cell, y0-13, text=LETTERS[x],
                               fill='#62492D', font=('Segoe UI', max(8, font_size-2)))
        for p, value in enumerate(values):
            x = p % n
            y = p // n
            x1=x0+x*cell
            y1=y0+y*cell
            canvas.create_rectangle(x1, y1, x1+cell, y1+cell,
                                    fill=signed_cell_color(value),
                                    outline='#8E7857', width=1)
            canvas.create_text(x1+cell/2, y1+cell/2, text=height_text(value),
                               fill='#312A23', font=('Segoe UI', font_size, 'bold'),
                               tags=('preview-value',))

    def start_selected(self):
        if not self.current_id:
            return
        if self.app.record and not messagebox.askyesno(
                tr('Начать новую партию?'),
                tr('Текущая партия будет заменена. Продолжить?'),
                parent=self.window):
            return
        self.app.mode_var.set(self.mode_var.get())
        self.app.n_var.set(self.size_var.get())
        self.app.change_mode()
        if self.mode_var.get() == MONO_MODE:
            self.app.mono_filter_var.set(self.filter_var.get())
            self.app.change_mono_filter()
        self.app.source_var.set(self.current_id)
        self.app.load_source()
        self.window.destroy()
