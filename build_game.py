import json

# Read the avatars JS file
with open("/Users/michael/projects/memory-game/avatars/avatars_data.js", "r") as f:
    js_content = f.read()

# Extract the base64 URLs from the JS
# The format is: const AVATARS = ["data:image/png;base64,...", ...];
import re
match = re.search(r'const AVATARS = \[(.*?)\];', js_content, re.DOTALL)
avatar_urls = json.loads(f'[{match.group(1)}]')
print(f"Extracted {len(avatar_urls)} avatar URLs")

html = '''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
<title>🃏 记忆翻牌PK</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif;
  background:linear-gradient(135deg,#0f0c29,#302b63,#24243e);min-height:100vh;
  display:flex;justify-content:center;align-items:center;color:#fff;overflow:hidden}
.game-wrap{max-width:420px;width:100%;padding:16px;text-align:center}
h1{font-size:1.6em;margin-bottom:4px;background:linear-gradient(90deg,#f093fb,#f5576c);
  -webkit-background-clip:text;-webkit-text-fill-color:transparent}
.subtitle{font-size:.85em;color:#aaa;margin-bottom:12px}
.stats{display:flex;justify-content:center;gap:24px;margin:10px 0;font-size:1.1em}
.stats span{background:rgba(255,255,255,.1);padding:6px 16px;border-radius:20px}
.stats .label{color:#aaa;font-size:.75em;display:block}
.stats .val{font-weight:700;font-size:1.2em}
.board{display:grid;grid-template-columns:repeat(4,1fr);gap:8px;margin:12px auto;
  perspective:800px}
.card{aspect-ratio:1;cursor:pointer;position:relative;transform-style:preserve-3d;
  transition:transform .4s;border-radius:12px}
.card.flipped{transform:rotateY(180deg)}
.card.matched{transform:rotateY(180deg);opacity:.7;pointer-events:none}
.card-face{position:absolute;inset:0;border-radius:12px;backface-visibility:hidden;
  display:flex;align-items:center;justify-content:center;overflow:hidden}
.card-back{background:linear-gradient(135deg,#667eea,#764ba2);border:2px solid rgba(255,255,255,.2);
  font-size:2em;box-shadow:0 4px 15px rgba(102,126,234,.4)}
.card-back::after{content:'🃏'}
.card-front{transform:rotateY(180deg);background:#1a1a2e;border:2px solid rgba(255,255,255,.15)}
.card-front img{width:80%;height:80%;object-fit:cover;border-radius:50%;
  border:3px solid rgba(255,255,255,.3)}
.btn{display:inline-block;padding:12px 28px;border:none;border-radius:25px;font-size:1em;
  font-weight:600;cursor:pointer;margin:6px;transition:all .2s}
.btn-primary{background:linear-gradient(135deg,#f093fb,#f5576c);color:#fff}
.btn-primary:hover{transform:scale(1.05);box-shadow:0 6px 20px rgba(245,87,108,.4)}
.btn-secondary{background:rgba(255,255,255,.15);color:#fff;border:1px solid rgba(255,255,255,.3)}
.btn-secondary:hover{background:rgba(255,255,255,.25)}
.modal{position:fixed;inset:0;background:rgba(0,0,0,.8);display:flex;align-items:center;
  justify-content:center;z-index:100;opacity:0;pointer-events:none;transition:opacity .3s}
.modal.show{opacity:1;pointer-events:auto}
.modal-content{background:linear-gradient(135deg,#1a1a2e,#16213e);padding:30px;
  border-radius:20px;text-align:center;max-width:340px;width:90%;
  border:1px solid rgba(255,255,255,.1);box-shadow:0 20px 60px rgba(0,0,0,.5)}
.modal-content h2{font-size:1.6em;margin-bottom:8px}
.rating{font-size:3em;margin:10px 0}
.result-stats{margin:15px 0;font-size:1.1em;line-height:2}
.result-stats .label{color:#aaa}
.pk-info{background:linear-gradient(135deg,#ff6b6b,#ee5a24);padding:10px 16px;
  border-radius:12px;margin:10px 0;font-size:.9em}
.pk-info .vs{font-size:1.4em;font-weight:700;margin:4px 0}
.leaderboard{margin-top:12px;text-align:left}
.leaderboard h3{font-size:1em;color:#aaa;margin-bottom:6px}
.leaderboard ol{padding-left:20px;font-size:.9em;line-height:1.8}
.leaderboard li{border-bottom:1px solid rgba(255,255,255,.05);padding:2px 0}
.confetti{position:fixed;top:-10px;font-size:1.5em;animation:fall linear forwards;z-index:200;
  pointer-events:none}
@keyframes fall{to{transform:translateY(110vh) rotate(720deg);opacity:0}}
.name-input{background:rgba(255,255,255,.1);border:1px solid rgba(255,255,255,.2);
  border-radius:8px;padding:8px 14px;color:#fff;font-size:1em;width:70%;margin:8px 0;
  text-align:center;outline:none}
.name-input:focus{border-color:#f093fb}
.name-input::placeholder{color:#666}
.hidden{display:none}
</style>
</head>
<body>
<div class="game-wrap">
  <h1>🃏 记忆翻牌PK</h1>
  <p class="subtitle">找出8对头像，挑战最少步数！</p>
  
  <!-- PK Challenge Banner -->
  <div id="pkBanner" class="pk-info hidden">
    ⚔️ <span id="challengerName"></span> 邀请你PK！<br>
    成绩：<span id="challengerSteps"></span>步 / <span id="challengerTime"></span>秒<br>
    <span class="vs">你能超越吗？</span>
  </div>

  <!-- Name Input -->
  <div id="nameSection">
    <input type="text" id="nameInput" class="name-input" placeholder="输入你的昵称" maxlength="10">
  </div>

  <div class="stats" id="statsBar">
    <span><span class="label">步数</span><span class="val" id="steps">0</span></span>
    <span><span class="label">时间</span><span class="val" id="timer">0s</span></span>
    <span><span class="label">配对</span><span class="val" id="pairs">0/8</span></span>
  </div>

  <div class="board" id="board"></div>

  <div id="controls">
    <button class="btn btn-primary" onclick="startGame()">🎮 开始游戏</button>
    <button class="btn btn-secondary" onclick="generatePKLink()" id="pkBtn" style="display:none">🔗 生成PK链接</button>
  </div>

  <div class="leaderboard" id="leaderboard"></div>
</div>

<!-- Result Modal -->
<div class="modal" id="resultModal">
  <div class="modal-content">
    <h2>🎉 恭喜完成！</h2>
    <div class="rating" id="ratingEmoji"></div>
    <div class="result-stats">
      <span class="label">步数：</span><strong id="finalSteps"></strong><br>
      <span class="label">用时：</span><strong id="finalTime"></strong><br>
      <span class="label">评级：</span><strong id="finalGrade"></strong>
    </div>
    <div id="pkResult" class="hidden" style="margin:10px 0"></div>
    <button class="btn btn-primary" onclick="startGame()">🔄 再来一局</button>
    <button class="btn btn-secondary" onclick="generatePKLink()">🔗 生成PK链接</button>
    <button class="btn btn-secondary" onclick="copyLink()" id="copyBtn" style="display:none">📋 复制链接</button>
  </div>
</div>

<script>
// Embedded avatar data from the group photo
const AVATAR_URLS = ''' + json.dumps(avatar_urls) + ''';

let cards=[], flipped=[], matched=0, steps=0, startTime=null, timerInterval=null, gameActive=false;
let playerName='';

// Check PK challenge from URL
const urlParams = new URLSearchParams(window.location.search);
const isPK = urlParams.get('pk') === 'challenge';
const challengerName = urlParams.get('challenger') || '挑战者';
const challengerSteps = parseInt(urlParams.get('steps')) || 0;
const challengerTime = parseInt(urlParams.get('time')) || 0;

if(isPK){
  document.getElementById('pkBanner').classList.remove('hidden');
  document.getElementById('challengerName').textContent = challengerName;
  document.getElementById('challengerSteps').textContent = challengerSteps;
  document.getElementById('challengerTime').textContent = challengerTime;
}

// Load name from localStorage
const savedName = localStorage.getItem('memgame_name') || '';
document.getElementById('nameInput').value = savedName;

// Show leaderboard
showLeaderboard();

function startGame(){
  playerName = document.getElementById('nameInput').value.trim() || '匿名玩家';
  localStorage.setItem('memgame_name', playerName);
  
  matched=0; steps=0; flipped=[];
  gameActive=true;
  document.getElementById('steps').textContent='0';
  document.getElementById('pairs').textContent='0/8';
  document.getElementById('timer').textContent='0s';
  document.getElementById('pkBtn').style.display='none';
  document.getElementById('resultModal').classList.remove('show');
  
  // Create card pairs (8 pairs = 16 cards)
  const pairIds = [];
  for(let i=0;i<8;i++) pairIds.push(i,i);
  shuffle(pairIds);
  
  const board = document.getElementById('board');
  board.innerHTML = '';
  cards = [];
  
  pairIds.forEach((id, idx) => {
    const card = document.createElement('div');
    card.className = 'card';
    card.dataset.pairId = id;
    card.innerHTML = `
      <div class="card-face card-back"></div>
      <div class="card-face card-front">
        <img src="${AVATAR_URLS[id]}" alt="头像${id+1}">
      </div>`;
    card.addEventListener('click', () => flipCard(card));
    board.appendChild(card);
    cards.push(card);
  });
  
  // Start timer
  startTime = Date.now();
  if(timerInterval) clearInterval(timerInterval);
  timerInterval = setInterval(()=>{
    const s = Math.floor((Date.now()-startTime)/1000);
    document.getElementById('timer').textContent = s+'s';
  }, 200);
}

function flipCard(card){
  if(!gameActive || card.classList.contains('flipped') || card.classList.contains('matched') || flipped.length>=2) return;
  card.classList.add('flipped');
  flipped.push(card);
  
  if(flipped.length === 2){
    steps++;
    document.getElementById('steps').textContent = steps;
    
    const [a,b] = flipped;
    if(a.dataset.pairId === b.dataset.pairId){
      // Match!
      setTimeout(()=>{
        a.classList.add('matched');
        b.classList.add('matched');
        matched++;
        document.getElementById('pairs').textContent = matched+'/8';
        flipped=[];
        if(matched===8) gameWon();
      }, 400);
    } else {
      // No match
      setTimeout(()=>{
        a.classList.remove('flipped');
        b.classList.remove('flipped');
        flipped=[];
      }, 800);
    }
  }
}

function gameWon(){
  gameActive=false;
  clearInterval(timerInterval);
  const elapsed = Math.floor((Date.now()-startTime)/1000);
  
  // Rating
  let grade, emoji;
  if(steps<=12){grade='S';emoji='🧠';}
  else if(steps<=18){grade='A';emoji='🎯';}
  else if(steps<=28){grade='B';emoji='👍';}
  else{grade='C';emoji='💪';}
  
  document.getElementById('ratingEmoji').textContent = emoji;
  document.getElementById('finalSteps').textContent = steps;
  document.getElementById('finalTime').textContent = elapsed+'秒';
  document.getElementById('finalGrade').textContent = grade;
  
  // PK comparison
  if(isPK){
    const pkDiv = document.getElementById('pkResult');
    pkDiv.classList.remove('hidden');
    const won = steps < challengerSteps || (steps === challengerSteps && elapsed < challengerTime);
    pkDiv.innerHTML = won
      ? `<div style="color:#4ecdc4;font-size:1.2em;font-weight:700">🏆 你赢了！</div>
         <div style="font-size:.9em;color:#aaa;margin-top:4px">
         你：${steps}步/${elapsed}秒 vs ${challengerName}：${challengerSteps}步/${challengerTime}秒</div>`
      : `<div style="color:#ff6b6b;font-size:1.2em;font-weight:700">😢 ${challengerName}更胜一筹</div>
         <div style="font-size:.9em;color:#aaa;margin-top:4px">
         你：${steps}步/${elapsed}秒 vs ${challengerName}：${challengerSteps}步/${challengerTime}秒</div>`;
  }
  
  // Save to leaderboard
  saveScore(playerName, steps, elapsed, grade);
  showLeaderboard();
  
  setTimeout(()=>{
    document.getElementById('resultModal').classList.add('show');
    document.getElementById('pkBtn').style.display='inline-block';
    spawnConfetti();
  }, 500);
}

function saveScore(name, steps, time, grade){
  let scores = JSON.parse(localStorage.getItem('memgame_scores')||'[]');
  scores.push({name,steps,time,grade,date:new Date().toLocaleDateString('zh-CN')});
  scores.sort((a,b)=>a.steps-b.steps || a.time-b.time);
  if(scores.length>20) scores=scores.slice(0,20);
  localStorage.setItem('memgame_scores', JSON.stringify(scores));
}

function showLeaderboard(){
  const scores = JSON.parse(localStorage.getItem('memgame_scores')||'[]');
  const lb = document.getElementById('leaderboard');
  if(!scores.length){lb.innerHTML='';return;}
  lb.innerHTML='<h3>🏆 排行榜</h3><ol>'+scores.slice(0,5).map(s=>
    `<li><strong>${s.name}</strong> — ${s.steps}步 / ${s.time}秒 <span style="color:#f093fb">${s.grade}</span></li>`
  ).join('')+'</ol>';
}

function generatePKLink(){
  const elapsed = Math.floor((Date.now()-startTime)/1000);
  const base = window.location.origin + window.location.pathname;
  const link = `${base}?pk=challenge&challenger=${encodeURIComponent(playerName)}&steps=${steps}&time=${elapsed}`;
  window._pkLink = link;
  document.getElementById('copyBtn').style.display='inline-block';
  // Also try Web Share API
  if(navigator.share){
    navigator.share({title:'🃏 记忆翻牌PK',text:`${playerName}挑战你！${steps}步/${elapsed}秒，你能超越吗？`,url:link}).catch(()=>{});
  }
}

function copyLink(){
  if(window._pkLink){
    navigator.clipboard.writeText(window._pkLink).then(()=>{
      const btn = document.getElementById('copyBtn');
      btn.textContent='✅ 已复制！';
      setTimeout(()=>{btn.textContent='📋 复制链接';},2000);
    });
  }
}

function shuffle(arr){
  for(let i=arr.length-1;i>0;i--){
    const j=Math.floor(Math.random()*(i+1));
    [arr[i],arr[j]]=[arr[j],arr[i]];
  }
}

function spawnConfetti(){
  const emojis=['🎉','🎊','✨','🌟','💫','🎈'];
  for(let i=0;i<30;i++){
    const el=document.createElement('div');
    el.className='confetti';
    el.textContent=emojis[Math.floor(Math.random()*emojis.length)];
    el.style.left=Math.random()*100+'vw';
    el.style.animationDuration=(2+Math.random()*2)+'s';
    el.style.animationDelay=Math.random()*0.5+'s';
    document.body.appendChild(el);
    setTimeout(()=>el.remove(),5000);
  }
}
</script>
</body>
</html>'''

with open("/Users/michael/projects/memory-game/index.html", "w") as f:
    f.write(html)

print(f"✅ Game HTML written: {len(html)} chars ({len(html)//1024}KB)")
print(f"   Avatars embedded: {len(avatar_urls)}")
print(f"   File: /Users/michael/projects/memory-game/index.html")
