#!/usr/bin/env python3
"""
人脸提取 v4 - 先缩图再检测，快速版
"""
import cv2
import os
import numpy as np
import hashlib

upload_dir = os.path.expanduser("~/.hermes-web-ui/upload/")
output_dir = os.path.expanduser("~/Desktop/portrait_gallery_v2/")
os.makedirs(output_dir, exist_ok=True)
for f in os.listdir(output_dir):
    os.remove(os.path.join(output_dir, f))

hashes = {}
for f in sorted(os.listdir(upload_dir)):
    if f.startswith('.'): continue
    fp = os.path.join(upload_dir, f)
    h = hashlib.md5(open(fp, 'rb').read()).hexdigest()
    if h not in hashes:
        hashes[h] = fp
source_images = list(hashes.values())
print(f"📷 独立源图: {len(source_images)}")

haar_dir = cv2.data.haarcascades
cascades = [
    ('def', cv2.CascadeClassifier(os.path.join(haar_dir, 'haarcascade_frontalface_default.xml'))),
    ('alt2', cv2.CascadeClassifier(os.path.join(haar_dir, 'haarcascade_frontalface_alt2.xml'))),
]
profile_cas = cv2.CascadeClassifier(os.path.join(haar_dir, 'haarcascade_profileface.xml'))

MAX_DIM = 2000  # 最大边长，超出则缩小
all_detections = []

for img_idx, img_path in enumerate(source_images):
    fname = os.path.basename(img_path)
    print(f"\n📸 [{img_idx+1}/{len(source_images)}] {fname}")
    
    img = cv2.imread(img_path)
    if img is None:
        print("  ❌ 无法读取"); continue
    
    h_img, w_img = img.shape[:2]
    scale = 1.0
    if max(w_img, h_img) > MAX_DIM:
        scale = MAX_DIM / max(w_img, h_img)
        img = cv2.resize(img, (0, 0), fx=scale, fy=scale, interpolation=cv2.INTER_AREA)
        h_img, w_img = img.shape[:2]
    print(f"  处理尺寸: {w_img}x{h_img} (scale={scale:.2f})")
    
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
    gray = clahe.apply(gray)
    
    img_dets = []
    
    # 策略1: 正面检测 - 3组参数
    for cname, cascade in cascades:
        for sf, mn in [(1.05, 3), (1.1, 2), (1.1, 3), (1.2, 2)]:
            min_sz = max(20, int(min(w_img, h_img) / 60))
            faces = cascade.detectMultiScale(gray, scaleFactor=sf, minNeighbors=mn, minSize=(min_sz, min_sz))
            for (x, y, w, h) in faces:
                pad = int(max(w, h) * 0.15)
                x1, y1 = max(0, x-pad), max(0, y-pad)
                x2, y2 = min(w_img, x+w+pad), min(h_img, y+h+pad)
                cw, ch = x2-x1, y2-y1
                r = cw / ch
                if 0.4 < r < 2.5 and cw >= 30:
                    img_dets.append((x1, y1, cw, ch, f"{cname}_s{sf}_n{mn}"))
    
    # 策略2: 侧面检测
    for sf, mn in [(1.05, 3), (1.1, 2)]:
        faces = profile_cas.detectMultiScale(gray, scaleFactor=sf, minNeighbors=mn, minSize=(30, 30))
        for (x, y, w, h) in faces:
            pad = int(max(w, h) * 0.15)
            x1, y1 = max(0, x-pad), max(0, y-pad)
            x2, y2 = min(w_img, x+w+pad), min(h_img, y+h+pad)
            cw, ch = x2-x1, y2-y1
            r = cw / ch
            if 0.4 < r < 2.5 and cw >= 30:
                img_dets.append((x1, y1, cw, ch, f"prof_s{sf}_n{mn}"))
    
    # 策略3: 50%缩小检测（捕获更大脸）
    small = cv2.resize(img, (0, 0), fx=0.5, fy=0.5, interpolation=cv2.INTER_AREA)
    small_gray = cv2.cvtColor(small, cv2.COLOR_BGR2GRAY)
    small_gray = clahe.apply(small_gray)
    for cname, cascade in cascades:
        min_sz = max(20, int(min(small.shape[1], small.shape[0]) / 50))
        faces = cascade.detectMultiScale(small_gray, scaleFactor=1.05, minNeighbors=2, minSize=(min_sz, min_sz))
        for (x, y, w, h) in faces:
            ox, oy = int(x/0.5), int(y/0.5)
            ow, oh = int(w/0.5), int(h/0.5)
            pad = int(max(ow, oh) * 0.15)
            x1, y1 = max(0, ox-pad), max(0, oy-pad)
            x2, y2 = min(w_img, ox+ow+pad), min(h_img, oy+oh+pad)
            cw, ch = x2-x1, y2-y1
            r = cw / ch
            if 0.4 < r < 2.5 and cw >= 30:
                img_dets.append((x1, y1, cw, ch, f"half_{cname}"))
    
    print(f"  🔍 原始检测: {len(img_dets)}")
    if not img_dets: continue
    
    # NMS IoU 0.3
    boxes = np.array([[d[0], d[1], d[0]+d[2], d[1]+d[3]] for d in img_dets])
    areas = (boxes[:,2]-boxes[:,0]) * (boxes[:,3]-boxes[:,1])
    order = areas.argsort()[::-1]
    keep = []
    while len(order) > 0:
        i = order[0]
        keep.append(i)
        if len(order) == 1: break
        xx1 = np.maximum(boxes[i,0], boxes[order[1:],0])
        yy1 = np.maximum(boxes[i,1], boxes[order[1:],1])
        xx2 = np.minimum(boxes[i,2], boxes[order[1:],2])
        yy2 = np.minimum(boxes[i,3], boxes[order[1:],3])
        inter = np.maximum(0, xx2-xx1) * np.maximum(0, yy2-yy1)
        iou = inter / (areas[i] + areas[order[1:]] - inter + 1e-6)
        order = order[np.where(iou < 0.3)[0] + 1]
    
    kept = [img_dets[i] for i in keep]
    kept.sort(key=lambda d: d[2]*d[3], reverse=True)
    print(f"  ✅ NMS后: {len(kept)}")
    
    for j, (x1, y1, cw, ch, method) in enumerate(kept):
        face = img[y1:y1+ch, x1:x1+cw]
        if face.size == 0: continue
        face_r = cv2.resize(face, (300, 300), interpolation=cv2.INTER_LANCZOS4)
        out_name = f"face_{img_idx+1:02d}_{j+1:02d}_{cw}x{ch}.jpg"
        cv2.imwrite(os.path.join(output_dir, out_name), face_r, [cv2.IMWRITE_JPEG_QUALITY, 92])
        all_detections.append((img_idx, out_name, cw, ch))

print(f"\n{'='*50}")
print(f"📊 提取完成！总候选: {len(all_detections)}")
print(f"📁 目录: {output_dir}")

from collections import Counter
by_img = Counter(d[0] for d in all_detections)
for idx in sorted(by_img.keys()):
    print(f"  照片{idx+1}: {by_img[idx]}个")

sizes = [(d[2], d[3]) for d in all_detections]
if sizes:
    ws = [s[0] for s in sizes]
    print(f"\n  宽度范围: {min(ws)}-{max(ws)}px")
