<script setup>
import { computed } from "vue";
import Navbar from "./components/Navbar.vue";
import { authStore } from "./store";

const dashboardRoute = computed(() =>
    authStore.user?.role === "Admin" ? "/admin/dashboard" : "/dashboard",
);
</script>

<template>
    <div class="min-h-screen bg-gray-50 text-gray-900">
        <Navbar />

        <main class="pt-[70px]">
            <router-view />
        </main>

        <!-- Footer -->
        <footer class="footer-main">
            <div class="mx-auto max-w-7xl px-6">
                <!-- Top section -->
                <div class="grid gap-10 py-12 md:grid-cols-4">
                    <!-- Brand -->
                    <div class="md:col-span-1">
                        <router-link to="/" class="flex items-center gap-2">
                            <span class="flex h-9 w-9 items-center justify-center rounded-xl bg-[#10B981] text-white text-lg">✚</span>
                            <span class="text-xl font-semibold text-white">NutriAI</span>
                        </router-link>
                        <p class="mt-4 text-sm leading-relaxed text-gray-400">
                            AI-powered malnutrition screening for frontline
                            health workers. Early detection. Better outcomes.
                        </p>
                    </div>

                    <!-- Navigation -->
                    <div>
                        <h4 class="text-xs font-semibold uppercase tracking-wider text-gray-400">Navigation</h4>
                        <ul class="mt-4 space-y-2.5">
                            <li>
                                <router-link to="/" class="text-sm text-gray-300 transition hover:text-white">Home</router-link>
                            </li>
                            <li>
                                <router-link to="/features" class="text-sm text-gray-300 transition hover:text-white">Features</router-link>
                            </li>
                            <li>
                                <router-link to="/how-it-works" class="text-sm text-gray-300 transition hover:text-white">How It Works</router-link>
                            </li>
                            <li>
                                <router-link to="/about" class="text-sm text-gray-300 transition hover:text-white">About</router-link>
                            </li>
                        </ul>
                    </div>

                    <!-- Resources -->
                    <div>
                        <h4 class="text-xs font-semibold uppercase tracking-wider text-gray-400">Resources</h4>
                        <ul class="mt-4 space-y-2.5">
                            <li>
                                <router-link :to="authStore.user ? dashboardRoute : '/login'" class="text-sm text-gray-300 transition hover:text-white">
                                    {{ authStore.user ? "Dashboard" : "Login / Dashboard" }}
                                </router-link>
                            </li>
                            <li>
                                <span class="text-sm text-gray-500">WHO Growth Standards</span>
                            </li>
                            <li>
                                <span class="text-sm text-gray-500">Documentation</span>
                            </li>
                        </ul>
                    </div>

                    <!-- Contact / CTA -->
                    <div>
                        <h4 class="text-xs font-semibold uppercase tracking-wider text-gray-400">Get Involved</h4>
                        <p class="mt-4 text-sm text-gray-400">
                            Interested in deploying NutriAI in your community?
                        </p>
                        <router-link
                            :to="authStore.user ? dashboardRoute : '/login'"
                            class="mt-4 inline-flex rounded-lg bg-[#10B981] px-5 py-2.5 text-sm font-semibold text-white transition hover:bg-[#0EA371]"
                        >
                            {{ authStore.user ? "Open Dashboard" : "Get Started" }}
                        </router-link>
                    </div>
                </div>

                <!-- Bottom bar -->
                <div class="flex flex-col items-center justify-between gap-3 border-t border-white/10 py-6 text-xs text-gray-500 md:flex-row">
                    <p>&copy; {{ new Date().getFullYear() }} NutriAI — AI for public health impact.</p>
                    <p>Built for community health workers worldwide.</p>
                </div>
            </div>
        </footer>
    </div>
</template>
