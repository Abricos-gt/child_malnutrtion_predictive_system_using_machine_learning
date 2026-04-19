<script setup>
import { ref } from "vue";
import { useRouter } from "vue-router";
import { authStore } from "../store";
import { logout } from "../services/api";

const isOpen = ref(false);
const router = useRouter();

function toggleMenu() {
    isOpen.value = !isOpen.value;
}

async function handleLogout() {
    try {
        await logout();
    } catch {
        // ignore logout errors and proceed with local cleanup
    }
    authStore.logout();
    isOpen.value = false;
    router.push("/");
}
</script>

<template>
    <header class="fixed top-0 z-50 w-full border-b border-gray-200 bg-white">
        <div
            class="mx-auto flex h-[70px] max-w-7xl items-center justify-between px-6"
        >
            <!-- Logo -->
            <router-link
                to="/"
                class="flex items-center gap-2 text-2xl font-semibold text-gray-900"
            >
                <span
                    class="flex h-9 w-9 items-center justify-center rounded-xl bg-[#10B981] text-white"
                >
                    ✚
                </span>
                <span class="text-[#10B981]">NutriAI</span>
            </router-link>

            <!-- Center Nav -->
            <nav
                class="hidden items-center gap-10 text-xl font-medium text-gray-600 md:flex"
            >
                <router-link class="transition hover:text-gray-900" to="/"
                    >Home</router-link
                >
                <a class="transition hover:text-gray-900" href="#user-ecosystem"
                    >Who's It For</a
                >
            </nav>

            <!-- Right CTA -->
            <div class="hidden md:flex">
                <router-link
                    v-if="!authStore.user"
                    to="/login"
                    class="rounded-lg bg-[#10B981] px-6 py-2.5 text-lg font-semibold text-white transition hover:bg-[#0EA371]"
                >
                    Login
                </router-link>
                <button
                    v-else
                    type="button"
                    class="rounded-lg border border-gray-200 px-6 py-2.5 text-lg font-semibold text-gray-700 transition hover:text-gray-900"
                    @click="handleLogout"
                >
                    Logout
                </button>
            </div>

            <!-- Mobile Menu Button -->
            <button
                type="button"
                class="inline-flex items-center justify-center rounded-lg border border-gray-200 p-2 text-gray-600 md:hidden"
                @click="toggleMenu"
                aria-label="Toggle navigation"
            >
                <svg
                    class="h-5 w-5"
                    viewBox="0 0 20 20"
                    fill="currentColor"
                    aria-hidden="true"
                >
                    <path
                        fill-rule="evenodd"
                        d="M3 5h14a1 1 0 010 2H3a1 1 0 010-2zm0 4h14a1 1 0 010 2H3a1 1 0 010-2zm0 4h14a1 1 0 010 2H3a1 1 0 010-2z"
                        clip-rule="evenodd"
                    />
                </svg>
            </button>
        </div>

        <!-- Mobile Menu -->
        <div v-if="isOpen" class="border-t border-gray-100 bg-white md:hidden">
            <div
                class="mx-auto flex max-w-7xl flex-col gap-4 px-6 py-4 text-xl font-medium text-gray-700"
            >
                <router-link class="transition hover:text-gray-900" to="/"
                    >Home</router-link
                >
                <a class="transition hover:text-gray-900" href="#user-ecosystem"
                    >Who's It For</a
                >
                <router-link
                    v-if="!authStore.user"
                    to="/login"
                    class="mt-2 inline-flex w-fit rounded-lg bg-[#10B981] px-6 py-2.5 text-lg font-semibold text-white transition hover:bg-[#0EA371]"
                >
                    Login
                </router-link>
                <button
                    v-else
                    type="button"
                    class="mt-2 inline-flex w-fit rounded-lg border border-gray-200 px-6 py-2.5 text-lg font-semibold text-gray-700 transition hover:text-gray-900"
                    @click="handleLogout"
                >
                    Logout
                </button>
            </div>
        </div>
    </header>
</template>
