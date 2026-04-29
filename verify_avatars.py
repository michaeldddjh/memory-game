import cv2
import numpy as np
import base64
import os

eye_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_eye.xml')
face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')

# Check each existing avatar
valid = []
invalid = []

for i in range(18):
    path = f"portraits_db/current_{i:02d}.jpg"
    img = cv2.imread(path)
    if img is None:
        print(f"  {i}: CANNOT READ")
        continue
    
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    h, w = img.shape[:2]
    
    # 1. Face detection on the crop
    faces = face_cascade.detectMultiScale(gray, scaleFactor=1.05, minNeighbors=5, minSize=(50, 50))
    face_count = len(faces)
    
    # 2. Eye detection (top 60%)
    top = gray[:int(h*0.6), :]
    eyes = eye_cascade.detectMultiScale(top, scaleFactor=1.05, minNeighbors=4, minSize=(12, 12))
    eye_count = len(eyes)
    
    # 3. Skin color check (center of image)
    cx, cy = w//2, h//2
    sz = min(w, h)//4
    center = img[cy-sz:cy+sz, cx-sz:cx+sz]
    hsv = cv2.cvtColor(center, cv2.COLOR_BGR2HSV)
    lower1 = np.array([0, 30, 60])
    upper1 = np.array([25, 180, 255])
    lower2 = np.array([170, 30, 60])
    upper2 = np.array([180, 180, 255])
    mask1 = cv2.inRange(hsv, lower1, upper1)
    mask2 = cv2.inRange(hsv, lower2, upper2)
    skin = (np.sum(mask1) + np.sum(mask2)) / center.size
    
    # 4. Variance check
    var = np.var(gray)
    
    # 5. Edge density (faces have moderate edge density, trees have very high)
    edges = cv2.Canny(gray, 50, 150)
    edge_density = np.sum(edges > 0) / edges.size
    
    # 6. Check for bilateral symmetry (real faces are more symmetric)
    left_half = gray[:, :w//2]
    right_half = cv2.flip(gray[:, w//2:], 1)
    min_w = min(left_half.shape[1], right_half.shape[1])
    left_crop = left_half[:, :min_w]
    right_crop = right_half[:, :min_w]
    # Resize to same if needed
    if left_crop.shape != right_crop.shape:
        left_crop = cv2.resize(left_crop, (100, 100))
        right_crop = cv2.resize(right_crop, (100, 100))
    symmetry = 1.0 - np.mean(np.abs(left_crop.astype(float) - right_crop.astype(float))) / 255.0
    
    # Decision: valid portrait needs face + 2+ eyes + decent skin + moderate edges + some symmetry
    is_valid = True
    reasons = []
    
    if face_count == 0:
        is_valid = False
        reasons.append("NO FACE")
    if eye_count < 2:
        is_valid = False
        reasons.append(f"ONLY {eye_count} EYES")
    if skin < 0.15:
        is_valid = False
        reasons.append(f"LOW SKIN {skin:.2f}")
    if edge_density > 0.35:
        is_valid = False
        reasons.append(f"HIGH EDGES {edge_density:.2f}")
    if symmetry < 0.65:
        is_valid = False
        reasons.append(f"LOW SYMM {symmetry:.2f}")
    if var < 500:
        is_valid = False
        reasons.append(f"LOW VAR {var:.0f}")
    
    status = "VALID" if is_valid else "INVALID"
    reason_str = " | ".join(reasons) if reasons else "all checks pass"
    print(f"  {i:2d}: {status} face={face_count} eyes={eye_count} skin={skin:.2f} var={var:.0f} edge={edge_density:.2f} sym={symmetry:.2f} => {reason_str}")
    
    if is_valid:
        valid.append(i)
    else:
        invalid.append(i)

print(f"\nValid: {len(valid)} {valid}")
print(f"Invalid: {len(invalid)} {invalid}")
print(f"Need: 18 total, have {len(valid)}, need {18-len(valid)} more")
