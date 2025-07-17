from dash import dcc
import dash_bootstrap_components as dbc
from dash import html
from datetime import datetime
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

def render_table_div(selected_data=None):
    def render_header():
        return html.Div([
            # ЧАСЫ (растянут на 2 строки)
            html.Div("ЧАСЫ", style={
                "min-width": "52px", "font-weight": "400", "font-size": "12px",
                "border-right": "0px solid #ccc", "background-color": "#F7F7F7","border-bottom": "1px solid #ccc",
                "padding": "4px", "text-align": "center",
                "display": "flex", "alignItems": "center", "justifyContent": "center",
                "flexDirection": "column",
                "height": "60px"  # высота, соответствующая 2 строкам
            }),

            # ЭТАП (тоже растянут на 2 строки)
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
                    "border": "0px solid #ccc", "background-color": "#f7e96c",
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

    def render_stage_block_columnwise(stage_name, rows=12, selected_data=None):
        user_work_data = db.get_user_work_data(13, 2025, 7)
        # Часы колонка
        hours_col = html.Div([
            html.Div(str(h+1), style={
                "height": "24px", "border": "solid #EDEDED", "border-width": "0px 0px 1px 0px",
                "text-align": "center", "font-size": "12px",
                "background-color": "#F7F7F7","min-width": "52px"
            }) for h in range(rows)
        ], style={"width": "52px"})

        # Этап колонка (одна ячейка на весь блок)
        stage_col = html.Div([
            html.Div(stage_name, style={
                "height": f"{24 * rows}px", "border-right": "2px solid #ccc", "border-left": "2px solid #ccc",
                "text-align": "center", "font-size": "12px","align-content":"center",
                "width": "120px", "background-size": "cover","min-width": "120px",
                "background-image": f"url('assets/img/background{all_stages.index(stage_name)+1}.png')"
            })
        ], style={"min-width": "120px"})

        # Каждая колонка дня (1..31)
        day_cols = []
        for day in days:
            cells = []
            for hour in range(1, rows + 1):
                style = {
                    "height": "24px", "border": "0.5px solid #F7F7F7",
                    "text-align": "center", "cursor": "pointer",
                    "font-size": "12px", "font-weight": "600", "color":"white"
                }
                # Базовая окраска из базы
                for i, record in enumerate(user_work_data):
                    if record["stage"] == stage_name and record["day"] == day and hour <= record["hours"]:
                        style["background-color"] = record["color"]
                        style["color"] = record["color"]
                        style["border"] = "1px rgba(255,255,255,0.10) solid"
                        if hour == record["hours"]:
                            left_rounded = True
                            right_rounded = True
                            # Проверка предыдущей записи (если есть)
                            if i > 0:
                                prev = user_work_data[i - 1]
                                if (
                                        prev["user_id"] == record["user_id"] and prev["stage"] == record["stage"] and
                                        prev["day"] == record["day"] - 1 and prev["hours"] >= record["hours"]
                                ):
                                    left_rounded = False

                            # Проверка следующей записи (если есть)
                            if i < len(user_work_data) - 1:
                                next_ = user_work_data[i + 1]
                                if ( next_["user_id"] == record["user_id"] and next_["stage"] == record["stage"] and
                                     next_["day"] == record["day"] + 1 and next_["hours"] >= record["hours"]
                                ):
                                    right_rounded = False
                            radius = f"0 0 {'8px' if right_rounded else '0'} {'8px' if left_rounded else '0'}"
                            style["border-radius"] = radius

                # Выделение через Store
                # if selected_data and selected_data.get("stage") == stage_name and selected_data.get("day") == day and hour <= selected_data.get("hour"):
                #     style["background-color"] = selected_data.get("color")
                #     style["color"] = selected_data.get("color")
                #     style["border"] = "1px rgba(255,255,255,0.18) solid"
                #     if hour == selected_data.get("hour"):
                #         style["border-radius"] = "0 0 8px 8px"

                cells.append(
                    html.Div(
                        str(hour),
                        id={"type": "calendar-cell", "stage": stage_name, "hour": hour, "day": day},
                        n_clicks=0,
                        style=style,
                        className='calendar-cell'
                    )
                )
            day_cols.append(
                html.Div(cells, style={
                    "display": "flex", "flex-direction": "column",
                    "min-width": "30px"
                }, id={"type": "day-block", "stage": stage_name, "day": day})
            )

        return html.Div([
            hours_col, stage_col, *day_cols
        ], style={"display": "flex", "flex-direction": "row","border_bottom":"2px solid"})

    return html.Div([
        render_header(),
        *sum([
            [
                render_stage_block_columnwise(name, 12, selected_data),
                html.Div(style={
                    "width": "100%",
                    "height": "2px",  # или сколько нужно
                    "backgroundColor": "#ccc"  # светло-серый цвет
                })
            ] for name in all_stages
        ], [])[:-1]
    ], style={"display": "flex", "flex-direction": "column", "gap": "0"})

def CALENDAR():
    today = datetime.today()
    content = html.Div([
        dcc.Store(id='filled-cells', data={}),
        html.Div('КАЛЕНДАРНЫЙ ОТЧЁТ', className='name'),
        html.Div([
            html.Div([], id='popupCal',)
        ], id='popupBoxCal', ),

        html.Div([
            # dcc.Loading([
                html.Div(render_table_div(), id='Calendar',),

            # ], color='grey', type='circle'),
        ], className='line calendar'),
        html.Div([
        html.Div([
            html.Div('Настройки'.upper(), style={'margin-bottom': '10px','margin-top': '10px', 'font-weight':'700px', 'font-size':'18px','color':'black'}),

                dbc.Row([
                    dbc.Col([
                    dcc.Dropdown(id='ProjectFilterCal',placeholder='Проект',
                                 options=[{'label':'АЗЕРБАЙДЖАНСКИЕ ИСТОРИИ', 'value':13}], value=13, clearable=False),
                    dcc.Dropdown(id='StageFilterCal',placeholder='Этап',
                                 options = [{'label': stage, 'value': i + 1} for i, stage in enumerate(all_stages)]+[{'label':'[Все этапы]', 'value':0}],value=0,clearable=False ),
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