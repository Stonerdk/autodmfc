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

ROOMS = {
    4: ["4-403", "4-405", "4-407"],
    5: ["2-211", "2-232"],
    6: ["1-128", "1-113"],
    7: ["3-307", "3-316", "3-322", "3-324", "3-315"]
}

MATTER_PRICE = 275
DENSITY = 0.7996

def CMD(idx, app):
    return f"{SANDBOXIE_DIR} {BOX_OPTION[idx]} {app}"