"""Offline tkinter UI for all board sizes; standard library only."""
from __future__ import annotations
import json,random,tkinter as tk
from tkinter import ttk,messagebox,filedialog
from dataclasses import asdict
from pathlib import Path
from .engine import Game,State,sources,lessons,make_source_pair,make_shared,original_lessons,make_original_lesson,LETTERS,print_maps

from .monochrome import MONO_SIZES, filtered_monochrome, make_monochrome, dynamic_description
from .science_full import full_count, full_by_id
from .scoreboard import format_scoreboard
from .i18n import (LanguageVar, LANGUAGE_NAMES, CHOICE_NAMES, get_language,
                   set_language, tr, refresh_tree)
from .dual_split import (DUAL_OVERLAYS,DUAL_ORIENTATIONS,DUAL_WIDTHS,
                         point_at,focus_text)
from .landscape_viewer import (LandscapeCatalogBrowser, OVERLAY_OPTIONS,
                               overlay_spec, signed_cell_color, height_text)

MONO_MODE = 'Монохромные · общая матрица'
MONO_FILTER_LABELS = {
    'Все карты': 'all', 'Первичный баланс V=0': 'v-zero',
    'Полная ничья U=0': 'u-zero', 'Пространственный фильтр': 'strict',
    'Dynamic: точный V': 'dynamic-exact', 'Dynamic: граница V': 'dynamic-bound',
    'Dynamic: V не решён': 'dynamic-unresolved',
    'Основной научный атлас': 'atlas',
    'Знаковые ландшафты': 'signed',
    'Полный научный архив (индекс)': 'full',
}

class LandscapeWindow:
    def __init__(self,root):
        self.root=root;root.title('LANDSCAPE_GO · v4 dev · Original / Dual Priority / Monochrome · 3×3–19×19')
        root.geometry('1100x850');root.minsize(790,650)
        self.n_var=LanguageVar(value='3')
        self.mode_var=LanguageVar(value='Оригинал · общая матрица')
        self.lesson_var=LanguageVar(value='1')
        self.mono_filter_var=LanguageVar(value='Все карты')
        self.source_var=LanguageVar(value='REF-3B')
        self.black_mode=LanguageVar(value='Человек')
        self.white_mode=LanguageVar(value='Компьютер')
        self.overlay=LanguageVar(value='Числа высот H_B')
        self.bot_profile=LanguageVar(value='tactical')
        self.status_var=LanguageVar(value='Выберите размер, урок или матрицу.')
        self.detail_var=LanguageVar(value='')
        self.score_var=LanguageVar(value='')
        self.score_outcome_var=LanguageVar(value='')
        self.score_breakdown_var=LanguageVar(value='')
        self.dual_orientation=LanguageVar(value='Рядом')
        self.dual_width=LanguageVar(value='560')
        self.dual_focus_var=LanguageVar(value='')
        self._dual_geometries={}
        self._dual_focus=None
        self.game=None;self.s=State();self.history=[State()];self.record=[];self.metadata={};self.rng=random.Random(31)
        self.ai_scheduled=False;self.over=False;self._ai_ticket=0
        frame=ttk.Frame(root,padding=8);frame.pack(fill='both',expand=True)
        top=ttk.Frame(frame);top.pack(fill='x')
        ttk.Label(top,text='LANDSCAPE_GO',font=('Segoe UI',18,'bold')).pack(side='left',padx=(2,20))
        ttk.Label(top,text='Оригинальный рельеф / две матрицы · вечная заморозка захваченных клеток',font=('Segoe UI',10)).pack(side='left')
        self.language_choice=tk.StringVar(value=CHOICE_NAMES[get_language()])
        self.language_cb=ttk.Combobox(top,textvariable=self.language_choice,
                     values=list(LANGUAGE_NAMES),state='readonly',width=12)
        self.language_cb.pack(side='right',padx=(8,2))
        self.language_cb.bind('<<ComboboxSelected>>',self.change_language)
        ttk.Label(top,text='Язык').pack(side='right',padx=(10,0))
        # The score is anchored ABOVE the board so it remains visible on 19x19.
        scorebox=ttk.LabelFrame(frame,text='Счёт FG-1 · без территории и коми',padding=(8,3))
        scorebox.pack(fill='x',pady=(6,0))
        ttk.Label(scorebox,textvariable=self.score_var,
                  font=('Segoe UI',12,'bold')).pack(anchor='w')
        ttk.Label(scorebox,textvariable=self.score_outcome_var,
                  font=('Segoe UI',10,'bold'),wraplength=1000).pack(anchor='w')
        ttk.Label(scorebox,textvariable=self.score_breakdown_var,
                  foreground='#555',wraplength=1000).pack(anchor='w')
        main=ttk.Frame(frame);main.pack(fill='both',expand=True,pady=8)
        panel=ttk.Frame(main,width=296);panel.pack(side='left',fill='y',padx=(0,14));panel.pack_propagate(False)
        ttk.Label(panel,text='Режим игры',font=('Segoe UI',10,'bold')).pack(anchor='w')
        self.mode_cb=ttk.Combobox(panel,textvariable=self.mode_var,values=['Оригинал · общая матрица','Dual Priority · две матрицы',MONO_MODE],state='readonly')
        self.mode_cb.pack(fill='x',pady=(2,8))
        self.mode_cb.bind('<<ComboboxSelected>>',self.change_mode)
        ttk.Label(panel,text='Размер поля',font=('Segoe UI',10,'bold')).pack(anchor='w')
        sizes=[f'{i}' for i in range(3,20)]
        self.size_cb=ttk.Combobox(panel,textvariable=self.n_var,values=sizes,state='readonly',width=12)
        self.size_cb.pack(anchor='w',pady=(2,10));self.size_cb.bind('<<ComboboxSelected>>',self.change_mode)
        self.lesson_label=ttk.Label(panel,text='Урок (1–5)',font=('Segoe UI',10,'bold'));self.lesson_label.pack(anchor='w')
        self.lesson_cb=ttk.Combobox(panel,textvariable=self.lesson_var,values=[str(i) for i in range(1,6)],state='readonly',width=12)
        self.lesson_cb.pack(fill='x',pady=(2,5))
        self.lesson_cb.bind('<<ComboboxSelected>>',self.change_mono_filter)
        self.lesson_button=ttk.Button(panel,text='Начать выбранный урок',command=self.load_lesson)
        self.lesson_button.pack(fill='x',pady=(0,14))
        ttk.Label(panel,text='Или любая исходная матрица',font=('Segoe UI',10,'bold')).pack(anchor='w')
        self.source_cb=ttk.Combobox(panel,textvariable=self.source_var,width=26)
        self.source_cb.pack(fill='x',pady=(2,5))
        ttk.Button(panel,text='Начать выбранную матрицу',command=self.load_source).pack(fill='x',pady=(0,14))
        ttk.Label(panel,text='Игроки',font=('Segoe UI',10,'bold')).pack(anchor='w')
        for caption,variable in [('● Чёрные',self.black_mode),('○ Белые',self.white_mode)]:
            r=ttk.Frame(panel);r.pack(fill='x',pady=3)
            ttk.Label(r,text=caption,width=12).pack(side='left')
            ttk.Combobox(r,textvariable=variable,values=['Человек','Компьютер'],state='readonly',width=14).pack(side='left')
        ttk.Label(panel,text='Стиль компьютера',font=('Segoe UI',10,'bold')).pack(anchor='w',pady=(12,2))
        ttk.Combobox(panel,textvariable=self.bot_profile,values=['tactical','denial','selfish','balanced','random'],state='readonly',width=18).pack(anchor='w')
        ttk.Label(panel,text='Подсветка высот',font=('Segoe UI',10,'bold')).pack(anchor='w',pady=(12,2))
        x=ttk.Combobox(panel,textvariable=self.overlay,values=OVERLAY_OPTIONS,state='readonly')
        self.overlay_cb=x
        x.pack(fill='x');x.bind('<<ComboboxSelected>>',lambda e:self.redraw())
        self.dual_controls=ttk.Frame(panel)
        ttk.Label(self.dual_controls,text='Две доски: расположение и размер',
                  font=('Segoe UI',9,'bold')).pack(anchor='w')
        row=ttk.Frame(self.dual_controls);row.pack(fill='x')
        orientation=ttk.Combobox(row,textvariable=self.dual_orientation,
                          values=DUAL_ORIENTATIONS,state='readonly',width=16)
        orientation.pack(side='left',padx=(0,5))
        orientation.bind('<<ComboboxSelected>>',lambda e:self.configure_dual())
        width_cb=ttk.Combobox(row,textvariable=self.dual_width,
                             values=DUAL_WIDTHS,state='readonly',width=7)
        width_cb.pack(side='left')
        width_cb.bind('<<ComboboxSelected>>',lambda e:self.configure_dual())
        ttk.Label(self.dual_controls,textvariable=self.dual_focus_var,
                  wraplength=278,foreground='#1D5575',
                  font=('Segoe UI',9,'bold')).pack(anchor='w',pady=(3,2))
        r=ttk.Frame(panel);r.pack(fill='x',pady=(16,2))
        ttk.Button(r,text='↶ Отмена',command=self.undo).pack(side='left',expand=True,fill='x',padx=(0,4))
        ttk.Button(r,text='Атлас / матрицы',command=self.open_maps).pack(side='left',expand=True,fill='x')
        r=ttk.Frame(panel);r.pack(fill='x',pady=5)
        ttk.Button(r,text='Сохранить',command=self.save).pack(side='left',expand=True,fill='x',padx=(0,4))
        ttk.Button(r,text='Открыть',command=self.load_saved).pack(side='left',expand=True,fill='x')
        ttk.Separator(panel,orient='horizontal').pack(fill='x',pady=14)
        ttk.Label(panel,text='Правила проекта FG-1',font=('Segoe UI',10,'bold')).pack(anchor='w')
        rules=('Чёрные ходят первыми. Оригинал: общий рельеф;\n'
          'Dual Priority: разные матрицы цветов.\n'
          'Группы связаны по четырём сторонам.\n'
          'Суицид запрещён до снятия пленных.\n'
          'Захваченные клетки навсегда заморожены.\n'
          'Пас допускается только вынужденно.\n'
          'Нет территорий и коми.\n'
          'Near-Zero в Dual — только экспериментальные\nрезультаты ботов, не точный minimax.')
        ttk.Label(panel,text=rules,wraplength=270,justify='left',foreground='#555').pack(anchor='w',pady=(3,0))
        self.boardframe=ttk.Frame(main)
        self.boardframe.pack(side='left',fill='both',expand=True)
        self.canvas=tk.Canvas(self.boardframe,bg='#E4BF84',
                              highlightthickness=1,highlightbackground='#996E3C')
        self.canvas.pack(fill='both',expand=True)
        self.canvas.bind('<Button-1>',self.click)
        self.canvas.bind('<Configure>',lambda e:self.redraw())

        # Two canvases are only two projections of one Game and one State.
        # The scrollable region avoids compressing two 19x19 boards.
        self.dual_container=ttk.Frame(self.boardframe)
        self.dual_container.rowconfigure(0,weight=1)
        self.dual_container.columnconfigure(0,weight=1)
        self.dual_view=tk.Canvas(self.dual_container,bg='#EFECE5',
                                 highlightthickness=0)
        self.dual_view.grid(row=0,column=0,sticky='nsew')
        xscroll=ttk.Scrollbar(self.dual_container,orient='horizontal',
                              command=self.dual_view.xview)
        yscroll=ttk.Scrollbar(self.dual_container,orient='vertical',
                              command=self.dual_view.yview)
        xscroll.grid(row=1,column=0,sticky='ew')
        yscroll.grid(row=0,column=1,sticky='ns')
        self.dual_view.configure(xscrollcommand=xscroll.set,
                                 yscrollcommand=yscroll.set)
        self.dual_inner=ttk.Frame(self.dual_view)
        self.dual_view.create_window((0,0),window=self.dual_inner,anchor='nw')
        self.dual_inner.bind('<Configure>',lambda e:
            self.dual_view.configure(scrollregion=self.dual_view.bbox('all')))
        self.black_tile=ttk.Frame(self.dual_inner)
        self.white_tile=ttk.Frame(self.dual_inner)
        ttk.Label(self.black_tile,text='● ЧЁРНЫЕ · H_B',
                  font=('Segoe UI',11,'bold')).pack(pady=(2,4))
        ttk.Label(self.white_tile,text='○ БЕЛЫЕ · H_W',
                  font=('Segoe UI',11,'bold')).pack(pady=(2,4))
        self.canvas_black=tk.Canvas(self.black_tile,bg='#E4BF84',width=560,
                              height=560,highlightthickness=1,
                              highlightbackground='#996E3C')
        self.canvas_white=tk.Canvas(self.white_tile,bg='#E4BF84',width=560,
                              height=560,highlightthickness=1,
                              highlightbackground='#996E3C')
        for c in (self.canvas_black,self.canvas_white):
            c.pack(padx=5,pady=(0,7))
            c.bind('<Button-1>',lambda e,which=c:self.click(e,which))
            c.bind('<Motion>',lambda e,which=c:self.dual_hover(e,which))
            c.bind('<Leave>',lambda e:self.dual_hover(None,None))
            c.bind('<Configure>',lambda e:self.redraw())
        self.status_label=ttk.Label(frame,textvariable=self.status_var,font=('Segoe UI',10,'bold'));self.status_label.pack(anchor='w')
        self.detail_label=ttk.Label(frame,textvariable=self.detail_var,foreground='#555',wraplength=750);self.detail_label.pack(anchor='w',pady=(2,0))
        self.change_size()
        self.load_lesson()
        refresh_tree(self.root)

    def change_language(self,event=None):
        """Switch live GUI presentation; do not change the game or save format."""
        set_language(LANGUAGE_NAMES[self.language_choice.get()])
        for value in vars(self).values():
            if isinstance(value,LanguageVar):
                value.refresh()
        self.update_status()
        refresh_tree(self.root)
        browser=getattr(self,'_catalog_browser',None)
        if browser is not None and browser.window.winfo_exists():
            browser.refresh_language()
        self.redraw()

    def is_dual(self):
        return self.mode_var.get().startswith('Dual Priority')

    def is_mono(self):
        return self.mode_var.get() == MONO_MODE

    def change_mode(self,event=None):
        self.change_size()
        if self.is_mono(): self.load_source()
        else: self.load_lesson()

    def change_size(self,event=None):
        if self.is_mono():
            self.size_cb['values']=[str(i) for i in MONO_SIZES]
            if int(self.n_var.get()) not in MONO_SIZES: self.n_var.set('3')
            self.mono_filter_var.set('Все карты')
            self.lesson_cb.configure(textvariable=self.mono_filter_var, state='readonly', values=list(MONO_FILTER_LABELS))
            self.lesson_button.configure(state='disabled')
            self.change_mono_filter()
            return
        self.size_cb['values']=[str(i) for i in range(3,20)]
        self.lesson_cb.configure(textvariable=self.lesson_var, state='readonly'); self.lesson_button.configure(state='normal')
        n=int(self.n_var.get());all_sources=sources(n)
        self.source_cb['values']=[a['id'] for a in all_sources]
        self.lesson_var.set('1')
        if self.is_dual():
            self.source_var.set(lessons(n)[0]['source_id'])
            self.lesson_cb['values']=[str(i) for i in range(1,21)]
            self.lesson_label.configure(text='Экспериментальный урок (1–20)')
            info=f'{len(all_sources)} исходных матриц · 20 экспериментальных пар · minimax не доказан'
        else:
            self.source_var.set(original_lessons(n)[0]['map_id'])
            self.lesson_cb['values']=[str(i) for i in range(1,6)]
            self.lesson_label.configure(text='Оригинальный урок (1–5)')
            info=f'{len(all_sources)} оригинальных матриц · 5 уроков исходного маршрута'
        self.detail_var.set(info)
        refresh_tree(self.root)

    def change_mono_filter(self,event=None):
        if not self.is_mono(): return
        n=int(self.n_var.get()); category=MONO_FILTER_LABELS[self.mono_filter_var.get()]
        rows=filtered_monochrome(n,category)
        ids=[x['id'] for x in rows]
        self.source_cb['values']=ids
        default='M3-B-01' if n==3 else 'M4-Q176' if n==4 else ids[0] if ids else ''
        self.source_var.set(default if default in ids else ids[0] if ids else '')
        count=full_count(n) if category=='full' else len(ids)
        suffix=f'{len(ids)}/{count}' if category=='full' and count else str(len(ids))
        self.lesson_label.configure(text=f'Фильтр Mono · {suffix} карт')
        if category=='full' and count==0:
            self.detail_var.set('Полный архив не установлен. См. DOCS/V4_SCIENCE_GAMEPLAY_01_RU.md')
        elif not self.game:
            self.detail_var.set(f'{n}×{n} · {suffix} карт · FG-1; научный статус отдельный')
        refresh_tree(self.root)

    def load_lesson(self):
        if self.is_mono():
            return self.load_source()
        try:
            n=int(self.n_var.get());id_=int(self.lesson_var.get())
            q=lessons(n)[id_-1] if self.is_dual() else make_original_lesson(n,id_)
            self.set_game(n,q)
        except Exception as ex:messagebox.showerror(tr('Ошибка выбора урока'),tr(str(ex)))

    def load_source(self):
        try:
            n=int(self.n_var.get());source=self.source_var.get().strip()
            if self.is_mono() and source not in self.source_cb['values']:
                if (MONO_FILTER_LABELS[self.mono_filter_var.get()]!='full'
                    or full_by_id(n,source) is None):
                    raise ValueError('Нет карты в выбранном фильтре. Выберите другой фильтр.')
            q=make_monochrome(n,source) if self.is_mono() else make_source_pair(n,source) if self.is_dual() else make_shared(n,source)
            self.set_game(n,q)
        except Exception as ex:messagebox.showerror(tr('Ошибка выбора матрицы'),tr(str(ex)))

    def set_game(self,n,q):
        self.game=Game(n,q['black'],q['white'])
        self.configure_board_mode()
        self.s=State();self.history=[self.s];self.record=[];self.metadata=dict(q)
        self.n_var.set(str(n));self.over=False;self.ai_scheduled=False;self._ai_ticket+=1
        self.rng=random.Random(31)
        self.update_status();self.redraw();self.schedule_ai()

    def update_status(self):
        if not self.game:return
        g=self.game; b,w=g.scores(self.s);u=g.utility(self.s)
        self.over=g.end(self.s)
        primary, outcome, breakdown = format_scoreboard(g,self.s,self.over)
        self.score_var.set(primary)
        self.score_outcome_var.set(outcome)
        self.score_breakdown_var.set(breakdown)
        if self.is_dual():
            self.dual_focus_var.set(focus_text(self.game,self.s,self._dual_focus))
        if self.over:
            winner='ЧЁРНЫЕ' if u>(0,)*6 else 'БЕЛЫЕ' if u<(0,)*6 else 'НИЧЬЯ'
            status=f'Партия завершена. V={u[0]} · U={u} · результат по U: {winner}'
        else:
            who='● ЧЁРНЫЕ' if self.s.turn==0 else '○ БЕЛЫЕ'
            status=f'Ход {len(self.record)+1}: {who} | B={b}, W={w}, текущее V={b-w}, заморожено={self.s.frozen.bit_count()}'
        self.status_var.set(status)
        origin=self.metadata.get('provenance','')
        mode_label='MONO' if self.metadata.get('catalog')=='monochrome' else 'DUAL' if g.rule_mode=='dual_priority' else 'ORIGINAL'
        detail=f'{g.n}×{g.n} · {mode_label} · {self.metadata.get("source_id", "?")} · {origin} · {self.metadata.get("status", "")}'; dynamic=dynamic_description(self.metadata)
        if dynamic: detail += ' · '+dynamic
        if mode_label=='MONO': detail += ' · minimax, не исход любой партии'
        self.detail_var.set(detail)

    def configure_board_mode(self):
        dual=self.is_dual() and self.game.rule_mode=='dual_priority'
        self._dual_focus=None
        self._dual_geometries={}
        if dual:
            self.canvas.pack_forget()
            self.dual_container.pack(fill='both',expand=True)
            self.dual_controls.pack(fill='x',pady=(5,3))
            self.overlay_cb['values']=DUAL_OVERLAYS
            if self.overlay.get() not in DUAL_OVERLAYS:
                self.overlay.set(DUAL_OVERLAYS[0])
            self.dual_focus_var.set(focus_text(self.game,self.s,None))
            self.configure_dual(redraw=False)
        else:
            self.dual_container.pack_forget()
            self.dual_controls.pack_forget()
            self.canvas.pack(fill='both',expand=True)
            self.overlay_cb['values']=OVERLAY_OPTIONS
            if self.overlay.get() in DUAL_OVERLAYS:
                self.overlay.set('Числа высот H_B')
            self.dual_focus_var.set('')
        refresh_tree(self.root)

    def configure_dual(self,redraw=True):
        width=int(self.dual_width.get())
        orientation='top' if self.dual_orientation.get()=='Друг над другом' else 'left'
        for tile in (self.black_tile,self.white_tile):
            tile.pack_forget()
        for c in (self.canvas_black,self.canvas_white):
            c.configure(width=width,height=width)
        for tile in (self.black_tile,self.white_tile):
            tile.pack(side=orientation,anchor='nw',padx=3,pady=2)
        self.dual_view.xview_moveto(0)
        self.dual_view.yview_moveto(0)
        if redraw:self.redraw()

    def redraw(self):
        if not self.game:return
        if self.is_dual() and self.game.rule_mode=='dual_priority':
            visible=self.overlay.get()!='Не показывать'
            color=self.overlay.get()==DUAL_OVERLAYS[1]
            for c,layer in ((self.canvas_black,0),(self.canvas_white,1)):
                self._dual_geometries[c]=self._render_layer(c,layer,color,visible)
                self._mark_focus(c,self._dual_focus)
        else:
            layer,color=overlay_spec(self.overlay.get())
            self._geom=self._render_layer(self.canvas,
                              0 if layer is None else layer,
                              color,layer is not None)

    def _mark_focus(self,canvas,p):
        canvas.delete('hover-focus')
        geom=self._dual_geometries.get(canvas)
        if p is None or geom is None:return
        x0,y0,sp=geom
        x=x0+(p%self.game.n)*sp
        y=y0+(p//self.game.n)*sp
        r=max(6,min(sp*.38,21))
        canvas.create_oval(x-r,y-r,x+r,y+r,
                           outline='#168AD0',width=2,tags=('hover-focus',))

    def dual_hover(self,event,canvas):
        if not self.game or not self.is_dual():return
        p=(point_at(event,self._dual_geometries.get(canvas),self.game.n)
           if event is not None else None)
        if p==self._dual_focus:return
        self._dual_focus=p
        self.dual_focus_var.set(focus_text(self.game,self.s,p))
        for c in (self.canvas_black,self.canvas_white):
            self._mark_focus(c,p)

    def click(self,event,canvas=None):
        if not self.game or self.over:return
        if (self.black_mode if self.s.turn==0 else self.white_mode).get()!='Человек':
            return
        dual=self.is_dual() and self.game.rule_mode=='dual_priority'
        c=self.canvas if canvas is None else canvas
        if dual and c not in (self.canvas_black,self.canvas_white):return
        geom=self._dual_geometries.get(c) if dual else getattr(self,'_geom',None)
        p=point_at(event,geom,self.game.n)
        if p is not None:self.apply_move(p)

    def _render_layer(self,C,layer,show_color,show_height):
        if not self.game:
            return
        g=self.game;n=g.n
        C.delete('all')
        w=max(200,C.winfo_width(),int(C.cget('width')))
        h=max(200,C.winfo_height(),int(C.cget('height')))
        side=min(w-80,h-80);space=side/(n-1)
        x0=(w-side)/2;y0=(h-side)/2
        geometry=(x0,y0,space)
        radius=max(4,min(space*.45,24))
        # Grid and click coordinates match the original verified FG-1 GUI.
        if layer is not None and show_color:
            for p, value in enumerate(g.h[layer]):
                x=x0+(p%n)*space;y=y0+(p//n)*space
                C.create_rectangle(x-space/2,y-space/2,x+space/2,y+space/2,
                                   fill=signed_cell_color(value),outline='',tags=('landscape-background',))
        for i in range(n):
            p=x0+i*space;q=y0+i*space
            C.create_line(x0,q,x0+side,q,fill='#715331',width=1)
            C.create_line(p,y0,p,y0+side,fill='#715331',width=1)
            C.create_text(p,y0-22,text=LETTERS[i],
                          font=('Segoe UI',max(8,min(12,int(space*.29)))),fill='#523716')
            C.create_text(x0-23,q,text=str(i+1),
                          font=('Segoe UI',max(8,min(12,int(space*.29)))),fill='#523716')
        if n>=9:
            stars=[3,n//2,n-4] if n%2 else [3,n-4]
            for a in stars:
                for b in stars:
                    C.create_oval(x0+a*space-3,y0+b*space-3,
                                  x0+a*space+3,y0+b*space+3,
                                  fill='#684B2C',outline='')
        for p in range(n*n):
            bit=1<<p
            x=x0+(p%n)*space;y=y0+(p//n)*space
            if self.s.frozen&bit:
                C.create_line(x-radius*.55,y-radius*.55,
                              x+radius*.55,y+radius*.55,fill='#9B361B',width=2,tags=('frozen-mark',))
                C.create_line(x+radius*.55,y-radius*.55,
                              x-radius*.55,y+radius*.55,fill='#9B361B',width=2,tags=('frozen-mark',))
            elif (self.s.b|self.s.w)&bit:
                black=bool(self.s.b&bit)
                C.create_oval(x-radius,y-radius,x+radius,y+radius,
                              fill='#191919' if black else '#F9F9F7',
                              outline='#161616',width=1.25,tags=('stone-black' if black else 'stone-white',))
            if show_height:
                value=height_text(g.h[layer][p])
                text_size=max(8,min(13,int(space*.28),int(radius*.56)))
                if self.s.b&bit:
                    color='#FFFFFF'
                elif self.s.w&bit:
                    color='#202020'
                elif self.s.frozen&bit:
                    color='#8D361D'
                else:
                    color='#4C3522'
                    width=max(12,len(value)*text_size*.65+4)
                    C.create_rectangle(x-width/2,y-text_size*.8,
                                       x+width/2,y+text_size*.8,
                                       fill='#FFF6E5' if not show_color else
                                       signed_cell_color(g.h[layer][p]),
                                       outline='',tags=('height-backdrop',))
                C.create_text(x,y,text=value,
                              font=('Segoe UI',text_size,'bold'),
                              fill=color,tags=('height-value',))
        if self.record and self.record[-1]!='PASS':
            p=self.game.parse(self.record[-1])
            x=x0+(p%n)*space;y=y0+(p//n)*space
            # Never cover the height figure with the last-move marker.
            dx=radius*.62 if show_height else 0
            dy=radius*.62 if show_height else 0
            C.create_oval(x+dx-3,y+dy-3,x+dx+3,y+dy+3,
                          fill='#E0B238',outline='#7B5B1F',tags=('last-move',))

        return geometry

    def apply_move(self,p):
        if not self.game or self.over:return
        try:
            move=self.game.coord(p) if p is not None else 'PASS'
            self.s=self.game.step(self.s,p)
        except ValueError:
            self.root.bell();return
        self.history.append(self.s);self.record.append(move)
        self.update_status();self.redraw()
        if not self.over:self.schedule_ai()

    def schedule_ai(self):
        if self.ai_scheduled or not self.game or self.over:return
        mode=(self.black_mode if self.s.turn==0 else self.white_mode).get()
        if mode!='Компьютер' and self.game.legal_moves(self.s):return
        self.ai_scheduled=True
        ticket=self._ai_ticket
        self.root.after(75,lambda:self.ai_turn(ticket))

    def ai_turn(self,ticket):
        if ticket!=self._ai_ticket:return
        self.ai_scheduled=False
        if not self.game or self.over:return
        legal=self.game.legal_moves(self.s)
        if not legal:
            if not self.game.end(self.s):self.apply_move(None)
            return
        mode=(self.black_mode if self.s.turn==0 else self.white_mode).get()
        if mode!='Компьютер':return
        p=self.game.choose(self.s,self.rng,self.bot_profile.get())
        self.apply_move(p)

    def undo(self):
        if len(self.history)<=1:return
        self._ai_ticket+=1;self.ai_scheduled=False
        self.history.pop();self.record.pop();self.s=self.history[-1]
        self.over=False;self.update_status();self.redraw()

    def open_maps(self):
        current=getattr(self,'_catalog_browser',None)
        if current is not None and current.window.winfo_exists():
            current.window.lift()
            current.window.focus_set()
            return
        self._catalog_browser=LandscapeCatalogBrowser(self,MONO_FILTER_LABELS)
        self._catalog_browser.refresh_language()

    def save(self):
        if not self.game:return
        p=filedialog.asksaveasfilename(title=tr('Сохранить партию'),defaultextension='.json',filetypes=[('JSON','*.json')])
        if not p:return
        payload={'format':'landscape_go_save_v1','size':self.game.n,'pair':self.metadata,'states':[asdict(q) for q in self.history],
                 'moves':self.record,'rules_version':'FG-1 / Scoring v0.2','rules_mode':(MONO_MODE if self.metadata.get('catalog')=='monochrome' else 'Dual Priority · две матрицы' if self.game.rule_mode=='dual_priority' else 'Оригинал · общая матрица'),'black_mode':self.black_mode.get(),'white_mode':self.white_mode.get(), 'rng_seed_restart_note':'RNG restored only by fresh seed, not a deterministic uninterrupted stream'}
        Path(p).write_text(json.dumps(payload,ensure_ascii=False,indent=2),'utf8')

    def load_saved(self):
        p=filedialog.askopenfilename(title=tr('Открыть сохранение'),filetypes=[('JSON','*.json')])
        if not p:return
        try:
            payload=json.loads(Path(p).read_text('utf8'))
            if payload['format']!='landscape_go_save_v1':raise ValueError('Unknown save format')
            n=payload['size'];pm=payload['pair']
            if payload.get('rules_version','FG-1 / Scoring v0.2')!='FG-1 / Scoring v0.2':
                raise ValueError('Unsupported rules version')
            game=Game(n,pm['black'],pm['white']); history=[State(**a) for a in payload['states']]
            moves=payload['moves']
            if len(history)!=len(moves)+1 or history[0]!=State():raise ValueError('Broken saved move sequence')
            for i,a in enumerate(moves):
                if game.end(history[i]) or game.step(history[i],None if a=='PASS' else game.parse(a))!=history[i+1]:
                    raise ValueError('Broken saved move sequence')
            mode=MONO_MODE if pm.get('catalog')=='monochrome' else ('Dual Priority · две матрицы' if game.rule_mode=='dual_priority' else 'Оригинал · общая матрица')
            if mode==MONO_MODE and n not in MONO_SIZES:raise ValueError('Unsupported monochrome size')
            self.black_mode.set(payload.get('black_mode','Человек'));self.white_mode.set(payload.get('white_mode','Компьютер'))
            self.mode_var.set(mode);self.n_var.set(str(n));self.change_size();self.set_game(n,pm)
            self.source_var.set(pm.get('source_id',''));self.history=history
            self.s=history[-1];self.record=moves
            self.update_status();self.redraw();self.schedule_ai()
        except Exception as ex:messagebox.showerror(tr('Ошибка загрузки'),tr(str(ex)))

def main():
    root=tk.Tk();LandscapeWindow(root);root.mainloop();return 0
