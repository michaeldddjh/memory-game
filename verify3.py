import cv2
import numpy as np
import base64

eye_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_eye.xml')
eye2_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_eye_tree_eyeglasses.xml')
face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
face_alt = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_alt.xml')
face_alt2 = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_alt2.xml')

results = []

for i in range(18):
    path = f"portraits_db/current_{i:02d}.jpg"
    img = cv2.imread(path)
    if img is None:
        continue
    
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    h, w = img.shape[:2]
    
    # Comprehensive face detection
    f1 = len(face_cascade.detectMultiScale(gray, 1.05, 4, minSize=(30,30)))
    f2 = len(face_alt.detectMultiScale(gray, 1.05, 4, minSize=(30,30)))
    f3 = len(face_alt2.detectMultiScale(gray, 1.05, 4, minSize=(30,30)))
    face_count = max(f1, f2, f3)
    
    # Comprehensive eye detection
    top = gray[:int(h*0.65), :]
    e1 = len(eye_cascade.detectMultiScale(top, 1.03, 2, minSize=(8,8)))
    e2 = len(eye_cascade.detectMultiScale(top, 1.05, 3, minSize=(10,10)))
    e3 = len(eye2_cascade.detectMultiScale(top, 1.03, 2, minSize=(8,8)))
    e4 = len(eye2_cascade.detectMultiScale(top, 1.05, 3, minSize=(10,10)))
    # Also try full image eye detection
    e5 = len(eye_cascade.detectMultiScale(gray, 1.03, 2, minSize=(8,8)))
    e6 = len(eye2_cascade.detectMultiScale(gray, 1.03, 2, minSize=(8,8)))
    eye_count = max(e1, e2, e3, e4, e5, e6)
    
    # Skin
    cx, cy = w//2, h//2
    sz = min(w,h)//4
    center = img[cy-sz:cy+sz, cx-sz:cx+sz]
    hsv = cv2.cvtColor(center, cv2.COLOR_BGR2HSV)
    lower1 = np.array([0, 25, 50])
    upper1 = np.array([25, 180, 255])
    lower2 = np.array([170, 25, 50])
    upper2 = np.array([180, 180, 255])
    mask1 = cv2.inRange(hsv, lower1, upper1)
    mask2 = cv2.inRange(hsv, lower2, upper2)
    skin = (np.sum(mask1) + np.sum(mask2)) / center.size
    
    # Symmetry
    left = gray[:, :w//2].astype(float)
    right = cv2.flip(gray[:, w//2:], 1).astype(float)
    if left.shape != right.shape:
        left = cv2.resize(left, (100,100))
        right = cv2.resize(right, (100,100))
    else:
        mw = min(left.shape[1], right.shape[1])
        left = left[:, :mw]
        right = right[:, :mw]
    sym = 1.0 - np.mean(np.abs(left - right)) / 255.0
    
    # Edge density
    edges = cv2.Canny(gray, 50, 150)
    edge_d = np.sum(edges > 0) / edges.size
    
    # Final score: weight all factors
    score = 0
    score += min(face_count, 2) * 20
    score += min(eye_count, 4) * 20
    score += min(skin, 0.9) * 25
    score += sym * 15
    score -= max(0, edge_d - 0.20) * 40
    
    # A portrait must have: at least 1 face detected + high skin + decent symmetry
    # Eye count is relaxed to >=1 (some faces are 3/4 profile with only 1 visible eye)
    is_valid = (face_count >= 1 and skin >= 0.20 and sym >= 0.70 and score >= 40)
    
    status = "VALID" if is_valid else "BAD  "
    print(f"  {i:2d}: {status} score={score:5.1f} face={face_count} eyes={eye_count} skin={skin:.2f} sym={sym:.2f} edge={edge_d:.2f}")
    
    results.append((i, score, is_valid, eye_count, face_count, skin, sym))

# Sort by score
valid = [(i,s) for i,s,v,e,f,sk,sy in results if v]
invalid = [(i,s) for i,s,v,e,f,sk,sy in results if not v]

print(f"\nValid: {len(valid)}")
valid.sort(key=lambda x: -x[1])
for rank, (i, s) in enumerate(valid):
    print(f"  {rank+1}. Avatar #{i} (score={s:.1f})")

print(f"\nInvalid: {len(invalid)}")
invalid.sort(key=lambda x: -x[1])
for rank, (i, s) in enumerate(invalid):
    print(f"  {rank+1}. Avatar #{i} (score={s:.1f})")

print(f"\nNeed 18, have {len(valid)}, gap = {18-len(valid)}")
