from configs import *

SANDBOXIE_DIR = 'C:"\\Program Files\\Sandboxie-Plus\\Start.exe"'
DAILY_LOG_DIR = "./usageSummary.xlsx"
DB_DIR = "./db/dmfc_log.db"

DMFC_DIR = {
    4: '"C:\\Program Files (x86)\\DMFC for Windows_4\\DMFC for Windows.exe"',
    5: '"C:\\Program Files (x86)\\DMFC for Windows_5\\DMFC for Windows.exe"',
    6: '"C:\\Program Files (x86)\\DMFC for Windows_6\\DMFC for Windows.exe"',
    7: '"C:\\Program Files (x86)\\DMFC for Windows\\DMFC for Windows.exe"'
}

LOG_DIR = {
    4: "C:\\Sandbox\\postech\\port_com4\\drive\\C\\Program Files (x86)\\DMFC for Windows_4\\LogData",
    5: "C:\\Sandbox\\postech\\port_com5\\drive\\C\\Program Files (x86)\\DMFC for Windows_5\\LogData",
    6: "C:\\Sandbox\\postech\\port_com6\\drive\\C\\Program Files (x86)\\DMFC for Windows_6\\LogData",
    7: "C:\\Sandbox\\postech\\port_com7\\drive\\C\\Program Files (x86)\\DMFC for Windows\\LogData",
}

BOX_OPTION = {
    4: "/box:port_com4",
    5: "/box:port_com5",
    6: "/box:port_com6",
    7: "/box:port_com7"
}

MATTER_PRICE = PRICE

ROOMS = {
    4: PORT_4,
    5: PORT_5,
    6: PORT_6,
    7: PORT_7
}

def CMD(idx, app):
    return f"{SANDBOXIE_DIR} {BOX_OPTION[idx]} {app}"