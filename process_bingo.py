# -*- coding: utf-8 -*-
"""
Bingo Data Processor (Refined)
Accurately separates titles, subtitles, rules, grid layouts, and cell OCR texts.
"""
import os
import glob
import json
import re
import cv2
import numpy as np
from PIL import Image

BINGO_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BINGO_DIR, 'data')
CARDS_DIR = os.path.join(DATA_DIR, 'cards')
os.makedirs(CARDS_DIR, exist_ok=True)

CATEGORIES_META = [
    {'id': 'all', 'name': '全部宾果', 'icon': '🎯', 'desc': '所有收录的宾果游戏'},
    {'id': 'tech', 'name': '科技与数码', 'icon': '💻', 'desc': '数码玩家、程序员、电脑极客与互联网老登'},
    {'id': 'gaming', 'name': '游戏世界', 'icon': '🎮', 'desc': '主机老玩家、Steam遗老与竞技游戏同好'},
    {'id': 'furry', 'name': '福瑞专区', 'icon': '🐾', 'desc': '福瑞控、自设、XP罐子与兽人文化'},
    {'id': 'subculture', 'name': '圈子与同好', 'icon': '🌈', 'desc': '男娘、南梁、同性、猫娘与独特圈子'},
    {'id': 'chat', 'name': '群聊与社交', 'icon': '💬', 'desc': '逆天群友、社群黑话与群聊氛围测试'},
    {'id': 'youth', 'name': '青春与成长', 'icon': '🎓', 'desc': '青春记忆、校园违纪与美好回忆'},
    {'id': 'life', 'name': '生活与日常', 'icon': '☕', 'desc': '健全人测试、牛马日常与人生清单'},
    {'id': 'kink', 'name': '成人与趣味', 'icon': '🔞', 'desc': '性癖测试、情趣小游戏与私密趣味'}
]

CAT_MAP = {c['id']: c for c in CATEGORIES_META}

# Custom manual overrides for known cards with complex layouts or special titles
TITLE_OVERRIDES = {
    '0@files_240714_190652_653.jpg': ('数码高手宾果', '如果能连成线你就是数码高手', 'tech'),
    '100@files_260422_012746_955.jpg': ('健全人BINGO', '如果五个连成一条线，那么恭喜你，你是现在偏少见的健全人', 'life'),
    '112@files_250130_123227_087.jpg': ('简中电报老人宾果', '连成一条线说明你不仅是简中电报老人，而且已经是个老贵物了', 'tech'),
    '114@files_250828_134840_804.jpg': ('TXL青春bingo (淫魔版)', '五个连成一条线，说明你有一个极其淫荡的青春', 'subculture'),
    '118@files_260422_015403_647.png': ('福瑞控这辈子有了bingo', '五个连成一条就说明你是哈比福瑞控', 'furry'),
    '119@files_260501_193157_735.jpg': ('DISCORD群男娘识别手册', '男娘行为特征大盘点，你中了几条？', 'subculture'),
    '11@files_240709_204521_425.jpg': ('肥宅宾果', '一秒没网路，能不出门就不出门的真实肥宅生活', 'gaming'),
    '122@0_260628_160043_728.jpg': ('群友行为鉴定宾果', '感觉有多少就涂多少，让你的群友看看你有多逆天', 'chat'),
    '124@files_260814_001025_612.jpg': ('中小学违纪BINGO', '五个连成一条线，说明你是当年的违纪大王', 'youth'),
    '126@files_260903_183733_276.jpg': ('地狱牛马冰果游戏', '工资拖发、房贷未还，打工人的地狱真实写照', 'life'),
    '12@files_240807_225230_644.jpg': ('工口身体大测试', '连成一线你就拥有一副十分色情的身体', 'kink'),
    '133@files_261023_182624_567.jpg': ('好色男娘宾果', '连成一线你这辈子就算完了', 'subculture'),
    '13@files_240711_173632_457.jpg': ('网络遗老宾果游戏', '圈出你玩过的游戏，五个连成一条线你就是网络老东西', 'gaming'),
    '14@files_240811_115603_484.jpg': ('青春打胶生活宾果', '五个连成一线证明你喜欢打胶（限定18岁以上）', 'kink'),
    '15@files_240711_190359_918.jpg': ('社会指数宾果游戏', '如果有其中一条线连起来，你就不仅不社会，还是完全的现充', 'life'),
    '16@files_240711_190359_914.jpg': ('自设批宾果游戏', '五个连成一线就是纯种自设批', 'furry'),
    '17@files_240711_190359_896.jpg': ('新时代中国青年宾果', '五个连成线，八辈子都有了', 'life'),
    '18@files_250601_210222_969.jpg': ('福瑞控XP宾果', '转发给你的朋友看看谁是真色批', 'furry'),
    '19@files_240718_151335_837.jpg': ('社交网络遗老宾果', '圈出你玩过的网络平台，一条线连成5个说明你是互联网乐子人', 'tech'),
    '1@files_240703_100714_406.jpg': ('无可救药的福瑞控 (中国大陆加强版)', '五个连成线你就是无可救药的福瑞控', 'furry'),
    '20@files_240718_195043_265.jpg': ('互联网老登宾果游戏', '5个连成一线你就是一个合格的互联网老登了', 'tech'),
    '21@files_240802_221453_571.jpg': ("CFERALSOREN'S Kink Bingo", 'Kink & XP preferences checklist', 'kink'),
    '22@files_240802_221453_562.jpg': ("SAMMY'S Kink Bingo", 'Adult preferences & Kink bingo', 'kink'),
    '23@files_250620_233330_390.jpg': ('人生已完成清单', '来看看你的人生已解锁了哪些精彩与遗憾', 'life'),
    '24@files_240804_213836_130.jpg': ('这辈子有了BINGO', '五个连成一线，你这辈子就彻彻底底完完全全地有了', 'life'),
    '25@files_240804_213836_133.jpg': ('Shiny 青春 BINGO', '五个连成一线，说明你度过了一个闪耀的青春，恭喜贺喜！', 'youth'),
    '26@files_251019_080126_924.jpg': ('My Silly Ass: Furry Bingo', 'Check off your silly furry traits', 'furry'),
    '29@files_240806_190323_406.jpg': ('小南梁宾果游戏', '五个连成一线的话你就是艾草小南梁', 'subculture'),
    '2@files_240629_193940_313.jpg': ('填满你的性癖罐子 (Furry)', '圈出属于你的福瑞偏好', 'furry'),
    '32@files_240814_172532_659.jpg': ('电脑高手宾果游戏 (初级)', '连成两条线=电脑高手', 'tech'),
    '34@files_240816_213708_820.jpg': ('群友逆天发言交流群BINGO', '记录群聊里的逆天瞬间与群友抽象言论', 'chat'),
    '35@files_240901_145348_189.jpg': ('男同性恋奇怪BINGO', '五个连成一线证明你是奇怪的人（限定18岁以上才能玩）', 'subculture'),
    '38@files_240807_173654_908.jpg': ('R18-G 重口BINGO', '5个连成一线/大于7个证明你是猎奇大魔', 'kink'),
    '39@files_240807_191721_365.jpg': ('Good青春BINGO (困难版)', '五个连成一线，说明你度过了一个相对幸福的青春，值得庆祝！', 'youth'),
    '3@files_240802_205052_011.jpg': ('人下人BINGO游戏', '五个连成一条线即可享受牛马人生', 'life'),
    '40@files_250522_194802_143.jpg': ('社会指数宾果游戏', '连成一条线证明你不社会，是完完全全的现充', 'life'),
    '42@files_261102_185514_195.png': ('BL性癖の瓶 (第一弹)', '译:TG @ZGQinC / 作:@mochikouki', 'kink'),
    '43@files_261102_185514_200.png': ('BL性癖の瓶 (第二弹)', '作:@mochikouki / 译:TG @ZGQinC', 'kink'),
    '44@files_250705_194907_795.jpg': ('快乐BINGO', '不必连成一条线，希望这张表能让你想起那些快乐的时刻', 'life'),
    '45@files_251215_003824_612.jpg': ('重度福瑞控BINGO', '经典5x5格子，连成一行你就妥妥的是重度福瑞控了～', 'furry'),
    '46@files_240807_204904_769.jpg': ('银行卡密码宾果游戏', '看看你的银行卡密码能不能连成一条线', 'tech'),
    '47@files_250715_143110_854.jpg': ('雄性喜好分数大调查 (重口味版)', '点选自己的喜好，最后结算分数', 'kink'),
    '48@files_260212_225512_496.jpg': ('青春打胶生活宾果', '连成线你就是赢家，记录青春的荷尔蒙冲动', 'kink'),
    '4@files_240705_114742_726.jpg': ('南通宾果游戏', '五个连成一线就是南通，分享你的作业找到南通朋友', 'subculture'),
    '51@files_251026_143211_703.jpg': ('南梁宾果游戏', '五个连成一线你就是超可爱的香香软软的小南梁啦awa', 'subculture'),
    '54@files_240904_115847_120.jpg': ('抽象糖氏BINGO', '五个连上你就糖丸了！制表人：Alice514', 'life'),
    '57@files_240926_193856_648.jpg': ('非典型福瑞控BINGO', '如果连成一条线说明还能喝中药救回来', 'furry'),
    '59@files_241016_090113_143.jpg': ('福瑞控青春BINGO (简单版)', '五个连成一条线，说明你有一个比较放得开的青春', 'furry'),
    '5@files_240705_114742_724.jpg': ('男娘与木桶饭宾果游戏', '4个连在一起你就是男娘，5个连在一起你就是木桶饭', 'subculture'),
    '60@files_260228_223821_799.jpg': ('CS 小男娘 BINGO', 'FPS硬核玩家与可爱男娘的奇妙交集', 'gaming'),
    '61@files_241016_134125_979.jpg': ('Good青春BINGO (极难版)', '五个连成一条线，说明你拥有一个极其幸福的青春', 'youth'),
    '63@files_241016_194559_241.jpg': ('工口身体测试 (极色版)', '连成一线你就拥有一副十分色情的身体，这辈子就算完了', 'kink'),
    '65@files_241021_213615_641.jpg': ('美食大师BINGO游戏', '五点连成一线说明你是无可挑剔的美食大师', 'life'),
    '66@files_241024_152020_113.jpg': ('地狱牛马打工冰果游戏', '工资拖发、房贷未还，打工人的真实写照', 'life'),
    '67@files_241026_110020_669.jpg': ('福瑞控青春BINGO (淫魔版)', '五个连成一条线，说明你有一个极其狂野的青春', 'furry'),
    '68@files_241202_223812_678.jpg': ('猫娘宾果游戏', '五点连成一线说明你是一只合格的傲娇可爱猫娘', 'subculture'),
    '69@files_241029_121400_695.jpg': ('阿宅宾果游戏', '如果5个连成一线，你就是纯度极高的老阿宅', 'gaming'),
    '6@files_240709_091829_671.jpg': ('电子天才宾果游戏', '如果其中一条连成线，说明你是天才黑客', 'tech'),
    '74@files_241203_201909_189.jpg': ('证明自己不是赛博电脑废物宾果 V1.3', '成功连接一条线吧！证明自己的硬核电脑技能', 'tech'),
    '75@files_241210_185513_917.jpg': ('Good青春BINGO (极难版)', '五个连成一条线，说明你度过了一个极其幸福的青春，恭喜你！', 'youth'),
    '76@files_241212_153014_064.jpg': ('群友如何评价我', '填给群玩具、群友的评价互动宾果表', 'chat'),
    '79@files_241227_085314_983.jpg': ('游戏老玩家宾果', '圈出你玩过的经典大作，看看你的玩家资历', 'gaming'),
    '7@files_240706_160138_280.jpg': ('先天计算机圣体宾果游戏', '如果其中一条连成线，说明你是先天计算机圣体', 'tech'),
    '81@files_241227_090643_448.jpg': ('高水平玩家宾果游戏', '硬核玩家与全成就达成测试', 'gaming'),
    '83@files_241227_100826_230.jpg': ('社会指数宾果游戏', '测试你的社会人属性与现充指数', 'life'),
    '87@files_241227_220524_554.jpg': ('你群宾果游戏', '连成一条线说明你群就是一个标准的逆天抽象群', 'chat'),
    '8@files_250202_205820_006.jpg': ('逆天群聊BINGO', '连成一条线就能超越95%的抽象神仙群聊', 'chat'),
    '9@files_251019_080126_914.jpg': ('My Silly Ass: Furry Bingo (EN)', 'Have furry stickers, furry music & silly traits', 'furry')
}

def detect_table_grid(im_path, items, w, h):
    im = cv2.imread(im_path)
    if im is not None:
        gray = cv2.cvtColor(im, cv2.COLOR_BGR2GRAY)
        thresh = cv2.adaptiveThreshold(~gray, 255, cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY, 15, -2)
        
        for k_div in [8, 12, 16, 20]:
            h_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (w // k_div, 1))
            h_lines = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, h_kernel)
            v_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, h // k_div))
            v_lines = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, v_kernel)
            
            table_mask = h_lines | v_lines
            contours, _ = cv2.findContours(table_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            for cnt in contours:
                x, y, bw, bh = cv2.boundingRect(cnt)
                if bw > w * 0.65 and bh > h * 0.45:
                    return (x, y, bw, bh)

    # Fallback based on OCR bounding boxes
    non_header = [it for it in items if min(p[1] for p in it['box']) > h * 0.12]
    if non_header:
        x_min = min(min(p[0] for p in it['box']) for it in non_header)
        x_max = max(max(p[0] for p in it['box']) for it in non_header)
        y_min = min(min(p[1] for p in it['box']) for it in non_header)
        y_max = max(max(p[1] for p in it['box']) for it in non_header)
        x_min = max(4, x_min - int(w * 0.02))
        x_max = min(w - 4, x_max + int(w * 0.02))
        y_min = max(int(h * 0.1), y_min - int(h * 0.02))
        y_max = min(h - 4, y_max + int(h * 0.02))
        return (x_min, y_min, x_max - x_min, y_max - y_min)
        
    return (int(w * 0.05), int(h * 0.18), int(w * 0.9), int(h * 0.78))

def main():
    raw_path = os.path.join(BINGO_DIR, '_ocr_raw.json')
    if not os.path.exists(raw_path):
        print('Error: _ocr_raw.json not found')
        return

    with open(raw_path, 'r', encoding='utf-8') as f:
        raw_ocr = json.load(f)

    games = []
    card_index = 0
    files = sorted(raw_ocr.keys())

    print(f'Processing {len(files)} bingo cards...')

    for fname in files:
        img_path = os.path.join(BINGO_DIR, fname)
        if not os.path.exists(img_path):
            continue

        im = Image.open(img_path)
        w, h = im.size
        items = raw_ocr[fname].get('items', [])
        all_text = ' '.join(it['text'] for it in items)

        # Detect grid
        gx, gy, gw, gh = detect_table_grid(img_path, items, w, h)
        
        # Dimensions
        rows, cols = (3, 5) if '13@files_240711_173632_457' in fname else (5, 5)

        # Title & Subtitle & Category
        if fname in TITLE_OVERRIDES:
            title, subtitle, cat_id = TITLE_OVERRIDES[fname]
        else:
            title = '宾果游戏'
            subtitle = '连成一条线即可达成BINGO'
            cat_id = 'life'

        cat_info = CAT_MAP.get(cat_id, CATEGORIES_META[1])

        cw = gw / cols
        ch = gh / rows

        card_id = f'card_{card_index:02d}'
        cells = []
        cell_idx = 0

        # Assign items to cells strictly within the grid area
        grid_items = [it for it in items if min(p[1] for p in it['box']) >= gy - 12]

        for r in range(rows):
            for c in range(cols):
                cx0 = gx + c * cw
                cy0 = gy + r * ch
                cx1 = cx0 + cw
                cy1 = cy0 + ch

                # Find items whose center falls inside this cell
                in_cell = []
                for it in grid_items:
                    b = it['box']
                    center_x = sum(p[0] for p in b) / 4.0
                    center_y = sum(p[1] for p in b) / 4.0
                    if cx0 <= center_x < cx1 and cy0 <= center_y < cy1:
                        in_cell.append(it)

                # Sort text by Y then X
                in_cell.sort(key=lambda x: (min(p[1] for p in x['box']), min(p[0] for p in x['box'])))
                cell_text = ' '.join(x['text'].strip() for x in in_cell if x['text'].strip())

                is_center = (rows == 5 and cols == 5 and r == 2 and c == 2)
                if not cell_text:
                    if is_center:
                        cell_text = '★ FREE 自由格 ★'
                    else:
                        cell_text = f'格子 {r+1}-{c+1}'

                cells.append({
                    'index': cell_idx,
                    'row': r,
                    'col': c,
                    'x': int(cx0),
                    'y': int(cy0),
                    'w': int(cw),
                    'h': int(ch),
                    'text': cell_text,
                    'isCenter': is_center
                })
                cell_idx += 1

        game_data = {
            'id': card_id,
            'filename': fname,
            'title': title,
            'subtitle': subtitle,
            'category': cat_info['name'],
            'categoryId': cat_id,
            'categoryIcon': cat_info['icon'],
            'width': w,
            'height': h,
            'grid': {
                'rows': rows,
                'cols': cols,
                'x': int(gx),
                'y': int(gy),
                'w': int(gw),
                'h': int(gh)
            },
            'cellCount': len(cells),
            'cells': cells
        }

        # Save individual card json
        card_file = os.path.join(CARDS_DIR, f'{card_id}.json')
        with open(card_file, 'w', encoding='utf-8') as fp:
            json.dump(game_data, fp, ensure_ascii=False, indent=2)

        games.append(game_data)
        card_index += 1

    # Save categories
    with open(os.path.join(DATA_DIR, 'categories.json'), 'w', encoding='utf-8') as fp:
        json.dump(CATEGORIES_META, fp, ensure_ascii=False, indent=2)

    # Save master games.json
    target_file = os.path.join(DATA_DIR, 'games.json')
    with open(target_file, 'w', encoding='utf-8') as fp:
        json.dump(games, fp, ensure_ascii=False, indent=2)

    print(f'Successfully refined and processed {len(games)} cards!')
    print(f'Saved to: {target_file}')

if __name__ == '__main__':
    main()
