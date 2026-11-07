# -*- coding: utf-8 -*-
"""
High-Precision Data Generator for Bingo, Bottle Jars & Checklists
Accurately categorizes and maps all 68 games.
"""
import os
import glob
import json
import re
import cv2
import numpy as np
from PIL import Image

BINGO_DIR = os.path.dirname(os.path.abspath(__file__))
IMAGES_DIR = os.path.join(BINGO_DIR, 'images')
DATA_DIR = os.path.join(BINGO_DIR, 'data')
CARDS_DIR = os.path.join(DATA_DIR, 'cards')
PERSONAL_DIR = os.path.join(BINGO_DIR, 'personal')

os.makedirs(CARDS_DIR, exist_ok=True)
os.makedirs(PERSONAL_DIR, exist_ok=True)

CATEGORIES_META = [
    {'id': 'all', 'name': '全部项目', 'icon': '🎯', 'desc': '所有收录的宾果、罐子与打卡清单'},
    {'id': 'bottle', 'name': '罐子与瓶子', 'icon': '🧪', 'desc': '性癖罐子、BL瓶子、群友涂抹等滑动百分比打卡'},
    {'id': 'tech', 'name': '科技与数码', 'icon': '💻', 'desc': '数码高手、老登软件、电脑极客与电报老人'},
    {'id': 'gaming', 'name': '游戏世界', 'icon': '🎮', 'desc': '网络遗老、主机老玩家、CS小男娘与高水平测试'},
    {'id': 'furry', 'name': '福瑞专区', 'icon': '🐾', 'desc': '福瑞控这辈子有了、自设批、重度福瑞控等'},
    {'id': 'subculture', 'name': '圈子与同好', 'icon': '🌈', 'desc': '男娘/南梁/南通、DISCORD男娘、猫娘等'},
    {'id': 'chat', 'name': '群聊与社交', 'icon': '💬', 'desc': '逆天群聊、群友评价、你群宾果等'},
    {'id': 'youth', 'name': '青春与成长', 'icon': '🎓', 'desc': 'Good青春系列、违纪BINGO、闪耀青春等'},
    {'id': 'life', 'name': '生活与日常', 'icon': '☕', 'desc': '健全人BINGO、人生已完成清单、快乐BINGO等'},
    {'id': 'kink', 'name': '成人与趣味', 'icon': '🔞', 'desc': '工口身体、鹿管宾果、喜好调查等'}
]

CAT_MAP = {c['id']: c for c in CATEGORIES_META}

# Custom labels for Bottle Cards
LABELS_42 = [
    ['口交', '捆绑', '双龙入洞', '援交', '地位差', '跟踪狂', '内射'],
    ['互攻', '现实向', '69', '女装', '私密自拍', '年龄差', '监禁'],
    ['绝世好攻', '多人', '舔穴', '阴茎摩擦', '骨科', '前列腺开发', '野战'],
    ['痴汉', '正太', '饮尿', '深喉', 'ABO', '体格差', '群攻'],
    ['媚药', '反差萌', '失禁', '人外', '睡奸', '性转', '尿道开发']
]

LABELS_43 = [
    ['玩弄乳头', '梅里巴', '坏结局', 'SM', '支配服从', '肌肉男', '美男子'],
    ['博美犬', '平凡', '干高潮', '下克上', '射精管理', '阿黑颜', 'NTR'],
    ['年下攻', '龟头刺激', '贞操带', '言语羞辱', '拘束', '潮吹', '共生'],
    ['憋尿', '边缘高潮', '本大爷', '小恶魔', '傲娇', '快感沦陷', '三角恋'],
    ['触手', '结肠刺激', '视奸', '吞精', '颜射', '挠痒', '吻痕']
]

LABELS_2 = [
    ['尿道交', '失禁', '瘙痒', '转化/变身(TF)', '丸吞(Vore)', '某处变大膨胀', '爪控/足控', '高潮体验', '肌肉/筋肉', '繁殖/繁衍', '巨乳', '兽娘控', '巨根'],
    ['子宫高潮', '三人行/多P', '榨精', '超大型/超小型', '怀孕/妊娠', '催眠', '咬', '性别转换(TG)', '面具', '感官剥夺', '泌乳', '恶堕/洗脑', '幼驯染'],
    ['露阴癖', '第四爱', '扶他', '含住全身(Mawplay)', '胶衣(Drone)', '主仆', '产卵', '胶玩具/毛玩具', '胶液', '袜子/黑袜/白袜', '空间环', '百合', 'Twink'],
    ['虫交', '淫纹', '开苞', '人外/怪物/非人', '填充/充气', '贞操锁/禁射', '全身变大', '体重增加', '触手', 'BDSM', '战损/战败凌辱', '龙性恋', '恋污']
]

LABELS_122 = [
    ['攻', '受', '帅', '傲娇', '直球', '腹黑', '毒舌', '极端'],
    ['温柔', '可爱', '天真', '热情', '冷漠', '暴躁', '中二', '嘴硬'],
    ['正经', '变态', '病娇', '白切黑', '天然呆', '天然黑', '傻白甜', '小太阳'],
    ['纯人妻', '转人工', '点子王', '外冷内热', '外热内冷', '缺安全感', '电子宠物', '纯键政批']
]

LABELS_20 = [
    ['千千静听', 'ACDSee', '迅雷5', '金山游侠', 'Nero刻录'],
    ['网络蚂蚁', 'RealPlayer', '网际快车', 'Adobe Reader', '网景浏览器'],
    ['Winamp', '暴风影音', 'IE6浏览器', '快播(Qvod)', '电驴(eMule)'],
    ['Linux企鹅', '傲游浏览器', '酷狗音乐', '金山毒霸', 'MSN Messenger'],
    ['酷我音乐', '瑞星小狮子', 'μTorrent', 'Windows Media', '卡卡安全助手']
]

LABELS_48 = [
    ['初中开始撸', '一周撸五次', '靠想象撸过', '尝试戒撸多次', '有三种以上性癖'],
    ['拥有多种资源', '不撸浑身难受', '用玩具撸过', '从没遗过精', '二三次元都撸'],
    ['打算一直撸到老', '在室外撸过', '压力大的时候撸', '开心的时候撸', '难受的时候撸'],
    ['一天撸过多次', '有百撸不厌资源', '经常有色情幻想', '小头控制过大头', '撸完精神萎靡'],
    ['没实战过', '对现实人撸过', '半夜起床撸过', '早上晨勃撸过', '撸后尿道刺痛']
]

# Manual custom configs for non-standard cards
CARD_CONFIGS = {
    # 1. Bottles
    '42@files_261102_185514_195.png': {
        'type': 'bottle',
        'title': 'BL性癖の瓶 (第一弹)',
        'subtitle': '译:TG @ZGQinC / 作:@mochikouki (填满之后也请附带原图发出哦♪)',
        'category': 'bottle',
        'labels': LABELS_42,
        'grid': {'rows': 5, 'cols': 7, 'x': 50, 'y': 340, 'w': 1184, 'h': 1550},
        'bottle_spec': {'cx0': 118, 'step_x': 170, 'y_bottom0': 548, 'step_y': 330, 'bw': 90, 'bh': 178}
    },
    '43@files_261102_185514_200.png': {
        'type': 'bottle',
        'title': 'BL性癖の瓶 2 (第二弹)',
        'subtitle': '作:@mochikouki / 译:TG @ZGQinC (填满之后也请附带原图发出哦♪)',
        'category': 'bottle',
        'labels': LABELS_43,
        'grid': {'rows': 5, 'cols': 7, 'x': 50, 'y': 340, 'w': 1184, 'h': 1550},
        'bottle_spec': {'cx0': 118, 'step_x': 170, 'y_bottom0': 548, 'step_y': 330, 'bw': 90, 'bh': 178}
    },
    '2@files_240629_193940_313.jpg': {
        'type': 'bottle',
        'title': '填满你的性癖罐子 (Furry)',
        'subtitle': '圈出并填满属于你的福瑞XP罐子 (转发时请附一张原图)',
        'category': 'bottle',
        'labels': LABELS_2,
        'grid': {'rows': 4, 'cols': 13, 'x': 18, 'y': 170, 'w': 1244, 'h': 540},
        'bottle_spec': {'cx0': 66, 'step_x': 95.8, 'y_bottom0': 230, 'step_y': 135, 'bw': 60, 'bh': 95}
    },
    '122@0_260628_160043_728.jpg': {
        'type': 'bottle',
        'title': '感觉有多少就涂多少 (群友评价)',
        'subtitle': '让你的群友评价评价你，发的时候留份原表不然没法玩',
        'category': 'bottle',
        'labels': LABELS_122,
        'grid': {'rows': 4, 'cols': 8, 'x': 40, 'y': 180, 'w': 880, 'h': 750},
        'bottle_spec': {'cx0': 95, 'step_x': 110, 'y_bottom0': 275, 'step_y': 190, 'bw': 82, 'bh': 88}
    },

    # 2. Special Grids
    '46@files_240807_204904_769.jpg': {
        'type': 'bingo',
        'title': '银行卡密码宾果游戏',
        'subtitle': '看看你的6位银行卡密码能不能连成一条线 (10行×6列)',
        'category': 'tech',
        'grid': {'rows': 10, 'cols': 6, 'x': 30, 'y': 290, 'w': 1160, 'h': 730}
    },
    '32@files_240814_172532_659.jpg': {
        'type': 'bingo',
        'title': '电脑高手宾果游戏 (初级)',
        'subtitle': '连成两条线=电脑高手 / 三条线=电脑奇才 / 四条线=电脑皇帝 (4行×4列)',
        'category': 'tech',
        'grid': {'rows': 4, 'cols': 4, 'x': 0, 'y': 228, 'w': 983, 'h': 1045}
    },
    '13@files_240711_173632_457.jpg': {
        'type': 'bingo',
        'title': '网络遗老宾果游戏',
        'subtitle': '圈出你玩过的经典老游戏，五个连成一线你就是网络老东西 (3行×5列)',
        'category': 'gaming',
        'grid': {'rows': 3, 'cols': 5, 'x': 8, 'y': 150, 'w': 568, 'h': 315}
    },
    '44@files_250705_194907_795.jpg': {
        'type': 'bingo',
        'title': '快乐BINGO',
        'subtitle': '不必连成一条线，希望这张表能让你想起那些快乐的时刻 (5行×7列)',
        'category': 'life',
        'grid': {'rows': 5, 'cols': 7, 'x': 20, 'y': 195, 'w': 1174, 'h': 875}
    },
    '20@files_240718_195043_265.jpg': {
        'type': 'bingo',
        'title': '互联网老登宾果游戏 (软件图标版)',
        'subtitle': '5个连成一线你就是一个合格的互联网老登了 (经典复古软件图标)',
        'category': 'tech',
        'grid': {'rows': 5, 'cols': 5, 'x': 18, 'y': 92, 'w': 1164, 'h': 800},
        'custom_cells': LABELS_20
    },
    '48@files_260212_225512_496.jpg': {
        'type': 'bingo',
        'title': '青春撸管生活宾果',
        'subtitle': '连成线你就是赢家，记录青春的荷尔蒙生活',
        'category': 'kink',
        'grid': {'rows': 5, 'cols': 5, 'x': 25, 'y': 140, 'w': 1130, 'h': 1030},
        'custom_cells': LABELS_48
    },

    # 3. Checklists
    '76@files_241212_153014_064.jpg': {
        'type': 'checklist',
        'title': '群友如何评价我',
        'subtitle': '填给群玩具、群友的互动评价表 (共63项)',
        'category': 'chat',
        'grid': {'rows': 21, 'cols': 3, 'x': 15, 'y': 48, 'w': 578, 'h': 1220}
    },
    '47@files_250715_143110_854.jpg': {
        'type': 'checklist',
        'title': '雄性喜好分数大调查 (重口味版)',
        'subtitle': '点选自己的喜好，最后结算积分评级 (多选打分)',
        'category': 'kink',
        'grid': {'rows': 15, 'cols': 6, 'x': 10, 'y': 40, 'w': 380, 'h': 580}
    },
    '23@files_250620_233330_390.jpg': {
        'type': 'checklist',
        'title': '人生已完成清单',
        'subtitle': '来看看你的人生已解锁了哪些经历与遗憾 (百项目标清单)',
        'category': 'life',
        'grid': {'rows': 19, 'cols': 1, 'x': 18, 'y': 95, 'w': 764, 'h': 880}
    }
}

# Standard titles
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
    '14@files_240811_115603_484.jpg': ('鹿管宾果', '五个连成一线证明你喜欢鹿管 (限定18岁以上才能玩)', 'kink'),
    '15@files_240711_190359_918.jpg': ('社会指数宾果游戏', '如果有其中一条线连起来，你就不仅不社会，还是完全的现充', 'life'),
    '16@files_240711_190359_914.jpg': ('自设批宾果游戏', '五个连成一线就是纯种自设批', 'furry'),
    '17@files_240711_190359_896.jpg': ('新时代中国青年宾果', '五个连成线，八辈子都有了', 'life'),
    '18@files_250601_210222_969.jpg': ('福瑞控XP宾果', '转发给你的朋友看看谁是真色批', 'furry'),
    '19@files_240718_151335_837.jpg': ('社交网络遗老宾果', '圈出你玩过的网络平台，一条线连成5个说明你是互联网乐子人', 'tech'),
    '1@files_240703_100714_406.jpg': ('无可救药的福瑞控 (中国大陆加强版)', '五个连成线你就是无可救药的福瑞控', 'furry'),
    '21@files_240802_221453_571.jpg': ("CFERALSOREN'S Kink Bingo", 'Kink & XP preferences checklist', 'kink'),
    '22@files_240802_221453_562.jpg': ("SAMMY'S Kink Bingo", 'Adult preferences & Kink bingo', 'kink'),
    '24@files_240804_213836_130.jpg': ('这辈子有了BINGO', '五个连成一线，你这辈子就彻彻底底完完全全地有了', 'life'),
    '25@files_240804_213836_133.jpg': ('Shiny 青春 BINGO', '五个连成一线，说明你度过了一个闪耀的青春，恭喜贺喜！', 'youth'),
    '26@files_251019_080126_924.jpg': ('My Silly Ass: Furry Bingo', 'Check off your silly furry traits', 'furry'),
    '29@files_240806_190323_406.jpg': ('小南梁宾果游戏', '五个连成一线的话你就是艾草小南梁', 'subculture'),
    '34@files_240816_213708_820.jpg': ('群友逆天发言交流群BINGO', '记录群聊里的逆天瞬间与群友抽象言论', 'chat'),
    '35@files_240901_145348_189.jpg': ('男同性恋奇怪BINGO', '五个连成一线证明你是奇怪的人 (限定18岁以上才能玩)', 'subculture'),
    '38@files_240807_173654_908.jpg': ('R18-G 猎奇BINGO', '5个连成一线/大于7个证明你是guro大魔', 'kink'),
    '39@files_240807_191721_365.jpg': ('Good青春BINGO (困难版)', '五个连成一线，说明你度过了一个相对幸福的青春，值得庆祝！', 'youth'),
    '3@files_240802_205052_011.jpg': ('人下人BINGO游戏', '五个连成一条线即可享受牛马人生', 'life'),
    '40@files_250522_194802_143.jpg': ('社会指数宾果游戏', '连成一条线证明你不社会，是完完全全的现充', 'life'),
    '45@files_251215_003824_612.jpg': ('重度福瑞控BINGO', '经典5x5格子，连成一行你就妥妥的是重度福瑞控了～', 'furry'),
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
    '79@files_241227_085314_983.jpg': ('游戏老玩家宾果', '圈出你玩过的经典大作，只要连成一线说明你是游戏王', 'gaming'),
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

def build_bottle_card(card_id, fname, im, cfg):
    w, h = im.size
    labels = cfg['labels']
    rows = len(labels)
    cols = len(labels[0])
    spec = cfg['bottle_spec']

    bottles = []
    idx = 0
    for r in range(rows):
        for c in range(cols):
            cx = spec['cx0'] + c * spec['step_x']
            y_bot = spec['y_bottom0'] + r * spec['step_y']
            bw = spec['bw']
            bh = spec['bh']
            bx = int(cx - bw / 2)
            by = int(y_bot - bh)

            label = labels[r][c]
            bottles.append({
                'index': idx,
                'row': r,
                'col': c,
                'label': label,
                'text': label,
                'x': bx,
                'y': by,
                'w': bw,
                'h': bh,
                'cx': int(cx),
                'y_bottom': int(y_bot),
                'defaultLevel': 0
            })
            idx += 1

    cat_info = CAT_MAP['bottle']
    return {
        'id': card_id,
        'type': 'bottle',
        'filename': f'images/{fname}',
        'title': cfg['title'],
        'subtitle': cfg['subtitle'],
        'category': cat_info['name'],
        'categoryId': 'bottle',
        'categoryIcon': cat_info['icon'],
        'width': w,
        'height': h,
        'grid': cfg['grid'],
        'cellCount': len(bottles),
        'cells': bottles
    }

def build_bingo_card(card_id, fname, im, items, cfg_override=None):
    w, h = im.size
    if cfg_override:
        title = cfg_override.get('title', '宾果游戏')
        subtitle = cfg_override.get('subtitle', '连成一条线即可达成BINGO')
        cat_id = cfg_override.get('category', 'life')
        gx = cfg_override['grid']['x']
        gy = cfg_override['grid']['y']
        gw = cfg_override['grid']['w']
        gh = cfg_override['grid']['h']
        rows = cfg_override['grid']['rows']
        cols = cfg_override['grid']['cols']
        custom_cells = cfg_override.get('custom_cells', None)
    elif fname in TITLE_MAP:
        title, subtitle, cat_id = TITLE_MAP[fname]
        gx, gy, gw, gh = detect_table_grid(os.path.join(IMAGES_DIR, fname), items, w, h)
        rows, cols = (5, 5)
        custom_cells = None
    else:
        title = '宾果游戏'
        subtitle = '连成一条线即可达成BINGO'
        cat_id = 'life'
        gx, gy, gw, gh = detect_table_grid(os.path.join(IMAGES_DIR, fname), items, w, h)
        rows, cols = (5, 5)
        custom_cells = None

    cat_info = CAT_MAP.get(cat_id, CATEGORIES_META[1])
    cw = gw / cols
    ch = gh / rows

    cells = []
    cell_idx = 0
    grid_items = [it for it in items if min(p[1] for p in it['box']) >= gy - 12]

    for r in range(rows):
        for c in range(cols):
            cx0 = gx + c * cw
            cy0 = gy + r * ch
            cx1 = cx0 + cw
            cy1 = cy0 + ch

            if custom_cells and r < len(custom_cells) and c < len(custom_cells[r]):
                cell_text = custom_cells[r][c]
            else:
                in_cell = []
                for it in grid_items:
                    b = it['box']
                    center_x = sum(p[0] for p in b) / 4.0
                    center_y = sum(p[1] for p in b) / 4.0
                    if cx0 <= center_x < cx1 and cy0 <= center_y < cy1:
                        in_cell.append(it)
                in_cell.sort(key=lambda x: (min(p[1] for p in x['box']), min(p[0] for p in x['box'])))
                cell_text = ' '.join(x['text'].strip() for x in in_cell if x['text'].strip())

            is_center = (rows == 5 and cols == 5 and r == 2 and c == 2)
            if not cell_text:
                cell_text = '★ FREE 自由格 ★' if is_center else f'格子 {r+1}-{c+1}'

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

    return {
        'id': card_id,
        'type': 'bingo',
        'filename': f'images/{fname}',
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

def build_checklist_card(card_id, fname, im, items, cfg):
    w, h = im.size
    grid = cfg['grid']
    rows, cols = grid['rows'], grid['cols']
    cw = grid['w'] / cols
    ch = grid['h'] / rows

    cells = []
    idx = 0
    # Gather items inside grid
    grid_items = [it for it in items if min(p[1] for p in it['box']) >= grid['y'] - 10]

    for r in range(rows):
        for c in range(cols):
            cx0 = grid['x'] + c * cw
            cy0 = grid['y'] + r * ch
            cx1 = cx0 + cw
            cy1 = cy0 + ch

            in_cell = []
            for it in grid_items:
                b = it['box']
                center_x = sum(p[0] for p in b) / 4.0
                center_y = sum(p[1] for p in b) / 4.0
                if cx0 <= center_x < cx1 and cy0 <= center_y < cy1:
                    in_cell.append(it)

            in_cell.sort(key=lambda x: (min(p[1] for p in x['box']), min(p[0] for p in x['box'])))
            cell_text = ' '.join(x['text'].strip() for x in in_cell if x['text'].strip())
            if not cell_text:
                cell_text = f'项目 {r+1}-{c+1}'

            cells.append({
                'index': idx,
                'row': r,
                'col': c,
                'x': int(cx0),
                'y': int(cy0),
                'w': int(cw),
                'h': int(ch),
                'text': cell_text
            })
            idx += 1

    cat_info = CAT_MAP[cfg['category']]
    return {
        'id': card_id,
        'type': 'checklist',
        'filename': f'images/{fname}',
        'title': cfg['title'],
        'subtitle': cfg['subtitle'],
        'category': cat_info['name'],
        'categoryId': cfg['category'],
        'categoryIcon': cat_info['icon'],
        'width': w,
        'height': h,
        'grid': grid,
        'cellCount': len(cells),
        'cells': cells
    }

def main():
    raw_path = os.path.join(BINGO_DIR, '_ocr_raw.json')
    with open(raw_path, 'r', encoding='utf-8') as f:
        raw_ocr = json.load(f)

    games = []
    card_index = 0
    files = sorted(raw_ocr.keys())

    print(f'Building cards for {len(files)} files...')

    for fname in files:
        img_path = os.path.join(IMAGES_DIR, fname)
        if not os.path.exists(img_path):
            continue

        im = Image.open(img_path)
        items = raw_ocr[fname].get('items', [])
        card_id = f'card_{card_index:02d}'

        if fname in CARD_CONFIGS:
            cfg = CARD_CONFIGS[fname]
            if cfg['type'] == 'bottle':
                card = build_bottle_card(card_id, fname, im, cfg)
            elif cfg['type'] == 'checklist':
                card = build_checklist_card(card_id, fname, im, items, cfg)
            else:
                card = build_bingo_card(card_id, fname, im, items, cfg)
        else:
            card = build_bingo_card(card_id, fname, im, items)

        # Save card JSON
        card_path = os.path.join(CARDS_DIR, f'{card_id}.json')
        with open(card_path, 'w', encoding='utf-8') as fp:
            json.dump(card, fp, ensure_ascii=False, indent=2)

        games.append(card)
        card_index += 1

    # Save categories
    with open(os.path.join(DATA_DIR, 'categories.json'), 'w', encoding='utf-8') as fp:
        json.dump(CATEGORIES_META, fp, ensure_ascii=False, indent=2)

    # Save games.json
    games_path = os.path.join(DATA_DIR, 'games.json')
    with open(games_path, 'w', encoding='utf-8') as fp:
        json.dump(games, fp, ensure_ascii=False, indent=2)

    # Initialize personal/personal_records.json template
    personal_file = os.path.join(PERSONAL_DIR, 'personal_records.json')
    if not os.path.exists(personal_file):
        sample_personal = {
            'version': '1.0',
            'owner': 'ZGQ',
            'title': 'ZGQ 的个人宾果与罐子打卡记录',
            'website': 'https://bingo.zgqinc.gq',
            'updatedAt': '2026-11-06T18:00:00Z',
            'records': {
                'card_00': {
                    'type': 'bingo',
                    'checked': [0, 1, 2, 6, 12, 18, 24],
                    'completedLines': 1
                },
                'card_06': {
                    'type': 'bingo',
                    'checked': [0, 5, 10, 15, 20],
                    'completedLines': 1
                }
            }
        }
        with open(personal_file, 'w', encoding='utf-8') as fp:
            json.dump(sample_personal, fp, ensure_ascii=False, indent=2)

    print(f'Successfully built {len(games)} cards!')
    print(f'Data saved to: {games_path}')
    print(f'Personal directory initialized at: {PERSONAL_DIR}')

if __name__ == '__main__':
    main()
