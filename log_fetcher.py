import shutil
import csv
import os
import time
from pathlib import Path
from constants import LOG_DIR, ROOMS
import pandas as pd
from utils import hms2sec, pairwise, calculate_price, strftoday
from datetime import datetime
from dbutils import conn, cursor
from error_logger import error, warning, succeed, verbose

class RecentLogs:
    dests = []
    def __enter__(self):
        for port in [4, 5, 6, 7]:
            log_dir = Path(LOG_DIR[port])
            csv_files = list(log_dir.glob("*.csv"))
            if (not csv_files):
                error(port, "로그 데이터를 찾지 못했습니다.") 
                continue
            recent_csv = max(csv_files, key=lambda file: file.stat().st_mtime)
            recent_mtime = recent_csv.stat().st_mtime
            recent_mtime_formatted = datetime.fromtimestamp(recent_mtime).strftime("%Y%m%d-%H:%M:%S")[9:]
            delta_currenttime = time.time() - recent_mtime
            if (delta_currenttime > 60):
                warning(port, f"최신 로그에 {int(delta_currenttime)}초 동안 로그가 작성되지 않았습니다.",
                f"가장 마지막에 작성된 시간은 {recent_mtime_formatted}입니다.") # warning
            # TODO: 어떤 프로세스에서 이 파일을 직접 쓰고 있는지 확인할 수 있음
            start_date = recent_csv.name[:8]
            dest_csv = f"./rmfc_logdata/port{port}_{start_date}.csv"
            try:
                shutil.copyfile(recent_csv, dest_csv)
            except Exception as e:
                error(port, "최신 로그를 복사하던 중 얘기치 못한 오류가 발생하였습니다.", e)
                continue
            self.dests.append((dest_csv, port, start_date))
        return self
    
    def __exit__(self, exc_type, exc_value, traceback):
        for dest, port, _ in self.dests:
            try:
                os.remove(dest)
            except Exception as e:
                warning(port, "복사한 최신 로그를 삭제하던 중 중 얘기치 못한 오류가 발생하였습니다.", e)
    
    def __getitem__(self, index):
        return self.dests[index]
    
    def __iter__(self):
        return iter(self.dests)


def check_is_valid_logfile(logfile, port):
    with open(logfile, 'r', newline='') as file:
        csv_reader = csv.reader(file)
        header = next(csv_reader)

        room_len = (len(header) - 2) // 4
        prefixes = [header[2 + idx * 4][:5] for idx in range(room_len) if header[2 + idx * 4]]

        if (sorted(prefixes) != sorted(ROOMS[port])):
            warning(port, f"로그파일에 기재된 호실이 정해진 호실(f{ROOMS[port]})과 일치하지 않습니다.", 
                  f"{port} 포트에서 실행되고 있는 DMFC의 Settings에서 포트가 COM {port}를 가리키고 있는지 확인하세요.")
        
        room_len = len(prefixes)

        suspicious_rows = []
        for row_idx, row in enumerate(csv_reader):
            for idx in range((len(row) - 2) // 4):
                itime = row[idx * 4 + 5]
                if (idx < room_len and not itime) or (idx >= room_len and itime):
                    suspicious_rows.append(row_idx)
                    break
        if suspicious_rows:
            warning(port, f"로그파일의 {", ".join(suspicious_rows)}번째 행의 열의 개수가 정해진 열의 개수", 
                f"({2 + 4 * room_len})가 아닙니다. 집계 도중 포트를 바꾼 것으로 추측됩니다.",
                f"{port} 포트에서 실행되고 있는 DMFC의 Settings에서 포트가 COM {port}를 가리키고 있는지 확인하세요.")
    return prefixes

def _store_sum_by_room(_date, port, room, check_empty_intervals = False):
    date = datetime.strftime(_date, "%Y%m%d")
    cursor.execute("select * from dmfc_log where date=? and room=? order by time asc", (date, room))
    res = cursor.fetchall()
    if check_empty_intervals:
        if not res:
            warning(port, f"{date} 날짜의 데이터가 없습니다.")
            return
        if (_date.date() != datetime.now().date()): # 오늘이 아닐 경우
            times = [0, *map(lambda x: hms2sec(x[1]), res), 86399]
            for idx, (t1, t2) in enumerate(pairwise(times)):
                if (t2 - t1 > 30):
                    start = "00:00:00" if idx == 0 else res[idx - 1][1]
                    end = "23:59:59" if idx == len(times) - 2 else res[idx][1]
                    warning(port, f"{date} 날짜에 {start}부터 {end}까지 간격이 너무 깁니다.")
    if res:
        dintegral = res[-1][6] - res[0][6]
        sumpv = sum(map(lambda x: x[3], res))

        cursor.execute("select * from dmfc_sum where date=? and room=?", (date, room))
        current = cursor.fetchall()
        if current: # update
            cursor.execute("update dmfc_sum set IntSum=?, PvSum=?, LatestTime=? where Date=? and Room=?", 
                        (dintegral, sumpv, res[-1][1], date, room))
        else:
            cursor.execute("insert into dmfc_sum(Date, Room, IntSum, PvSum, LatestTime) values (?,?,?,?,?)",
                        (date, room, dintegral, sumpv, res[-1][1]))

def store_to_db():
    with RecentLogs() as logs:
        for log, port, start_date in logs:
            rooms = check_is_valid_logfile(log, port)
            if not rooms:
                continue
            with open(log, 'r', newline='') as file:
                csv_reader = csv.reader(file)
                next(csv_reader)
                cursor.execute("select Date, Time from dmfc_log where Room=? order by date, time desc", (rooms[0], ))
                recent_query = cursor.fetchone()
                rd, rt = recent_query if recent_query else (None, None)
                data = []
                for row in csv_reader:
                    if recent_query and (row[0] < rd or (rd == row[0] and row[1] < rt)):
                        continue
                    data.append((
                        row[0],
                        row[1],
                        [float(row[idx * 4 + 2]) for idx in range(len(rooms))],
                        [float(row[idx * 4 + 2 + 1]) for idx in range(len(rooms))],
                        [row[idx * 4 + 2 + 2] for idx in range(len(rooms))],
                        [float(row[idx * 4 + 2 + 3]) for idx in range(len(rooms))]
                    ))

                    # Bulk Insert를 위한 데이터 포맷
                insert_data = [(d, t, room, p[idx], s[idx], it[idx], ifl[idx])
                    for d, t, p, s, it, ifl in data for idx, room in enumerate(rooms)]

                cursor.executemany('''INSERT OR IGNORE INTO dmfc_log(Date, Time, Room, PV, SV, IntegralTime, IntegralFlow)
                                        VALUES (?, ?, ?, ?, ?, ?, ?)''', insert_data)
        conn.commit()
        succeed(None, "LOG DB에 성공적으로 데이터를 작성하였습니다.")
        for log, port, start_date in logs:
            daterange = pd.date_range(start_date, datetime.now())
            for date in daterange:
                for i, room in enumerate(ROOMS[port]):
                    _store_sum_by_room(date, port, room, i == 0)
        conn.commit()
        succeed(None, "LOG 합계 DB에 성공적으로 데이터를 작성하였습니다.")

intsum_alias = "IntSum (L)"
price_alias = "Price (원)"

def db_to_xlsx():
    query = "SELECT Date, Room, IntSum FROM dmfc_sum order by Date asc"
    df = pd.read_sql_query(query, conn)
    df.rename(columns={"IntSum": intsum_alias}, inplace=True)
    df = df.loc[df['Date'] != strftoday()]
    df[price_alias] = df[intsum_alias].apply(calculate_price)
    
    agg_info = { intsum_alias: 'sum', price_alias: 'sum' }

    temp_df = df.copy()
    temp_df['Date'] = pd.to_datetime(temp_df['Date'])
    temp_df['Year'] = temp_df['Date'].dt.year
    temp_df['Month'] = temp_df['Date'].dt.month
    temp_df['Week'] = temp_df['Date'] - pd.to_timedelta(temp_df['Date'].dt.weekday, unit='D')

    current_year = datetime.now().year
    current_month = datetime.now().month
    current_week = (datetime.now() - pd.to_timedelta(datetime.now().weekday(), unit='D')).date()

    year_df = temp_df.groupby(['Year', 'Room']).agg(agg_info).reset_index()
    year_df = year_df.loc[year_df['Year'] != current_year]
    
    month_df = temp_df.groupby(['Year', 'Month', 'Room']).agg(agg_info).reset_index()
    month_df = month_df.loc[~((month_df['Year'] == current_year) & (month_df['Month'] == current_month))]

    week_df = temp_df.groupby(['Year', 'Week', 'Room']).agg(agg_info).reset_index()
    week_df = week_df.loc[~((week_df['Year'] == current_year) & \
                            (week_df['Week'].dt.strftime("%Y%m%d") == current_week.strftime("%Y%m%d")))]
    week_df['Week'] = week_df['Week'].dt.strftime('%U주차 (%Y%m%d ~ ') + \
         (week_df['Week'] + pd.to_timedelta(6, unit='D')).dt.strftime('%Y%m%d)')
    while True:
        try:
            with pd.ExcelWriter('./usageSummary.xlsx', mode='w') as writer:
                df.to_excel(writer, sheet_name="일별", index=False)
                week_df.to_excel(writer, sheet_name="주별", index=False)
                month_df.to_excel(writer, sheet_name="월별", index=False)
                year_df.to_excel(writer, sheet_name="연도별", index=False)
            break
        except PermissionError as e:
            input(f"usageSummary.xlsx이 이미 열려 있어 엑셀에 작성할 수 없습니다. 파일을 닫고 Enter 키를 눌러 다시 시도하세요.")
        
    succeed(None, "합계 DB를 엑셀 파일로 변환하였습니다. usageSummary.xlsx에서 확인해 보세요.")