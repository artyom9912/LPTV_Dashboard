import datetime
from datetime import datetime as dt
import dash_bootstrap_components as dbc
from dash import dcc, callback_context
from dash.dependencies import Input, Output, State, ALL, MATCH
# from app import appDash, calendar_cache, WEEKDAYS, engine, dbDF, cache
import db
from app import appDash, cache
import dash
from utils import get_user_picture, rgba_string_to_hex, hex_to_rgba01, month_name_ru, get_month_info
from time import sleep, time
from dash import html
from datetime import date
from logger import logger
from view_calendar import render_stage_block, all_stages
import random
import plotly.graph_objects as go
import flask_login
from datatables import UsersTable, ProjectsTable, to_css_rgba
from dash.exceptions import PreventUpdate
from PIL import Image
import io
from plotly.graph_objs import Bar, Figure, Layout
import plotly.colors as pc
import base64



# WEEK_NUMBERS = dict(zip(WEEKDAYS, range(0, 7)))
CACHE = {}

def success_emoji():
    emojis = ["😎", "🥰", "😄", "🥳"]
    return random.choice(emojis)

@appDash.callback(
    Output('USER', 'children'),
    Output('ROLE', 'children'),
    Output('UserPic', 'src'),
    Output('UserPic', 'style'),
    Output('admBtn', 'className'),
    Input('content', 'children')
)
def SetUser(style):
    try:
        user = flask_login.current_user
        return user.name, 'Администратор' if user.admin == 1 else 'Сотрудник',\
               get_user_picture(db.get_user_login(user.name)), \
               {'border':f'{rgba_string_to_hex(user.color)} 3px solid'}, \
                '' if user.admin == 1 else 'hidden'
    except Exception as e:
        logger.exception("Ошибка в SetUser: %s", str(e))
        return dash.no_update

@appDash.callback(
    Output('menu', 'className'),
    Output('main', 'className'),
    Output('miniBtnSpan', 'className'),
    Input('miniBtn', 'n_clicks'),
    State('miniBtnSpan', 'className'),
    prevent_initial_call=True
)
def change_menu_mode(clicks, classname):
    triggered = callback_context.triggered
    print(triggered)
    print(classname)
    if not triggered:
        return dash.no_update, dash.no_update, dash.no_update
    if classname == 'ico7':
        return 'mini side menu', 'side main minimain', 'ico8'
    else:
        return 'side menu', 'side main', 'ico7'


@appDash.callback(
    Output('UploadBlock', 'children'),
    Input('UploadBlock', 'children'),
    Input('ChangePic', 'n_clicks'),
    Input('UploadPhoto', 'contents', allow_optional=True),
    State('UploadPhoto', 'filename', allow_optional=True)
)
def update_photo_block(children,clicks,contents, filename):
    triggered = callback_context.triggered
    user = flask_login.current_user
    if contents is None:
        if 'ChangePic' not in triggered[0]['prop_id']:
            path = get_user_picture(user.username)
            return html.Img(
                src=path,
                style={'width': '200px', 'border-radius': '6px'}
            )

        # Показываем upload до загрузки
        return dcc.Upload(
                    id='UploadPhoto',
                    children=html.Div([
                        'Перетащи файл или ',
                        html.A('выбери на устройстве', style={'color':rgba_string_to_hex(user.color)})
                    ], style={'padding-top':'20%', 'color':'gray'}),
                    style={
                        'width': '100%',
                        'height': '200px',
                        'user-select':'none',
                        'cursor': 'pointer',
                        'borderWidth': '2px',
                        'border-color': 'gray',
                        'borderStyle': 'dashed',
                        'borderRadius': '6px',
                        'textAlign': 'center',
                        'margin-bottom': '10px'
                    },
                    multiple=False
                ),

    # Если файл загружен — обрабатываем и показываем картинку
    content_type, content_string = contents.split(',')
    decoded = base64.b64decode(content_string)

    # Обработка изображения
    image = Image.open(io.BytesIO(decoded)).convert("RGB")
    image = image.resize((200, 200))
    path = f'assets/img/users/{user.username}.png'

    buffered = io.BytesIO()
    image.save(path, format="PNG")
    image.save(buffered, format="PNG")
    CACHE['img'] ='new'
    encoded_img = base64.b64encode(buffered.getvalue()).decode()

    return html.Img(
        src=f"data:image/png;base64,{encoded_img}",
        style={ 'width': '200px', 'border-radius': '6px'}
    )

@appDash.callback(
    Output('ProjectDesk', 'children'),
    Input('RelevantFilterDesk', 'value'),
    Input('YearFilterDesk', 'value'),
)
def UpdateProjectDesk(relevant, year):
    try:
        projects = db.get_project_cards(relevant, year)
        content = [
                html.Div([
                    html.Div([project['name'], html.Div([dcc.Markdown(str(project['square']) + " m²", className='prjStage'),]),],
                             className='prjName'),

                    html.Div([
                        html.Div([project['sum_hours'], html.Span('часов', className='tail')], className='num line'),
                        html.Div([project['count_users'], html.Span('чел.', className='tail')], className='num line dim'),
                        html.Div([project['level']], className='num line last'),
                    ], className='line-wrap prjInfo', style={'background':'linear-gradient(to right, rgba(243, 243, 243, 0) 210px, #E1D2BEFF 20px)'} if project['isDone']==1 else {}),
                  ], className="archive card" if project["isDone"]==1 else "card", id={'type': 'project-card', 'id': project['id']}, ) for id, project in projects.iterrows()]
        return content
    except Exception as e:
        logger.exception("Ошибка в UpdateProjectDesk: %s", str(e))
        return dash.no_update

@appDash.callback(
    Output('selected-project-id', 'data'),
    Input({'type': 'project-card', 'id': ALL}, 'n_clicks'),
    Input('RelevantFilterDesk', 'value'),
    Input('YearFilterDesk', 'value'),
    State({'type': 'project-card', 'id': ALL}, 'id'),
    prevent_initial_call=True
)
def store_selected_card(n_clicks_list,relevant, year, ids):
    triggered = callback_context.triggered
    if not triggered:
        return dash.no_update
    if 'RelevantFilterDesk' in triggered[0]['prop_id'] or 'YearFilterDesk' in triggered[0]['prop_id']:
        return None

    prop_id = triggered[0]['prop_id'].split('.')[0]
    try:
        import json
        parsed = json.loads(prop_id)
        clicked_id = parsed['id']
    except Exception:
        return dash.no_update

    # Важный момент — проверяем, был ли клик (n_clicks > 0)
    index = ids.index(parsed)
    if n_clicks_list[index] and n_clicks_list[index] > 0:
        return clicked_id

    return dash.no_update

@appDash.callback(
    Output({'type': 'project-card', 'id': ALL}, 'style'),
    Output('ProjectInfo', 'className'),
    Input('selected-project-id', 'data'),
    State({'type': 'project-card', 'id': ALL}, 'id'),
    prevent_initial_call=True
)
def highlight_selected_card(selected_id, all_ids):
    if selected_id is None:
        return [{} for _ in all_ids], 'cloud filter hidden'

    color = to_css_rgba(flask_login.current_user.color)
    selected_style = {
        'border-color': '#343434',
        'border-width': '3px',
        # 'background-color': color,
        'background-image': 'url("assets/img/prjActive1.png")',
        # 'box-shadow': f'0 0 0 2px {color}'
    }
    default_style = {}


    return [
        selected_style if id_['id'] == selected_id else default_style
        for id_ in all_ids
    ], 'cloud filter'


@appDash.callback(
    Output('MonthFilter', 'disabled'),
    Output('DayFilter', 'disabled'),
    Input('MonthFilter', 'value'),
    Input('YearFilter', 'value'),
    prevent_initial_call=True
)
def update_db( month, year):
    if year is not None:
        if month is not None:
            return False, False
        else:
            return False, True
    else:
        return False, False


@appDash.callback(
    Output('UserFilter', 'value'),
    Output('ProjectFilter', 'value'),
    Output('StageFilter', 'value'),
    Output('DayFilter', 'value'),
    Output('MonthFilter', 'value'),
    Output('YearFilter', 'value'),
    Output('SquareFilter', 'value'),
    Input('refresh', 'n_clicks'),
    prevent_initial_call=True
)
def clean_filter(n_clicks):
    return None, None, None, None, None, None, None


@appDash.callback(
    Output('tabs-content', 'children'),
    Input('tabs', 'value'))
def render_content(tab):
    try:
        match tab:
            case 'tab-c':
                return html.Div([
                    UsersTable()
                ], className='db')
            case 'tab-p':
                return html.Div([
                    ProjectsTable()
                ], className='db')
    except Exception as e:
        logger.exception("Ошибка в render_content: %s", str(e))
        return dash.no_update


@appDash.callback(
    Output('ConfirmDelete', 'displayed'),
    Output('ConfirmDelete', 'message'),
    Input('ModalDelete', 'n_clicks'),
    prevent_initial_call=True
)
def show_confirm(n_clicks):
    if n_clicks:
        return True, 'Вы уверены? Все связанные записи также безвозвратно удалятся!'
    return dash.no_update



def get_calendar_body_cached(project_id, year, month, num_days, user_work_data):

    deadlines = db.get_project_stages(project_id)
    print(user_work_data)
    # stages = [stage] if stage else all_stages
    return sum([
        [
            render_stage_block(name, deadline, year, month, user_work_data, num_days),
        ] for name, deadline in dict(zip(all_stages, deadlines)).items()
    ], [])

@appDash.callback(
    Output({"type": "stage-block", "stage": ALL}, "className"),
    Input("StageFilterCal", "value"),
    prevent_initial_call=True
)
def filter_stages(selected_stage):
    print(selected_stage)
    if not selected_stage or selected_stage == 0:
        # Показываем все этапы
        return ["" for _ in all_stages]

    return [
        "" if stage == selected_stage else "hidden-stage"
        for stage in all_stages
    ]

def style_day_cells(year, month, num_days, weekends):

    base_style = {
        "min-width": "30px", "font-weight": "400", "font-size": "12px",
        "border": "1px solid #EDEDED", "border-bottom": "1px solid #ccc",
        "text-align": "center", "padding": "4px", "height": "30px"
    }

    styles = []
    for day in range(1,32):
        day_style = base_style.copy()
        day_style["background-color"] = "#EEEEEE" if day in weekends else "white"
        day_style["border-right"] = "1px #E4E4E4 solid" if day in weekends else "1px #EDEDED solid"
        day_style["display"] = "none" if day > num_days else "block"
        styles.append(day_style)

    return styles


@appDash.callback(
    Output('CalendarBody', 'children'),
    Output('CalendarTitle', 'children'),
    Output('CalendarMonth', 'children'),
    Output({"type": "day-cell", "day": ALL}, 'style'),
    Output('UserList', 'children'),
    Input('ProjectFilterCal', 'value'),
    Input('YearFilterCal', 'value'),
    Input('MonthFilterCal', 'value')

)
def update_calendar_body(project_id, year, month):
    user_work_data = db.get_user_work_data(project_id, year, month)
    num_days, weekends = get_month_info(month, year)
    title = [html.Span('КАЛЕНДАРЬ ', style={"font-family": '"Futura PT Medium", monospace'}),
             db.get_project_name(project_id).upper()]
    userlines = db.get_user_legend(project_id,year,month)

    userlist = [html.Div([html.Span([], style={'background-color':rgba_string_to_hex(line['color']), 'border-radius':'50px','padding':'2px 4px', 'margin-right':'10px'})
                             ,line['name']],style={'margin-bottom':'8px'}) for line in userlines] if len(userlines)>0 else [html.Div([html.Span([], style={'background-color':'lightgray', 'border-radius':'50px','padding':'2px 4px', 'margin-right':'10px'}),'Нет данных'],style={'margin-bottom':'8px'})]
    return get_calendar_body_cached(project_id, year, month, num_days, user_work_data), title, month_name_ru(month).upper(), style_day_cells(year, month, num_days, weekends), userlist

@appDash.callback(
    Output({"type": "calendar-cell", "stage": MATCH, "day": MATCH, "hour": ALL, "month": MATCH, "year": MATCH }, "style"),
    Input({"type": "calendar-cell", "stage": MATCH, "hour": ALL, "day": MATCH,  "month": MATCH, "year": MATCH}, "n_clicks"),
    State({"type": "calendar-cell", "stage": MATCH, "hour": ALL, "day": MATCH,  "month": MATCH, "year": MATCH}, "id"),
    State("ProjectFilterCal", "value"),
    State("YearFilterCal", "value"),
    State("MonthFilterCal", "value"),
    State("DeleteMode", "value"),
    prevent_initial_call=True
)
def update_cell_styles(n_clicks, cell_ids, project_id, year, month, delete_mode):
    triggered = callback_context.triggered_id
    if not triggered:
        raise dash.exceptions.PreventUpdate


    user_id = flask_login.current_user.id
    user_color = rgba_string_to_hex(flask_login.current_user.color)

    selected_stage = triggered["stage"]
    selected_day = triggered["day"]
    selected_hour = triggered["hour"]

    # Получаем работу за месяц
    user_work_data = db.get_user_work_data(project_id, year, month)

    # Моя запись
    my_record = next((r for r in user_work_data or []
                      if r["stage"] == selected_stage and r["day"] == selected_day and r["user_id"] == user_id), None)

    my_hours = my_record["hours"] if my_record else 0

    # Чужая запись
    records = [r for r in user_work_data or []
                  if r["stage"] == selected_stage and r["day"] == selected_day and r["user_id"] != user_id]
    if len(records) > 1:
        return [dash.no_update] * 12
    other = records[0] if len(records)>0 else None

    other_hours = other["hours"] if other else 0
    other_color = other["color"] if other else None

    rows = len(cell_ids)
    styles = []

    is_delete = "delete" in (delete_mode or [])

    # === DELETE MODE ===
    if is_delete:
        if not my_record or selected_hour > my_hours:
            # чужая запись или нет моей
            return [dash.no_update] * len(cell_ids)

        for i in range(rows):
            hour = cell_ids[i]["hour"]
            style = {
                "height": "24px",
                "border": "1px solid #F7F7F7",
                "text-align": "center",
                # "cursor": "pointer",
                "font-size": "12px",
                "font-weight": "600",
                "color": "white",
                "position": "relative"
            }

            # Оставляем чужие закраски
            if other and hour <= other_hours:
                style["border"] = "1px rgba(255,255,255,0.18) solid"
                style["background-color"] = other_color
                style["color"] = other_color
                if hour == other_hours:
                    style["border-radius"] = "0 0 8px 8px"

            styles.append(style)

        return styles

    # === NORMAL MODE === (добавление/изменение записи)
    for i in range(rows):
        hour = cell_ids[i]["hour"]
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

        my_occupied = hour <= selected_hour
        other_occupied = other and hour <= other_hours

        if my_occupied and other_occupied:
            style["color"] = "rgba(255,255,255,0.05)"
            style["box-shadow"] = "inset 0 0 0 1px rgba(255,255,255,0.1)"
            style["border"] = "none"
            style["background"] = f"linear-gradient(to right, {user_color} 50%, {other_color} 50%)"

            if selected_hour == other_hours and hour == selected_hour:
                style["border-radius"] = "0 0 8px 8px"

        elif my_occupied:
            style["background-color"] = user_color
            style["color"] = user_color
            style["border"] = "1px rgba(255,255,255,0.18) solid"
            if hour == selected_hour:
                style["border-radius"] = "0 0 8px 8px"

        elif other_occupied:
            style["border"] = "1px rgba(255,255,255,0.18) solid"
            style["background-color"] = other_color
            style["color"] = other_color
            if hour == other_hours:
                style["border-radius"] = "0 0 8px 8px"

        styles.append(style)
        print(len(styles))

    return styles


@appDash.callback(
    Output('popupCal', 'children'),
    Input({"type": "calendar-cell", "stage": ALL, "hour": ALL, "day": ALL, "month": ALL, "year": ALL }, "n_clicks_timestamp"),
    State({"type": "calendar-cell", "stage": ALL, "hour": ALL, "day": ALL, "month": ALL, "year": ALL }, "id"),
    State("ProjectFilterCal", "value"),
    State("YearFilterCal", "value"),
    State("MonthFilterCal", "value"),
    State("DeleteMode", "value"),
    prevent_initial_call=True
)
def handle_cell_click(timestamps, ids, project_id, year, month, delete_mode):
    try:
        if not timestamps or all(ts is None for ts in timestamps):
            return dash.no_update

        # Найди последнюю кликнутую ячейку
        latest_idx = max(
            ((i, ts) for i, ts in enumerate(timestamps) if ts is not None),
            key=lambda x: x[1]
        )[0]
        triggered = ids[latest_idx]
        stageId = all_stages.index(triggered["stage"]) + 1
        user_id = flask_login.current_user.id

        if 'delete' in delete_mode:

            success = db.delete_work_record(
                user_id,
                project_id,
                stageId,
                triggered["day"],
                triggered["hour"],
                year,
                month
            )
            if not success:
                return dash.no_update
            else:
                return [
                    html.Div(
                        [html.Span("✂️", className='symbol emoji'), 'Запись удалена'],
                        className='cloud line popup green',
                        hidden=False
                    )
                ]

        success = db.insert_or_update_record(
            user_id,
            project_id,
            stageId,
            triggered["day"],
            triggered["hour"],
            year,
            month
        )

        if not success:
            return [
                html.Div(
                    [html.Span("⚠️", className='symbol emoji'), 'День уже занят'],
                    className='cloud line popup orange',
                    hidden=False
                )
            ]

        return [
            html.Div(
                [html.Span(success_emoji(), className='symbol emoji'), 'Запись сохранена'],
                className='cloud line popup green',
                hidden=False
            )
        ]

    except Exception as e:
        logger.exception("Ошибка при обработке нажатия в календаре: %s", str(e))
        return [
            html.Div(
                [html.Span("❌", className='symbol emoji'), 'Необработанная ошибка!'],
                className='cloud line popup red',
                hidden=False
            )
        ]



@appDash.callback(
    Output('delete-switch','className'),
    Output('Calendar','className'),
    Input('DeleteMode', 'value'),
    prevent_initial_call=True
)
def DeleteMode(delete_mode):
    if 'delete' in delete_mode:
        return 'red cloud', 'delete-mode'
    else: return 'cloud', ''

@appDash.callback(
    Output('DeleteMode', 'value'),
    Input('key-listener', 'n_events'),
    State('key-listener', 'event'),
    State('DeleteMode', 'value'),
    prevent_initial_call=True
)
def toggle_delete_mode_by_ctrl(n, event, current_val):
    if event and event.get('ctrlKey'):
        # Если уже включено — выключим, иначе включим
        return [] if 'delete' in current_val else ['delete']
    return dash.no_update

@appDash.callback(
    Output('BigTitle','children'),
    Input('FilterGraph', 'value'),
    State('GraphMode', 'data'),
)
def update_graph_title(id, is_project):
    return [html.Span('ГРАФИК ', style={"font-family":'"Futura PT Medium", monospace'}),db.get_project_name(id) if is_project else db.get_user_name(id).upper()]

@appDash.callback(
    Output('YearFilterGraph', 'value'),
    Output('MonthFilterGraph', 'value'),
    Input('RefreshGraph','n_clicks'),
    prevent_initial_call=True
)
def update_graph_filters(click):
    if click:
        today = datetime.datetime.now()
        return today.year, today.month
    return dash.no_update, dash.no_update

@appDash.callback(
    Output('YearFilterCal', 'value'),
    Output('MonthFilterCal', 'value'),
    Output('StageFilterCal', 'value'),
    Input('RefreshCal','n_clicks'),
    State('YearFilterCal', 'value'),
    State('MonthFilterCal', 'value'),
    State('StageFilterCal', 'value'),
    prevent_initial_call=True
)
def update_cal_filters(click, year, month, stage):
    today = datetime.datetime.now()
    if year != today.year or month != today.month or stage is not None:
        if click:
            today = datetime.datetime.now()
            return today.year, today.month, None
    return dash.no_update, dash.no_update, dash.no_update
@appDash.callback(
    Output('Graph','figure'),
    Output('GraphTable','data'),
    Output('GraphTable','columns'),
    Output('GraphTable','style_header_conditional'),
    Input('FilterGraph', 'value'),
    Input('YearFilterGraph', 'value'),
    Input('MonthFilterGraph', 'value'),
    State('GraphMode', 'data'),
    # prevent_initial_call=True

)
def update_graph(id, year, month, is_project):
    raw_data = db.get_lines_users(project_id=id, month=month, year=year) if is_project else db.get_lines_projects(user_id=id, month=month, year=year)
    num_days, weekends = get_month_info(month, year)

    palette = ["#66C2A5", "#FC8D62", "#8DA0CB", "#E78AC3", "#A6D854", "#FFD92F", "#E5C494", "#B3B3B3"]


    table_data, table_columns = db.get_graph_project_data(project_id=id, month=month, year=year) if is_project else db.get_graph_user_data(user_id=id, month=month, year=year)

    if not is_project:
        table_columns[0] = {'name': 'Проект', 'id': 'index'}
        project_names = sorted(raw_data.keys())
        color_map = {name: palette[i % len(palette)] for i, name in enumerate(project_names)}
    else:
        table_columns[0] = {'name': 'Этап', 'id': 'index'}
        color_map = {
            name: rgba_string_to_hex(data.get('color')) or "#000000"
            for name, data in raw_data.items()
        }
        print(color_map)
    style_header_conditional = [
        {
            "if": {"column_id": name},
            "backgroundColor": color,
            "color": "black",
            "min-width":"75px",


        }
        for name, color in color_map.items()
    ]

    traces = []

    for name, item_info in raw_data.items():
        day_hours = item_info['data']
        color = color_map.get(name, '#000000')

        if not day_hours:
            continue

        sorted_days = sorted(day_hours.items())
        full_x = []
        full_y = []

        for i in range(len(sorted_days)):
            day, hours = sorted_days[i]
            full_x.append(day)
            full_y.append(hours)

            # проверка на разрыв
            if i + 1 < len(sorted_days):
                next_day = sorted_days[i + 1][0]
                if next_day - day > 1:
                    # вставляем разрыв
                    full_x.append(None)
                    full_y.append(None)

        traces.append(go.Scatter(
            x=full_x,
            y=full_y,
            mode='lines+markers',
            name=name,
            line=dict(color=color, width=4),
            marker=dict(size=6)
        ))

    fig = go.Figure(data=traces)
    fig.update_layout(
        font=dict(family="Rubik, sans-serif", size=14, color="black"),
        title=f'{month_name_ru(month)} {year}' if year else 'Нет данных',
        xaxis=dict(title='', dtick=1, range=[0, num_days+0.2] if month else [0,12]),
        yaxis=dict(title='', range=[0, 12] ) if month else dict(autorange=True, fixedrange=False),
        plot_bgcolor='#fff',
        paper_bgcolor='#fff',
        autosize=True,
        legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1),
        margin=dict(l=10, r=10, t=50, b=20),
    )
    fig.layout.xaxis.fixedrange = True
    fig.layout.yaxis.fixedrange = True

    fig.update_xaxes(
        ticks='outside', ticklen=5, tickwidth=2, tickcolor='#EBEBEB',
        showline=True, linewidth=2, linecolor='#EBEBEB', showgrid=True
    )
    fig.update_yaxes(
        ticks='outside', ticklen=5, tickwidth=2, tickcolor='#EBEBEB',
        showline=True, linewidth=2, linecolor='#EBEBEB', showgrid=True
    )
    return fig, table_data, table_columns, style_header_conditional

@cache.memoize()
def get_raw_data_cached(page_current, page_size, relevant):
    return db.get_db_chunk(page_current, page_size, relevant)

@cache.memoize()
def get_filtered_data_cached(select, group_by, filters, join, order_by):
    return db.get_filtered_data(
        select=select,
        group_by=group_by,
        filters=filters,
        join=join,
        order_by=order_by
    )

@appDash.callback(
    Output("TableDB", "data"),
    Output("TableDB", "columns"),
    Output("TableDB", "page_size"),
    Output("TableDB", "page_action"),
    Output("RowCount", "children"),
    Input("TableDB", "page_current"),
    Input("TableDB", "page_size"),
    Input('UserFilter', 'value'),
    Input('ProjectFilter', 'value'),
    Input('SquareFilter', 'value'),
    Input('StageFilter', 'value'),
    Input('DayFilter', 'value'),
    Input('MonthFilter', 'value'),
    Input('YearFilter', 'value'),
    Input('RelevantFilter', 'value'),
)
def update_table(page_current, page_size, user, project, square, stage, day, month, year, relevant):
    try:
        HEAD_MAP = {
            'year': 'ГОД',
            'month': 'ММ',
            'day': 'ДД',
            'user': 'СОТРУДНИК',
            'project': 'ПРОЕКТ',
            'stage': 'ЭТАП',
            'square': 'м²',
            'hours': 'ЧАСЫ'
        }

        field_map = {
            'year': [year, 'YEAR(dateStamp) year', None, 'YEAR(dateStamp)'],
            'month': [month,'MONTH(dateStamp) month', None, 'MONTH(dateStamp)'],
            'day': [day,'DAY(dateStamp) day', None, 'DAY(dateStamp)'],
            'relevant': [None if relevant is None else not relevant, None, 'JOIN project p ON main.projectId=p.id\n', 'p.isDone'],
            'user': [user, 'u.name user', 'JOIN user u ON main.userId=u.id\n', 'u.name'],
            'project': [project, 'p.name project', 'JOIN project p ON main.projectId=p.id\n', 'p.name'],
            'square': [square, 'p.square square', 'JOIN project p ON main.projectId=p.id\n', 'p.square'],
            'stage': [stage, 's.name stage', 'JOIN stage s ON main.stageId=s.id\n', 's.name'],
        }


        # Если ни один фильтр не выбран — показать "сырые" данные
        if all(v[0] is None for k, v in field_map.items() if k != 'relevant'):
            data, columns = get_raw_data_cached(page_current, page_size, relevant)
            page_size = 40
            page_action = 'custom'
            count = db.get_main_count(relevant)


        else:
            page_size = 250
            page_action = 'native'
            print('isDONE')
            print(relevant)
            # Фильтрация и группировка по выбранным
            select_keys = [field_map[k][1] for k, v in field_map.items() if v[0] is not None and v[1] is not None]
            group_by_keys = [k for k, v in field_map.items() if v[0] is not None and k != 'relevant']
            filters = [
                f"{field_map[k][-1]} = {v[0] if k == 'relevant' else repr(v[0])}"
                for k, v in field_map.items()
                if v[0] is not None and v[0] != 'Все'
            ]
            joins = [field_map[k][2] for k, v in field_map.items() if v[0] is not None and v[2] is not None]
            order = [k+" DESC" for k, v in list(field_map.items())[:3] if v[0] is not None]

            select_clause = ', '.join(select_keys)
            where_clause = " AND ".join(filters) if filters else "1=1"
            join_clause = ''.join(list(set(joins))) if len(joins) > 0 else ''
            group_by_clause = ', '.join(group_by_keys)
            order_by_clause = ', '.join(order)
            order_by_clause+= ',' if len(order_by_clause) > 0 else ''
            data, columns = get_filtered_data_cached(select_clause, group_by_clause, where_clause, join_clause, order_by_clause)
            count = len(data)

        # Формирование колонок таблицы
        column_defs = [{"name": HEAD_MAP.get(col, col.upper()), "id": col} for col in columns]
        return data, column_defs, page_size, page_action, [count, html.Span('кол. строк', className='tail')]

    except Exception as e:
        logger.exception("Ошибка в update_table: %s", str(e))
        return [], [], 20, 'native', ["Ошибка загрузки", html.Span("⚠", className="tail")]

@appDash.callback(
    Output('DialogModal', 'children'),
    Output('DialogModal', 'is_open'),
    [State("tabs", "value"),
     State("AdmTable", "derived_virtual_selected_row_ids")],
    [Input('EditButton', 'n_clicks'),
     Input('AddButton', 'n_clicks'),
     Input('ModalSubmit', 'n_clicks'),
     Input('ModalDelete', 'n_clicks')],
    prevent_initial_call=True
)
def RenderModal(tab, row, clickE, clickA, clickS, clickD):
    try:
        changed_id = dash.callback_context.triggered[0]['prop_id']
        UPDATE_DICT = 'EditButton' in changed_id
        Open = 'EditButton' in changed_id or 'AddButton' in changed_id

        if 'ModalSubmit' in changed_id or 'ModalDelete' in changed_id:
            return dash.no_update, False

        CACHE.clear()
        id = row[0] if row else None
        CACHE['id'] = id

        if tab == 'tab-c':
            if UPDATE_DICT:
                u = db.get_user_full(id)
                user_data = dict(
                    Title=u[1].upper(),
                    Span=f'ID: {id}',
                    UserName=u[1],
                    UserLogin=u[2],
                    UserRole=u[3],
                    UserActual=u[4],
                    UserColor=u[5],
                    UserPass=u[6]
                )
            else:
                user_data = dict(
                    Title='НОВЫЙ ЮЗЕР',
                    Span='',
                    UserName=None,
                    UserLogin=None,
                    UserPass=None,
                    UserRole=0,
                    UserActual=1,
                    UserColor='0.3,0.3,0.3,1'
                )


            modal = [
                dbc.ModalHeader(
                    [user_data['Title'], html.Span(user_data['Span'], style=dict(fontFamily='"Noah Regular", monospace', marginLeft=6, fontSize=18))],
                    id='ModalHead', style={'background-color': to_css_rgba(user_data['UserColor'])}
                ),
                dbc.ModalBody([
                    dbc.Row([
                        dbc.Col([
                            dbc.Label("Имя", style={'margin-bottom': 0, 'color': '#999'}),
                            dcc.Input(id='UserName', placeholder='Имя сотрудника', className='inp', value=user_data['UserName']),
                            dbc.Label("Логин", style={'margin-bottom': 0, 'color': '#999'}),
                            dcc.Input(id='UserLogin', placeholder='Логин', className='inp', value=user_data['UserLogin']),
                            dbc.Label("Пароль", style={'margin-bottom': 0, 'color': '#999'}),
                            dcc.Input(id='UserPass', placeholder='Пароль', className='inp', value=user_data['UserPass']),
                        ], width=6),
                        dbc.Col([
                            dbc.Label("Фото", style={'margin-bottom': 0, 'color': '#999'}),
                            html.Img(src=get_user_picture(user_data['UserLogin']), style={'height': '200px', 'border-radius': '6px'}),
                        ], width=6)
                    ], className="gx-5"),
                    dbc.Row([
                        dbc.Col([
                            dbc.Label("Роль"),
                            dcc.Tabs(
                                id='UserRole',
                                value='tab-admin' if user_data['UserRole'] else 'tab-user',
                                children=[
                                    dcc.Tab(label='Юзер', value='tab-user', className='custom-tab switch', selected_className='custom-tab--selected switch_selected'),
                                    dcc.Tab(label='Админ', value='tab-admin', className='custom-tab switch', selected_className='custom-tab--selected switch_selected')
                                ],
                                parent_className='role_switch',
                                className='custom-tabs-container'
                            )
                        ], width=6),
                        dbc.Col([
                            dbc.Label("Цвет"),
                            dbc.Input(
                                type="color",
                                id="UserColor",
                                value=rgba_string_to_hex(user_data['UserColor']),
                                className='colorpicker'
                            )
                        ], width=6)
                    ], className="gx-5"),
                    dcc.Checklist(id='UserActual', className='check', options=[{'label': 'Актуальный', 'value': '1'}],
                                  value=f'{user_data["UserActual"]}', style={'width': '170px'})
                ], style={'paddingLeft': 16}),
                dbc.ModalFooter([
                    dbc.Button("🗑️ Удалить", id="ModalDelete", className="button cloud delete",
                               style={'visibility': 'visible' if UPDATE_DICT else 'hidden'}),
                    dbc.Button("Сохранить", id="ModalSubmit", className="button cloud submit")
                ])
            ]
            return modal, Open

        elif tab == 'tab-p':
            today = date.today().strftime('%Y-%m-%d')
            if UPDATE_DICT:
                p = db.get_project_full(id)
                stages = db.get_project_stages(id)
                prj_data = dict(
                    Title=p[1],
                    Span=f'ID: {id}',
                    PrjName=p[1],
                    PrjSqr=p[2],
                    PrjLvl=p[3],
                    PrjStart=p[4],
                    PrjDone=p[5],
                    stages=stages
                )
            else:
                prj_data = dict(
                    Title='НОВЫЙ ПРОЕКТ',
                    Span='',
                    PrjName=None,
                    PrjSqr=None,
                    PrjStart=today,
                    PrjLvl=1,
                    PrjDone=0,
                    stages=[None] * 6
                )

            def generate_stage_rows(stages, today):
                stage_data = [
                    ("1. Подготовка", 'StageDate1', stages[0]),
                    ("2. 3D Графика", 'StageDate2', stages[1]),
                    ("3. Заказные позиции", 'StageDate3', stages[2]),
                    ("4. СМР", 'StageDate4', stages[3]),
                    ("5. Комплектация", 'StageDate5', stages[4]),
                    ("6. Реализация", 'StageDate6', stages[5]),
                ]

                rows = []
                for i in range(0, len(stage_data), 2):
                    row = dbc.Row([
                        dbc.Col([
                            html.Label(stage_data[i][0], className='d-table',
                                       style={'margin-bottom': '0', 'color': '#999999'}),
                            dcc.DatePickerSingle(
                                id=stage_data[i][1],
                                initial_visible_month=today,
                                display_format='YYYY-MM-DD',
                                placeholder='Дата дедлайна',
                                style={'text-align': 'left'},
                                date=stage_data[i][2],

                            )
                        ], width=6),
                        dbc.Col([
                            html.Label(stage_data[i + 1][0], className='d-table',
                                       style={'margin-bottom': '0', 'color': '#999999'}),
                            dcc.DatePickerSingle(
                                id=stage_data[i + 1][1],
                                initial_visible_month=today,
                                display_format='YYYY-MM-DD',
                                placeholder='Дата дедлайна',
                                style={'text-align': 'left'},
                                date=stage_data[i + 1][2]
                            )
                        ], width=6)
                    ], className="gx-3", style={'margin-bottom': '8px' if i < 4 else '24px'})
                    rows.append(row)
                return rows

            modal = [
                dbc.ModalHeader([prj_data['Title'], html.Span(prj_data['Span'], style=dict(color='lightgray',
                                                                                           fontFamily='"Noah Regular", monospace',
                                                                                           marginLeft=6, fontSize=18))],
                                id='ModalHead'),
                dbc.ModalBody([
                    dbc.Row([dbc.Col([
                        dbc.Label("Название проекта", style={'margin-top': '12px'}),
                        dbc.Input(id='PrjName', placeholder='Введите название', className='inp long',
                                  value=prj_data['PrjName'], required=True)
                    ], width=6)]),
                    dbc.Row([
                        dbc.Col([
                            dbc.Label("Дата начала", style={'color': '#999'}),
                            dcc.Input(id='PrjStart', placeholder='Дата', className='inp', value=prj_data['PrjStart'])
                        ], width=6),
                        dbc.Col([
                            dbc.Label("Площадь", style={'color': '#999'}),
                            dcc.Input(id='PrjSqr', placeholder='м²', className='inp short', value=prj_data['PrjSqr'])
                        ], width=6)
                    ]),
                    dbc.Label("Стадии проекта", style={'margin-top': '14px'}),
                    dbc.Row([dbc.Col(generate_stage_rows(prj_data['stages'], today))]),
                    dbc.Label("Уровень важности"),
                    dcc.Slider(id="PrjLvl", min=1, max=5, step=1, value=prj_data['PrjLvl'],
                               marks={i: str(i) for i in range(1, 6)}),
                    dcc.Checklist(id='PrjActual', className='check',
                                  options=[{'label': 'Закончен', 'value': '1'}],
                                  value=f'{prj_data["PrjDone"]}')
                ], style={'paddingLeft': 16}),
                dbc.ModalFooter([
                    dbc.Button("🗑️ Удалить", id="ModalDelete", className="button cloud delete",
                               style={'visibility': 'visible' if UPDATE_DICT else 'hidden'}),
                    dbc.Button("Сохранить", id="ModalSubmit", className="button cloud submit")
                ])
            ]

            return modal, Open

        raise PreventUpdate

    except Exception as e:
        logger.exception("Ошибка в RenderModal: %s", str(e))
        return dash.no_update, False


@appDash.callback(
    Output('ModalDelete', 'style'),
    [Input('PrjName', 'value')],
    [Input('PrjStart', 'value')],
    [Input('PrjSqr', 'value')],
    [Input('PrjLvl', 'value')],
    [Input('PrjActual', 'value')],
    [Input('StageDate1', 'date')],
    [Input('StageDate2', 'date')],
    [Input('StageDate3', 'date')],
    [Input('StageDate4', 'date')],
    [Input('StageDate5', 'date')],
    [Input('StageDate6', 'date')],
    prevent_initial_call=True
)
def ProjectChanges(PrjName, PrjStart, PrjSqr, PrjLvl, PrjDone,
                StageDate1, StageDate2, StageDate3, StageDate4, StageDate5, StageDate6):
    try:
        changed_id = dash.callback_context.triggered[0]['prop_id']
        info_fields = {
            'PrjName': PrjName,
            'PrjStart': PrjStart,
            'PrjSqr': PrjSqr,
            'PrjLvl': PrjLvl,
        }

        for key, value in info_fields.items():
            if key in changed_id:
                CACHE[key] = f"'{value}'"
                CACHE['info'] = True
                break

        if 'PrjActual' in changed_id:
            CACHE['PrjDone'] = 1 if '1' in PrjDone else 0
            CACHE['info'] = True

        for i in range(1, 7):
            stage_key = f'StageDate{i}'
            if stage_key in changed_id:
                date_value = locals()[stage_key]
                CACHE[stage_key] = f"'{date_value}'"
                CACHE['stages'] = True
                break
        return dash.no_update

    except Exception as e:
        logger.exception("Ошибка в ProjectChanges: %s", str(e))
        return dash.no_update

@appDash.callback(
    Output('popupCab', 'style'),
    [Input('UserNameCab', 'value')],
    [Input('UserLoginCab', 'value')],
    [Input('UserPassCab', 'value')],
    [Input('UserColorCab', 'value')],
    prevent_initial_call=True
)
def UserChangesCab(UserName, UserLogin, UserPass, UserColor):
    try:
        changed_id = [p['prop_id'] for p in dash.callback_context.triggered][0]
        if 'UserName' in changed_id:
            CACHE['UserName'] = f"{UserName}"
        elif 'UserLogin' in changed_id:
            CACHE['UserLogin'] = f"{UserLogin}"
        elif 'UserPass' in changed_id:
            CACHE['UserPass'] = f"{UserPass}"
        elif 'UserColor' in changed_id:
            CACHE['UserColor'] = hex_to_rgba01(UserColor)
        return dash.no_update
    except Exception as e:
        logger.exception("Ошибка в UserChangesCab: %s", str(e))
        return dash.no_update

@appDash.callback(
    Output('popupCab', 'children'),
    [Input('CabinetSubmit', 'n_clicks')],
    [State('popupCab', 'children')],
    prevent_initial_call=True
)
def UpdateUser(n_clicks1, old):

    triggered = dash.callback_context.triggered
    if not triggered or triggered[0]['value'] is None:
        return dash.no_update

    if not n_clicks1:
        return dash.no_update

    if len(CACHE) == 0:
        return dash.no_update

    try:
        db.execute_user_queries(CACHE, flask_login.current_user.id, 'update')

    except Exception as e:
        logger.exception(f"Ошибка при обновлении User: {e}")
        CACHE.clear()
        return old + [html.Div([html.Span('😧', className='symbol emoji'), 'Ошибка при записи в базу'], className='cloud line popup red', hidden=False)]

    CACHE.clear()

    return old + [html.Div([html.Span('💾', className='symbol emoji'), 'Данные обновлены'], className='cloud line popup green', hidden=False)]


@appDash.callback(
    Output('popupAdm', 'style'),
    [Input('UserName', 'value')],
    [Input('UserLogin', 'value')],
    [Input('UserPass', 'value')],
    [Input('UserRole', 'value')],
    [Input('UserActual', 'value')],
    [Input('UserColor', 'value')],
    prevent_initial_call=True
)
def UserChanges(UserName, UserLogin, UserPass, UserRole, UserActual, UserColor):
    try:
        changed_id = [p['prop_id'] for p in dash.callback_context.triggered][0]
        if 'UserName' in changed_id:
            CACHE['UserName'] = f"{UserName}"
        elif 'UserLogin' in changed_id:
            CACHE['UserLogin'] = f"{UserLogin}"
        elif 'UserPass' in changed_id:
            CACHE['UserPass'] = f"{UserPass}"
        elif 'UserRole' in changed_id:
            CACHE['UserRole'] = UserRole
        elif 'UserColor' in changed_id:
            CACHE['UserColor'] = hex_to_rgba01(UserColor)
        elif 'UserActual' in changed_id:
            CACHE['UserActual'] = 1 if '1' in UserActual else 0
        return dash.no_update
    except Exception as e:
        logger.exception("Ошибка в UserChanges: %s", str(e))
        return dash.no_update

@appDash.callback(
    Output('popupAdm', 'children'),
    [Input('ModalSubmit', 'n_clicks'),
     Input('ConfirmDelete', 'submit_n_clicks')],
    [State('popupAdm', 'children'),
     State('ModalHead', 'children'),
     State("tabs", "value")],
    prevent_initial_call=True
)
def UpdateDict(n_clicks1, n_clicks2, old, head, tab):
    triggered = dash.callback_context.triggered
    if not triggered or triggered[0]['value'] is None:
        return dash.no_update

    if not n_clicks1 and not n_clicks2:
        return dash.no_update

    changed_id = [p['prop_id'] for p in dash.callback_context.triggered][0]

    if 'ModalSubmit' in changed_id and ('новый юзер' in head[0].lower() or 'новый проект' in head[0].lower()):
        mode = 'insert'
    elif 'ConfirmDelete' in changed_id:
        mode = 'delete'
    elif 'ModalSubmit' in changed_id:
        mode = 'update'
    else:
        return dash.no_update

    item_id = CACHE.pop('id', None)

    # ВАЛИДАЦИЯ ПОЛЕЙ ПРИ ДОБАВЛЕНИИ
    if mode == 'insert':
        if tab == 'tab-c':
            # для пользователя
            required_fields = ['UserName', 'UserLogin', 'UserPass']
            missing = [f for f in required_fields if not CACHE.get(f)]
            if missing:
                return old + [html.Div(
                    [html.Span('⚠️', className='symbol emoji'), f"Заполните все поля!"],
                    className='cloud line popup orange'
                )]
        elif tab == 'tab-p':
            # для проекта
            required_fields = ['PrjName', 'PrjStart', 'PrjSqr']
            missing = [f for f in required_fields if not CACHE.get(f)]
            if missing:
                return old + [html.Div(
                    [html.Span('⚠️', className='symbol emoji'), f"Заполните все поля!"],
                    className='cloud line popup orange'
                )]

    try:
        if tab == 'tab-c':
            db.execute_user_queries(CACHE, item_id, mode)
        elif tab == 'tab-p':
            db.execute_project_queries(CACHE, item_id, mode)
        else:
            raise ValueError(f"Неизвестная вкладка: {tab}")
    except Exception as e:
        logger.exception(f"Ошибка при выполнении SQL: {e}")
        CACHE.clear()
        return old + [html.Div([html.Span('😧', className='symbol emoji'), 'Ошибка при записи в базу'], className='cloud line popup orange')]

    CACHE.clear()

    msg = {
        'insert': [success_emoji(), "Данные добавлены!"],
        'update': [success_emoji(), "Данные обновлены!"],
        'delete': ["✂️", "Успешно удалено!"],
    }[mode]

    return old + [html.Div([html.Span(msg[0], className='symbol emoji'), msg[1]], className='cloud line popup green')]

@appDash.callback(
    Output('GraphGantt', 'figure'),
    Input('YearFilterGantt', 'value'),
    Input('RelevantFilterGantt', 'value'),
    Input('PaletteFilterGantt', 'value'),
)
def update_gantt_chart(year, relevance, palette_name):
    gantt_data = db.get_gantt_data(year, relevance)
    num_projects = len(gantt_data)

    # Базовая высота на проект
    base_height_per_project = 40
    calculated_height = min(720, max(300, num_projects * base_height_per_project))

    # Выбираем палитру
    colorscale = getattr(pc.sequential, palette_name, pc.sequential.Aggrnyl)
    colors = [pc.sample_colorscale(colorscale, i / max(num_projects - 1, 1)) for i in range(num_projects)]

    bars = []
    for idx, proj in enumerate(gantt_data):
        duration = proj['end'] - proj['start']
        bars.append(Bar(
            x=[duration if duration != 0 else 0.2],
            y=[proj['name']],
            base=[proj['start']],
            orientation='h',
            name=proj['name'],
            marker=dict(color=colors[idx % len(colors)]),
            width=0.8,
            hoverinfo='text',
            hovertext=f"{proj['name']}: {proj['start']} → {proj['end']}",
        ))

    layout = Layout(
        barmode='stack',
        xaxis=dict(
            tickmode='array',
            tick0=1,
            dtick=1,
            range=[0.9, 12.1],
            tickvals=list(range(1, 13)),
            ticktext=[month_name_ru(m) for m in range(1, 13)],
            showgrid=False,
            showline=True,
            linecolor='#E8E8E8',
            linewidth=1.6,
            ticks='outside',
            ticklen=6,
            tickcolor='#E8E8E8',
            tickwidth=1.5,
            title=None
        ),
        yaxis=dict(
            title=None,
            showgrid=False,
            automargin=True,
            tickfont=dict(size=12 if num_projects > 10 else 14)
        ),
        font=dict(
            family="Rubik, sans-serif",
            size=14,
            color="#333"
        ),
        paper_bgcolor='white',
        plot_bgcolor='white',
        margin=dict(l=120, r=30, t=20, b=40),
        height=calculated_height,
        showlegend=False
    )

    return Figure(data=bars, layout=layout)


@appDash.callback(
    Output('popupBoxAdm', 'children'),
    Input('popupAdm', 'children'),
    prevent_initial_call=True
)
def SaveAdm(ch):
    # print(ch)
    if len(ch) != 0:
        sleep(2.5)
        return html.Div([], id='popupAdm', className='line')
    else:
        return dash.no_update

@appDash.callback(
    Output('popupBoxCal', 'children'),
    Input('popupCal', 'children'),
    prevent_initial_call=True
)
def SaveAdm(ch):
    # print(ch)
    if len(ch) != 0:
        sleep(1.5)
        return html.Div([], id='popupCal', )
    else:
        return dash.no_update

@appDash.callback(
    Output('popupBoxCab', 'children'),
    Input('popupCab', 'children'),
    prevent_initial_call=True
)
def SaveAdm(ch):
    # print(ch)
    if len(ch) != 0:
        sleep(1.9)
        return html.Div([], id='popupCal', )
    else:
        return dash.no_update
