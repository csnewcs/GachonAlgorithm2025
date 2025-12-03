/* Kakao 로그인 기반 + 기존 업로드 로직 유지
   - Kakao 로그인: 클라이언트에서 로그인 후 사용자 정보를 받아 로컬에 저장
   - 업로드: 기존 방식과 동일하게 서버 `/upload`에 POST 시도, 실패 시 로컬 시뮬레이션
*/

const selectors = {
  loginSection: document.getElementById('login-section'),
  dashboard: document.getElementById('dashboard'),
  displayUser: document.getElementById('display-user'),
  logoutBtn: document.getElementById('logout'),
  fileInput: document.getElementById('file-input'),
  uploadBtn: document.getElementById('upload-btn'),
  filePreview: document.getElementById('file-preview'),
  uploadsList: document.getElementById('uploads-list'),
  kakaoButtonContainer: document.getElementById('kakao-button')
}

// .env 파일에서 Kakao REST API 키를 읽음 (또는 서버에서 주입)
let KAKAO_APP_KEY = 'REPLACE_WITH_YOUR_KAKAO_APP_KEY';

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

  selectors.logoutBtn.addEventListener('click', onLogout);
  selectors.fileInput.addEventListener('change', onFileSelect);
  selectors.uploadBtn.addEventListener('click', onUpload);

  // 기존에 로그인 정보가 있으면 대시보드로
  const auth = localStorage.getItem('auth');
  if(auth){
    const a = JSON.parse(auth);
    showDashboard(a.user.name || a.user.email);
  }

  // 서버에서 설정 로드
  loadConfig();
}

async function loadConfig(){
  try{
    console.log('Config 로드 시작:', BACKEND_URL + '/config');
    const response = await fetch(BACKEND_URL + '/config');
    if(response.ok){
      const config = await response.json();
      KAKAO_APP_KEY = config.kakao_app_key;
      console.log('Kakao 설정 로드 완료:', KAKAO_APP_KEY);
    } else {
      console.error('Config 응답 상태:', response.status);
    }
  }catch(e){
    console.error('Config 로드 실패:', e);
  }
  // Kakao SDK 초기화 시도
  waitForKakaoAndInit();
}

function waitForKakaoAndInit(){
  console.log('Kakao SDK 대기 시작');
  
  // Kakao SDK 로드 확인
  if(window.Kakao){
    console.log('✅ Kakao SDK 감지됨');
    // SDK는 로드되었지만 아직 초기화되지 않았을 수 있음
    initKakao();
    return;
  }
  
  // 100ms 간격으로 최대 100회 대기 (10초)
  let tries = 0;
  const t = setInterval(()=>{
    tries++;
    if(window.Kakao){
      console.log('✅ Kakao SDK 로드 감지 (시도 횟수:', tries + ')');
      clearInterval(t); 
      initKakao();
    }else if(tries > 100){
      clearInterval(t); 
      console.error('❌ Kakao SDK 로드 실패: 타임아웃 (10초 초과)');
    }
  }, 100);
}

function initKakao(){
  console.log('initKakao 함수 호출');
  if(!selectors.kakaoButtonContainer){ 
    console.error('❌ Kakao 버튼 컨테이너 없음. ID: kakao-button');
    return; 
  }
  console.log('✅ Kakao 버튼 컨테이너 찾음');
  
  if(!KAKAO_APP_KEY || KAKAO_APP_KEY === 'REPLACE_WITH_YOUR_KAKAO_APP_KEY'){
    console.error('❌ Kakao APP KEY가 설정되지 않았습니다');
    selectors.kakaoButtonContainer.innerHTML = '<p style="color:red;">Kakao 앱 키가 설정되지 않았습니다</p>';
    return;
  }
  
  console.log('Kakao 초기화 중:', KAKAO_APP_KEY);
  Kakao.init(KAKAO_APP_KEY);
  
  // Kakao 로그인 버튼 생성
  const btn = document.createElement('button');
  btn.type = 'button';
  btn.style.cssText = 'width:100%;padding:12px 20px;font-size:16px;font-weight:bold;background-color:#FEE500;border:none;border-radius:4px;cursor:pointer;color:#000;';
  btn.textContent = 'Kakao로 로그인';
  btn.addEventListener('click', kakaoLogin);
  selectors.kakaoButtonContainer.appendChild(btn);
  console.log('✅ Kakao 버튼 렌더링 완료');
}

function kakaoLogin(){
  Kakao.Auth.login({
    scope: 'profile_nickname,profile_image,account_email',
    success: function(authObj) {
      Kakao.API.request({
        url: '/v2/user/me',
        success: function(response) {
          const user = {
            id: response.id,
            name: response.kakao_account?.profile?.nickname,
            email: response.kakao_account?.email,
            picture: response.kakao_account?.profile?.profile_image_url
          };
          localStorage.setItem('auth', JSON.stringify({ user, accessToken: authObj.access_token }));
          showDashboard(user.name || user.email);
        },
        fail: function(error) {
          console.error('사용자 정보 조회 실패', error);
          alert('사용자 정보를 조회할 수 없습니다.');
        }
      });
    },
    fail: function(error) {
      console.error('Kakao 로그인 실패', error);
      alert('로그인에 실패했습니다.');
    }
  });
}

function onLogout(){
  const auth = localStorage.getItem('auth');
  if(auth){
    try{
      if(window.Kakao && Kakao.Auth.getAccessToken()){
        // Kakao 로그아웃
        Kakao.Auth.logout(function() {
          console.log('Kakao 로그아웃 완료');
        });
      }
    }catch(e){ console.warn('Kakao 로그아웃 실패', e); }
  }
  localStorage.removeItem('auth');
  selectors.dashboard.classList.add('hidden');
  selectors.loginSection.classList.remove('hidden');
}

function showDashboard(user){
  selectors.displayUser.textContent = user;
  selectors.loginSection.classList.add('hidden');
  selectors.dashboard.classList.remove('hidden');
}

function onFileSelect(e){
  const f = e.target.files && e.target.files[0];
  currentFile = f || null;
  selectors.filePreview.innerHTML = '';
  if(!f) return;
  const info = document.createElement('div');
  info.textContent = `${f.name} · ${Math.round(f.size/1024)} KB · ${f.type || 'n/a'}`;
  selectors.filePreview.appendChild(info);
  if(f.type && f.type.startsWith('image/')){
    const img = document.createElement('img');
    img.src = URL.createObjectURL(f);
    selectors.filePreview.appendChild(img);
  }
}

async function onUpload(){
  if(!currentFile){ alert('먼저 파일을 선택하세요.'); return; }
  const uploadUrl = '/upload';
  try{
    const form = new FormData();
    form.append('file', currentFile);
    const resp = await fetch(uploadUrl, {method:'POST', body: form});
    if(resp.ok){
      const result = await resp.text();
      addUploadEntry({name: currentFile.name, size: currentFile.size, type: currentFile.type, remote: true, info: result});
      alert('서버에 업로드 성공 (응답 확인)');
      selectors.fileInput.value=''; currentFile=null; selectors.filePreview.innerHTML='';
      return;
    }
  }catch(e){ }
  addUploadEntry({name: currentFile.name, size: currentFile.size, type: currentFile.type, remote: false, date: new Date().toISOString()});
  alert('서버 업로드 실패 — 브라우저에 시뮬레이션 저장되었습니다.');
  selectors.fileInput.value=''; currentFile=null; selectors.filePreview.innerHTML='';
}

function addUploadEntry(entry){
  uploads.unshift(entry);
  try{ localStorage.setItem('uploads_meta', JSON.stringify(uploads)); }catch(e){ console.warn('저장 실패', e); }
  renderUploads();
}

function renderUploads(){
  selectors.uploadsList.innerHTML='';
  if(uploads.length===0){ selectors.uploadsList.innerHTML = '<li class="muted small">업로드된 파일이 없습니다.</li>'; return; }
  for(const u of uploads){
    const li = document.createElement('li');
    const left = document.createElement('div');
    left.textContent = `${u.name} · ${Math.round((u.size||0)/1024)} KB` + (u.remote? ' · (서버)': ' · (로컬 시뮬)');
    const right = document.createElement('div');
    if(!u.remote){
      const btn = document.createElement('button');
      btn.textContent = '정보';
      btn.addEventListener('click', ()=> alert(JSON.stringify(u, null, 2)));
      right.appendChild(btn);
    }else{
      const span = document.createElement('span');
      span.textContent = '서버 저장됨';
      right.appendChild(span);
    }
    li.appendChild(left); li.appendChild(right);
    selectors.uploadsList.appendChild(li);
  }
}

document.addEventListener('DOMContentLoaded', init);
