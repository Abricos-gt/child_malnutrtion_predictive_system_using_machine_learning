import { reactive } from "vue";

const storedUser = (() => {
  try {
    const raw = localStorage.getItem("nutriai_user");
    return raw ? JSON.parse(raw) : null;
  } catch {
    return null;
  }
})();

export const authStore = reactive({
  user: storedUser,
  loading: false,
  error: "",
  login(payload) {
    this.user = payload;
    try {
      localStorage.setItem("nutriai_user", JSON.stringify(payload));
    } catch {
      // ignore storage failures
    }
  },
  logout() {
    this.user = null;
    try {
      localStorage.removeItem("nutriai_user");
    } catch {
      // ignore storage failures
    }
  },
});
