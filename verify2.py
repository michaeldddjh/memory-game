import cv2
import numpy as np
import base64
import os

eye_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_eye.xml')
eye2_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_eye_tree_eyeglasses.xml')
face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
face2_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_alt2.xml')

results = []

for i in range(18):
    path = f"portraits_db/current_{i:02d}.jpg"
    img = cv2.imread(path)
    if img is None:
        continue
    
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    h, w = img.shape[:2]
    
    # Face detection with multiple cascades
    faces1 = face_cascade.detectMultiScale(gray, scaleFactor=1.05, minNeighbors=4, minSize=(40, 40))
    faces2 = face2_cascade.detectMultiScale(gray, scaleFactor=1.05, minNeighbors=4, minSize=(40, 40))
    face_count = max(len(faces1), len(faces2))
    
    # Eye detection with multiple cascades and parameters
    top = gray[:int(h*0.65), :]
    
    # Standard eye cascade with various parameters
    eyes_a = eye_cascade.detectMultiScale(top, scaleFactor=1.05, minNeighbors=3, minSize=(10, 10))
    eyes_b = eye_cascade.detectMultiScale(top, scaleFactor=1.1, minNeighbors=2, minSize=(8, 8))
    eyes_c = eye2_cascade.detectMultiScale(top, scaleFactor=1.05, minNeighbors=3, minSize=(10, 10))
    eyes_d = eye2_cascade.detectMultiScale(top, scaleFactor=1.1, minNeighbors=2, minSize=(8, 8))
    
    eye_count = max(len(eyes_a), len(eyes_b), len(eyes_c), len(eyes_d))
    
    # Skin check
    cx, cy = w//2, h//2
    sz = min(w, h)//4
    center = img[cy-sz:cy+sz, cx-sz:cx+sz]
    hsv = cv2.cvtColor(center, cv2.COLOR_BGR2HSV)
    lower1 = np.array([0, 25, 50])
    upper1 = np.array([25, 180, 255])
    lower2 = np.array([170, 25, 50])
    upper2 = np.array([180, 180, 255])
    mask1 = cv2.inRange(hsv, lower1, upper1)
    mask2 = cv2.inRange(hsv, lower2, upper2)
    skin = (np.sum(mask1) + np.sum(mask2)) / center.size
    
    # Edge density
    edges = cv2.Canny(gray, 50, 150)
    edge_density = np.sum(edges > 0) / edges.size
    
    # Symmetry
    left_half = gray[:, :w//2]
    right_half = cv2.flip(gray[:, w//2:], 1)
    min_w2 = min(left_half.shape[1], right_half.shape[1])
    left_crop = left_half[:, :min_w2].astype(float)
    right_crop = right_half[:, :min_w2].astype(float)
    if left_crop.shape != right_crop.shape:
        left_crop = cv2.resize(left_crop, (100, 100))
        right_crop = cv2.resize(right_crop, (100, 100))
    symmetry = 1.0 - np.mean(np.abs(left_crop - right_crop)) / 255.0
    
    # Variance
    var = np.var(gray)
    
    # Score: higher = more likely a valid portrait
    score = 0
    score += min(eye_count, 4) * 25  # 0-100 from eyes
    score += min(face_count, 2) * 15  # 0-30 from face
    score += min(skin, 0.9) * 30      # 0-30 from skin
    score += symmetry * 15            # 0-15 from symmetry
    score -= max(0, edge_density - 0.15) * 50  # penalty for high edges
    
    # Decision
    is_valid = score >= 45 and eye_count >= 2 and skin >= 0.15
    
    status = "VALID" if is_valid else "INVALID"
    print(f"  {i:2d}: {status} score={score:.0f} face={face_count} eyes={eye_count} skin={skin:.2f} sym={symmetry:.2f} edge={edge_density:.2f} var={var:.0f}")
    
    if is_valid:
        results.append((i, score))

results.sort(key=lambda x: -x[1])
print(f"\nValid portraits ({len(results)}):")
for idx, (i, score) in enumerate(results):
    print(f"  {idx+1}. Avatar #{i} (score={score:.0f})")

print(f"\nNeed 18, have {len(results)}, need {max(0, 18-len(results))} more")
