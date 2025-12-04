/* 간단한 ID 로그인 + 회원가입 + 파일 업로드 로직 */

const selectors = {
  loginForm: document.getElementById('login-form'),
  idInput: document.getElementById('id-input'),
  loginSection: document.getElementById('login-section'),
  signupSection: document.getElementById('signup-section'),
  signupForm: document.getElementById('signup-form'),
  signupIdInput: document.getElementById('signup-id-input'),
  signupToggle: document.getElementById('signup-toggle'),
  signupCancel: document.getElementById('signup-cancel'),
  dashboard: document.getElementById('dashboard'),
  displayUser: document.getElementById('display-user'),
  logoutBtn: document.getElementById('logout'),
  fileInput: document.getElementById('file-input'),
  uploadBtn: document.getElementById('upload-btn'),
  checkBtn: document.getElementById('check-btn'),
  filePreview: document.getElementById('file-preview'),
  uploadsList: document.getElementById('uploads-list')
}

// 백엔드 서버 URL (환경에 따라 수정 가능)
const BACKEND_URL = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1'
  ? 'http://localhost:5000'
  : window.location.origin;

let currentFile = null;
let uploads = [];

function init(){
  // 업로드 메타데이터 복원
  const saved = localStorage.getItem('uploads_meta');
  if(saved){
    try{ uploads = JSON.parse(saved); }catch(e){ uploads = []; }
  }
  renderUploads();

  // 로그인 폼 핸들러
  selectors.loginForm.addEventListener('submit', onLogin);
  selectors.signupToggle.addEventListener('click', toggleSignupForm);
  selectors.signupForm.addEventListener('submit', onSignup);
  selectors.signupCancel.addEventListener('click', toggleSignupForm);
  selectors.logoutBtn.addEventListener('click', onLogout);
  selectors.fileInput.addEventListener('change', onFileSelect);
  selectors.uploadBtn.addEventListener('click', onUpload);
  selectors.checkBtn.addEventListener('click', onCheck);

  // 기존에 로그인 정보가 있으면 대시보드로
  const auth = localStorage.getItem('auth');
  if(auth){
    const a = JSON.parse(auth);
    showDashboard(a.username);
  }

  // 결과 표시 영역 생성 (없으면)
  if(!document.getElementById('check-results')){
    const r = document.createElement('div');
    r.id = 'check-results';
    r.style.marginTop = '12px';
    selectors.uploadsList.parentNode.appendChild(r);
  }
}

function toggleSignupForm(e){
  e.preventDefault();
  selectors.loginSection.classList.toggle('hidden');
  selectors.signupSection.classList.toggle('hidden');
  if(!selectors.signupSection.classList.contains('hidden')){
    selectors.signupIdInput.focus();
  }else{
    selectors.idInput.focus();
  }
}

function onSignup(e){
  e.preventDefault();
  const username = selectors.signupIdInput.value.trim();
  
  if(!username){
    alert('아이디를 입력하세요.');
    return;
  }

  // 서버에 회원가입 요청
  fetch(BACKEND_URL + '/signup', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ username })
  })
  .then(resp => resp.json())
  .then(data => {
    if(data.error){
      alert(data.error);
    } else {
      alert(data.message || username + '님 회원가입이 완료되었습니다!');
      selectors.signupIdInput.value = '';
      toggleSignupForm({ preventDefault: () => {} });
      selectors.idInput.focus();
    }
  })
  .catch(err => {
    alert('회원가입 중 오류가 발생했습니다: ' + err);
  });
}

function onLogin(e){
  e.preventDefault();
  const username = selectors.idInput.value.trim();
  
  if(!username){
    alert('아이디를 입력하세요.');
    return;
  }

  // 서버에 로그인 요청
  fetch(BACKEND_URL + '/login', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ username })
  })
  .then(resp => resp.json())
  .then(data => {
    if(data.error){
      alert(data.error);
    } else {
      // 로그인 정보 저장
      localStorage.setItem('auth', JSON.stringify({ id: data.id, username: data.username }));
      showDashboard(data.username);
      selectors.idInput.value = '';
    }
  })
  .catch(err => {
    alert('로그인 중 오류가 발생했습니다: ' + err);
  });
}

function onLogout(){
  localStorage.removeItem('auth');
  selectors.dashboard.classList.add('hidden');
  selectors.loginSection.classList.remove('hidden');
  selectors.idInput.focus();
}

function showDashboard(username){
  selectors.displayUser.textContent = username;
  selectors.loginSection.classList.add('hidden');
  selectors.dashboard.classList.remove('hidden');
}

function onFileSelect(e){
  const f = e.target.files && e.target.files[0];
  currentFile = null;
  selectors.filePreview.innerHTML = '';
  
  if(!f) return;
  
  // PDF 파일만 허용
  if(f.type !== 'application/pdf' && !f.name.toLowerCase().endsWith('.pdf')){
    alert('PDF 파일만 업로드 가능합니다.');
    selectors.fileInput.value = '';
    return;
  }
  
  currentFile = f;
  const info = document.createElement('div');
  info.textContent = `${f.name} · ${Math.round(f.size/1024)} KB`;
  selectors.filePreview.appendChild(info);
}

async function onUpload(){
  if(!currentFile){ alert('먼저 파일을 선택하세요.'); return; }
  const uploadUrl = BACKEND_URL + '/file';
  const authRaw = localStorage.getItem('auth');
  if(!authRaw){ alert('로그인 후 업로드하세요.'); return; }
  const auth = JSON.parse(authRaw);
  const userId = auth.username || auth.id || 'unknown';
  try{
    const form = new FormData();
    form.append('file', currentFile);
    form.append('user', userId);
    const resp = await fetch(uploadUrl, {method:'POST', body: form});
    if(resp.ok){
      const result = await resp.json();
      // 서버가 반환한 저장명(pdp) 사용
      addUploadEntry({name: currentFile.name, size: currentFile.size, type: currentFile.type, remote: true, server_name: result.pdf, info: result});
      alert('서버에 업로드 및 추출 성공');
      selectors.fileInput.value=''; currentFile=null; selectors.filePreview.innerHTML='';
      return;
    } else {
      const txt = await resp.text();
      console.error('upload failed', txt);
    }
  }catch(e){ console.error(e); }
  addUploadEntry({name: currentFile.name, size: currentFile.size, type: currentFile.type, remote: false, date: new Date().toISOString()});
  alert('서버 업로드 실패 — 브라우저에 시뮬레이션 저장되었습니다.');
  selectors.fileInput.value=''; currentFile=null; selectors.filePreview.innerHTML='';
}

function addUploadEntry(entry){
  uploads.unshift(entry);
  try{ localStorage.setItem('uploads_meta', JSON.stringify(uploads)); }catch(e){ }
  renderUploads();
}

function renderUploads(){
  selectors.uploadsList.innerHTML='';
  
  // 통합 검사 버튼 상태 업데이트
  selectors.checkBtn.disabled = uploads.length === 0;
  
  if(uploads.length===0){ selectors.uploadsList.innerHTML = '<li class="muted small">업로드된 파일이 없습니다.</li>'; return; }
  for(let i = 0; i < uploads.length; i++){
    const u = uploads[i];
    const li = document.createElement('li');
    const left = document.createElement('div');
    left.textContent = `${u.name} · ${Math.round((u.size||0)/1024)} KB` + (u.remote? ' · (서버)': ' · (로컬 시뮬)');
    const right = document.createElement('div');
    const deleteBtn = document.createElement('button');
    deleteBtn.textContent = '✕';
    deleteBtn.style.cssText = 'background:none;border:none;color:red;cursor:pointer;font-size:18px;padding:0;width:24px;height:24px;';
    deleteBtn.addEventListener('click', () => {
      uploads.splice(i, 1);
      try{ localStorage.setItem('uploads_meta', JSON.stringify(uploads)); }catch(e){ }
      renderUploads();
    });
    right.appendChild(deleteBtn);
    li.appendChild(left);
    li.appendChild(right);
    selectors.uploadsList.appendChild(li);
  }
}

function onCheck(){
  if(uploads.length === 0){
    alert('업로드된 파일이 없습니다. 먼저 파일을 업로드하세요.');
    return;
  }
  const authRaw = localStorage.getItem('auth');
  if(!authRaw){ alert('로그인 후 이용하세요.'); return; }
  const auth = JSON.parse(authRaw);
  const userId = auth.username || auth.id || 'unknown';

  selectors.checkBtn.disabled = true;
  selectors.checkBtn.textContent = '검사 중...';

  (async () => {
    const serverFiles = [];

    // 1) 현재 선택된 파일이 있으면 먼저 업로드하여 서버 저장명 확보
    if(currentFile){
      try{
        const form = new FormData(); form.append('file', currentFile);
        form.append('user', userId);
        const r = await fetch(BACKEND_URL + '/file', {method:'POST', body: form});
        if(r.ok){
          const j = await r.json();
          if(j && j.pdf) serverFiles.push(j.pdf);
          // 업로드 목록에도 추가
          addUploadEntry({name: currentFile.name, size: currentFile.size, type: currentFile.type, remote: true, server_name: j.pdf, info: j});
        }
      }catch(e){ console.error('upload currentFile failed', e); }
    }

    // 2) 기존 업로드 메타에서 서버에 이미 올라간 파일명 수집
    for(const u of uploads){
      if(u.remote && u.server_name){
        serverFiles.push(u.server_name);
      } else if(u.remote && u.info){
        // info에 JSON이 들어있을 수도 있음
        try{
          const parsed = (typeof u.info === 'string')? JSON.parse(u.info) : u.info;
          if(parsed && parsed.pdf) serverFiles.push(parsed.pdf);
        }catch(e){ /* ignore */ }
      }
    }

    if(serverFiles.length === 0){
      alert('서버에 저장된 파일이 없습니다. 먼저 파일을 업로드하세요.');
      selectors.checkBtn.disabled = uploads.length === 0;
      selectors.checkBtn.textContent = '통합 검사';
      return;
    }

    // 3) 요청: user만 보내면 서버가 extracted/<user>/ 내 모든 파일을 검사
    try{
      // gather optional keywords from the input (comma/semicolon separated)
      const keywordRaw = document.getElementById('keyword-input')?.value || ''
      let keywords = []
      if (keywordRaw.trim()) {
        keywords = keywordRaw.split(/[,;]+/).map(k => k.trim()).filter(Boolean)
      }

      const payload = { user: userId, files: serverFiles }
      if (keywords.length > 0) payload.keywords = keywords

      const resp = await fetch(BACKEND_URL + '/combine_check', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      const data = await resp.json();
      renderCheckResults(data);
    }catch(err){
      alert('통합 검사 중 오류가 발생했습니다: ' + err);
    }finally{
      selectors.checkBtn.disabled = uploads.length === 0;
      selectors.checkBtn.textContent = '통합 검사';
    }
  })();
}

function renderCheckResults(data){
  const out = document.getElementById('check-results');
  out.innerHTML = '';
  if(!data){ out.textContent = '빈 결과'; return; }
  if(data.message){ out.textContent = data.message; return; }

  const h = document.createElement('div');
  h.innerHTML = `<strong>파일수:</strong> ${data.file_count || 0}`;
  out.appendChild(h);

  if(data.comparisons && data.comparisons.length){
    data.comparisons.forEach(f => {
      const section = document.createElement('div');
      section.style.borderTop = '1px solid #eee';
      section.style.padding = '8px 0';
      const title = document.createElement('div');
      title.innerHTML = `<strong>${f.file}</strong>`;
      if(f.keywords && f.keywords.length){
        title.innerHTML += ` <span style="color:#666; font-weight:normal;">[키워드: ${f.keywords.join(', ')}]</span>`;
      }
      section.appendChild(title);
      const list = document.createElement('ul');
      list.style.margin = '6px 0 0 16px';
      if(f.comparisons && f.comparisons.length){
        f.comparisons.forEach(c => {
          const li = document.createElement('li');
          const lcs = (c.lcs_score !== undefined && c.lcs_score !== null) ? `LCS: ${c.lcs_score}` : '';
          const ng = (c.ngram_score !== undefined && c.ngram_score !== null) ? `n-gram: ${c.ngram_score}` : '';
          let posText = '';
          if(c.positions && c.positions.a_start >= 0){
            posText = ` [위치: 업로드=${c.positions.a_start}~${c.positions.a_end}, 참조=${c.positions.b_start}~${c.positions.b_end}]`;
          }
          li.textContent = `${c.keyword} · ${c.ref_title || '(no title)'} ${lcs ? '· ' + lcs : ''} ${ng ? '· ' + ng : ''}${posText}`.trim();
          list.appendChild(li);
        });
      } else {
        const li = document.createElement('li');
        li.textContent = '(비교 결과 없음)';
        li.style.color = '#999';
        list.appendChild(li);
      }
      section.appendChild(list);
      out.appendChild(section);
    });
  }
}

document.addEventListener('DOMContentLoaded', init);
