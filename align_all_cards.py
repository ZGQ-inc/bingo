# -*- coding: utf-8 -*-
"""
High-Precision Pixel Alignment & OCR Data Generator for all 68 Bingo Cards
"""
import os
import glob
import json
import cv2
import numpy as np

BINGO_DIR = os.path.dirname(os.path.abspath(__file__))
IMAGES_DIR = os.path.join(BINGO_DIR, 'images')
DATA_DIR = os.path.join(BINGO_DIR, 'data')
CARDS_DIR = os.path.join(DATA_DIR, 'cards')
DEBUG_DIR = os.path.join(BINGO_DIR, 'grid_debug_images')
os.makedirs(CARDS_DIR, exist_ok=True)
os.makedirs(DEBUG_DIR, exist_ok=True)

# Load OCR raw data
with open(os.path.join(BINGO_DIR, '_ocr_raw.json'), 'r', encoding='utf-8') as f:
    OCR_RAW = json.load(f)

# Categories
CATEGORIES = json.load(open(os.path.join(DATA_DIR, 'categories.json'), encoding='utf-8'))
CAT_MAP = {c['id']: c for c in CATEGORIES}

def cluster(indices, max_gap=12):
    if len(indices) == 0: return []
    res = []
    cur = [indices[0]]
    for idx in indices[1:]:
        if idx - cur[-1] <= max_gap:
            cur.append(idx)
        else:
            res.append(int(np.mean(cur)))
            cur = [idx]
    res.append(int(np.mean(cur)))
    return res

# Explicit configurations for cards that have special shapes or need exact coordinate tuning
SPECIAL_CONFIGS = {
    # Bottle cards (now categorized into real themes: Furry, Subculture, Chat)
    '42@files_261102_185514_195.png': {
        'type': 'bottle',
        'title': 'BL性癖の瓶 (第一弹)',
        'subtitle': '译:TG @ZGQinC / 作:@mochikouki (填满之后也请附带原图发出哦♪)',
        'categoryId': 'subculture',
        'rows': 5, 'cols': 7,
        'grid': {'x': 50, 'y': 340, 'w': 1184, 'h': 1550},
        'spec': {'cx0': 118, 'step_x': 170, 'y_bottom0': 548, 'step_y': 330, 'bw': 90, 'bh': 178}
    },
    '43@files_261102_185514_200.png': {
        'type': 'bottle',
        'title': 'BL性癖の瓶 2 (第二弹)',
        'subtitle': '作:@mochikouki / 译:TG @ZGQinC (填满之后也请附带原图发出哦♪)',
        'categoryId': 'subculture',
        'rows': 5, 'cols': 7,
        'grid': {'x': 50, 'y': 340, 'w': 1184, 'h': 1550},
        'spec': {'cx0': 118, 'step_x': 170, 'y_bottom0': 548, 'step_y': 330, 'bw': 90, 'bh': 178}
    },
    '2@files_240629_193940_313.jpg': {
        'type': 'bottle',
        'title': '填满你的性癖罐子 (Furry)',
        'subtitle': '圈出并填满属于你的福瑞XP罐子 (转发时请附一张原图)',
        'categoryId': 'furry',
        'rows': 4, 'cols': 13,
        'grid': {'x': 18, 'y': 170, 'w': 1244, 'h': 540},
        'spec': {'cx0': 66, 'step_x': 95.8, 'y_bottom0': 230, 'step_y': 135, 'bw': 60, 'bh': 95}
    },
    '122@0_260628_160043_728.jpg': {
        'type': 'bottle',
        'title': '感觉有多少就涂多少 (群友评价)',
        'subtitle': '让你的群友评价评价你，发的时候留份原表不然没法玩',
        'categoryId': 'chat',
        'rows': 4, 'cols': 8,
        'grid': {'x': 40, 'y': 180, 'w': 880, 'h': 750},
        'spec': {'cx0': 95, 'step_x': 110, 'y_bottom0': 275, 'step_y': 190, 'bw': 82, 'bh': 88}
    },
    # Checklists
    '76@files_241212_153014_064.jpg': {
        'type': 'checklist',
        'title': '群友如何评价我',
        'subtitle': '填给群玩具、群友的互动评价表 (共63项)',
        'categoryId': 'chat',
        'rows': 21, 'cols': 3,
        'grid': {'x': 15, 'y': 48, 'w': 578, 'h': 1220}
    },
    '47@files_250715_143110_854.jpg': {
        'type': 'checklist',
        'title': '雄性喜好分数大调查 (重口味版)',
        'subtitle': '点选自己的喜好，最后结算积分评级 (多选打分)',
        'categoryId': 'kink',
        'rows': 15, 'cols': 6,
        'grid': {'x': 10, 'y': 40, 'w': 380, 'h': 580}
    },
    '23@files_250620_233330_390.jpg': {
        'type': 'checklist',
        'title': '人生已完成清单',
        'subtitle': '来看看你的人生已解锁了哪些经历与遗憾 (百项目标清单)',
        'categoryId': 'life',
        'rows': 19, 'cols': 1,
        'grid': {'x': 18, 'y': 95, 'w': 764, 'h': 880}
    },
    # Non 5x5 grids
    '46@files_240807_204904_769.jpg': {
        'type': 'bingo',
        'title': '银行卡密码宾果游戏',
        'subtitle': '看看你的6位银行卡密码能不能连成一条线 (10行×6列)',
        'categoryId': 'tech',
        'rows': 10, 'cols': 6,
        'grid': {'x': 30, 'y': 290, 'w': 1160, 'h': 730}
    },
    '32@files_240814_172532_659.jpg': {
        'type': 'bingo',
        'title': '电脑高手宾果游戏 (初级)',
        'subtitle': '连成两条线=电脑高手 / 三条线=电脑奇才 / 四条线=电脑皇帝 (4行×4列)',
        'categoryId': 'tech',
        'rows': 4, 'cols': 4,
        'grid': {'x': 0, 'y': 230, 'w': 982, 'h': 778}
    },
    '57@files_240926_193856_648.jpg': {
        'type': 'bingo',
        'title': '非典型福瑞控BINGO',
        'subtitle': '如果连成一条线说明还能喝中药救回来 (4行×4列)',
        'categoryId': 'furry',
        'rows': 4, 'cols': 4,
        'grid': {'x': 72, 'y': 167, 'w': 537, 'h': 502}
    },
    '79@files_241227_085314_983.jpg': {
        'type': 'bingo',
        'title': '游戏老玩家宾果',
        'subtitle': '圈出你玩过的经典大作，只要连成一线说明你是游戏王 (6行×6列)',
        'categoryId': 'gaming',
        'rows': 6, 'cols': 6,
        'grid': {'x': 26, 'y': 247, 'w': 924, 'h': 925}
    },
    '7@files_240706_160138_280.jpg': {
        'type': 'bingo',
        'title': '先天计算机圣体宾果游戏',
        'subtitle': '如果其中一条连成线，说明你是先天计算机圣体',
        'categoryId': 'tech',
        'rows': 5, 'cols': 5,
        'grid': {'x': 2, 'y': 111, 'w': 488, 'h': 505}
    },
    '17@files_240711_190359_896.jpg': {
        'type': 'bingo',
        'title': '新时代中国青年宾果',
        'subtitle': '五个连成线，八辈子都有了',
        'categoryId': 'life',
        'rows': 5, 'cols': 5,
        'grid': {'x': 1, 'y': 72, 'w': 582, 'h': 362}
    },
    '39@files_240807_191721_365.jpg': {
        'type': 'bingo',
        'title': 'Good青春BINGO (困难版)',
        'subtitle': '五个连成一条线，说明你度过了一个相对幸福的青春，值得庆祝！',
        'categoryId': 'youth',
        'rows': 5, 'cols': 5,
        'grid': {'x': 0, 'y': 167, 'w': 1277, 'h': 539}
    },
    '60@files_260228_223821_799.jpg': {
        'type': 'bingo',
        'title': 'CS 小男娘 BINGO',
        'subtitle': 'FPS硬核玩家与可爱男娘的奇妙交集',
        'categoryId': 'gaming',
        'rows': 5, 'cols': 5,
        'grid': {'x': 1, 'y': 152, 'w': 973, 'h': 984}
    },
    '48@files_260212_225512_496.jpg': {
        'type': 'bingo',
        'title': '青春撸管生活宾果',
        'subtitle': '连成线你就是赢家，记录青春的荷尔蒙生活',
        'categoryId': 'kink',
        'rows': 5, 'cols': 5,
        'grid': {'x': 43, 'y': 95, 'w': 1092, 'h': 1091},
        'cell_texts': [
            ["初中开始撸", "一周撸五次", "靠想象撸过", "尝试戒撸多次", "有三种以上的性癖"],
            ["拥有多种资源", "不撸浑身难受", "用玩具撸过", "从没遗过精", "二三次元都撸"],
            ["打算一直撸到老", "在室外撸过", "压力大的时候撸", "开心的时候撸", "难受的时候撸"],
            ["一天撸过多次", "有百撸不厌的资源", "经常有色情幻想", "小头控制过大头", "撸完精神萎靡"],
            ["没实战过", "对着现实的人撸过", "半夜起床撸过", "早上晨勃撸过", "撸后尿道刺痛"]
        ]
    },
    '20@files_240718_195043_265.jpg': {
        'type': 'bingo',
        'title': '互联网老登宾果游戏 (软件图标版)',
        'subtitle': '5个连成一线你就是一个合格的互联网老登了',
        'categoryId': 'tech',
        'rows': 5, 'cols': 5,
        'grid': {'x': 22, 'y': 83, 'w': 1148, 'h': 798},
        'cell_texts': [
            ["Winamp", "ACDSee", "FlashGet (快车)", "金山游侠", "Nero Burning ROM"],
            ["暴风影音 (早期)", "RealPlayer", "网络蚂蚁 (NetAnts)", "千千静听 (TTPlayer)", "网景 (Netscape)"],
            ["Windows Media Player", "东方快车 / 金山词霸", "Internet Explorer 6", "QuickTime", "eMule (电驴)"],
            ["Linux (Tux)", "傲游浏览器 (Maxthon)", "foobar2000", "金山毒霸", "MSN Messenger"],
            ["豪杰超级解霸", "瑞星杀毒 (小狮子)", "µTorrent", "暴风影音 (彩环)", "瑞星卡卡安全助手"]
        ]
    },
    '13@files_240711_173632_457.jpg': {
        'type': 'bingo',
        'title': '网络遗老宾果游戏',
        'subtitle': '圈出你玩过的经典老游戏，五个连成一线你就是网络老东西 (3行×5列)',
        'categoryId': 'gaming',
        'rows': 3, 'cols': 5,
        'grid': {'x': 8, 'y': 150, 'w': 568, 'h': 315}
    },
    '44@files_250705_194907_795.jpg': {
        'type': 'bingo',
        'title': '快乐BINGO',
        'subtitle': '不必连成一条线，希望这张表能让你想起那些快乐的时刻 (5行×7列)',
        'categoryId': 'life',
        'rows': 5, 'cols': 7,
        'grid': {'x': 20, 'y': 195, 'w': 1174, 'h': 875}
    }
}

def detect_grid_lines(im, expected_rows=5, expected_cols=5, fname=""):
    h, w = im.shape[:2]
    gray = cv2.cvtColor(im, cv2.COLOR_BGR2GRAY)
    thresh = cv2.adaptiveThreshold(~gray, 255, cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY, 15, -2)

    best_grid = None

    for k_ratio in [0.15, 0.20, 0.10, 0.08, 0.05, 0.25]:
        h_k = cv2.getStructuringElement(cv2.MORPH_RECT, (max(12, int(w * k_ratio)), 1))
        h_lines = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, h_k)
        v_k = cv2.getStructuringElement(cv2.MORPH_RECT, (1, max(12, int(h * k_ratio))))
        v_lines = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, v_k)

        # Find internal vertical lines
        v_proj = np.sum(v_lines > 0, axis=0)
        v_max = np.max(v_proj)
        if v_max == 0: continue
        
        # Test varying thresholds to find exactly expected_cols + 1
        for v_mult in [0.35, 0.30, 0.25, 0.40, 0.45]:
            v_idx = np.where(v_proj > v_max * v_mult)[0]
            x_lines = cluster(v_idx, max_gap=int(w * 0.025))

            if len(x_lines) == expected_cols + 1:
                # Check vertical range of interior vertical dividers (ignore outer borders)
                int_v = np.sum(v_lines[:, x_lines[1]-4:x_lines[-2]+4], axis=1)
                y_active = np.where(int_v > 0)[0]
                if len(y_active) > 0:
                    y_start = y_active[0]
                    y_end = y_active[-1]
                    
                    # Horizontal lines within this active vertical range
                    h_sub = h_lines[max(0, y_start-20):min(h, y_end+20), :]
                    h_proj = np.sum(h_sub > 0, axis=1)
                    h_max = np.max(h_proj)
                    if h_max > 0:
                        for h_mult in [0.35, 0.30, 0.25, 0.40]:
                            h_idx = np.where(h_proj > h_max * h_mult)[0] + max(0, y_start-20)
                            y_lines = cluster(h_idx, max_gap=int(h * 0.025))
                            if len(y_lines) == expected_rows + 1:
                                return {
                                    'x_lines': x_lines,
                                    'y_lines': y_lines,
                                    'x': x_lines[0],
                                    'y': y_lines[0],
                                    'w': x_lines[-1] - x_lines[0],
                                    'h': y_lines[-1] - y_lines[0],
                                    'method': 'line_projection'
                                }

    # Fallback method: Use OCR bounding boxes excluding header area
    items = OCR_RAW.get(fname, {}).get('items', [])
    non_header = [it for it in items if min(p[1] for p in it['box']) > h * 0.15]
    if non_header and len(non_header) >= 15:
        # Find x_min, x_max, y_min, y_max of cell texts
        x_min = min(min(p[0] for p in it['box']) for it in non_header)
        x_max = max(max(p[0] for p in it['box']) for it in non_header)
        y_min = min(min(p[1] for p in it['box']) for it in non_header)
        y_max = max(max(p[1] for p in it['box']) for it in non_header)
        
        # Add padding to reach cell borders
        pad_x = int((x_max - x_min) / expected_cols * 0.18)
        pad_y = int((y_max - y_min) / expected_rows * 0.22)
        
        gx = max(6, x_min - pad_x)
        gy = max(int(h * 0.12), y_min - pad_y)
        gw = min(w - gx - 4, (x_max - x_min) + 2 * pad_x)
        gh = min(h - gy - 4, (y_max - y_min) + 2 * pad_y)
        
        x_lines = [int(gx + i * (gw / expected_cols)) for i in range(expected_cols + 1)]
        y_lines = [int(gy + i * (gh / expected_rows)) for i in range(expected_rows + 1)]
        return {
            'x_lines': x_lines,
            'y_lines': y_lines,
            'x': gx, 'y': gy, 'w': gw, 'h': gh,
            'method': 'ocr_bounds'
        }

    # Ultimate fallback: 5x5 centered
    gx = int(w * 0.05)
    gy = int(h * 0.20)
    gw = int(w * 0.90)
    gh = int(h * 0.76)
    x_lines = [int(gx + i * (gw / expected_cols)) for i in range(expected_cols + 1)]
    y_lines = [int(gy + i * (gh / expected_rows)) for i in range(expected_rows + 1)]
    return {
        'x_lines': x_lines,
        'y_lines': y_lines,
        'x': gx, 'y': gy, 'w': gw, 'h': gh,
        'method': 'fallback'
    }

print("Grid detector ready.")
