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

      localStorage.setItem("user_id", username);
      if (nRes.ok && nData?.user_name) {
        localStorage.setItem("nickname", nData.user_name);
        alert(`${nData.user_name}님, 환영합니다!`);
      } else {
        alert("로그인 성공!");
      }
      location.href = "/index.html";

    } catch (err) {
      console.error(err);
      alert("서버 연결 오류");
    } finally {
      loginBtn && (loginBtn.disabled = false);
    }
  });

  // 회원가입 이동
  signupBtn?.addEventListener("click", () => {
    location.href = "/";
  });

  // ===== 로그아웃 처리 =====
  const logoutBtn = document.getElementById("logout-btn");
  if (logoutBtn) {
    logoutBtn.addEventListener("click", () => {
      localStorage.removeItem("user_id");
      localStorage.removeItem("nickname");
      alert("로그아웃 되었습니다.");

      // 현재 경로에 따라 로그인 페이지 경로 분기
      const loginPath = location.pathname.includes("/pages/")
        ? "../pages/login.html"  // /pages/* 안쪽에서
        : "./pages/login.html";  // 루트(index.html)에서
      location.href = loginPath;
    });
  }
});
