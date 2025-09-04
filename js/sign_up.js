const API = window.API || ""; // 같은 도메인에서 서빙 시 빈 문자열이면 OK

document.addEventListener("DOMContentLoaded", () => {
  const $ = (s) => document.querySelector(s);

  const form = $("#signupForm");
  const username = $("#username");
  const nickname = $("#nickname");
  const password = $("#password");
  const confirm = $("#confirm");

  const submitBtn = $("#submitBtn");
  const goLoginBtn = $("#goLoginBtn");

  const errorBox = $("#errorBox");
  const successBox = $("#successBox");

  const pwRules = $("#pwRules");
  const confirmHint = $("#confirmHint");

  // ===== 비밀번호 보이기/숨기기 (이미지 아이콘 방식, 로그인 페이지와 동일 톤)
  document.querySelectorAll(".eye-btn").forEach((btn) => {
    const targetId = btn.dataset.target;
    const input = document.getElementById(targetId);
    const img = btn.querySelector(".eye-icon");

    btn.addEventListener("click", () => {
      const isPw = input.type === "password";
      input.type = isPw ? "text" : "password";
      if (img) {
        img.src = isPw ? "../images/icon_eye.png" : "../images/icon_close_eye.png";
        img.alt = isPw ? "비밀번호 보이기" : "비밀번호 숨기기";
      }
    });
  });

  // ===== 비밀번호 규칙 검증(서버 정책 동일)
  function validatePwRules(pw){
    const r = {
      len: pw.length >= 8,
      num: /[0-9]/.test(pw),
      eng: /[a-zA-Z]/.test(pw),
      spc: /[!@#$%^&*(),.?":{}|<>]/.test(pw),
    };
    for(const [k, ok] of Object.entries(r)){
      const li = pwRules.querySelector(`[data-rule="${k}"]`);
      li?.classList.toggle("ok", ok);
      li?.classList.toggle("bad", !ok && pw.length>0);
    }
    return Object.values(r).every(Boolean);
  }

  password.addEventListener("input", () => {
    validatePwRules(password.value.trim());
    refreshConfirmMessage();
  });
  confirm.addEventListener("input", refreshConfirmMessage);

  function refreshConfirmMessage(){
    const pw = password.value.trim();
    const cf = confirm.value.trim();
    if(!cf){ confirmHint.textContent = ""; return; }
    const same = pw && cf && pw === cf;
    confirmHint.textContent = same ? "비밀번호가 일치합니다." : "비밀번호가 일치하지 않습니다.";
    confirmHint.style.color = same ? "#10b981" : "#fca5a5";
  }

  function showError(msg){
    errorBox.hidden = false; errorBox.textContent = msg;
    successBox.hidden = true; successBox.textContent = "";
  }
  function showSuccess(msg){
    successBox.hidden = false; successBox.textContent = msg;
    errorBox.hidden = true; errorBox.textContent = "";
  }

  // ===== 제출
  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    errorBox.hidden = true; successBox.hidden = true;

    const id = username.value.trim();
    const nick = nickname.value.trim();
    const pw = password.value.trim();
    const cf = confirm.value.trim();

    if(!id || !nick || !pw || !cf){
      showError("모든 필드를 입력해주세요.");
      return;
    }
    if(!validatePwRules(pw)){
      showError("비밀번호는 8자 이상이며 숫자/영문/특수문자를 포함해야 합니다.");
      return;
    }
    if(pw !== cf){
      showError("비밀번호가 일치하지 않습니다.");
      return;
    }

    submitBtn.disabled = true; submitBtn.textContent = "등록 중…";

    try{
      // 서버 요청: POST /sign_up/
      const res = await fetch(`${API}/sign_up/`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username: id, password: pw, nickname: nick })
      });

      const text = await res.text();
      let data = {};
      try{ data = JSON.parse(text); } catch { data = { message: text }; }

      if(!res.ok){
        showError(data?.detail || `요청 실패 (HTTP ${res.status})`);
        return;
      }

      showSuccess(data?.message || "회원가입이 완료되었습니다.");
      setTimeout(()=> location.href="/pages/login.html", 900);

    }catch(err){
      console.error(err);
      showError("서버 연결에 실패했습니다. 다시 시도해 주세요.");
    }finally{
      submitBtn.disabled = false; submitBtn.textContent = "회원가입 완료";
    }
  });

  // 로그인 페이지로
  goLoginBtn.addEventListener("click", () => {
    location.href = "/pages/login.html";
  });
});

