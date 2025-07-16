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
    {"user_id": 6, "color": "#ADD8E6", "day": 15, "hours": 7, "stage": "ПОДГОТОВКА"},
    {"user_id": 6, "color": "#ADD8E6", "day": 16, "hours": 5, "stage": "ПОДГОТОВКА"},
]

stages = [
    ("ПОДГОТОВКА", 12),
    ("3D ГРАФИКА", 12),
    ("ЗАКАЗНЫЕ ПОЗИЦИИ", 12),
    ("СМР", 12),
    ("КОМПЛЕКТАЦИЯ", 12),
    ("РЕАЛИЗАЦИЯ", 12)
]
all_stages = [
        'ПОДГОТОВКА',
        '3D ГРАФИКА',
        'ЗАКАЗНЫЕ ПОЗИЦИИ',
        'СМР',
        'КОМПЛЕКТАЦИЯ',
        'РЕАЛИЗАЦИЯ'
    ]
def render_cell(stage_name, hour, day, selected_data=None):
    cell_style = {
        "cursor": "pointer",
        "color": "white",
        "border": "1px solid #F5F5F5",
        "text-align": "center",
        "font-size": "12px",
        "font-weight": "600",
        "min-width": "30px"
    }

    # 1. Из БД
    for record in user_work_data:
        if (
            record["stage"] == stage_name and
            record["day"] == day and
            hour <= record["hours"]
        ):
            if hour == record["hours"]:
                cell_style["border-radius"] = '0 0 10px 10px'
            cell_style["background-color"] = record["color"]
            cell_style["border"] = '1px rgba(255,255,255,0.18) solid'
            cell_style["color"] = record["color"]

    # 2. Выделение по текущему клику
    if selected_data:
        if (
            selected_data.get("stage") == stage_name and
            selected_data.get("day") == day and
            hour <= selected_data.get("hour")
        ):
            if hour == selected_data.get("hour"):
                cell_style["border-radius"] = '0 0 10px 10px'
            cell_style["background-color"] = selected_data.get("color")
            cell_style["border"] = '1px rgba(255,255,255,0.18) solid'
            cell_style["color"] = selected_data.get("color")

    return html.Td(
        str(hour),
        id={
            "type": "calendar-cell",
            "stage": stage_name,
            "hour": hour,
            "day": day
        },
        className="calendar-cell",
        n_clicks=0,
        style=cell_style
    )




def create_stage_block(stage_name, rows, selected_data=None):
    return [
        html.Tr([
            html.Td(row + 1, style={
                "border": "1px solid #EEEEEE",
                "background-color": "#F7F7F7",
                "border-left": "0",
                "text-align": "center",
                "font-size": "12px"
            }) if col == 0 else
            html.Td(stage_name, rowSpan=rows, style={
                "border": "2px solid #ccc",
                "text-align": "center",
                "font-size": "12px",
                "max-width": "105px",
                "background-image": f"url('assets/img/background{all_stages.index(stage_name)+1}.png')",
                "background-size": "cover",
            }) if col == 1 and row == 0 else
            render_cell(stage_name, row + 1, col - 2 + 1, selected_data) if col >= 2 else
            None
            for col in range(2 + len(days))
        ])
        for row in range(rows)
    ]




def render_table(selected_data=None):
    content= html.Div([
        html.Table([
            # Заголовок таблицы
            html.Thead([
                html.Tr([
                    html.Th("ЧАСЫ", rowSpan=2,
                            style={"border": "1 solid #ccc", "border-radius": "12px 0 0 0", "text-align": "center",
                                   "border-top": "0",
                                   "background-color": "#F7F7F7", "font-size": "12px", "font-weight": "500", }),
                    html.Th("ЭТАП", rowSpan=2,
                            style={"border": "2px solid #ccc", "background-color": "", "font-size": "12px",
                                   "border-top": "0",
                                   "font-weight": "500", "text-align": "center", }),
                    html.Th("ИЮЛЬ", colSpan=len(days),
                            style={"border": "1px solid #ccc", "background-color": "#f7e96c", "text-align": "center",
                                   "border-top": "0", "border-bottom": "0",
                                   "font-size": "14px", "font-weight": "500", "padding": "4px 2px", })
                ]),
                html.Tr([
                    html.Th(day, style={"border": "1px solid #ccc", "text-align": "center", "border-top": "0",
                                        "font-size": "12px", "font-weight": "500", "min-width": "30px", }) for day in
                    days
                ], )
            ], style={"position": "sticky", "top": "0", "zIndex": 2, "border-bottom": "2px solid #ccc",
                      "background-color": "white", "box-shadow": "inset 0 -1px 0 #ccc", "user-select":"none"}),
            # Секции по этапам
            *[
                html.Tbody(
                    id={"type": "stage-block", "stage": all_stages[i]},
                    children=create_stage_block(name, rows, selected_data),
                    style={"border": "2px solid #ccc", "border-left": "0"}
                )
                for i, (name, rows) in enumerate(stages)
            ]
        ], style={"width": "100%", "border-collapse": "collapse", "border-spacing": "0px", })
    ])
    print("calendar prepared")
    return content


def CALENDAR():
    today = datetime.today()
    content = html.Div([
        dcc.Store(id='filled-cells', data={}),
        html.Div('КАЛЕНДАРНЫЙ ОТЧЁТ', className='name'),

        html.Div([
            # dcc.Loading([
                html.Div(render_table(), id='Calendar'),

            # ], color='grey', type='circle'),
        ], className='line calendar'),
        html.Div([
        html.Div([
            html.Div('Настройки'.upper(), style={'margin-bottom': '10px','margin-top': '10px', 'font-weight':'700px', 'font-size':'18px','color':'black'}),

                dbc.Row([
                    dbc.Col([
                    dcc.Dropdown(id='ProjectFilter',placeholder='Проект',
                                 options=[]),
                    dcc.Dropdown(id='StageFilter',placeholder='Этап',
                                 options=[]),
                    dcc.Dropdown(id='YearFilterGraph', placeholder='Год',
                                 options=[], value=today.year, clearable=False),
                    dcc.Dropdown(id='MonthFilterGraph', placeholder='Месяц',
                                 options=[], value=today.month),
                    ]),
                ]),
        ], className='cloud', style={'margin-bottom':'0', 'padding-bottom':'14px', 'min-width':'260px'}),
        html.Button('Сбросить', className='clean', id='refresh'),
        html.Div(id='selected-cells', className='cloud', style={'margin-top': '20px'}),
        ], className='filters line'),
    ])
    return content