#!/usr/bin/env python3
"""
超宽松人脸提取 v2 - 多策略组合
目标：从合照中提取尽可能多的候选人像，宁多勿漏
"""
import cv2
import os
import numpy as np

upload_dir = os.path.expanduser("~/.hermes-web-ui/upload/")
output_dir = os.path.expanduser("~/Desktop/portrait_gallery_v2/")
os.makedirs(output_dir, exist_ok=True)

# 清空旧文件
for f in os.listdir(output_dir):
    os.remove(os.path.join(output_dir, f))

# 去重后的源图
import hashlib
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

# Haar级联 - 加载所有4个
haar_dir = cv2.data.haarcascades
cascades = {
    'default': cv2.CascadeClassifier(os.path.join(haar_dir, 'haarcascade_frontalface_default.xml')),
    'alt': cv2.CascadeClassifier(os.path.join(haar_dir, 'haarcascade_frontalface_alt.xml')),
    'alt2': cv2.CascadeClassifier(os.path.join(haar_dir, 'haarcascade_frontalface_alt2.xml')),
    'alt_tree': cv2.CascadeClassifier(os.path.join(haar_dir, 'haarcascade_frontalface_alt_tree.xml')),
}
profile_cascade = cv2.CascadeClassifier(os.path.join(haar_dir, 'haarcascade_profileface.xml'))
eye_cascade = cv2.CascadeClassifier(os.path.join(haar_dir, 'haarcascade_eye.xml'))

all_detections = []  # (img_idx, x, y, w, h, confidence, method)

for img_idx, img_path in enumerate(source_images):
    fname = os.path.basename(img_path)
    print(f"\n📸 [{img_idx+1}/{len(source_images)}] {fname} ({os.path.getsize(img_path)/1024:.0f}KB)")
    
    img = cv2.imread(img_path)
    if img is None:
        print(f"  ❌ 无法读取，跳过")
        continue
    
    h_img, w_img = img.shape[:2]
    print(f"  尺寸: {w_img}x{h_img}")
    
    img_detections = []
    
    # 策略1: 多缩放 + 多级联，参数极宽松
    for scale_factor in [1.05, 1.08, 1.1, 1.15, 1.2, 1.3]:
        for min_neighbors in [1, 2, 3]:
            for cascade_name, cascade in cascades.items():
                gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
                # CLAHE增强
                clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8,8))
                gray = clahe.apply(gray)
                
                min_size = max(20, int(min(w_img, h_img) / 80))
                faces = cascade.detectMultiScale(
                    gray,
                    scaleFactor=scale_factor,
                    minNeighbors=min_neighbors,
                    minSize=(min_size, min_size),
                    flags=cv2.CASCADE_SCALE_IMAGE
                )
                
                for (x, y, w, h) in faces:
                    # 扩大裁剪区域20%
                    pad = int(max(w, h) * 0.2)
                    x1 = max(0, x - pad)
                    y1 = max(0, y - pad)
                    x2 = min(w_img, x + w + pad)
                    y2 = min(h_img, y + h + pad)
                    cw = x2 - x1
                    ch = y2 - y1
                    
                    # 宽高比检查 (人脸不会太扁或太窄)
                    ratio = cw / ch
                    if ratio < 0.4 or ratio > 2.5:
                        continue
                    
                    # 最小尺寸
                    if cw < 30 or ch < 30:
                        continue
                    
                    confidence = 1.0 / (min_neighbors + 1)  # 低neighbors=高置信度
                    img_detections.append((x1, y1, cw, ch, confidence, f"haar_{cascade_name}_s{scale_factor}_n{min_neighbors}"))
    
    # 策略2: 侧面检测
    for scale_factor in [1.05, 1.1, 1.2]:
        for min_neighbors in [1, 2, 3]:
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8,8))
            gray = clahe.apply(gray)
            
            min_size = max(20, int(min(w_img, h_img) / 80))
            faces = profile_cascade.detectMultiScale(
                gray,
                scaleFactor=scale_factor,
                minNeighbors=min_neighbors,
                minSize=(min_size, min_size),
            )
            
            for (x, y, w, h) in faces:
                pad = int(max(w, h) * 0.2)
                x1 = max(0, x - pad)
                y1 = max(0, y - pad)
                x2 = min(w_img, x + w + pad)
                y2 = min(h_img, y + h + pad)
                cw = x2 - x1
                ch = y2 - y1
                ratio = cw / ch
                if ratio < 0.4 or ratio > 2.5:
                    continue
                if cw < 30 or ch < 30:
                    continue
                confidence = 0.8 / (min_neighbors + 1)
                img_detections.append((x1, y1, cw, ch, confidence, f"profile_s{scale_factor}_n{min_neighbors}"))
    
    # 策略3: 缩小图片再检测（捕获更大的脸）
    for shrink in [0.5, 0.3]:
        small = cv2.resize(img, (0, 0), fx=shrink, fy=shrink)
        gray = cv2.cvtColor(small, cv2.COLOR_BGR2GRAY)
        clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8,8))
        gray = clahe.apply(gray)
        
        for cascade_name, cascade in cascades.items():
            min_size = max(20, int(min(small.shape[1], small.shape[0]) / 60))
            faces = cascade.detectMultiScale(
                gray,
                scaleFactor=1.05,
                minNeighbors=2,
                minSize=(min_size, min_size),
            )
            for (x, y, w, h) in faces:
                # 映射回原图坐标
                ox, oy, ow, oh = int(x/shrink), int(y/shrink), int(w/shrink), int(h/shrink)
                pad = int(max(ow, oh) * 0.2)
                x1 = max(0, ox - pad)
                y1 = max(0, oy - pad)
                x2 = min(w_img, ox + ow + pad)
                y2 = min(h_img, oy + oh + pad)
                cw = x2 - x1
                ch = y2 - y1
                ratio = cw / ch
                if ratio < 0.4 or ratio > 2.5:
                    continue
                if cw < 30 or ch < 30:
                    continue
                img_detections.append((x1, y1, cw, ch, 0.7, f"shrink{shrink}_{cascade_name}"))
    
    print(f"  🔍 原始检测数: {len(img_detections)}")
    
    # NMS去重 - IoU阈值0.3 (宽松合并)
    if not img_detections:
        continue
    
    boxes = np.array([[d[0], d[1], d[0]+d[2], d[1]+d[3]] for d in img_detections])
    scores = np.array([d[4] for d in img_detections])
    
    # 按面积排序，大脸优先
    areas = (boxes[:, 2] - boxes[:, 0]) * (boxes[:, 3] - boxes[:, 1])
    order = areas.argsort()[::-1]
    
    keep = []
    while len(order) > 0:
        i = order[0]
        keep.append(i)
        
        xx1 = np.maximum(boxes[i, 0], boxes[order[1:], 0])
        yy1 = np.maximum(boxes[i, 1], boxes[order[1:], 1])
        xx2 = np.minimum(boxes[i, 2], boxes[order[1:], 2])
        yy2 = np.minimum(boxes[i, 3], boxes[order[1:], 3])
        
        inter = np.maximum(0, xx2 - xx1) * np.maximum(0, yy2 - yy1)
        iou = inter / (areas[i] + areas[order[1:]] - inter + 1e-6)
        
        # 保留IoU < 0.3的（不完全重叠的）
        remaining = np.where(iou < 0.3)[0]
        order = order[remaining + 1]
    
    kept_dets = [img_detections[i] for i in keep]
    print(f"  ✅ NMS后: {len(kept_dets)}")
    
    # 保存提取的人像
    for j, (x1, y1, cw, ch, conf, method) in enumerate(kept_dets):
        # 裁剪并调整为300x300
        face = img[y1:y1+ch, x1:x1+cw]
        if face.size == 0:
            continue
        face_resized = cv2.resize(face, (300, 300), interpolation=cv2.INTER_LANCZOS4)
        
        out_name = f"face_{img_idx+1:02d}_{j+1:02d}_{cw}x{ch}.jpg"
        out_path = os.path.join(output_dir, out_name)
        cv2.imwrite(out_path, face_resized, [cv2.IMWRITE_JPEG_QUALITY, 92])
        all_detections.append((img_idx, out_name, cw, ch, conf, method))

# 统计
print(f"\n{'='*60}")
print(f"📊 提取完成！")
print(f"  总候选数: {len(all_detections)}")
print(f"  输出目录: {output_dir}")

# 按来源分组
from collections import Counter
by_img = Counter(d[0] for d in all_detections)
for img_idx in sorted(by_img.keys()):
    print(f"  照片{img_idx+1}: {by_img[img_idx]}个候选")

# 尺寸分布
sizes = [(d[2], d[3]) for d in all_detections]
if sizes:
    ws = [s[0] for s in sizes]
    hs = [s[1] for s in sizes]
    print(f"\n  宽度范围: {min(ws)}-{max(ws)}px")
    print(f"  高度范围: {min(hs)}-{max(hs)}px")
