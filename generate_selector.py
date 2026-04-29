#!/usr/bin/env python3
"""生成筛选页面 - 按源照片分组展示候选人像"""
import os, hashlib, base64, json

upload_dir = os.path.expanduser("~/.hermes-web-ui/upload/")
gallery_dir = os.path.expanduser("~/Desktop/portrait_gallery_v2/")

# 去重源图
hashes = {}
for f in sorted(os.listdir(upload_dir)):
    if f.startswith('.'): continue
    fp = os.path.join(upload_dir, f)
    h = hashlib.md5(open(fp, 'rb').read()).hexdigest()
    if h not in hashes:
        hashes[h] = fp
source_images = list(hashes.values())

# 按照片分组候选人像
gallery_files = sorted([f for f in os.listdir(gallery_dir) if f.endswith('.jpg')])
groups = {}
for f in gallery_files:
    img_idx = int(f.split('_')[1])  # face_XX_...
    if img_idx not in groups:
        groups[img_idx] = []
    groups[img_idx].append(f)

# 生成HTML
html = '''<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>头像筛选器</title>
<style>
* { margin:0; padding:0; box-sizing:border-box; }
body { background:#1a1a2e; color:#eee; font-family:system-ui; padding:20px; }
h1 { text-align:center; margin-bottom:20px; color:#e94560; font-size:28px; }
.stats { text-align:center; margin-bottom:20px; font-size:18px; color:#0f3460; background:#16213e; padding:10px; border-radius:10px; }
.stats span { color:#e94560; font-weight:bold; font-size:24px; }
.group { margin-bottom:30px; background:#16213e; border-radius:15px; padding:20px; }
.group-header { display:flex; align-items:center; gap:15px; margin-bottom:15px; }
.group-header h2 { color:#0f3460; font-size:20px; }
.group-header .count { background:#e94560; color:white; padding:3px 10px; border-radius:20px; font-size:14px; }
.source-img { max-width:400px; max-height:250px; border-radius:10px; border:2px solid #0f3460; }
.candidates { display:flex; flex-wrap:wrap; gap:12px; margin-top:15px; }
.candidate { position:relative; cursor:pointer; border-radius:10px; overflow:hidden; border:3px solid transparent; transition:all 0.2s; width:120px; }
.candidate:hover { border-color:#0f3460; transform:scale(1.05); }
.candidate.selected { border-color:#00ff88; box-shadow:0 0 15px rgba(0,255,136,0.5); }
.candidate.rejected { border-color:#ff4444; opacity:0.4; }
.candidate img { width:120px; height:120px; object-fit:cover; display:block; }
.candidate .label { position:absolute; top:3px; right:3px; background:rgba(0,0,0,0.7); color:white; padding:1px 6px; border-radius:8px; font-size:10px; }
.candidate .check { position:absolute; top:50%; left:50%; transform:translate(-50%,-50%); font-size:40px; display:none; text-shadow:0 2px 10px rgba(0,0,0,0.8); }
.candidate.selected .check { display:block; color:#00ff88; }
.candidate .info { position:absolute; bottom:0; left:0; right:0; background:rgba(0,0,0,0.7); color:#aaa; padding:2px 6px; font-size:9px; text-align:center; }
.actions { position:fixed; bottom:0; left:0; right:0; background:#0f3460; padding:15px 20px; display:flex; justify-content:center; gap:20px; z-index:100; box-shadow:0 -5px 20px rgba(0,0,0,0.5); }
.actions button { padding:12px 30px; border:none; border-radius:10px; font-size:16px; cursor:pointer; font-weight:bold; }
.btn-confirm { background:#00ff88; color:#000; }
.btn-confirm:hover { background:#00cc66; }
.btn-clear { background:#ff4444; color:white; }
.btn-clear:hover { background:#cc2222; }
.instructions { background:#16213e; padding:15px; border-radius:10px; margin-bottom:20px; line-height:1.8; }
.instructions b { color:#e94560; }
</style>
</head>
<body>
<h1>🎯 头像筛选器</h1>
<div class="instructions">
<b>操作方式：</b>点击 = ✅选中真实人脸（绿框） | 再点 = ❌标记为误检（红框淡出） | 再点 = 取消选择<br>
<b>目标：</b>至少选出 <b>20个</b> 有效头像！选完后点底部"确认筛选"
</div>
<div class="stats">已选中 <span id="count">0</span> 个有效头像</div>
'''

for i, src_path in enumerate(source_images):
    img_idx = i + 1
    candidates = groups.get(img_idx, [])
    if not candidates:
        continue
    
    # 读取源图缩略图
    import cv2
    img = cv2.imread(src_path)
    if img is not None:
        # 缩小到400px宽
        h, w = img.shape[:2]
        scale = 400 / w
        img = cv2.resize(img, (0,0), fx=scale, fy=scale)
        _, buf = cv2.imencode('.jpg', img, [cv2.IMWRITE_JPEG_QUALITY, 80])
        src_b64 = base64.b64encode(buf).decode()
    
    html += f'''
<div class="group">
  <div class="group-header">
    <img class="source-img" src="data:image/jpeg;base64,{src_b64}">
    <div>
      <h2>📷 照片 {img_idx}</h2>
      <div class="count">{len(candidates)} 个候选</div>
    </div>
  </div>
  <div class="candidates" id="group_{img_idx}">
'''
    
    for j, fname in enumerate(candidates):
        face_path = os.path.join(gallery_dir, fname)
        face_b64 = base64.b64encode(open(face_path, 'rb').read()).decode()
        # 从文件名提取尺寸信息
        parts = fname.replace('.jpg','').split('_')
        size_info = parts[-2] if len(parts) >= 2 else ''
        method = parts[-1] if len(parts) >= 1 else ''
        
        html += f'''
    <div class="candidate" data-file="{fname}" onclick="toggle(this)">
      <img src="data:image/jpeg;base64,{face_b64}">
      <span class="label">{j+1}</span>
      <span class="check">✓</span>
      <div class="info">{method}</div>
    </div>
'''
    
    html += '  </div>\n</div>\n'

html += '''
<div class="actions">
  <button class="btn-clear" onclick="clearAll()">🔄 清空选择</button>
  <button class="btn-confirm" onclick="confirm()">✅ 确认筛选</button>
</div>

<script>
let selected = new Set();

function toggle(el) {
  const f = el.dataset.file;
  if (el.classList.contains('selected')) {
    el.classList.remove('selected');
    el.classList.add('rejected');
    selected.delete(f);
  } else if (el.classList.contains('rejected')) {
    el.classList.remove('rejected');
    selected.delete(f);
  } else {
    el.classList.add('selected');
    selected.add(f);
  }
  document.getElementById('count').textContent = selected.size;
}

function clearAll() {
  document.querySelectorAll('.candidate').forEach(el => {
    el.classList.remove('selected', 'rejected');
  });
  selected.clear();
  document.getElementById('count').textContent = 0;
}

function confirm() {
  if (selected.size < 20) {
    alert('⚠️ 你只选了 ' + selected.size + ' 个，至少需要20个！继续选吧~');
    return;
  }
  const files = Array.from(selected);
  const text = JSON.stringify(files);
  navigator.clipboard.writeText(text).then(() => {
    alert('✅ 已复制 ' + files.length + ' 个头像到剪贴板！粘贴给麦白即可~');
  }).catch(() => {
    prompt('复制以下内容给麦白:', text);
  });
}
</script>
</body>
</html>
'''

out_path = os.path.expanduser("~/Desktop/face_selector_v2.html")
with open(out_path, 'w') as f:
    f.write(html)
print(f"✅ 筛选页面已生成: {out_path}")
print(f"📊 总候选: {len(gallery_files)} 个")
print(f"📷 来源照片: {len(source_images)} 张")
