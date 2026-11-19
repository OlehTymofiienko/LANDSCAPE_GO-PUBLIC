"""Pure GUI formatting of the existing FG-1 point score and final lexicographic utility.

A current-game V is not a proven minimax value for a scientific matrix.
"""
def format_scoreboard(game, state, finished):
    """Return primary points, provisional/final verdict, and component breakdown."""
    black,white=game.scores(state)
    difference=black-white
    u=game.utility(state)
    score=(f'● Чёрные: {black:+d}    ○ Белые: {white:+d}'
           f'    Разница V: {difference:+d}')
    breakdown=(f'Камни: чёрные {black-state.cb:+d}, белые {white-state.cw:+d}'
               f'; бонус захватов: чёрные +{state.cb}, белые +{state.cw}.')
    if not finished:
        if difference>0:
            status=f'чёрные впереди на {difference} очк.'
        elif difference<0:
            status=f'белые впереди на {-difference} очк.'
        else:
            status='равенство по первичному счёту V=0'
        outcome='ПРЕДВАРИТЕЛЬНО · '+status+' · итоговый победитель определяется по U.'
    else:
        winner='ЧЁРНЫЕ' if u>(0,)*6 else 'БЕЛЫЕ' if u<(0,)*6 else 'НИЧЬЯ'
        if winner=='НИЧЬЯ':
            outcome='ИТОГ · НИЧЬЯ по полному U=0.'
        elif difference:
            outcome=(f'ИТОГ · победили {winner} с разницей {abs(difference)} очк.'
                     f' по V · U={u}.')
        else:
            outcome=(f'ИТОГ · победили {winner} по дополнительным критериям'
                     f' U при V=0 · U={u}.')
    return score,outcome,breakdown
