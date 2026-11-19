"""Command-line, text-only interface and validation mode."""
from __future__ import annotations
import argparse,random,sys,json
from pathlib import Path
from .engine import Game,State,sources,lessons,make_source_pair,make_shared,original_lessons,make_original_lesson,print_board,print_maps

from .monochrome import MONO_FILTERS, SCIENCE_FILTERS, filtered_monochrome, make_monochrome, dynamic_description
from .science_full import full_by_id, full_count

def parse_args(argv=None):
    ap=argparse.ArgumentParser(description='LANDSCAPE_GO 3x3—19x19, original Scoring v0.2 or experimental Dual Priority')
    ap.add_argument('--mode',choices=['classic','dual','mono'],default='classic',help='classic = shared H; dual = distinct maps; mono = shared 3x3..19x19 selected scientific atlas')
    ap.add_argument('--mono-filter',choices=MONO_FILTERS + SCIENCE_FILTERS,default='all',help='Filter monochrome catalog or default selection')
    ap.add_argument('--size',type=int,default=3,choices=range(3,20))
    ap.add_argument('--lesson',type=int,default=1)
    ap.add_argument('--source',default=None,help='Catalog source ID, e.g. G13G_157')
    ap.add_argument('--black-orientation',type=int,default=0,choices=range(8))
    ap.add_argument('--white-orientation',type=int,default=2,choices=range(8))
    ap.add_argument('--black',choices=['human','ai'],default='human')
    ap.add_argument('--white',choices=['human','ai'],default='ai')
    ap.add_argument('--black-profile',choices=['tactical','denial','selfish','balanced','random'],default='tactical')
    ap.add_argument('--white-profile',choices=['tactical','denial','selfish','balanced','random'],default='denial')
    ap.add_argument('--seed',type=int,default=31)
    ap.add_argument('--list',action='store_true',help='List lessons')
    ap.add_argument('--catalog',action='store_true',help='List all source matrices for size')
    ap.add_argument('--maps',action='store_true',help='Print both numeric maps before play')
    ap.add_argument('--verify',action='store_true',help='Run a finished AI-vs-AI game and validate termination')
    ap.add_argument('--cli',action='store_true',help='Force console mode')
    return ap.parse_args(argv)

def select(args):
    if args.mode=='mono':
        rows=filtered_monochrome(args.size,args.mono_filter)
        if not rows and not args.source:
            raise ValueError('Нет доступных карт: для полного каталога сначала установите проверенный внешний индекс')
        default = 'M3-B-01' if args.size==3 else 'M4-Q176' if args.size==4 else rows[0]['id']
        source=args.source or default
        if args.source is None and args.mono_filter!='all' and rows:
            source=rows[0]['id']
        if not any(x['id']==source for x in rows):
            if args.mono_filter!='full' or full_by_id(args.size,source) is None:
                raise ValueError('Нет такой карты в выбранном фильтре')
        return make_monochrome(args.size,source)
    if args.source:
        return (make_source_pair(args.size,args.source,args.black_orientation,args.white_orientation) if args.mode=='dual' else make_shared(args.size,args.source))
    l=lessons(args.size) if args.mode=='dual' else original_lessons(args.size)
    if not 1<=args.lesson<=len(l):raise ValueError(f'Expected lesson 1..{len(l)}')
    return l[args.lesson-1] if args.mode=='dual' else make_original_lesson(args.size,args.lesson)

def run(args):
    n=args.size
    if args.mode=='mono' and (args.catalog or args.list):
        rows=filtered_monochrome(n,args.mono_filter)
        if args.mono_filter=='full':
            print('FULL_SCIENCE_INDEX',n,'total',full_count(n),'showing',len(rows),
                  '(use --source FULL-MN-000001 to select any verified indexed ID)')
        for o in rows:
            print(o['id'],o['class'],'V=',o['V'],'U=',o['U'],dynamic_description(o))
        return 0
    if args.catalog:
        for o in sources(n):print(o['id'],o['family'],o['provenance'])
        return 0
    if args.list:
        for i,l in enumerate(lessons(n) if args.mode=='dual' else original_lessons(n),1):print(f'{i:2}',l.get('source_id',l.get('map_id')),l.get('status',l.get('status_class','')))
        return 0
    pair=select(args)
    g=Game(n,pair['black'],pair['white'])
    print(f'LANDSCAPE_GO {n}x{n} / mode={args.mode} / {pair["source_id"]} / {pair.get("status","")}')
    print('НЕ ГО С ТЕРРИТОРИЯМИ. Запрет суицида до захвата, захваченные клетки замораживаются.')
    print('Exact-статус из исходного каталога относится только к original/shared. В dual Near-Zero не гарантирован.')
    if args.mode=='mono':
        print('Minimax относится к оптимальной игре, не к произвольной партии.')
        if pair.get('dynamic'):print(dynamic_description(pair),'— не режим игры.')
    if args.maps:print_maps(g)
    if args.verify:
        s,h=g.play_bots(seed=args.seed,black=args.black_profile,white=args.white_profile)
        print('PASS:',n,'source',pair['source_id'],'moves',len(h),'U',g.utility(s),'terminal',g.end(s))
        return 0
    s=State();rng=random.Random(args.seed);move_index=0;history=[]
    for _ in range(2*n*n+10):
        if g.end(s):break
        print_board(g,s)
        a,b=g.scores(s)
        print(f'Ход {move_index+1}, {"чёрные" if s.turn==0 else "белые"}; предварительно B={a} W={b} V={a-b}; захвачено/заморожено {s.frozen.bit_count()}')
        mode=args.black if s.turn==0 else args.white
        legal=g.legal_moves(s)
        if not legal:
            print('ВЫНУЖДЕННЫЙ ПАС')
            s=g.step(s,None);history.append('PASS');continue
        if mode=='ai':
            p=g.choose(s,rng,args.black_profile if s.turn==0 else args.white_profile)
            print('ИИ:',g.coord(p))
        else:
            while True:
                try:st=input('Координата (q — выйти, m — карты): ').strip()
                except EOFError:return 0
                if st.lower() in ('q','quit','exit'):return 0
                if st.lower()=='m':print_maps(g);continue
                try:
                    p=g.parse(st)
                    if p not in legal:print('Недопустимый ход');continue
                    break
                except ValueError as ex:print(ex)
        s=g.step(s,p);history.append(g.coord(p));move_index+=1
    else:raise RuntimeError('Game length cap exceeded')
    print_board(g,s)
    U=g.utility(s)
    print('ПАРТИЯ ЗАВЕРШЕНА; U=',U, 'V=',U[0], '|V|=',abs(U[0]),'ходов',len(history))
    print('По полному U:', 'чёрные' if U>(0,)*6 else 'белые' if U<(0,)*6 else 'ничья')
    return 0
