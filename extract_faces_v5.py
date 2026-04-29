#!/usr/bin/env python3
"""
人脸提取 v5 - MediaPipe Tasks API + Haar兜底
"""
import cv2
import os
import numpy as np
import hashlib
import mediapipe as mp
from mediapipe.tasks.python import vision
from mediapipe.tasks.python.core import base_options

upload_dir = os.path.expanduser("~/.hermes-web-ui/upload/")
output_dir = os.path.expanduser("~/Desktop/portrait_gallery_v2/")
os.makedirs(output_dir, exist_ok=True)
for f in os.listdir(output_dir):
    os.remove(os.path.join(output_dir, f))

# 去重
hashes = {}
for f in sorted(os.listdir(upload_dir)):
    if f.startswith('.'): continue
    fp = os.path.join(upload_dir, f)
    h = hashlib.md5(open(fp, 'rb').read()).hexdigest()
    if h not in hashes:
        hashes[h] = fp
source_images = list(hashes.values())
print(f"📷 独立源图: {len(source_images)}")

# Haar级联兜底
haar_dir = cv2.data.haarcascades
cascade_default = cv2.CascadeClassifier(os.path.join(haar_dir, 'haarcascade_frontalface_default.xml'))
cascade_profile = cv2.CascadeClassifier(os.path.join(haar_dir, 'haarcascade_profileface.xml'))

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SHORT_MODEL = os.path.join(SCRIPT_DIR, "face_detector.tflite")
FULL_MODEL = os.path.join(SCRIPT_DIR, "face_detector_full.tflite")

MAX_DIM = 2500
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
    print(f"  处理尺寸: {w_img}x{h_img}")
    
    img_dets = []
    
    # ===== 策略1: MediaPipe Full Range =====
    if os.path.exists(FULL_MODEL):
        options = vision.FaceDetectorOptions(
            base_options=base_options.BaseOptions(model_asset_path=FULL_MODEL),
            running_mode=vision.RunningMode.IMAGE,
            min_detection_confidence=0.3,
        )
        detector = vision.FaceDetector.create_from_options(options)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
        # Need to import mediapipe as mp
        result = detector.detect(mp_image)
        for det in result.detections:
            bbox = det.bounding_box
            x, y, w, h = bbox.origin_x, bbox.origin_y, bbox.width, bbox.height
            pad = int(max(w, h) * 0.15)
            x1, y1 = max(0, x-pad), max(0, y-pad)
            x2, y2 = min(w_img, x+w+pad), min(h_img, y+h+pad)
            cw, ch = x2-x1, y2-y1
            r = cw / ch if ch > 0 else 0
            if 0.3 < r < 3.0 and cw >= 20:
                img_dets.append((x1, y1, cw, ch, "mp_full"))
        detector.close()
        print(f"  MediaPipe Full: {len([d for d in img_dets if d[4]=='mp_full'])}个")
    
    # ===== 策略2: MediaPipe Short Range =====
    if os.path.exists(SHORT_MODEL):
        options = vision.FaceDetectorOptions(
            base_options=base_options.BaseOptions(model_asset_path=SHORT_MODEL),
            running_mode=vision.RunningMode.IMAGE,
            min_detection_confidence=0.3,
        )
        detector = vision.FaceDetector.create_from_options(options)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
        result = detector.detect(mp_image)
        for det in result.detections:
            bbox = det.bounding_box
            x, y, w, h = bbox.origin_x, bbox.origin_y, bbox.width, bbox.height
            pad = int(max(w, h) * 0.15)
            x1, y1 = max(0, x-pad), max(0, y-pad)
            x2, y2 = min(w_img, x+w+pad), min(h_img, y+h+pad)
            cw, ch = x2-x1, y2-y1
            r = cw / ch if ch > 0 else 0
            if 0.3 < r < 3.0 and cw >= 20:
                img_dets.append((x1, y1, cw, ch, "mp_short"))
        detector.close()
        print(f"  MediaPipe Short: {len([d for d in img_dets if d[4]=='mp_short'])}个")
    
    # ===== 策略3: Haar兜底 =====
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
    gray = clahe.apply(gray)
    
    min_sz = max(20, int(min(w_img, h_img) / 60))
    faces = cascade_default.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=3, minSize=(min_sz, min_sz))
    haar_dets = 0
    for (x, y, w, h) in faces:
        pad = int(max(w, h) * 0.15)
        x1, y1 = max(0, x-pad), max(0, y-pad)
        x2, y2 = min(w_img, x+w+pad), min(h_img, y+h+pad)
        cw, ch = x2-x1, y2-y1
        r = cw / ch
        if 0.4 < r < 2.5 and cw >= 30:
            img_dets.append((x1, y1, cw, ch, "haar_def"))
            haar_dets += 1
    
    faces = cascade_profile.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=3, minSize=(min_sz, min_sz))
    for (x, y, w, h) in faces:
        pad = int(max(w, h) * 0.15)
        x1, y1 = max(0, x-pad), max(0, y-pad)
        x2, y2 = min(w_img, x+w+pad), min(h_img, y+h+pad)
        cw, ch = x2-x1, y2-y1
        r = cw / ch
        if 0.4 < r < 2.5 and cw >= 30:
            img_dets.append((x1, y1, cw, ch, "haar_prof"))
            haar_dets += 1
    print(f"  Haar: {haar_dets}个")
    
    print(f"  🔍 原始总计: {len(img_dets)}")
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
        out_name = f"face_{img_idx+1:02d}_{j+1:02d}_{cw}x{ch}_{method}.jpg"
        cv2.imwrite(os.path.join(output_dir, out_name), face_r, [cv2.IMWRITE_JPEG_QUALITY, 92])
        all_detections.append((img_idx, out_name, cw, ch, method))

print(f"\n{'='*50}")
print(f"📊 提取完成！总候选: {len(all_detections)}")
print(f"📁 目录: {output_dir}")

from collections import Counter
by_img = Counter(d[0] for d in all_detections)
for idx in sorted(by_img.keys()):
    print(f"  照片{idx+1}: {by_img[idx]}个")

mp_count = sum(1 for d in all_detections if d[4].startswith('mp_'))
haar_count = sum(1 for d in all_detections if d[4].startswith('haar_'))
print(f"\n  MediaPipe: {mp_count}个, Haar: {haar_count}个")
