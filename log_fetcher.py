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
            if (delta_currenttime > 15):
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
            error(port, f"로그파일에 기재된 호실이 정해진 호실(f{ROOMS[port]})과 일치하지 않습니다.", 
                  f"{port} 포트에서 실행되고 있는 DMFC의 Settings에서 포트가 COM {port}를 가리키고 있는지 확인하세요.")
            return False
        
        room_len = len(ROOMS[port]) # invariant

        suspicious_rows = []
        for row_idx, row in enumerate(csv_reader):
            for idx in range((len(row) - 2) // 4):
                itime = row[idx * 4 + 5]
                if (idx < room_len and not itime) or (idx >= room_len and itime):
                    suspicious_rows.append(row_idx)
                    break
        if suspicious_rows:
            error(port, f"로그파일의 {", ".join(suspicious_rows)}번째 행의 열의 개수가 정해진 열의 개수", 
                f"({2 + 4 * room_len})가 아닙니다. 집계 도중 포트를 바꾼 것으로 추측됩니다.",
                f"{port} 포트에서 실행되고 있는 DMFC의 Settings에서 포트가 COM {port}를 가리키고 있는지 확인하세요.")
            return False
    return prefixes

def _store_sum_by_room(date, port, room, check_empty_intervals = False):
    date = datetime.strftime(date, "%Y%m%d")
    cursor.execute("select * from dmfc_log where date=? and room=? order by time asc", (date, room))
    res = cursor.fetchall()
    if not res:
        warning(port, f"{date} 날짜의 데이터가 없습니다.")
        return
    if check_empty_intervals:
        times = [0, *map(lambda x: hms2sec(x[1]), res), 86399]
        for idx, (t1, t2) in enumerate(pairwise(times)):
            if (t2 - t1 > 10):
                start = "00:00:00" if idx == 0 else res[idx - 1][1]
                end = "23:59:59" if idx == len(times) - 2 else res[idx][1]
                warning(port, f"{date} 날짜에 {start}부터 {end}까지 간격이 너무 깁니다.")

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
            succeed(port, "로그 파일이 유효합니다.")
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

def db_to_xlsx():
    query = "SELECT * FROM dmfc_sum"
    df = pd.read_sql_query(query, conn)
    df["Price"] = df["IntSum"].apply(calculate_price)
    try:
        df.to_excel('./usageSummary.xlsx', index=False, engine='openpyxl')
    except PermissionError:
        warning(None, "./usageSummary.xlsx 파일이 다른 프로그램에 의해 사용 중이거나 접근 권한이 없습니다.",
                f"대신, ./usageSummary_{strftoday()}에 저장합니다.")
        df.to_excel(f"./usageSummary_{strftoday()}.xlsx", index = False, engine='openpyxl')
        
    succeed(None, "합계 DB를 엑셀 파일로 변환하였습니다. usageSummary.xlsx에서 확인해 보세요.")