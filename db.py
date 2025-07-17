from app import engine
from sqlalchemy import text
from utils import month_name_ru, rgba_string_to_hex
import pandas as pd
from datetime import date, timedelta
import os



def execute_query(con, query: str):
    if query:
        res= con.execute(text(query))
        con.commit()
        return res

def get_user_info(user_id):
    with engine.connect() as con:
        res = con.execute(
            text('SELECT id, username, relevant, admin, name, color FROM lptv.user WHERE id = :user_id'),
            {"user_id": user_id}
        )
        return res.fetchone()
def get_user_color(name):
    with engine.connect() as con:
        res = con.execute(
            text('SELECT color FROM lptv.user WHERE relevant = 1 AND username LIKE :name'),
            {"name": name}
        )
        if res.scalar():
            return rgba_string_to_hex(res.scalar())
        else:
            return 'rgba(1,1,1,0)'

def get_user(username):
    with engine.connect() as con:
        res = con.execute(
            text('SELECT id, password FROM lptv.user WHERE relevant = 1 AND username LIKE :username'),
            {"username": username}
        )
        return res.fetchone()

def get_user_login(name):
    with engine.connect() as con:
        res = con.execute(
            text('SELECT username FROM lptv.user WHERE relevant = 1 AND name LIKE :name'),
            {"name": name}
        )
        return res.scalar()

def get_user_login_by_id(id):
    with engine.connect() as con:
        res = con.execute(
            text('SELECT username FROM lptv.user WHERE id = :id'),
            {"id": id}
        )
        return res.scalar()

def get_user_full(id):
    with engine.connect() as con:
        res = con.execute(
            text('SELECT id, name, username, admin, relevant, color, password FROM lptv.user WHERE id = :id'),
            {"id": id}
        )
        return res.fetchone()

def get_project_full(id):
    with engine.connect() as con:
        res = con.execute(
            text('SELECT id, name, square, level, startdate, isDone FROM lptv.project WHERE id = :id'),
            {"id": id}
        )
        return res.fetchone()

def get_project_name(id):
    with engine.connect() as con:
        res = con.execute(
            text('SELECT name FROM lptv.project WHERE id = :id'),
            {"id": id}
        )
        return res.scalar()

def get_user_name(id):
    with engine.connect() as con:
        res = con.execute(
            text('SELECT name FROM lptv.user WHERE id = :id'),
            {"id": id}
        )
        return res.scalar()

def get_project_count(is_relevant=1):
    with engine.connect() as con:
        res = con.execute(
            text('SELECT count(*) AS rel FROM lptv.project WHERE isDone != :is_relevant'),
            {"is_relevant": is_relevant}
        )
        return res.scalar()


def get_years():
    with engine.connect() as con:
        res = con.execute(
            text('SELECT DISTINCT YEAR(dateStamp) AS year FROM lptv.main ORDER BY year DESC')
        )
        return [str(row[0]) for row in res]

def get_users():
    with engine.connect() as con:
        df = pd.read_sql("SELECT id, name, color, admin, relevant  FROM lptv.user", con)
        return df

def get_projects():
    with engine.connect() as con:
        df = pd.read_sql("SELECT id, name, square, startdate, isDone "
                         "FROM lptv.project ORDER BY id DESC", con)
        return df

def get_project_stages(id):
    with engine.connect() as con:
        res = con.execute(
            text('SELECT finishdate FROM lptv.projectstage '
                 'WHERE projectId = :id ORDER BY stageId'),
            {"id": id}
        )
        return [str(row[0]) for row in res]

def get_project_cards(relevant, year):
    base_query = text("""
        SELECT id, name, square, count_users, sum_hours, isDone, level
        FROM lptv.project p
        LEFT JOIN (
            SELECT projectId, count(distinct userId) count_users, sum(hours) sum_hours, max(dateStamp) lastAct
            FROM lptv.main
            GROUP BY projectId
        ) as agr ON (projectId = p.id)
        WHERE 1=1
        {relevant_filter}
        {year_filter}
        ORDER BY isDone, p.level DESC, lastAct DESC
    """)

    # фильтры
    filters = {
        "relevant_filter": "",
        "year_filter": ""
    }
    params = {}

    if relevant == 'Архивные':
        filters["relevant_filter"] = " AND p.isDone != :relevant_val"
        params["relevant_val"] = 0
    elif relevant == 'Актуальные':
        filters["relevant_filter"] = " AND p.isDone != :relevant_val"
        params["relevant_val"] = 1

    if year is not None and year != 'Всё время':
        filters["year_filter"] = """
            AND p.id IN (
                SELECT DISTINCT projectId
                FROM lptv.main
                WHERE YEAR(dateStamp) = :year_val
            )
        """
        params["year_val"] = int(year)

    # Подставляем текст фильтров
    final_query = text(
        base_query.text.format(
            relevant_filter=filters["relevant_filter"],
            year_filter=filters["year_filter"]
        )
    )

    with engine.connect() as con:
        df = pd.read_sql(final_query, con=con, params=params)

    return df

def execute_user_queries(cache, user_id, mode):
    MAP = {
        'UserName': 'name',
        'UserLogin': 'username',
        'UserPass': 'password',
        'UserRole': 'admin',
        'UserActual': 'relevant',
        'UserColor': 'color'
    }

    def fmt(value):
        return f"'{value}'" if isinstance(value, str) and not value.startswith("'") else str(value)

    with engine.connect() as con:
        if mode == 'update':
            updates = [
                f"{MAP[k]} = {fmt(cache[k])}"
                for k in cache if k in MAP
            ]
            if updates:
                if 'UserLogin' in cache.keys():
                    path = 'assets/img/users/'
                    old_name = get_user_login_by_id(user_id)
                    print(old_name)
                    if os.path.isfile(path+old_name+'.png'):
                        os.rename(path+old_name+'.png', path+cache['UserLogin']+'.png')

                sql = f"UPDATE lptv.user SET {', '.join(updates)} WHERE id = {user_id}"
                execute_query(con, sql)

        elif mode == 'insert':
            cache.setdefault('UserRole', 0)
            cache.setdefault('UserActual', 1)
            cache.setdefault('UserColor', '0.5,0.5,0.5,1')

            fields = [MAP[k] for k in MAP]
            values = [fmt(cache.get(k)) for k in MAP]

            sql = f"""INSERT INTO lptv.user 
                      ({', '.join(fields)}) 
                      VALUES ({', '.join(values)})"""
            execute_query(con, sql)

        elif mode == 'delete':
            sql1 = f"DELETE FROM lptv.main WHERE userId = {user_id}"
            sql2 = f"DELETE FROM lptv.user WHERE id = {user_id}"
            execute_query(con, sql1)
            execute_query(con, sql2)



def execute_project_queries(cache, project_id, mode):
    with engine.connect() as con:
        MAP = {
            'PrjName': 'name',
            'PrjStart': 'startdate',
            'PrjSqr': 'square',
            'PrjLvl': 'level',
            'PrjDone': 'isDone',
        }

        def fmt(value):
            return f"'{value}'" if isinstance(value, str) and not value.startswith("'") else str(value)


        if mode == 'update':
            cache.setdefault('info', 0)
            cache.setdefault('stages', 0)
            if cache['info']:
                fields = ', '.join(
                    f"{MAP[k]} = {fmt(cache[k])}" for k in cache if k in MAP
                )
                sql = f"UPDATE lptv.project SET {fields} WHERE id = {project_id}"
                execute_query(con, sql)
            if cache['stages']:
                for k in cache:
                    if k.startswith('StageDate'):
                        stage_id = k[-1]
                        sql = f"""UPDATE lptv.projectstage
                                             SET finishdate = {fmt(cache[k])}
                                             WHERE projectId = {project_id} AND stageId = {stage_id}"""
                        execute_query(con, sql)


        elif mode == 'insert':
            cache.setdefault('PrjDone', 0)
            cache.setdefault('PrjLvl', 1)
            cache.setdefault('PrjStart', f"'{date.today().strftime('%Y-%m-%d')}'")

            columns = ', '.join(MAP.values())
            values = ', '.join(fmt(cache.get(k, 'NULL')) for k in MAP)

            sql = f"INSERT INTO lptv.project ({columns}) VALUES ({values})"
            res = execute_query(con, sql)
            last_id = res.lastrowid

            for stage in range(1, 7):
                key = f"StageDate{stage}"
                if key in cache:
                    sql = f"""INSERT INTO lptv.projectstage (projectId, stageId, finishdate)
                                          VALUES ({last_id}, {stage}, {fmt(cache[key])})"""
                    execute_query(con, sql)

        elif mode == 'delete':
            sql = f"DELETE FROM lptv.main WHERE projectId = {project_id}"
            sql2 = f"DELETE FROM lptv.projectstage WHERE projectId = {project_id}"
            sql3 = f"DELETE FROM lptv.project WHERE id = {project_id}"
            execute_query(con,sql)
            execute_query(con,sql2)
            execute_query(con,sql3)


def get_db_chunk(page_current, page_size):
    offset = page_current * page_size
    query = text("""
        SELECT 
            YEAR(dateStamp) AS year,
            MONTH(dateStamp) AS month,
            DAY(dateStamp) AS day,
            u.name AS user,
            p.name AS project,
            s.name AS stage,
            p.square,
            main.hours
        FROM main
        JOIN user u ON u.id = main.userId
        JOIN project p ON main.projectId = p.id
        JOIN stage s ON main.stageId = s.id
        ORDER BY dateStamp DESC
        LIMIT :limit OFFSET :offset
    """)

    with engine.connect() as con:
        result = con.execute(query, {"limit": page_size, "offset": offset})
        rows = result.fetchall()
        columns = result.keys()
        data = [dict(zip(columns, row)) for row in rows]
        return data, columns

def get_filtered_data(select, group_by, filters, join, order_by):
    query = text(f"""
        SELECT {select}, SUM(hours) AS hours 
        FROM lptv.main
        {join}
        WHERE {filters}
        GROUP BY {group_by}
        ORDER BY {order_by} SUM(hours) DESC
    """)

    with engine.connect() as con:
        result = con.execute(query)
        rows = result.fetchall()
        columns = result.keys()
        data = [dict(zip(columns, row)) for row in rows]
        return data, columns


def get_main_count():
    with engine.connect() as con:
        res = con.execute(text(""" SELECT COUNT(*) FROM main"""))
        return res.scalar()


def get_filters():
    options = {}

    with engine.connect() as con:
        # Годы
        res = con.execute(text("SELECT DISTINCT YEAR(dateStamp) AS year FROM main ORDER BY year DESC"))
        options['year'] = [{'label': str(row[0]), 'value': row[0]} for row in res.fetchall()]

        # Месяцы
        res = con.execute(text("SELECT DISTINCT MONTH(dateStamp) AS month FROM main ORDER BY month"))
        options['month'] = [{'label': f"{row[0]:02d}", 'value': row[0]} for row in res.fetchall()]

        # Дни
        res = con.execute(text("SELECT DISTINCT DAY(dateStamp) AS day FROM main ORDER BY day"))
        options['day'] = [{'label': f"{row[0]:02d}", 'value': row[0]} for row in res.fetchall()]

        # Сотрудники
        res = con.execute(text("SELECT DISTINCT u.name FROM main JOIN user u ON u.id = main.userId ORDER BY u.name"))
        options['user'] = [{'label': row[0], 'value': row[0]} for row in res.fetchall()]

        # Проекты
        res = con.execute(text("SELECT DISTINCT p.name FROM main JOIN project p ON p.id = main.projectId ORDER BY p.name"))
        options['project'] = [{'label': row[0], 'value': row[0]} for row in res.fetchall()]

        # Площадь
        res = con.execute(
            text("SELECT DISTINCT p.square FROM main JOIN project p ON p.id = main.projectId ORDER BY p.square DESC"))
        options['square'] = [{'label': row[0], 'value': row[0]} for row in res.fetchall()]

        # Этапы
        res = con.execute(text("SELECT DISTINCT s.name FROM main JOIN stage s ON s.id = main.stageId ORDER BY s.name"))
        options['stage'] = [{'label': row[0], 'value': row[0]} for row in res.fetchall()]

    return options

def get_graph_filters():
    options = {}
    with engine.connect() as con:
        # Годы
        res = con.execute(text("SELECT DISTINCT YEAR(dateStamp) AS year FROM main ORDER BY year DESC"))
        options['year'] = [{'label': str(row[0]), 'value': row[0]} for row in res.fetchall()]

        # Месяцы
        res = con.execute(text("SELECT DISTINCT MONTH(dateStamp) AS month FROM main ORDER BY month"))
        options['month'] = [{'label': f"{month_name_ru(row[0])}", 'value': row[0]} for row in res.fetchall()]

        # Сотрудники
        res = con.execute(text("SELECT DISTINCT u.name, u.id FROM main JOIN user u ON u.id = main.userId ORDER BY u.name"))
        options['user'] = [{'label': row[0], 'value': row[1]} for row in res.fetchall()]

        # Проекты
        res = con.execute(text("SELECT DISTINCT p.name, p.id FROM main JOIN project p ON p.id = main.projectId ORDER BY p.name"))
        options['project'] = [{'label': row[0], 'value': row[1]} for row in res.fetchall()]

    return options

def get_lines_users(project_id, month, year):
    result = {}

    where_clauses = ["projectId = :project_id", "YEAR(dateStamp) = :year"]
    params = {'project_id': project_id, 'year': year}

    if month is not None:
        where_clauses.append("MONTH(dateStamp) = :month")
        params['month'] = month
        group_by = "DAY(dateStamp)"
        select_fields = "DAY(dateStamp) AS x, SUM(hours) AS hours"
    else:
        group_by = "MONTH(dateStamp)"
        select_fields = "MONTH(dateStamp) AS x, SUM(hours) AS hours"

    where_sql = " AND ".join(where_clauses)

    with engine.connect() as con:
        # Получаем пользователей и цвет
        user_query = text(f"""
            SELECT DISTINCT u.id AS user_id, u.name AS user_name, u.color
            FROM main m
            JOIN user u ON u.id = m.userId
            WHERE m.projectId = :project_id AND YEAR(m.dateStamp) = :year
            {"AND MONTH(m.dateStamp) = :month" if month else ""}
        """)
        users = con.execute(user_query, params).fetchall()

        for user in users:
            user_params = dict(params, user_id=user.user_id)
            data_query = text(f"""
                SELECT {select_fields}
                FROM main
                WHERE {where_sql} AND userId = :user_id
                GROUP BY {group_by}
                ORDER BY x
            """)
            rows = con.execute(data_query, user_params).fetchall()
            days_dict = {row.x: row.hours for row in rows}

            result[user.user_name] = {
                'color': user.color,
                'data': days_dict
            }

    return result

def get_lines_projects(user_id, month, year):
    result = {}

    where_clauses = ["userId = :user_id", "YEAR(dateStamp) = :year"]
    params = {'user_id': user_id, 'year': year}

    if month is not None:
        where_clauses.append("MONTH(dateStamp) = :month")
        params['month'] = month
        group_by = "DAY(dateStamp)"
        select_fields = "DAY(dateStamp) AS x, SUM(hours) AS hours"
    else:
        group_by = "MONTH(dateStamp)"
        select_fields = "MONTH(dateStamp) AS x, SUM(hours) AS hours"

    where_sql = " AND ".join(where_clauses)

    with engine.connect() as con:
        p_query = text(f"""
            SELECT DISTINCT p.id AS project_id, p.name AS project_name
            FROM main m
            JOIN project p ON p.id = m.projectId
            WHERE m.userId = :user_id AND YEAR(m.dateStamp) = :year
            {"AND MONTH(m.dateStamp) = :month" if month else ""}
        """)
        prjs = con.execute(p_query, params).fetchall()

        for prj in prjs:
            prj_params = dict(params, project_id=prj.project_id)
            data_query = text(f"""
                SELECT {select_fields}
                FROM main
                WHERE {where_sql} AND projectId = :project_id
                GROUP BY {group_by}
                ORDER BY x
            """)
            rows = con.execute(data_query, prj_params).fetchall()
            days_dict = {row.x: row.hours for row in rows}

            result[prj.project_name] = {
                'data': days_dict
            }
    return result


def get_user_color_map(project_id):
    query = text("""
        SELECT DISTINCT LEFT(u.name, LOCATE(' ', u.name) - 1) AS user, u.color
        FROM main m
        JOIN user u ON u.id = m.userId
        WHERE m.projectId = :project_id
    """)

    with engine.connect() as con:
        rows = con.execute(query, {"project_id": project_id}).fetchall()

    # Собираем словарь
    color_map = {row.user: rgba_string_to_hex(row.color) for row in rows if row.color}
    # color_map["Σ"] = "#EAEAEA"  # для сумм

    return color_map

def get_graph_project_data(project_id, year, month=None):
    all_stages = [
        'ПОДГОТОВКА',
        '3D ГРАФИКА',
        'ЗАКАЗНЫЕ ПОЗИЦИИ',
        'СМР',
        'КОМПЛЕКТАЦИЯ',
        'РЕАЛИЗАЦИЯ'
    ]

    query = text(f"""
        SELECT u.name AS user, s.name AS stage, SUM(hours) AS hours  
        FROM main m
        JOIN user u ON u.id = m.userId
        JOIN stage s ON s.id = m.stageId
        WHERE YEAR(m.dateStamp) = :year
        {f"AND MONTH(m.dateStamp) = :month" if month else ""}
        AND m.projectId = :project_id
        GROUP BY u.name, s.name
    """)

    params = {"year": year, "project_id": project_id}
    if month:
        params["month"] = month

    with engine.connect() as con:
        df = pd.read_sql(query, con, params=params)

    if df.empty:
        df = pd.DataFrame(columns=['stage', 'Сотрудник', 'Σ'])
        columns = [{"name": col, "id": col} for col in df.columns]
        return df.to_dict('records'), columns

    pivot = df.pivot_table(index='stage', columns='user', values='hours', aggfunc='sum', fill_value=0)


    for stage in all_stages:
        if stage not in pivot.index:
            pivot.loc[stage] = 0

    pivot = pivot.loc[all_stages]

    pivot['Σ'] = pivot.sum(axis=1)


    total_row = pd.DataFrame(pivot.sum(axis=0)).T
    total_row.index = ['Σ']
    pivot = pd.concat([pivot, total_row])

    final_df = pivot.reset_index()

    columns = [{"name": col.partition(" ")[0], "id": col} for col in final_df.columns]
    print(columns)
    return final_df.to_dict('records'), columns

def get_graph_user_data(user_id, year, month=None):
    query = text(f"""
            SELECT p.name AS project, SUM(hours) AS hours  
            FROM main m
            JOIN project p ON p.id = m.projectId
            WHERE YEAR(m.dateStamp) = :year
            {f"AND MONTH(m.dateStamp) = :month" if month else ""}
            AND m.userId = :user_id
            GROUP BY p.name
        """)
    params = {"year": year, "user_id": user_id}
    if month:
        params["month"] = month

    with engine.connect() as con:
        df = pd.read_sql(query, con, params=params)
    if df.empty:
        df = pd.DataFrame(columns=['Проект',])
        columns = [{"name": col, "id": col} for col in df.columns]
        return df.to_dict('records'), columns
    df.rename(columns={'hours': 'Часы'}, inplace=True)

    final_df = df.transpose()
    final_df.columns = final_df.iloc[0]
    final_df = final_df.drop(final_df.index[0])
    final_df = final_df.reset_index()
    print(final_df)
    columns = [{"name": col[:9], "id": col} for col in final_df.columns]
    print(columns)
    return final_df.to_dict('records'), columns


# def get_project_id(name):
#     with engine.connect() as con:
#         res = con.execute(text(f"""
#             SELECT id FROM project WHERE name = :pname
#         """), {"pname":name})
#         return res.scalar()
def is_contiguous(user_id, project_id, stage_id, year, month, day, hour):
    current_date = date(year, month, day)
    left_date = (current_date - timedelta(days=1)).isoformat()
    right_date = (current_date + timedelta(days=1)).isoformat()

    query = text("""
        SELECT 1
        FROM main
        WHERE userId = :user_id
          AND projectId = :project_id
          AND stageId = :stage_id
          AND dateStamp = :date
          AND hours >= :hour
        LIMIT 1
    """)


    with engine.connect() as con:
        left = con.scalar(query, {
            "user_id": user_id, "project_id": project_id, "stage_id": stage_id,
            "date": left_date, "hour": hour
        })
        right = con.scalar(query, {
            "user_id": user_id, "project_id": project_id, "stage_id": stage_id,
            "date": right_date, "hour": hour
        })
    return bool(left), bool(right)

def get_user_work_data(project_id, year, month,stage=None):
    query = text(f"""
        SELECT 
            m.userId AS user_id,
            u.color AS color,
            DAY(m.dateStamp) AS day,
            m.hours AS hours,
            s.name AS stage,
            projectId
        FROM main m
        JOIN user u ON u.id = m.userId
        JOIN stage s ON s.id = m.stageId
        WHERE m.projectId = :project_id
          AND YEAR(m.dateStamp) = :year
          AND MONTH(m.dateStamp) = :month
          {'AND s.name = :stage' if stage else ''}
        ORDER BY stageId, user_id, day 
    """)

    params = {
        "project_id": project_id,
        "year": year,
        "month": month,
    }
    if stage: params['stage'] = stage

    with engine.connect() as conn:
        result = conn.execute(query, params)
        rows = result.fetchall()

    # Преобразуем результат в список словарей
    user_work_data = [
        {
            "user_id": row.user_id,
            "color": rgba_string_to_hex(row.color),
            "day": row.day,
            "hours": row.hours,
            "stage": row.stage,
            "project_id": row.projectId,

        }
        for row in rows
    ]

    return user_work_data