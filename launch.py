import os
from subprocess import getstatusoutput
from log_fetcher import store_to_db, db_to_xlsx
from constants import CMD, SANDBOXIE_DIR, DMFC_DIR, BOX_OPTION, LOG_DIR
from dbutils import db_init, db_close
from error_logger import logger_init, error, warning, succeed

def check_sandboxie_running():
    # check if sandboxie is running
    working = [False, False, False, False]
    for idx in [4, 5, 6, 7]:
        try: 
            fetch = getstatusoutput(CMD(idx, "/listpids | more"))
            fetch = fetch[1].split("\n")
        except Exception as e:
            warning(idx, "작동 중인 프로세스를 찾지 못했습니다.", e)
            continue
    
        if (len(fetch) <= 2):
            warning(idx, "DMFC for Windows가 작동하지 않습니다. (동작하는 프로그램이 없습니다.)")
            continue
        fetch = fetch[1:-1]

        flag = False
        for pid in fetch:
            try:
                _, cl = getstatusoutput(f"wmic process where processid={pid} get commandline")
            except Exception as e:
                continue
            if "DMFC for Windows.exe" in cl:
                flag = True

        working[idx - 4] = flag
        if flag:
            succeed(idx, "DMFC for Windows가 작동합니다.")
        else:
            warning(idx, "DMFC for Windows가 작동하지 않습니다. (동작 중인 프로그램이 있으나, DMFC를 찾지 못했습니다.)")
    
    return working


def run_sandboxie():
    for idx in [4, 5, 6, 7]:
        try:
            os.system(CMD(idx, DMFC_DIR[idx]))
        except Exception as e:
            error(idx, "프로그램 재실행 중 오류가 발생하였습니다.", e)
        finally:
            succeed(idx, "프로그램 재실행 성공")

def terminate_sandboxie():
    for idx in [4, 5, 6, 7]:
        try:
            os.system(CMD(idx, f"/terminate {DMFC_DIR[idx]}"))
        except Exception as e:
            warning(idx, "프로그램 종료 중 오류가 발생하였습니다.", e)

if (__name__ == "__main__"):
    logger_init()
    db_init()
    check_sandboxie_running()
    store_to_db()
    db_to_xlsx()
    terminate_sandboxie()
    run_sandboxie()
    db_close()