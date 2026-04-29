#!/usr/bin/env python3
"""
超宽松人脸提取 v3 - 精简参数组合，快速运行
"""
import cv2
import os
import numpy as np
import hashlib

upload_dir = os.path.expanduser("~/.hermes-web-ui/upload/")
output_dir = os.path.expanduser("~/Desktop/portrait_gallery_v2/")
os.makedirs(output_dir, exist_ok=True)

# 清空旧文件
for f in os.listdir(output_dir):
    os.remove(os.path.join(output_dir, f))

# 去重
hashes = {}
for f in sorted(os.listdir(upload_dir)):
    if f.startswith('.'):
        continue
    fp = os.path.join(upload_dir, f)
    h = hashlib.md5(open(fp, 'rb').read()).hexdigest()
    if h not in hashes:
        hashes[h] = fp

source_images = list(hashes.values())
print(f"📷 独立源图: {len(source_images)}")

# 只用2个最好的级联 + profile
haar_dir = cv2.data.haarcascades
cascade_default = cv2.CascadeClassifier(os.path.join(haar_dir, 'haarcascade_frontalface_default.xml'))
cascade_alt2 = cv2.CascadeClassifier(os.path.join(haar_dir, 'haarcascade_frontalface_alt2.xml'))
cascade_profile = cv2.CascadeClassifier(os.path.join(haar_dir, 'haarcascade_profileface.xml'))

all_detections = []

for img_idx, img_path in enumerate(source_images):
    fname = os.path.basename(img_path)
    print(f"\n📸 [{img_idx+1}/{len(source_images)}] {fname}")
    
    img = cv2.imread(img_path)
    if img is None:
        print(f"  ❌ 无法读取")
        continue
    
    h_img, w_img = img.shape[:2]
    print(f"  尺寸: {w_img}x{h_img}")
    
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8,8))
    gray_enhanced = clahe.apply(gray)
    
    img_dets = []
    
    # 策略1: 原图 + 2个级联, 宽松参数
    for cascade, name in [(cascade_default, 'def'), (cascade_alt2, 'alt2')]:
        for sf in [1.05, 1.1, 1.2]:
            for mn in [1, 2, 3]:
                min_sz = max(20, int(min(w_img, h_img) / 80))
                faces = cascade.detectMultiScale(gray_enhanced, scaleFactor=sf, minNeighbors=mn, minSize=(min_sz, min_sz))
                for (x, y, w, h) in faces:
                    pad = int(max(w, h) * 0.15)
                    x1, y1 = max(0, x-pad), max(0, y-pad)
                    x2, y2 = min(w_img, x+w+pad), min(h_img, y+h+pad)
                    cw, ch = x2-x1, y2-y1
                    r = cw/ch
                    if 0.4 < r < 2.5 and cw >= 30 and ch >= 30:
                        img_dets.append((x1, y1, cw, ch, f"{name}_s{sf}_n{mn}"))
    
    # 策略2: profile侧面检测
    for sf in [1.05, 1.1]:
        faces = cascade_profile.detectMultiScale(gray_enhanced, scaleFactor=sf, minNeighbors=2, minSize=(30, 30))
        for (x, y, w, h) in faces:
            pad = int(max(w, h) * 0.15)
            x1, y1 = max(0, x-pad), max(0, y-pad)
            x2, y2 = min(w_img, x+w+pad), min(h_img, y+h+pad)
            cw, ch = x2-x1, y2-y1
            r = cw/ch
            if 0.4 < r < 2.5 and cw >= 30 and ch >= 30:
                img_dets.append((x1, y1, cw, ch, f"profile_s{sf}"))
    
    # 策略3: 缩小图片检测大脸
    for shrink in [0.5, 0.3]:
        small = cv2.resize(img, (0, 0), fx=shrink, fy=shrink)
        small_gray = cv2.cvtColor(small, cv2.COLOR_BGR2GRAY)
        small_gray = clahe.apply(small_gray)
        for cascade, name in [(cascade_default, 'def'), (cascade_alt2, 'alt2')]:
            min_sz = max(20, int(min(small.shape[1], small.shape[0]) / 50))
            faces = cascade.detectMultiScale(small_gray, scaleFactor=1.05, minNeighbors=2, minSize=(min_sz, min_sz))
            for (x, y, w, h) in faces:
                ox, oy, ow, oh = int(x/shrink), int(y/shrink), int(w/shrink), int(h/shrink)
                pad = int(max(ow, oh) * 0.15)
                x1, y1 = max(0, ox-pad), max(0, oy-pad)
                x2, y2 = min(w_img, ox+ow+pad), min(h_img, oy+oh+pad)
                cw, ch = x2-x1, y2-y1
                r = cw/ch
                if 0.4 < r < 2.5 and cw >= 30 and ch >= 30:
                    img_dets.append((x1, y1, cw, ch, f"shrink{shrink}_{name}"))
    
    print(f"  🔍 原始检测: {len(img_dets)}")
    
    if not img_dets:
        continue
    
    # NMS去重 IoU 0.3
    boxes = np.array([[d[0], d[1], d[0]+d[2], d[1]+d[3]] for d in img_dets])
    areas = (boxes[:, 2] - boxes[:, 0]) * (boxes[:, 3] - boxes[:, 1])
    order = areas.argsort()[::-1]
    
    keep = []
    while len(order) > 0:
        i = order[0]
        keep.append(i)
        if len(order) == 1:
            break
        xx1 = np.maximum(boxes[i, 0], boxes[order[1:], 0])
        yy1 = np.maximum(boxes[i, 1], boxes[order[1:], 1])
        xx2 = np.minimum(boxes[i, 2], boxes[order[1:], 2])
        yy2 = np.minimum(boxes[i, 3], boxes[order[1:], 3])
        inter = np.maximum(0, xx2 - xx1) * np.maximum(0, yy2 - yy1)
        iou = inter / (areas[i] + areas[order[1:]] - inter + 1e-6)
        order = order[np.where(iou < 0.3)[0] + 1]
    
    kept = [img_dets[i] for i in keep]
    print(f"  ✅ NMS后: {len(kept)}")
    
    # 按面积排序（大脸=前排/近景，小脸=后排/远景）
    kept.sort(key=lambda d: d[2]*d[3], reverse=True)
    
    for j, (x1, y1, cw, ch, method) in enumerate(kept):
        face = img[y1:y1+ch, x1:x1+cw]
        if face.size == 0:
            continue
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
