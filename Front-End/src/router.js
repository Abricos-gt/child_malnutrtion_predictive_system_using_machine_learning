import { createRouter, createWebHistory } from "vue-router";
import HomeView from "./views/HomeView.vue";
import FeaturesView from "./views/FeaturesView.vue";
import HowItWorksView from "./views/HowItWorksView.vue";
import AboutView from "./views/AboutView.vue";
import LoginView from "./views/LoginView.vue";
import DashboardView from "./views/DashboardView.vue";
import { authStore } from "./store";

const routes = [
  { path: "/", name: "Home", component: HomeView },
  { path: "/features", name: "Features", component: FeaturesView },
  { path: "/how-it-works", name: "HowItWorks", component: HowItWorksView },
  { path: "/about", name: "About", component: AboutView },
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

router.beforeEach((to, from, next) => {
  const requiresAuth = to.matched.some((record) => record.meta?.requiresAuth);

  if (requiresAuth && !authStore.user) {
    next("/login");
    return;
  }

  if (to.meta?.role && authStore.user?.role !== to.meta.role) {
    next("/");
    return;
  }

  if (to.path === "/login" && authStore.user) {
    next(authStore.user.role === "Admin" ? "/admin/dashboard" : "/dashboard");
    return;
  }

  next();
});

export default router;
