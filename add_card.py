# -*- coding: utf-8 -*-
"""
Add Bingo Card CLI Tool
Allows easily adding new bingo images to the collection, running OCR,
detecting grid coordinates, and updating games.json modularly.

Usage:
  python add_card.py "path/to/image.jpg" --title "自定义标题" --category "tech"
  python add_card.py "path/to/image.jpg" (will auto-detect title and category)
"""
import os
import sys
import json
import argparse
import shutil
import cv2
import numpy as np
from PIL import Image
from rapidocr_onnxruntime import RapidOCR

BINGO_DIR = os.path.dirname(os.path.abspath(__file__))
IMAGES_DIR = os.path.join(BINGO_DIR, 'images')
DATA_DIR = os.path.join(BINGO_DIR, 'data')
CARDS_DIR = os.path.join(DATA_DIR, 'cards')

os.makedirs(IMAGES_DIR, exist_ok=True)
os.makedirs(CARDS_DIR, exist_ok=True)

def detect_grid(img_path, w, h):
    im = cv2.imread(img_path)
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
    return (int(w * 0.05), int(h * 0.18), int(w * 0.9), int(h * 0.78))

def main():
    parser = argparse.ArgumentParser(description="Add a new bingo or bottle image card.")
    parser.add_argument("image_path", help="Path to the bingo card image.")
    parser.add_argument("--title", default="", help="Custom title for the bingo card.")
    parser.add_argument("--subtitle", default="", help="Custom subtitle / rules.")
    parser.add_argument("--category", default="life", help="Category ID (tech/gaming/furry/subculture/chat/youth/life/kink/bottle).")
    parser.add_argument("--type", default="bingo", choices=["bingo", "bottle", "checklist"], help="Card type: bingo, bottle, or checklist.")
    parser.add_argument("--rows", type=int, default=5, help="Number of rows (default 5).")
    parser.add_argument("--cols", type=int, default=5, help="Number of cols (default 5).")

    args = parser.parse_args()

    src_path = os.path.abspath(args.image_path)
    if not os.path.exists(src_path):
        print(f"Error: Image not found at {src_path}")
        sys.exit(1)

    fname = os.path.basename(src_path)
    dest_path = os.path.join(IMAGES_DIR, fname)
    if src_path != dest_path:
        shutil.copy2(src_path, dest_path)
        print(f"Copied image to: {dest_path}")

    # Load categories metadata
    cat_file = os.path.join(DATA_DIR, "categories.json")
    with open(cat_file, "r", encoding="utf-8") as f:
        categories = json.load(f)
    cat_map = {c["id"]: c for c in categories}

    # Run OCR
    print("Running RapidOCR...")
    ocr = RapidOCR()
    res, _ = ocr(dest_path)
    items = []
    if res:
        for box, text, score in res:
            items.append({
                "box": [[int(p[0]), int(p[1])] for p in box],
                "text": str(text).strip(),
                "score": round(float(score), 3)
            })

    im = Image.open(dest_path)
    w, h = im.size

    # Load games.json
    games_file = os.path.join(DATA_DIR, "games.json")
    with open(games_file, "r", encoding="utf-8") as f:
        games = json.load(f)

    card_id = f"card_{len(games):02d}"

    # Auto detect title if omitted
    title = args.title
    subtitle = args.subtitle
    if not title and items:
        title = items[0]["text"]
    if not title:
        title = os.path.splitext(fname)[0]
    if not subtitle and len(items) > 1:
        subtitle = items[1]["text"]

    gx, gy, gw, gh = detect_grid(dest_path, w, h)
    rows, cols = args.rows, args.cols
    cw, ch = gw / cols, gh / rows

    cells = []
    cell_idx = 0
    grid_items = [it for it in items if min(p[1] for p in it["box"]) >= gy - 12]

    for r in range(rows):
        for c in range(cols):
            cx0 = gx + c * cw
            cy0 = gy + r * ch
            cx1 = cx0 + cw
            cy1 = cy0 + ch

            in_cell = []
            for it in grid_items:
                b = it["box"]
                center_x = sum(p[0] for p in b) / 4.0
                center_y = sum(p[1] for p in b) / 4.0
                if cx0 <= center_x < cx1 and cy0 <= center_y < cy1:
                    in_cell.append(it)

            in_cell.sort(key=lambda x: (min(p[1] for p in x["box"]), min(p[0] for p in x["box"])))
            cell_text = " ".join(x["text"].strip() for x in in_cell if x["text"].strip())
            is_center = (rows == 5 and cols == 5 and r == 2 and c == 2)
            if not cell_text:
                cell_text = "★ FREE 自由格 ★" if is_center else f"格子 {r+1}-{c+1}"

            cells.append({
                "index": cell_idx,
                "row": r,
                "col": c,
                "x": int(cx0),
                "y": int(cy0),
                "w": int(cw),
                "h": int(ch),
                "text": cell_text,
                "isCenter": is_center
            })
            cell_idx += 1

    cat_id = args.category if args.category in cat_map else ("bottle" if args.type == "bottle" else "life")
    cat_info = cat_map[cat_id]

    card_data = {
        "id": card_id,
        "type": args.type,
        "filename": f"images/{fname}",
        "title": title,
        "subtitle": subtitle,
        "category": cat_info["name"],
        "categoryId": cat_id,
        "categoryIcon": cat_info["icon"],
        "width": w,
        "height": h,
        "grid": {
            "rows": rows,
            "cols": cols,
            "x": int(gx),
            "y": int(gy),
            "w": int(gw),
            "h": int(gh)
        },
        "cellCount": len(cells),
        "cells": cells
    }

    # Save card json
    card_path = os.path.join(CARDS_DIR, f"{card_id}.json")
    with open(card_path, "w", encoding="utf-8") as f:
        json.dump(card_data, f, ensure_ascii=False, indent=2)

    games.append(card_data)
    with open(games_file, "w", encoding="utf-8") as f:
        json.dump(games, f, ensure_ascii=False, indent=2)

    print(f"Successfully added {title} ({card_id}) as type={args.type}!")
    print(f"Card saved to: {card_path}")

if __name__ == "__main__":
    main()
