// /pages/js/my_page.js
document.addEventListener("DOMContentLoaded", init);

async function init() {
  const API = window.API || "http://localhost:8000";

  // 1) 로그인 확인 & user_id 주입
  const uid = localStorage.getItem("user_id");
  if (!uid) {
    alert("로그인이 필요합니다.");
    location.href = "./login.html";
    return;
  }
  document.body.dataset.userId = uid;

  // 2) 데이터 가져오기
  let data = null;
  try {
    const res = await fetch(`${API}/mypage/${encodeURIComponent(uid)}`);
    data = await res.json();
  } catch (e) {
    console.error("[mypage] fetch error:", e);
  }

  // 3) 에러/미로그인 처리
  if (!data || data.message === "UserNotFound") {
    alert("사용자 정보를 찾을 수 없습니다.");
    return;
  }
  if (data.message === "Error") {
    console.error("[mypage] server error:", data.detail);
    alert("서버 오류가 발생했습니다.");
    return;
  }

  // 4) DOM 채우기 (백엔드 스키마에 정확히 맞춤)
  //    참고: /mypage/{user_id} 응답 컬럼들 (nickname, nickname_color 등) 
  setText("#userId", data.id ?? uid);

  // 닉네임 + 색상
  const nickEl = document.querySelector("#nickname");
  const nickname = data.nickname ?? data.name ?? "익명";
  if (nickEl) {
    nickEl.textContent = nickname;
    if (data.nickname_color) nickEl.style.color = data.nickname_color;
    nickEl.style.fontWeight = 700;
  }

  setText("#contact", data.contact ?? "미등록");
  setText("#email", data.email ?? "미등록");

  // 출석
  setText("#attendance", toInt(data.attendance, 0));
  setText("#continuousAttendance", toInt(data.continuous_attendance, 0));
  setText("#lastAttendanceDate", data.last_attendance_date ?? "기록 없음");

  // 포인트
  const totalPoint = toInt(data.total_point, 0);
  const dailyBonus = toInt(data.daily_point_bonus, 0);
  setText("#totalPoint", `${totalPoint} P`);
  setText("#dailyPointBonus", `${dailyBonus} P`);
  setText("#dailyPointDelta", `${dailyBonus >= 0 ? "↑ +" : "↓ "}${Math.abs(dailyBonus)} P`);

  // 훈장
  renderList(
    "#trophiesList",
    data.my_trophies ?? [],
    (li, key) => (li.textContent = mapTrophyName(key)),
    "#trophiesEmpty"
  );

  // 보조지표
  renderList(
    "#indicatorsList",
    data.purchased_indicators ?? [],
    (li, name) => (li.textContent = name),
    "#indicatorsEmpty"
  );
}

// ---------- helpers ----------
function setText(sel, text) {
  const el = document.querySelector(sel);
  if (el) el.textContent = `${text}`;
}
function toInt(v, d=0) {
  const n = Number(v);
  return Number.isFinite(n) ? n : d;
}
function renderList(ulSel, arr, fill, emptySel) {
  const ul = document.querySelector(ulSel);
  const empty = document.querySelector(emptySel);
  if (!ul) return;
  ul.innerHTML = "";
  if (!arr || arr.length === 0) {
    if (empty) empty.hidden = false;
    return;
  }
  if (empty) empty.hidden = true;
  for (const item of arr) {
    const li = document.createElement("li");
    li.className = "list-item";
    fill(li, item);
    ul.appendChild(li);
  }
}

// 훈장 코드 → 보기 좋은 이름 (간단 매핑, 필요 시 확장)
function mapTrophyName(key) {
  const meta = {
    "quiz_master_7days": "퀴즈 마스터 (7일 연속)",
    "daily_champion": "데일리 챔피언",
    "unique_learner": "유니크 러너",
    "legendary_investor": "레전드 투자자"
  };
  return meta[key] || key;
}
