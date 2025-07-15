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

stages = [
    ("ПОДГОТОВКА", 12),
    ("3D ГРАФИКА", 12),
    ("ЗАКАЗНЫЕ ПОЗИЦИИ", 12),
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
def render_cell(stage_name, hour, day):
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
        style={
            "cursor": "pointer", "color":"white",
            # "background-color": "white",
            "border": "1px solid #F5F5F5",
            "text-align": "center",
            "font-size": "12px", "font-weight": "500", "min-width": "30px"
        }
    )

def create_stage_block(stage_name, rows):
    return html.Tbody([
        html.Tr([
            html.Td(row + 1, style={
                "border": "1px solid #ccc",
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
            render_cell(stage_name, row + 1, col - 2 + 1) if col >= 2 else
            None
            for col in range(2 + len(days))
        ])
        for row in range(rows)
    ], style={"border": "2px solid #ccc", "border-left": "0"})




def render_table():
    return  html.Div([
        html.Table([
            # Заголовок таблицы
            html.Thead([
                html.Tr([
                    html.Th("ЧАСЫ", rowSpan=2,
                            style={"border": "0 solid #ccc", "border-radius": "12px 0 0 0", "text-align": "center",
                                   "border-top": "0",
                                   "background-color": "", "font-size": "12px", "font-weight": "500", }),
                    html.Th("ЭТАП РАБОТЫ", rowSpan=2,
                            style={"border": "2px solid #ccc", "background-color": "", "font-size": "12px",
                                   "border-top": "0",
                                   "font-weight": "500", "text-align": "center", }),
                    html.Th("АПРЕЛЬ", colSpan=len(days),
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
                      "background-color": "white", "box-shadow": "inset 0 -1px 0 #ccc", }),
            # Секции по этапам
            *[create_stage_block(name, rows) for name, rows in stages]
        ], style={"width": "100%", "border-collapse": "collapse", "border-spacing": "0px", })
    ])


def CALENDAR():
    today = datetime.today()
    content = html.Div([
        dcc.Store(id='filled-cells', data={}),
        html.Div('КАЛЕНДАРНЫЙ ОТЧЁТ', className='name'),

        html.Div([
            dcc.Loading([
                html.Div(render_table(), ),

            ], color='grey', type='circle'),
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