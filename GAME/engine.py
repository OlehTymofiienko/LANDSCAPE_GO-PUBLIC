#!/usr/bin/env python3
"""LANDSCAPE_GO unified 3..19 Scoring v0.2 / Dual Priority FG-1 engine (Python stdlib).
Exact legality under project's NONSTANDARD rules, independent of bot quality.
No territory, no komi, no voluntary pass, captured intersections frozen.
Suicide tested BEFORE opponent capture (unlike traditional Go).
"""
from __future__ import annotations
from dataclasses import dataclass,replace,asdict
from functools import lru_cache
import random,re,json
from pathlib import Path

LETTERS='ABCDEFGHIJKLMNOPQRS' # Intentionally includes I: project uses A..S, not standard Go column skipping I.

@dataclass(frozen=True)
class State:
    b:int=0; w:int=0; frozen:int=0;turn:int=0
    cb:int=0;cw:int=0;raw_b:int=0;raw_w:int=0
    zero_b:int=0;zero_w:int=0;lost_b:int=0;lost_w:int=0
    n_b:int=0;n_w:int=0

@lru_cache(maxsize=20)
def neighbors_for_size(n):
    if not 3<=n<=19:raise ValueError('Only board sizes 3..19')
    nei=[]; masks=[]
    for i in range(n*n):
        y,x=divmod(i,n)
        a=tuple(n*Y+X for X,Y in ((x-1,y),(x+1,y),(x,y-1),(x,y+1)) if 0<=X<n and 0<=Y<n)
        nei.append(a);masks.append(sum(1<<p for p in a))
    return tuple(nei),tuple(masks)

class Game:
    def __init__(self,n,hb,hw):
        self.n=n;self.total=n*n;self.full=(1<<self.total)-1
        self.nei,self.masks=neighbors_for_size(n)
        self.h=(tuple(int(a) for a in hb),tuple(int(b) for b in hw))
        if any(len(x)!=self.total for x in self.h):raise ValueError(f'Each map must have exactly {self.total} cells')
        self.rule_mode = 'original_shared' if self.h[0] == self.h[1] else 'dual_priority'
        self.cap=tuple(tuple(0 if v==0 else max(1,v,1-v) for v in layer) for layer in self.h)

    def coord(self,p):
        if not 0<=p<self.total:raise ValueError('outside board')
        return LETTERS[p%self.n]+str(p//self.n+1)

    def parse(self,s):
        m=re.fullmatch(r'\s*([A-Sa-s])(\d{1,2})\s*',s)
        if not m:raise ValueError('Use column and row, e.g. D4')
        x=LETTERS.index(m.group(1).upper()); y=int(m.group(2))-1
        if not 0<=x<self.n or not 0<=y<self.n:raise ValueError(f'Coordinate outside {self.n}×{self.n}')
        return y*self.n+x

    def neighbors(self,bits):
        m=0
        while bits:
            l=bits&-bits; bits-=l; m|=self.masks[l.bit_length()-1]
        return m

    def group(self,stones,seed):
        group=seed
        while True:
            nxt=group|(self.neighbors(group)&stones)
            if nxt==group:return group
            group=nxt

    def try_move(self,s,p):
        if p is None:
            if self.legal_moves(s):raise ValueError('Voluntary pass is forbidden')
            return replace(s,turn=1-s.turn)
        if p<0 or p>=self.total: return None
        bit=1<<p
        if bit&(s.b|s.w|s.frozen):return None
        own=s.b if s.turn==0 else s.w
        opp=s.w if s.turn==0 else s.b
        own|=bit
        # Empty cells before removal: suicide forbidden if own group has no liberty now.
        free=self.full & ~(own|opp|s.frozen)
        if not (self.neighbors(self.group(own,bit))&free):return None
        contacts=self.masks[p]&opp
        taken=0
        while contacts:
            seed=contacts&-contacts
            grp=self.group(opp,seed)
            contacts &= ~grp
            if not self.neighbors(grp)&free:taken|=grp
        opp &= ~taken
        award=raw=zeros=0
        bits=taken
        while bits:
            low=bits&-bits;bits-=low; i=low.bit_length()-1
            award+=self.cap[s.turn][i]
            raw+=self.h[s.turn][i]
            zeros+=self.h[s.turn][i]==0
        loss=taken.bit_count()
        if s.turn==0:
            return State(own,opp,s.frozen|taken,1,s.cb+award,s.cw,s.raw_b+raw,s.raw_w,s.zero_b+zeros,s.zero_w,s.lost_b,s.lost_w+loss,s.n_b+1,s.n_w)
        return State(opp,own,s.frozen|taken,0,s.cb,s.cw+award,s.raw_b,s.raw_w+raw,s.zero_b,s.zero_w+zeros,s.lost_b+loss,s.lost_w,s.n_b,s.n_w+1)

    def legal_moves(self,s):
        free=self.full & ~(s.b|s.w|s.frozen)
        own=s.b if s.turn==0 else s.w
        # Fast test: an adjacent empty point guarantees a pre-capture liberty.
        positions=[]; rest=free
        while rest:
            low=rest&-rest;rest-=low;p=low.bit_length()-1
            if self.masks[p]&free:
                positions.append(p)
            elif self.neighbors(self.group(own|low,low))&(free^low):
                positions.append(p)
        return positions

    def step(self,s,p):
        new=self.try_move(s,p)
        if new is None:raise ValueError('Недопустимый ход: '+str(p))
        return new

    def end(self,s):
        return not self.legal_moves(s) and not self.legal_moves(replace(s,turn=1-s.turn))

    def utility(self,s):
        b=sum(self.h[0][i] for i in range(self.total) if (s.b>>i)&1)+s.cb
        w=sum(self.h[1][i] for i in range(self.total) if (s.w>>i)&1)+s.cw
        v=b-w;c=s.raw_b-s.raw_w;z=s.zero_b-s.zero_w;r=s.n_w-s.n_b;loss=s.lost_w-s.lost_b
        return (v,c,z,r,loss,loss)

    def scores(self,s):
        b=sum(self.h[0][i] for i in range(self.total) if (s.b>>i)&1)+s.cb
        w=sum(self.h[1][i] for i in range(self.total) if (s.w>>i)&1)+s.cw
        return b,w

    def capture_threats(self,s):
        """Approximate instantaneous gain of placing at a group's only liberty."""
        opp=s.w if s.turn==0 else s.b
        free=self.full & ~(s.b|s.w|s.frozen)
        pending=opp; gains={}
        while pending:
            seed=pending&-pending;group=self.group(opp,seed);pending &= ~group
            liberties=self.neighbors(group)&free
            if liberties and not liberties&(liberties-1):
                p=liberties.bit_length()-1;bits=group;v=0
                while bits:
                    low=bits&-bits;bits-=low;i=low.bit_length()-1
                    v+=self.cap[s.turn][i]+self.h[1-s.turn][i]
                gains[p]=gains.get(p,0)+v
        return gains

    def choose(self,s,rng=None,profile='tactical'):
        legal=self.legal_moves(s)
        if not legal:return None
        if rng is None:rng=random.Random(0)
        if profile=='random':return rng.choice(legal)
        own=self.h[s.turn];op=self.h[1-s.turn];fr=s.b if s.turn==0 else s.w;en=s.w if s.turn==0 else s.b
        gains=self.capture_threats(s)
        alpha={'tactical':.5,'denial':.85,'selfish':.22,'balanced':.35}.get(profile,.5)
        cap_factor={'tactical':1.55,'denial':1.35,'selfish':1.4,'balanced':1.6}.get(profile,1.55)
        c=(self.n-1)/2
        best=-1e100; pick=legal[0]
        for p in legal:
            x=p%self.n;y=p//self.n
            align=.15*(self.masks[p]&fr).bit_count()+.07*(self.masks[p]&en).bit_count()+.035*(self.n*2-abs(x-c)-abs(y-c))
            score=own[p]+alpha*op[p]+cap_factor*gains.get(p,0)+align+rng.uniform(-.09,.09)
            if score>best:best=score;pick=p
        return pick

    def play_bots(self,seed=1,black='tactical',white='denial',first=None):
        rng=random.Random(seed);s=State();history=[]
        if first is not None:
            s=self.step(s,first);history.append(self.coord(first))
        for _ in range(2*self.total+10):
            if self.end(s):break
            p=self.choose(s,rng,black if s.turn==0 else white)
            history.append(self.coord(p) if p is not None else 'PASS')
            s=self.step(s,p)
        else:raise RuntimeError('Unexpected game length')
        assert self.end(s)
        return s,history

def transform(mat,t):
    n=len(mat)
    o=[r[:] for r in mat]
    if t>=4:o=[list(reversed(row)) for row in o]
    for _ in range(t%4):o=[[o[n-1-y][x] for y in range(n)] for x in range(n)]
    return o

def data_folder():
    return Path(__file__).resolve().parents[1]/'DATA'

@lru_cache(maxsize=18)
def sources(n):
    return json.loads((data_folder()/f'SOURCES_{n:02}X{n:02}.json').read_text('utf8'))['sources']

@lru_cache(maxsize=18)
def lessons(n):
    return json.loads((data_folder()/f'LESSONS_{n:02}X{n:02}.json').read_text('utf8'))

def make_source_pair(n,source_id,black_rot=0,white_rot=2):
    pool=sources(n);source=next((x for x in pool if x['id']==source_id),None)
    if source is None:raise ValueError(f'Source {source_id!r} not found for {n}x{n}')
    hb=transform(source['matrix'],black_rot);hw=transform(source['matrix'],white_rot)
    method='same_source_D4'
    if hb==hw:
        for t in range(8):
            x=transform(source['matrix'],t)
            if x!=hb:hw=x;method='same_source_D4_auto';break
        else:
            # D4 invariant source cannot produce two different maps from itself.
            for cand in pool:
                if cand['id']!=source_id and cand['matrix']!=hb:
                    hw=transform(cand['matrix'],2)
                    if hw!=hb:
                        method='different_source_fallback_'+cand['id'];break
            else:raise ValueError('No non-identical map exists')
    return {'size':n,'source_id':source_id,'title':source_id,'black':[v for row in hb for v in row],
            'white':[v for row in hw for v in row], 'method':method,'provenance':source['provenance'],
            'status':'Source from catalog — not proven Near-Zero'}

def matrix_rows(flat,n):return [flat[i*n:(i+1)*n] for i in range(n)]

def print_board(game,s):
    print('     '+' '.join(f'{x:^3}' for x in LETTERS[:game.n]))
    for y in range(game.n):
        a=[]
        for x in range(game.n):
            bit=1<<(y*game.n+x)
            a.append('●' if s.b&bit else '○' if s.w&bit else '×' if s.frozen&bit else '·')
        print(f'{y+1:>2}:  '+' '.join(f'{v:^3}' for v in a))

def print_maps(game):
    for title,mat in [('ЧЁРНЫЕ H_B',game.h[0]),('БЕЛЫЕ H_W',game.h[1])]:
        print(title)
        for y in range(game.n):print(' '.join(f'{v:>3}' for v in mat[y*game.n:(y+1)*game.n]))



@lru_cache(maxsize=1)
def original_curriculum():
    """The user's original 85-lesson route; same weight matrix for Black and White."""
    return json.loads((data_folder()/'ORIGINAL_CURRICULUM_85_LESSONS.json').read_text(encoding='utf8'))

@lru_cache(maxsize=18)
def original_lessons(n):
    if not 3 <= n <= 19:raise ValueError('Board size must be 3..19')
    return [x for x in original_curriculum() if x['board_size'] == f'{n}x{n}']

def make_shared(n,source_id):
    """Original Landscape Go scoring v0.2: SAME map for both players.
    Proof flags, if present in metadata, apply only to this single-matrix mode.
    """
    item=next((x for x in sources(n) if x['id']==source_id), None)
    if item is None:raise ValueError(f'Original matrix {source_id!r} not found for {n}x{n}')
    flat=[v for row in item['matrix'] for v in row]
    return {'size':n,'source_id':source_id,'black':flat,'white':flat.copy(),
            'game_mode':'original_shared','provenance':'uploaded_original_3132',
            'status':(item.get('source_status') or 'ORIGINAL')+' — статус из исходного каталога, не новый расчёт',
            'source_claim_exact_V':item.get('exact_V_proven_in_source',False),
            'title':item.get('title') or source_id}

def make_original_lesson(n,number):
    items=original_lessons(n)
    if not 1<=number<=len(items):raise ValueError(f'Уроки 1..{len(items)} для {n}x{n}')
    x=items[number-1]
    out=make_shared(n,x['map_id'])
    out.update({'lesson':number,'original_global_lesson':x['lesson'],'objective':x.get('objective'),
                'status':x.get('source_status') or x.get('status_class') or 'ORIGINAL',
                'source_claim_exact_V':x.get('exact_V_proven',False),
                'historic_V':x.get('V'),'historic_U':x.get('U')})
    return out
