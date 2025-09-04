document.addEventListener("DOMContentLoaded", () => {
  const API = window.API || "";

  // ===== 로그인 처리 =====
  const form = document.querySelector("form");
  const userEl = document.getElementById("username");
  const passEl = document.getElementById("password");
  const signupBtn = document.querySelector(".signup-button");
  const eyeIcon = document.querySelector(".eye-icon");
  const loginBtn = document.querySelector(".login-button");

  // 비밀번호 토글(비밀번호 보이기/비밀번호 숨기기)
  if (eyeIcon && passEl) {
    eyeIcon.addEventListener("click", () => {
      const isPw = passEl.type === "password";
      passEl.type = isPw ? "text" : "password";
      eyeIcon.src = isPw ? "../images/icon_eye.png" : "../images/icon_close_eye.png";
      eyeIcon.alt = isPw ? "비밀번호 보이기" : "비밀번호 숨기기";
    });
  }

  // 로그인 submit
  form?.addEventListener("submit", async (e) => {
    e.preventDefault();
    const username = userEl?.value.trim();
    const password = passEl?.value || "";

    if (!username || !password) {
      alert("아이디/비밀번호를 입력해주세요.");
      return;
    }

    loginBtn && (loginBtn.disabled = true);

    try {
      const vRes = await fetch(`${API}/login/validation`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username, password })
      });
      const vData = await vRes.json();

      if (!(vRes.ok && vData?.message === "LoginSuccess")) {
        alert("아이디 또는 비밀번호가 올바르지 않습니다.");
        return;
      }

      const nRes = await fetch(`${API}/login/get_name`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username, password })
      });
      const nData = await nRes.json();

      localStorage.setItem(window.CONFIG?.STORAGE_KEYS?.USER_ID || "user_id", username);
      if (nRes.ok && nData?.user_name) {
        localStorage.setItem(window.CONFIG?.STORAGE_KEYS?.NICKNAME || "nickname", nData.user_name);
        alert(`${nData.user_name}님, 환영합니다!`);
      } else {
        alert("로그인 성공!");
      }
      location.href = window.CONFIG?.PAGES?.HOME || "/index.html";

    } catch (err) {
      console.error(err);
      alert("서버 연결 오류");
    } finally {
      loginBtn && (loginBtn.disabled = false);
    }
  });

  // 회원가입 이동
  signupBtn?.addEventListener("click", () => {
    location.href = "./sign_up.html";
  });

  // ===== 로그아웃 처리 =====
  const logoutBtn = document.getElementById("logout-btn");
  if (logoutBtn) {
    logoutBtn.addEventListener("click", () => {
      // 로그아웃 확인
      if (confirm("정말 로그아웃 하시겠습니까?")) {
        localStorage.removeItem(window.CONFIG?.STORAGE_KEYS?.USER_ID || "user_id");
        localStorage.removeItem(window.CONFIG?.STORAGE_KEYS?.NICKNAME || "nickname");
        localStorage.removeItem(window.CONFIG?.STORAGE_KEYS?.POINTS || "points"); // 포인트 캐시도 제거
        alert("로그아웃 되었습니다.");

        // 로그인 페이지로 리다이렉트 (절대 경로 사용)
        location.href = window.CONFIG?.PAGES?.LOGIN || "/pages/login.html";
      }
    });
  }
});
