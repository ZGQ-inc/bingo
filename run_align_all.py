# -*- coding: utf-8 -*-
"""
Run Full Pixel-Accurate Alignment on all 68 Bingo & Bottle Cards
"""
import os
import glob
import json
import cv2
import numpy as np
from align_all_cards import (
    BINGO_DIR, IMAGES_DIR, DATA_DIR, CARDS_DIR, DEBUG_DIR,
    OCR_RAW, CATEGORIES, CAT_MAP, SPECIAL_CONFIGS, detect_grid_lines
)

TITLE_MAP = {
    '0@files_240714_190652_653.jpg': ('数码高手宾果', '如果能连成线你就是数码高手', 'tech'),
    '100@files_260422_012746_955.jpg': ('健全人BINGO', '如果五个连成一条线，那么恭喜你，你是现在偏少见的健全人', 'life'),
    '112@files_250130_123227_087.jpg': ('简中电报老人宾果', '连成一条线说明你不仅是简中电报老人，而且已经是个老贵物了', 'tech'),
    '114@files_250828_134840_804.jpg': ('TXL青春bingo (淫魔版)', '五个连成一条线，说明你有一个极其淫荡的青春', 'subculture'),
    '118@files_260422_015403_647.png': ('福瑞控这辈子有了bingo', '五个连成一条就说明你是哈比福瑞控', 'furry'),
    '119@files_260501_193157_735.jpg': ('DISCORD群男娘识别手册', '男娘行为特征大盘点，你中了几条？', 'subculture'),
    '11@files_240709_204521_425.jpg': ('肥宅賓果', '一秒沒網路就會發瘋，能不出門就不出門的真實肥宅生活', 'gaming'),
    '124@files_260814_001025_612.jpg': ('中小学违纪BINGO', '五个连成一条线，说明你是当年的违纪大王', 'youth'),
    '126@files_260903_183733_276.jpg': ('地狱牛马冰果游戏', '工资拖发、房贷未还，打工人的地狱真实写照', 'life'),
    '12@files_240807_225230_644.jpg': ('エロ身体ビンゴゲーム', '连成一线你就拥有一副十分色情的身体，你这辈子就算完了', 'kink'),
    '133@files_261023_182624_567.jpg': ('好色男娘宾果', '连成一线你这辈子就算完了', 'subculture'),
    '13@files_240711_173632_457.jpg': ('网络遗老宾果游戏', '圈出你玩过的经典老游戏，五个连成一线你就是网络老东西', 'gaming'),
    '14@files_240811_115603_484.jpg': ('鹿管宾果', '五个连成一线证明你喜欢鹿管 (限定18岁以上才能玩)', 'kink'),
    '15@files_240711_190359_918.jpg': ('社会指数宾果游戏', '如果有其中一条线连起来，你就不仅不社会，还是完全的现充', 'life'),
    '16@files_240711_190359_914.jpg': ('自设批宾果游戏', '五个连成一线就是纯种自设批', 'furry'),
    '17@files_240711_190359_896.jpg': ('新时代中国青年宾果', '五个连成线，八辈子都有了', 'life'),
    '18@files_250601_210222_969.jpg': ('福瑞控XP宾果', '转发给你的朋友看看谁是真色批', 'furry'),
    '19@files_240718_151335_837.jpg': ('社交网络遗老宾果', '圈出你玩过的网络平台，一条线连成5个说明你是互联网乐子人', 'tech'),
    '1@files_240703_100714_406.jpg': ('无可救药的福瑞控 (中国大陆加强版)', '五个连成线你就是无可救药的福瑞控', 'furry'),
    '20@files_240718_195043_265.jpg': ('互联网老登宾果游戏 (软件图标版)', '5个连成一线你就是一个合格的互联网老登了', 'tech'),
    '21@files_240802_221453_571.jpg': ("CFERALSOREN'S Kink Bingo", 'Adult preferences & kink board', 'kink'),
    '22@files_240802_221453_562.jpg': ("SAMMY'S Kink Bingo", 'Adult preferences & Kink bingo', 'kink'),
    '23@files_250620_233330_390.jpg': ('人生已完成清单', '来看看你的人生已解锁了哪些经历与遗憾 (百项目标清单)', 'life'),
    '24@files_240804_213836_130.jpg': ('这辈子有了BINGO', '五个连成一线，你这辈子就彻彻底底完完全全地有了', 'life'),
    '25@files_240804_213836_133.jpg': ('Shiny 青春 BINGO', '五个连成一线，说明你度过了一个闪耀的青春，恭喜贺喜！', 'youth'),
    '26@files_251019_080126_924.jpg': ('My Silly Ass: Furry Bingo', 'Check off your silly furry traits', 'furry'),
    '27@files_240806_190323_406.jpg': ('小南梁宾果游戏', '五个连成一线的话你就是艾草小南梁', 'subculture'),
    '29@files_240806_190323_406.jpg': ('小南梁宾果游戏', '五个连成一线的话你就是艾草小南梁', 'subculture'),
    '2@files_240629_193940_313.jpg': ('填满你的性癖罐子 (Furry)', '圈出并填满属于你的福瑞XP罐子 (转发时请附一张原图)', 'furry'),
    '32@files_240814_172532_659.jpg': ('电脑高手宾果游戏 (初级)', '连成两条线=电脑高手 / 三条线=电脑奇才 / 四条线=电脑皇帝', 'tech'),
    '34@files_240816_213708_820.jpg': ('群友逆天发言交流群BINGO', '记录群聊里的逆天瞬间与群友抽象言论', 'chat'),
    '35@files_240901_145348_189.jpg': ('男同性恋奇怪BINGO', '五个连成一线证明你是奇怪的人 (限定18岁以上才能玩)', 'subculture'),
    '38@files_240807_173654_908.jpg': ('R18-G 猎奇BINGO', '5个连成一线/大于7个证明你是guro大魔', 'kink'),
    '39@files_240807_191721_365.jpg': ('Good青春BINGO (困难版)', '五个连成一线，说明你度过了一个相对幸福的青春，值得庆祝！', 'youth'),
    '3@files_240802_205052_011.jpg': ('人下人BINGO游戏', '五个连成一条线即可享受牛马人生', 'life'),
    '40@files_250522_194802_143.jpg': ('社会指数宾果游戏', '连成一条线证明你不社会，是完完全全的现充', 'life'),
    '42@files_261102_185514_195.png': ('BL性癖の瓶 (第一弹)', '译:TG @ZGQinC / 作:@mochikouki (填满之后也请附带原图发出哦♪)', 'subculture'),
    '43@files_261102_185514_200.png': ('BL性癖の瓶 2 (第二弹)', '作:@mochikouki / 译:TG @ZGQinC (填满之后也请附带原图发出哦♪)', 'subculture'),
    '44@files_250705_194907_795.jpg': ('快乐BINGO', '不必连成一条线，希望这张表能让你想起那些快乐的时刻 (5行×7列)', 'life'),
    '45@files_251215_003824_612.jpg': ('重度福瑞控BINGO', '经典5x5格子，连成一行你就妥妥的是重度福瑞控了～', 'furry'),
    '46@files_240807_204904_769.jpg': ('银行卡密码宾果游戏', '看看你的6位银行卡密码能不能连成一条线 (10行×6列)', 'tech'),
    '47@files_250715_143110_854.jpg': ('雄性喜好分数大调查 (重口味版)', '点选自己的喜好，最后结算积分评级 (多选打分)', 'kink'),
    '48@files_260212_225512_496.jpg': ('青春撸管生活宾果', '连成线你就是赢家，记录青春的荷尔蒙生活', 'kink'),
    '4@files_240705_114742_726.jpg': ('南通宾果游戏', '五个连成一线就是南通，分享你的作业找到南通朋友', 'subculture'),
    '51@files_251026_143211_703.jpg': ('南梁宾果游戏', '五个连成一线你就是超可爱的香香软软的小南梁啦awa', 'subculture'),
    '54@files_240904_115847_120.jpg': ('抽象唐氏BINGO', '五个连上你就糖丸了！制表人：Alice514', 'life'),
    '57@files_240926_193856_648.jpg': ('非典型福瑞控BINGO', '如果连成一条线说明还能喝中药救回来', 'furry'),
    '59@files_241016_090113_143.jpg': ('福瑞控青春BINGO (简单版)', '五个连成一条线，说明你有一个比较放得开的青春', 'furry'),
    '5@files_240705_114742_724.jpg': ('男娘与木桶饭宾果游戏', '4个连在一起你就是男娘，5个连在一起你就是木桶饭', 'subculture'),
    '60@files_260228_223821_799.jpg': ('CS 小男娘 BINGO', 'FPS硬核玩家与可爱男娘的奇妙交集', 'gaming'),
    '61@files_241016_134125_979.jpg': ('Good青春BINGO (极难版)', '五个连成一条线，说明你拥有一个极其幸福的青春', 'youth'),
    '63@files_241016_194559_241.jpg': ('エロ身体宾果 (极色版)', '连成一线你就拥有一副十分色情的身体，这辈子就算完了', 'kink'),
    '65@files_241021_213615_641.jpg': ('美食大师BINGO游戏', '五点连成一线说明你是无可挑剔的美食大师', 'life'),
    '66@files_241024_152020_113.jpg': ('地狱牛马打工冰果游戏', '工资拖发、房贷未还，打工人的真实写照', 'life'),
    '67@files_241026_110020_669.jpg': ('福瑞控青春BINGO (淫魔版)', '五个连成一条线，说明你有一个极其狂野的青春', 'furry'),
    '68@files_241202_223812_678.jpg': ('猫娘宾果游戏', '五点连成一线说明你是一只合格的傲娇可爱猫娘', 'subculture'),
    '69@files_241029_121400_695.jpg': ('阿宅宾果游戏', '如果5个连成一线，你就是纯度极高的老阿宅', 'gaming'),
    '6@files_240709_091829_671.jpg': ('电子天才宾果游戏', '如果其中一条连成线，说明你是天才黑客', 'tech'),
    '74@files_241203_201909_189.jpg': ('证明自己不是赛博电脑废物宾果 V1.3', '成功连接一条线吧！证明自己的硬核电脑技能', 'tech'),
    '75@files_241210_185513_917.jpg': ('Good青春BINGO (超极难版)', '五个连成一条线，说明你度过了一个极其幸福的青春，恭喜你！', 'youth'),
    '76@files_241212_153014_064.jpg': ('群友如何评价我', '填给群玩具、群友的互动评价表 (共63项)', 'chat'),
    '79@files_241227_085314_983.jpg': ('游戏老玩家宾果', '圈出你玩过的经典大作，只要连成一线说明你是游戏王', 'gaming'),
    '7@files_240706_160138_280.jpg': ('先天计算机圣体宾果游戏', '如果其中一条连成线，说明你是先天计算机圣体', 'tech'),
    '81@files_241227_090643_448.jpg': ('高水平玩家宾果游戏', '硬核玩家与全成就达成测试', 'gaming'),
    '83@files_241227_100826_230.jpg': ('社会指数宾果游戏', '测试你的社会人属性与现充指数', 'life'),
    '87@files_241227_220524_554.jpg': ('你群宾果游戏', '连成一条线说明你群就是一个标准的逆天抽象群', 'chat'),
    '8@files_250202_205820_006.jpg': ('逆天群聊BINGO', '连成一条线就能超越95%的抽象神仙群聊', 'chat'),
    '9@files_251019_080126_914.jpg': ('My Silly Ass: Furry Bingo (EN)', 'Have furry stickers, furry music & silly traits', 'furry'),
    '122@0_260628_160043_728.jpg': ('感觉有多少就涂多少 (群友评价)', '让你的群友评价评价你，发的时候留份原表不然没法玩', 'chat')
}

img_files = sorted(os.listdir(IMAGES_DIR))
print(f"Aligning {len(img_files)} images...")

all_games = []

for idx, fname in enumerate(img_files):
    card_id = f"card_{idx:02d}"
    im_path = os.path.join(IMAGES_DIR, fname)
    im = cv2.imread(im_path)
    if im is None:
        print(f"Warning: could not read {fname}")
        continue
    h, w = im.shape[:2]

    # Meta
    if fname in SPECIAL_CONFIGS:
        sp = SPECIAL_CONFIGS[fname]
        card_type = sp['type']
        title = sp['title']
        sub = sp['subtitle']
        cat_id = sp['categoryId']
        rows = sp['rows']
        cols = sp['cols']
    elif fname in TITLE_MAP:
        title, sub, cat_id = TITLE_MAP[fname]
        card_type = 'bingo'
        rows = 5
        cols = 5
    else:
        title = f"宾果游戏 #{idx}"
        sub = "连成一线即为胜出"
        cat_id = "life"
        card_type = 'bingo'
        rows = 5
        cols = 5

    cat_meta = CAT_MAP.get(cat_id, {'name': '生活与日常', 'icon': '☕'})

    # Cell calculation
    cells = []
    annotated = im.copy()

    if card_type == 'bottle':
        sp = SPECIAL_CONFIGS[fname]
        grid = sp['grid']
        spec = sp['spec']
        # Load bottle labels from old json if present
        old_json_p = os.path.join(CARDS_DIR, f"{card_id}.json")
        labels = []
        if os.path.exists(old_json_p):
            try:
                old_d = json.load(open(old_json_p, encoding='utf-8'))
                labels = [c.get('label') or c.get('text') for c in old_d.get('cells', [])]
            except:
                pass
        
        c_idx = 0
        for r in range(rows):
            for c in range(cols):
                cx = spec['cx0'] + c * spec['step_x']
                y_bot = spec['y_bottom0'] + r * spec['step_y']
                bw = spec['bw']
                bh = spec['bh']
                bx = int(cx - bw / 2)
                by = int(y_bot - bh)
                lbl = labels[c_idx] if c_idx < len(labels) else f"罐子 {r+1}-{c+1}"
                cells.append({
                    'index': c_idx,
                    'row': r,
                    'col': c,
                    'x': bx, 'y': by, 'w': int(bw), 'h': int(bh),
                    'y_bottom': int(y_bot),
                    'bw': int(bw), 'bh': int(bh),
                    'label': lbl, 'text': lbl
                })
                # Draw on annotated
                cv2.rectangle(annotated, (bx, by), (bx + int(bw), by + int(bh)), (255, 0, 0), 2)
                cv2.circle(annotated, (int(cx), int(y_bot - bh/2)), 4, (0, 0, 255), -1)
                c_idx += 1

    else:
        # Bingo or Checklist
        # If special explicit grid given, use it
        if fname in SPECIAL_CONFIGS and 'grid' in SPECIAL_CONFIGS[fname]:
            grid = SPECIAL_CONFIGS[fname]['grid']
            x_lines = [int(grid['x'] + i * (grid['w'] / cols)) for i in range(cols + 1)]
            y_lines = [int(grid['y'] + i * (grid['h'] / rows)) for i in range(rows + 1)]
        else:
            grid_res = detect_grid_lines(im, expected_rows=rows, expected_cols=cols, fname=fname)
            grid = {
                'rows': rows,
                'cols': cols,
                'x': grid_res['x'],
                'y': grid_res['y'],
                'w': grid_res['w'],
                'h': grid_res['h']
            }
            x_lines = grid_res['x_lines']
            y_lines = grid_res['y_lines']

        # Get OCR items for text assignment
        ocr_items = OCR_RAW.get(fname, {}).get('items', [])

        # Build each cell
        c_idx = 0
        for r in range(rows):
            for c in range(cols):
                cx = x_lines[c]
                cy = y_lines[r]
                cw = x_lines[c+1] - cx
                ch = y_lines[r+1] - cy

                # If explicit cell texts provided
                if fname in SPECIAL_CONFIGS and 'cell_texts' in SPECIAL_CONFIGS[fname]:
                    cell_str = SPECIAL_CONFIGS[fname]['cell_texts'][r][c]
                else:
                    # Find OCR text items inside this cell box
                    cell_texts = []
                    for it in ocr_items:
                        pts = it['box']
                        center_x = sum(p[0] for p in pts) / 4.0
                        center_y = sum(p[1] for p in pts) / 4.0
                        # Check if center falls inside the cell with slight tolerance
                        if cx - 5 <= center_x <= cx + cw + 5 and cy - 5 <= center_y <= cy + ch + 5:
                            cell_texts.append(it['text'])

                    cell_str = ''.join(cell_texts).strip()
                
                is_center = (rows % 2 == 1 and cols % 2 == 1 and r == rows // 2 and c == cols // 2)
                
                if not cell_str:
                    cell_str = "FREE" if is_center else f"格子 {r+1}-{c+1}"

                cells.append({
                    'index': c_idx,
                    'row': r,
                    'col': c,
                    'x': cx,
                    'y': cy,
                    'w': cw,
                    'h': ch,
                    'text': cell_str,
                    'isCenter': is_center
                })

                # Debug draw
                cv2.rectangle(annotated, (cx, cy), (cx + cw, cy + ch), (255, 120, 0), 2)
                cv2.circle(annotated, (int(cx + cw/2), int(cy + ch/2)), 4, (0, 0, 255), -1)
                c_idx += 1

        # Draw grid boundary
        cv2.rectangle(annotated, (grid['x'], grid['y']), (grid['x'] + grid['w'], grid['y'] + grid['h']), (0, 255, 0), 3)

    # Save debug image
    debug_path = os.path.join(DEBUG_DIR, f"{card_id}_{fname.split('@')[0]}.jpg")
    cv2.imwrite(debug_path, annotated)

    # Save Card JSON
    card_json = {
        'id': card_id,
        'type': card_type,
        'filename': f"images/{fname}",
        'title': title,
        'subtitle': sub,
        'category': cat_meta['name'],
        'categoryId': cat_id,
        'categoryIcon': cat_meta['icon'],
        'width': w,
        'height': h,
        'grid': {
            'rows': rows,
            'cols': cols,
            'x': grid['x'],
            'y': grid['y'],
            'w': grid['w'],
            'h': grid['h']
        },
        'cellCount': len(cells),
        'cells': cells
    }

    with open(os.path.join(CARDS_DIR, f"{card_id}.json"), 'w', encoding='utf-8') as f:
        json.dump(card_json, f, ensure_ascii=False, indent=2)

    # Full card in games.json
    all_games.append(card_json)

# Save games.json
with open(os.path.join(DATA_DIR, 'games.json'), 'w', encoding='utf-8') as f:
    json.dump(all_games, f, ensure_ascii=False, indent=2)

print(f"Successfully processed all {len(all_games)} cards!")
