import datetime
from datetime import datetime as dt
import dash_bootstrap_components as dbc
from dash import dcc, callback_context
from dash.dependencies import Input, Output, State, ALL, MATCH
# from app import appDash, calendar_cache, WEEKDAYS, engine, dbDF, cache
import db
from app import appDash, cache
import dash
from view_calendar import render_table, create_stage_block, stages, all_stages
from utils import get_user_picture, rgba_string_to_hex, hex_to_rgba01, month_name_ru
from time import sleep
from dash import html
from datetime import date
from logger import logger
import traceback
import sys
import plotly.graph_objects as go
import flask_login
from datatables import UsersTable, ProjectsTable, to_css_rgba
from dash.exceptions import PreventUpdate




# WEEK_NUMBERS = dict(zip(WEEKDAYS, range(0, 7)))
CACHE = {}



@appDash.callback(
    Output('USER', 'children'),
    Output('ROLE', 'children'),
    Output('UserPic', 'src'),
    Input('content', 'children')
)
def SetUser(style):
    try:
        user = flask_login.current_user
        return user.name, 'Администратор' if user.admin == 1 else 'Сотрудник', get_user_picture(db.get_user_login(user.name))
    except Exception as e:
        logger.exception("Ошибка в SetUser: %s", str(e))
        return dash.no_update

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
                  ], className='card',id={'type': 'project-card', 'id': project['id']}, style={'border-color':'#E1D2BEFF'} if project['isDone']==1 else {}) for id, project in projects.iterrows()]
        return content
    except Exception as e:
        logger.exception("Ошибка в UpdateProjectDesk: %s", str(e))
        return dash.no_update

@appDash.callback(
    Output('selected-project-id', 'data'),
    Input({'type': 'project-card', 'id': ALL}, 'n_clicks'),
    State({'type': 'project-card', 'id': ALL}, 'id'),
    prevent_initial_call=True
)
def store_selected_card(n_clicks_list, ids):
    triggered = callback_context.triggered
    if not triggered:
        return dash.no_update

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
    Input('selected-project-id', 'data'),
    State({'type': 'project-card', 'id': ALL}, 'id')
)
def highlight_selected_card(selected_id, all_ids):
    if selected_id is None:
        return [{} for _ in all_ids]

    color = to_css_rgba(flask_login.current_user.color)
    selected_style = {
        'border-color': 'black',
        'background-color': color,
        # 'background-image': 'url("assets/img/prjActive1.png")',
        # 'box-shadow': f'0 0 0 2px {color}'
    }
    default_style = {}


    return [
        selected_style if id_['id'] == selected_id else default_style
        for id_ in all_ids
    ]

@cache.memoize()
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

#
#
# calendar = None
#
#
# @appDash.callback(
#     Output('Datepicker', 'date'),
#     Output('EndDate', 'children'),
#     Output('CalendarTable', 'data'),
#     Output('CalendarTable', 'columns'),
#     Output('AddProjectCal', 'value'),
#     Input('AddProjectCal', 'value'),
#     Input('Datepicker', 'date'),
# )
# def SetDatesCalendar(addProject, start_date):
#     con = engine.connect()
#     # con = connect('clickhouse://10.200.2.113')
#     try:
#         start_date = dt.strptime(start_date, '%Y-%m-%d')
#     except:
#         start_date = dt.strptime(start_date, '%Y-%m-%dT%H:%M:%S')
#     weekday = int(start_date.weekday())
#     start = start_date + datetime.timedelta(days=-1 * weekday)
#     end = start_date + datetime.timedelta(days=6 - weekday)
#     # В ЦИКЛЕ СОБИРАЕМ ВСЕ ДНИ НЕДЕЛИ
#     for i in range(0, 7):
#         day = (start + datetime.timedelta(days=i)).strftime('%Y-%m-%d')
#         # СБОР ДАННЫХ КАЛЕНДАРЯ (ПРИСОЕДИНЕНИЕ ЧЕРЕЗ WHERE)
#         df = pd.read_sql \
#             (f"""
#             SELECT title, timestamp, hours FROM skameyka.main_table m, skameyka.project_table p
#             WHERE m.timestamp = '{day}' AND user_id = (SELECT id FROM user_table WHERE fullname like '{flask_login.current_user.name}')
#             AND m.project_id = p.id;
#         """, con)
#         df = df.drop('timestamp', axis=1)
#         df.columns = ['НАЗВАНИЕ ПРОЕКТА', WEEKDAYS[i]]
#
#         if i == 0:
#             calendar = df
#         else:
#             calendar = calendar.merge(df, on='НАЗВАНИЕ ПРОЕКТА', how='outer')
#     if addProject is not None:
#         newdf = pd.DataFrame({'НАЗВАНИЕ ПРОЕКТА': [addProject], 'ПН': [None], 'ВТ': [None], 'СР': [None], 'ЧТ': [None], 'ПТ': [None], 'СБ': [None], 'ВС': [None]})
#         calendar = pd.concat([calendar,newdf])
#     columns = [{"name": i, "id": i} for i in ['НАЗВАНИЕ ПРОЕКТА'] + WEEKDAYS]
#     columns[0]['editable'] = False
#
#     return start, end.strftime('%d.%m.%Y'), calendar.to_dict('records'), columns, None
#
# @appDash.callback(
#     Output('popup', 'children'),
#     Input('CalendarSave', 'n_clicks'),
#     State('popup', 'children'),
#     prevent_initial_call=True
# )
# def SaveCalendar(n_clicks, old):
#     con = engine.connect()
#     # con = connect('clickhouse://10.200.2.113')
#     if len(calendar_cache) == 0:
#         for i in range(0, len(calendar_cache)): del calendar_cache[0]
#         return old + [
#             html.Div([html.Span('😬', className='symbol emoji'), 'Нет изменений'], className='cloud line popup white',hidden=False)]
#     try:
#         for sql in calendar_cache:
#             con.execute(text(sql))
#         con.commit()
#         for i in range(0, len(calendar_cache)): del calendar_cache[0]
#         return old + [html.Div([html.Span('✔', className='symbol'), 'Успешно сохранено'], className='cloud line popup green', hidden=False)]
#
#     except Exception as e:
#         e_type, e_val, e_tb = sys.exc_info()
#         traceback.print_exception(e_type, e_val, e_tb, file=open('log.txt', 'a'))
#         for i in range(0, len(calendar_cache)): del calendar_cache[0]
#         return old + [html.Div([html.Span('😧', className='symbol emoji'), 'Возникла ошибка!'], className='cloud line popup orange', hidden=False)]
#
#
#
# @appDash.callback(
#     Output('popupBox', 'children'),
#     Input('popup', 'children'),
#     prevent_initial_call=True
# )
# def SaveCalendar(ch):
#     if len(ch) != 0:
#         sleep(2.5)
#         return html.Div([], id='popup', className='line')
#     else:
#         dash.no_update()
#
#
# @appDash.callback(
#     Output('pie-chart', 'figure'),
#     Output('pie-chart', 'style'),
#     Input('CalendarTable', 'data'),
# )
# def UpdatePie(data):
#     global calendar
#     calendar = pd.DataFrame(data)
#     if calendar.empty:
#         style = dict(display='none')
#         return dash.no_update, style
#     else:
#         style = dict(visibility='visible')
#         calendar[WEEKDAYS] = calendar[WEEKDAYS].apply(pd.to_numeric)
#
#     # calendar.info()
#     colors = ['#393E46', '#00ADB5', '#AAD8D3', '#EEEEEE', '#8ee8e4', '#F3F4ED', '#30475E', '4CA1A3']
#     mart = calendar.fillna(0)
#
#     # print(style)
#     mart['sum'] = mart['ПН'] + mart['ВТ'] + mart['СР'] + mart['ЧТ'] + mart['ПТ'] + mart['СБ'] + mart['ВС']
#     mart = mart[['НАЗВАНИЕ ПРОЕКТА', 'sum']]
#     labels = mart['НАЗВАНИЕ ПРОЕКТА'].tolist()
#     values = mart['sum'].tolist()
#     # print(mart)
#     # print(mart.info())
#     fig = go.Figure(data=[go.Pie(labels=labels, values=values, hole=.5)])
#     fig.update_traces(automargin=False, selector=dict(type='pie'),
#                       marker=dict(colors=colors), textfont_size=12,
#                       hoverinfo='label+percent', textinfo='none')
#     fig.update_layout(
#         font_family="Roboto",
#         font_color="black",
#         font_size=16,
#         margin=dict(l=4, r=12, t=20, b=40),
#         height=280,
#         width=410,
#         legend=dict(font=dict(family="Rubik", size=12, color="black")),
#         hoverlabel=dict(
#             font_size=14,
#             font_family="Rubik",
#         )
#     )
#     return fig, style
#
#
# @appDash.callback(
#     Output('CalendarSave', 'style'),
#     [Input('CalendarTable', 'data')],
#     [State('CalendarTable', 'data_previous')],
#     [State('Datepicker', 'date')],
#     prevent_initial_call=True
# )
# def CalendarChanges(current, previous, start_date):
#
#     if previous is None: return dash.no_update
#     total = []
#     i = 0
#     for project in current:
#         old_project = previous[i]
#         i += 1
#         diff = [[k, project[k]] for k in project if k in old_project and project[k] != old_project[k]]
#         if len(diff) != 0:
#             if old_project[diff[0][0]] is None: status = 'INS'
#             elif project[diff[0][0]] == '0' or project[diff[0][0]] is None: status = 'DEL'
#             else: status = 'UPD'
#             total.append([project['НАЗВАНИЕ ПРОЕКТА']] + diff[0]+[status])
#             break
#     UPDATE = total[0]
#
#     user = flask_login.current_user.name
#
#     start_date = dt.strptime(start_date, '%Y-%m-%dT%H:%M:%S')
#     date = start_date + datetime.timedelta(days=WEEK_NUMBERS[UPDATE[1]])
#     date = date.strftime('%Y-%m-%d')
#     # КУЧА ПОДЗАПРОСОВ CRUD
#     if UPDATE[3] == 'UPD':
#         query = f"""
#                 UPDATE skameyka.main_table SET hours = {UPDATE[2]} WHERE user_id =
#                 (SELECT id FROM skameyka.user_table WHERE fullname like '{user}')
#                 AND project_id =
#                 (SELECT id FROM skameyka.project_table WHERE title like '{UPDATE[0]}')
#                 AND timestamp = '{date}'
#         """
#     elif UPDATE[3] == 'DEL':
#         query = f"""
#                 DELETE FROM skameyka.main_table WHERE user_id =
#                 (SELECT id FROM skameyka.user_table WHERE fullname like '{user}')
#                 AND project_id =
#                 (SELECT id FROM skameyka.project_table WHERE title like '{UPDATE[0]}')
#                 AND timestamp = '{date}'
#         """
#     else:
#         query = f"""
#                 INSERT INTO skameyka.main_table (user_id, project_id, timestamp, hours) VALUES
#                 (
#                     (SELECT id FROM skameyka.user_table WHERE fullname like '{user}'),
#                     (SELECT id FROM skameyka.project_table WHERE title like '{UPDATE[0]}'),
#                     '{date}', {UPDATE[2]}
#                 )
#                 """
#     calendar_cache.append(query)
#
#     return dash.no_update

@appDash.callback(
    Output({"type": "stage-block", "stage": MATCH}, "children"),
    Input({"type": "calendar-cell", "stage": MATCH, "hour": ALL, "day": ALL}, "n_clicks"),
    State({"type": "stage-block", "stage": MATCH}, "id"),
    prevent_initial_call=True
)
def update_stage_block(n_clicks_list, stage_id):
    # triggered = callback_context.triggered_id
    stage_index = all_stages.index(stage_id["stage"])
    stage_name, rows = stage_id["stage"], 12


    # Можно получить ID нажатой клетки через callback_context
    triggered = callback_context.triggered_id

    if not triggered:
        return dash.no_update

    selected = {
        "stage": stage_name,
        "hour": triggered["hour"],
        "day": triggered["day"],
        "color": rgba_string_to_hex(flask_login.current_user.color)
    }
    print(selected)

    return create_stage_block(stage_name, rows, selected_data=selected)

# @appDash.callback(
#     Output("filled-cells", "data"),
#     Input({"type": "calendar-cell", "stage": ALL, "hour": ALL, "day": ALL}, "n_clicks"),
#     State("filled-cells", "data"),
#     prevent_initial_call=True
# )
# def update_single_cell(n_clicks_list, prev_data):
#
#     ctx = callback_context
#     triggered = ctx.triggered_id
#
#
#     if not triggered:
#         return dash.no_update
#
#     # Обновляем данные
#     return {
#         "stage": triggered["stage"],
#         "hour": triggered["hour"],
#         "day": triggered["day"],
#         "color": rgba_string_to_hex(flask_login.current_user.color)
#     }


@appDash.callback(
    Output("selected-cells", "children"),
    Input("filled-cells", "data"),
    prevent_initial_call=True
)
def display_current_cell(data):
    print(data)
    if not data:
        return "Нет выбранной ячейки"

    return f"{data['stage']} — День {data['day']}, Час {data['hour']}"

@appDash.callback(
    Output('Calendar', 'children'),
    Input('filled-cells', 'data'),
    prevent_initial_call=True
)
def update_table(selected_data):
    print(selected_data)
    return render_table(selected_data)

@appDash.callback(
    Output('BigTitle','children'),
    Input('FilterGraph', 'value'),
    State('GraphMode', 'data'),
)
def update_graph_title(id, is_project):
    return db.get_project_name(id) if is_project else db.get_user_name(id).upper()

@appDash.callback(
    Output('YearFilterGraph', 'value'),
    Output('MonthFilterGraph', 'value'),
    Input('RefreshGraph','n_clicks'),
    prevent_initial_call=True
)
def update_graph_filters(click):
    if click:
        print("CLEAR")
        today = datetime.datetime.now()
        return today.year, today.month
    return dash.no_update, dash.no_update

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
        xaxis=dict(title='', dtick=1, range=[0, 31] if month else [0,12]),
        yaxis=dict(title='', range=[0, 12] ) if month else dict(autorange=True, fixedrange=False),
        plot_bgcolor='#fff',
        paper_bgcolor='#fff',
        autosize=True,
        legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1),
        margin=dict(l=20, r=20, t=50, b=40),
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
def get_raw_data_cached(page_current, page_size):
    return db.get_db_chunk(page_current, page_size)

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
)
def update_table(page_current, page_size, user, project, square, stage, day, month, year):
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
            'user': [user, 'u.name user', 'JOIN user u ON main.userId=u.id\n', 'u.name'],
            'project': [project, 'p.name project', 'JOIN project p ON main.projectId=p.id\n', 'p.name'],
            'square': [square, 'p.square square', 'JOIN project p ON main.projectId=p.id\n', 'p.square'],
            'stage': [stage, 's.name stage', 'JOIN stage s ON main.stageId=s.id\n', 's.name'],
        }

        # Если ни один фильтр не выбран — показать "сырые" данные
        if all(v[0] is None for v in field_map.values()):
            data, columns = get_raw_data_cached(page_current, page_size)
            page_size= 40
            page_action='custom'
            count = db.get_main_count()


        else:
            page_size = 250
            page_action = 'native'

            # Фильтрация и группировка по выбранным
            select_keys = [field_map[k][1] for k, v in field_map.items() if v[0] is not None]
            group_by_keys = [k for k, v in field_map.items() if v[0] is not None]
            filters = [f"{field_map[k][-1]} = '{v[0]}'" for k, v in field_map.items() if v[0] is not None and 'Все' != v[0] ]
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
                        dcc.Input(id='PrjName', placeholder='Введите название', className='inp long',
                                  value=prj_data['PrjName'])
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
        return old + [html.Div(["😧 Ошибка при записи в базу"], className='cloud line popup orange', hidden=False)]

    CACHE.clear()

    msg = {
        'insert': "✔ Данные добавлены!",
        'update': "✔ Данные обновлены!",
        'delete': "✂️ Успешно удалено!"
    }[mode]
    print(msg)

    return old + [html.Div([msg], className='cloud line popup green', hidden=False)]


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
        dash.no_update()

