/* ========== 짧은 DOM 헬퍼 ========== */
const $  = (s) => document.querySelector(s);
const $$ = (s) => document.querySelectorAll(s);

/* ========== 서버 기본 주소 & 상태 ========== */
const API_BASE = window.API || "";
const state = {
  userId: document.body.dataset.userId || "anonymous",    // <body data-user-id="...">
  points: Number(window.__initialPoints__ ?? 0),          // 시작 포인트
  items: [],                                              // 렌더할 아이템 목록
  selectedItem: null,                                     // 모달에서 선택된 아이템
  isBuying: false,                                        // 중복 구매 방지
};

/* ========== 자주 쓰는 요소 캐시 ========== */
const els = {
  points: $("#points"),
  grid: $("#storeGrid"),
  notice: $(".store__notice"),
  // 모달
  backdrop: $("#backdrop"),
  modal: $("#modal"),
  modalTitle: $("#modal-title"),
  modalDesc: $("#modal-desc"),
  buyConfirm: $("#buyConfirm"),
  buyCancel: $("#buyCancel"),
  // 토스트
  toast: $("#toast"),
};

/* ========== 아이템 목록 (서버 PRICING과 code/price 일치 필수) ========== */
const ITEMS = [
  // 인게임(확률형 보상)
  { key: "rng_box_small", code: "RNG_BOX_SMALL", name: "랜덤 포인트 상자(소)", price: 20, desc: "0/8/20/25/100 중 하나", sellable: true },
  { key: "rng_box_big",   code: "RNG_BOX_BIG",   name: "랜덤 포인트 상자(대)", price: 50, desc: "0/20/50/65/250 중 하나", sellable: true },

  // 실제 상품 (예정)
  { key: "coffee_americano", code: "COFFEE_AMERICANO", name: "아메리카노 (예정)", price: 180, desc: "미리보기", sellable: true,
    image: "https://image.homeplus.kr/td/ed6b7ce1-031f-45f2-a8ee-86fa781aa1e0" },
  { key: "coffee_latte", code: "COFFEE_LATTE", name: "카페라떼 (예정)", price: 200, desc: "미리보기", sellable: true,
    image: "https://image.homeplus.kr/td/ad42d3de-ea74-4b95-b612-2267d50da108" },
  { key: "icecream_cone", code: "ICECREAM_CONE", name: "아이스크림 콘 (예정)", price: 150, desc: "미리보기", sellable: false,
    image: "https://image.homeplus.kr/td/e7bf9658-6132-4947-a818-fe2a8504c3d2" },
  { key: "sandwich_basic", code: "SANDWICH_BASIC", name: "샌드위치 (예정)", price: 250, desc: "미리보기", sellable: false,
    image: "https://image.homeplus.kr/td/111e0e48-4471-46ba-9040-1f79e6057b4b" },
];

/* ========== 초기화 ========== */
document.addEventListener("DOMContentLoaded", init);
async function init(){
  await syncPointsFromServer();       // ⬅️ 추가 (최신 포인트 서버에서 받아오기)
  updatePointsUI(state.points);
  bindEvents();
  await loadItems();
}

/* ========== 서버에서 최신 포인트 동기화 ========== */
async function syncPointsFromServer(){
  if(!state.userId || state.userId === "anonymous") return;
  try {
    const res = await fetch(`${API_BASE}/mypage/${state.userId}`);
    if(res.ok){
      const data = await res.json();
      if(data && !data.message){  // 서버가 {"message": "..."} 리턴하면 에러 상황
        state.points = Number(data.total_point) || state.points;
        console.log("[PointStore] Synced points from server:", state.points);
      }
    } else {
      console.warn("[PointStore] Failed to sync points:", res.status);
    }
  } catch(err){
    console.error("[PointStore] Sync error:", err);
  }
}


/* ========== 아이템 로드 & 렌더 ========== */
async function loadItems(){
  showNotice("상품 정보를 불러오는 중입니다…");
  state.items = ITEMS;
  renderStore(state.items);
  state.items.length ? hideNotice() : showNotice("판매 중인 아이템이 없어요 💤");
}

function renderStore(items){
  els.grid.innerHTML = "";
  const frag = document.createDocumentFragment();
  for(const item of items){
    frag.appendChild(createCard(item));
  }
  els.grid.appendChild(frag);
}

function createCard(item){
  const lackPoint = state.points < Number(item.price);
  const sellable = item.sellable !== false;

  const root = document.createElement("article");
  root.className = "store-card";
  root.dataset.code = item.code;

  const thumb = document.createElement("div");
  thumb.className = "store-card__thumb";
  if(item.image){
    const img = document.createElement("img");
    img.src = item.image;
    img.alt = `${item.name} 이미지`;
    img.style.width = "100%";
    img.style.height = "100%";
    img.style.objectFit = "cover";
    thumb.appendChild(img);
  }else{
    thumb.textContent = "🛍️";
  }

  const title = document.createElement("h3");
  title.className = "store-card__title";
  title.textContent = item.name;

  const desc = document.createElement("p");
  desc.className = "store-card__desc";
  desc.textContent = item.desc || "설명이 준비 중입니다.";

  const meta = document.createElement("div");
  meta.className = "store-card__meta";

  const price = document.createElement("span");
  price.className = "price-badge";
  price.textContent = `${item.price}P`;

  const btn = document.createElement("button");
  btn.className = "btn btn--primary";
  const label = !sellable ? "곧 오픈" : (lackPoint ? "포인트 부족" : "구매하기");
  btn.textContent = label;
  btn.disabled = !sellable || lackPoint;

  btn.addEventListener("click", () => openBuyModal(item));

  meta.append(price, btn);
  root.append(thumb, title, desc, meta);
  return root;
}

/* ========== 포인트 표시 갱신 ========== */
function updatePointsUI(newPoints){
  state.points = Number(newPoints) || 0;
  if(els.points) els.points.textContent = `${state.points}P`;

  // 카드 버튼 상태도 같이 업데이트
  for(const card of $$(".store-card")){
    const code = card.dataset.code;
    const item = state.items.find(it => it.code === code);
    if(!item) continue;
    const btn = card.querySelector(".btn");
    if(!btn) continue;
    const sellable = item.sellable !== false;
    const lack = state.points < Number(item.price);
    btn.textContent = !sellable ? "곧 오픈" : (lack ? "포인트 부족" : "구매하기");
    btn.disabled = !sellable || lack;
  }
}

/* ========== 공지(빈 상태 등) ========== */
function showNotice(msg){
  if(!els.notice) return;
  els.notice.hidden = false;
  els.notice.textContent = msg;
}
function hideNotice(){
  if(!els.notice) return;
  els.notice.hidden = true;
  els.notice.textContent = "";
}

/* ========== 모달 ========== */
function openBuyModal(item){
  if(item.sellable === false){
    showToast("이 상품은 아직 오픈되지 않았어요.", "danger");
    return;
  }
  state.selectedItem = item;
  els.modalTitle.textContent = "구매 확인";
  els.modalDesc.textContent = `「${item.name}」을(를) ${item.price}P로 구매할까요?`;
  els.backdrop.hidden = false;
  els.modal.hidden = false;
  els.buyConfirm.focus();
}
function closeBuyModal(){
  state.selectedItem = null;
  els.backdrop.hidden = true;
  els.modal.hidden = true;
}

/* ========== 구매 처리 (POST /shop/purchase) ========== */
async function handleBuyConfirm(){
  if(state.isBuying) return;
  const item = state.selectedItem;
  if(!item) return;

  try{
    state.isBuying = true;
    els.buyConfirm.disabled = true;
    els.buyConfirm.textContent = "구매 중…";

    const payload = {
      user_id: state.userId,          // 문자열
      item_code: item.code,           // 서버 PRICING 키
      item_name: item.name,           // 표시용
      price: Number(item.price),      // 검증용(서버 PRICING과 같아야 함)
    };

    const res = await fetch(`${API_BASE}/shop/purchase`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });

    // handleBuyConfirm()의 fetch 직후 실패 처리 부분 교체
    if(!res.ok){
      let detail = "";
      let status = res.status;
      try { const data = await res.json(); detail = data?.detail || ""; }
      catch { detail = await res.text().catch(()=> ""); }

      console.error("[/shop/purchase] FAILED", status, detail);
      // 상황별 친절 메시지
      if (status === 0) {
          // 네트워크/CORS로 대부분 0에 걸림
          showToast("서버에 연결되지 않았습니다. (CORS/서버 실행 여부 확인)", "danger");
      } else if (status === 400) {
        // 서버 검증 실패류
        if (detail.includes("가격")) showToast("가격 검증 실패: 아이템 가격/코드를 최신으로 맞춰주세요.", "danger");
        else if (detail.includes("포인트")) showToast("포인트가 부족합니다.", "danger");
        else showToast(detail || "요청 형식 오류(400)", "danger");
      } else if (status === 404) {
          showToast("사용자를 찾을 수 없습니다. user_id를 확인하세요.", "danger");
      } else if (status >= 500) {
          showToast("서버 오류(5xx). 콘솔 로그를 확인하세요.", "danger");
      } else {
          showToast(detail || `구매 실패 (HTTP ${status})`, "danger");
      }
      throw new Error(detail || `HTTP ${status}`);
    }


    // 성공 응답: { ok, total_point, rng_gain }
    const data = await res.json();
    if(!data?.ok) throw new Error("구매 처리 실패");

    // ★ 서버가 내려준 최종 포인트를 그대로 반영
    updatePointsUI(data.total_point);

    // RNG 보상 안내
    const gain = Number(data.rng_gain ?? 0);
    if(!isNaN(gain)){
      if(gain > 0) showToast(`🎁 보상 +${gain}P`, "ok");
      else if(item.code === "RNG_BOX_SMALL" || item.code === "RNG_BOX_BIG")
        showToast("😵‍💫 꽝! 보상 0P", "ok");
      else
        showToast(`구매 완료: ${item.name}`, "ok");
    }else{
      showToast(`구매 완료: ${item.name}`, "ok");
    }
  }catch(err){
    console.error(err);
    showToast(err?.message || "구매에 실패했습니다.", "danger");
  }finally{
    state.isBuying = false;
    els.buyConfirm.disabled = false;
    els.buyConfirm.textContent = "예, 구매할게요 ✅";
    closeBuyModal();
  }
}

/* ========== 토스트 ========== */
let toastTimer = null;
function showToast(message, type="ok"){
  els.toast.textContent = message;
  els.toast.className = "toast";
  if(type === "ok") els.toast.classList.add("toast--ok");
  if(type === "danger") els.toast.classList.add("toast--danger");
  els.toast.hidden = false;
  if(toastTimer) clearTimeout(toastTimer);
  toastTimer = setTimeout(()=> els.toast.hidden = true, 2200);
}

/* ========== 이벤트 바인딩 ========== */
function bindEvents(){
  els.buyConfirm?.addEventListener("click", handleBuyConfirm);
  els.buyCancel?.addEventListener("click", closeBuyModal);
  els.backdrop?.addEventListener("click", closeBuyModal);
  document.addEventListener("keydown", (e)=>{
    if(e.key === "Escape" && !els.modal.hidden) closeBuyModal();
  });
}