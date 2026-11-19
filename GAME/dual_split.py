"""Pure index/focus helpers for two synchronized FG-1 visual canvases."""
from .landscape_viewer import height_text

DUAL_OVERLAYS=('Числа двух полей','Рельеф + числа двух полей','Не показывать')
DUAL_ORIENTATIONS=('Рядом','Друг над другом')
DUAL_WIDTHS=('480','560','640','720')

def point_at(event, geometry, n):
    if event is None or geometry is None: return None
    x0,y0,step=geometry
    if step<=0 or not 3<=n<=19:return None
    col=round((event.x-x0)/step);row=round((event.y-y0)/step)
    if not (0<=col<n and 0<=row<n):return None
    if abs(event.x-(x0+col*step))>step*.49:return None
    if abs(event.y-(y0+row*step))>step*.49:return None
    return row*n+col

def focus_text(game,state,p):
    if p is None:return 'Наведите курсор: H_B / H_W / занятость узла'
    if not 0<=p<game.total:raise ValueError('Invalid node')
    bit=1<<p
    status=('заморожен' if state.frozen&bit else
            'занят чёрными' if state.b&bit else
            'занят белыми' if state.w&bit else 'свободен')
    return (f'{game.coord(p)} | H_B={height_text(game.h[0][p])}'
            f' | H_W={height_text(game.h[1][p])} | {status}')
