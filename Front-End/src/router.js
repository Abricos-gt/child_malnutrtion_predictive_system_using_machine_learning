import { createRouter, createWebHistory } from "vue-router";
import HomeView from "./views/HomeView.vue";
import LoginView from "./views/LoginView.vue";
import DashboardView from "./views/DashboardView.vue";
import { authStore } from "./store";

const routes = [
  { path: "/", name: "Home", component: HomeView },
  { path: "/login", name: "Login", component: LoginView },
  {
    path: "/dashboard",
    name: "Dashboard",
    component: DashboardView,
    meta: { requiresAuth: true },
  },
  {
    path: "/admin/dashboard",
    name: "AdminDashboard",
    component: DashboardView,
    meta: { requiresAuth: true, role: "Admin" },
  },
];

const router = createRouter({
  history: createWebHistory(),
  routes,
  scrollBehavior() {
    return { top: 0 };
  },
});

router.beforeEach((to) => {
  const requiresAuth = to.matched.some((record) => record.meta?.requiresAuth);

  if (requiresAuth && !authStore.user) {
    return "/login";
  }

  if (to.meta?.role && authStore.user?.role !== to.meta.role) {
    return "/";
  }

  if (to.path === "/login" && authStore.user) {
    return authStore.user.role === "Admin" ? "/admin/dashboard" : "/dashboard";
  }

  return true;
});

export default router;
