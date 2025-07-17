import flask_login
from dash import dcc
import dash_bootstrap_components as dbc
from dash import html
from datetime import datetime
from utils import rgba_string_to_hex
from dash import dash_table
from app import cache
import db

STAGES = ['ПОДГОТОВКА', '3D ГРАФИКА', 'ЗАКАЗНЫЕ ПОЗИЦИИ', 'СМР', 'КОМПЛЕКТАЦИЯ', 'РЕАЛИЗАЦИЯ']
HOURS = list(range(1, 13))
days = list(range(1, 32))

user_work_data = [
    {"user_id": 6, "color": "#ADD8E6", "day": 14, "hours": 7, "stage": "ПОДГОТОВКА"},
    {"user_id": 6, "color": "#ADD8E6", "day": 15, "hours": 7, "stage": "ПОДГОТОВКА"},
    {"user_id": 6, "color": "#ADD8E6", "day": 16, "hours": 5, "stage": "ПОДГОТОВКА"},
    {"user_id": 6, "color": "#ADD8E6", "day": 17, "hours": 2, "stage": "ПОДГОТОВКА"},
    {"user_id": 2, "color": "#E083B9", "day": 3, "hours": 2, "stage": "ПОДГОТОВКА"},
    {"user_id": 2, "color": "#E083B9", "day": 4, "hours": 4, "stage": "ПОДГОТОВКА"},
]

all_stages = [
        'ПОДГОТОВКА',
        '3D ГРАФИКА',
        'ЗАКАЗНЫЕ ПОЗИЦИИ',
        'СМР',
        'КОМПЛЕКТАЦИЯ',
        'РЕАЛИЗАЦИЯ'
    ]


def render_stage_block_columnwise(project_id, stage_name, rows=12, year=None, month=None, user_work_data=None):

    # Часы колонка
    hours_col = html.Div([
        html.Div(str(h + 1), style={
            "height": "24px", "border": "solid #EDEDED", "border-width": "0px 0px 1px 0px",
            "text-align": "center", "font-size": "12px",
            "background-color": "#F7F7F7", "min-width": "52px"
        }) for h in range(rows)
    ], style={"width": "52px"})

    # Этап колонка
    stage_col = html.Div([
        html.Div(stage_name, style={
            "height": f"{24 * rows}px", "border-right": "2px solid #ccc", "border-left": "2px solid #ccc",
            "text-align": "center", "font-size": "12px", "align-content": "center",
            "width": "120px", "background-size": "cover", "min-width": "120px",
            "background-image": f"url('assets/img/background{all_stages.index(stage_name) + 1}.png')"
        })
    ], style={"min-width": "120px"})

    # Каждая колонка дня
    day_cols = []
    for day in days:
        cells = []
        for hour in range(1, rows + 1):
            style = {
                "height": "24px",
                "border": "1px solid #F7F7F7",
                "text-align": "center",
                "cursor": "pointer",
                "font-size": "12px",
                "font-weight": "600",
                "color": "white",
                "position": "relative"
            }

            # Найди записи, которые касаются этой ячейки
            records = [r for r in user_work_data if
                       r["stage"] == stage_name and r["day"] == day and hour <= r["hours"]]
            if not records:
                # Пустая ячейка
                cells.append(html.Div(
                    str(hour),
                    id={"type": "calendar-cell", "stage": stage_name, "hour": hour, "day": day},
                    n_clicks=0,
                    style=style,
                    className='calendar-cell'
                ))
                continue
            style["box-shadow"] = "inset 0 0 0 1px rgba(255,255,255,0.1)"
            style["border"] = "none"

            # Один пользователь
            if len(records) == 1:
                rec = records[0]
                style["background-color"] = rec["color"]
                style["color"] = rec["color"]

                if hour == rec["hours"]:
                    left, right = db.is_contiguous(rec['user_id'], rec['project_id'],
                                                   all_stages.index(rec['stage']) + 1, year, month, day, hour)
                    style["border-radius"] = f"0 0 {'0' if right else '8px'} {'0' if left else '8px'}"
                cells.append(html.Div(
                    str(hour),
                    id={"type": "calendar-cell", "stage": stage_name, "hour": hour, "day": day},
                    n_clicks=0,
                    style=style,
                    className='calendar-cell'
                ))
                continue

            # Два пользователя — делаем градиент
            if len(records) >= 2:
                rec1, rec2 = records[:2]
                c1, c2 = rec1["color"], rec2["color"]

                style["background"] = f"linear-gradient(to right, {c1} 50%, {c2} 50%)"
                style["color"] = "rgba(255,255,255,0.05)"  # почти невидимый текст

                # Проверка на одинаковую длину записей — тогда скругляем
                if hour == rec1["hours"] == rec2["hours"]:
                    style["border-radius"] = "0 0 8px 8px"

                cells.append(html.Div(
                    str(hour),
                    id={"type": "calendar-cell", "stage": stage_name, "hour": hour, "day": day},
                    n_clicks=0,
                    style=style,
                    className='calendar-cell'
                ))

        day_cols.append(
            html.Div(cells, style={
                "display": "flex", "flex-direction": "column",
                "min-width": "30px"
            }, id={"type": "day-block", "stage": stage_name, "day": day})
        )

    return html.Div([
        hours_col, stage_col, *day_cols
    ], style={"display": "flex", "flex-direction": "row"}, className='stage-block')

def render_header():
    return html.Div([
        # ЧАСЫ
        html.Div("ЧАСЫ", style={
            "min-width": "52px", "font-weight": "400", "font-size": "12px",
            "border-right": "0px solid #ccc", "background-color": "#F7F7F7","border-bottom": "1px solid #ccc",
            "padding": "4px", "text-align": "center",
            "display": "flex", "alignItems": "center", "justifyContent": "center",
            "flexDirection": "column",
            "height": "60px"
        }),

        # ЭТАП
        html.Div("ЭТАП", style={
            "min-width": "120px", "font-weight": "400", "font-size": "12px",
            "border-right": "2px solid #ccc", "border-left": "2px solid #ccc","border-bottom": "1px solid #ccc",
            "background-color": "white",
            "padding": "4px", "text-align": "center",
            "display": "flex", "alignItems": "center", "justifyContent": "center",
            "flexDirection": "column",
            "height": "60px"
        }),

        # Блок с МЕСЯЦЕМ и ДНЯМИ
        html.Div([
            # Первая строка: месяц
            html.Div("ИЮЛЬ", style={
                "display": "flex", "justifyContent": "center", "alignItems": "center",
                "min-width": f"{30 * len(days)}px",
                "font-weight": "500", "font-size": "14px",
                "border": "0px solid #ccc", "background-color": rgba_string_to_hex(flask_login.current_user.color),
                "padding": "4px", "text-align": "center",
                "height": "30px"
            }),

            # Вторая строка: дни
            html.Div([
                *[
                    html.Div(str(day), style={
                        "min-width": "30px", "font-weight": "400", "font-size": "12px",
                        "border": "1px solid #EDEDED","border-bottom": "1px solid #ccc",
                        "background-color": "white",
                        "text-align": "center", "padding": "4px",
                        "height": "30px"
                    }) for day in days
                ]
            ], style={"display": "flex", "flex-direction": "row"})
        ], style={
            "display": "flex", "flex-direction": "column"
        })
    ], style={
        "display": "flex", "flex-direction": "row",
        "position": "sticky",
        "top": "0",
        "zIndex": "1000",
        "backgroundColor": "white",
        "boxShadow": "0 2px 3px rgba(0,0,0,0.1)"
    })

@cache.memoize()
def render_table_div(project_id=None, stages=None, year=None, month=None):
    return html.Div([
        render_header(),
        # dcc.Loading([
            html.Div(
                children=sum([
                    [
                        render_stage_block_columnwise(project_id, name, 12, year, month) ,
                        html.Div(style={
                            "width": "100%", "height": "2px", "backgroundColor": "#ccc"
                        })
                    ] for name in stages
                ], [])[:-1] if project_id else '',
                id='CalendarBody'
            ),
        # ], color='grey', type='circle'),
    ], style={"display": "flex", "flex-direction": "column", "gap": "0"})


def CALENDAR():
    today = datetime.today()
    content = html.Div([
        html.Div('КАЛЕНДАРНЫЙ ОТЧЁТ', className='name'),
        html.Div(id='popupBoxCal', children=[
            html.Div(id='popupCal'),
            dcc.Interval(id='popupClearInterval', interval=1800, n_intervals=0, disabled=True)
        ]),

        html.Div([

            html.Div([render_table_div(stages=all_stages)], id='Calendar')


        ], className='line calendar'),
        html.Div([
        html.Div([
            html.Div('Настройки'.upper(), style={'margin-bottom': '10px','margin-top': '10px', 'font-weight':'700px', 'font-size':'18px','color':'black'}),

                dbc.Row([
                    dbc.Col([
                    dcc.Dropdown(id='ProjectFilterCal',placeholder='Проект',
                                 options=[{'label':'АЗЕРБАЙДЖАНСКИЕ ИСТОРИИ', 'value':13}], value=13, clearable=False),
                    dcc.Dropdown(id='StageFilterCal',placeholder='Этап',
                                 options = [{'label': stage, 'value': stage} for stage in all_stages],value=0, ),
                    dcc.Dropdown(id='YearFilterCal', placeholder='Год',
                                 options=[{'label':'2025', 'value':2025}], value=today.year, clearable=False),
                    dcc.Dropdown(id='MonthFilterCal', placeholder='Месяц',
                                 options=[{'label':'Июль', 'value':7}], value=today.month, clearable=False),
                    ]),
                ]),
        ], className='cloud', style={'margin-bottom':'0', 'padding-bottom':'14px', 'min-width':'260px'}),
        html.Button('Сбросить', className='clean', id='refresh'),
        html.Div(id='selected-cells', className='cloud', style={'margin-top': '20px'}),
        ], className='filters line'),
    ])
    return content