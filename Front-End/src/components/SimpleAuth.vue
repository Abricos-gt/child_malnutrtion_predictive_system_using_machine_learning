<script setup>
import { reactive, ref } from "vue";
import { useRouter } from "vue-router";
import { login } from "../services/api";
import { authStore } from "../store";

const submitting = ref(false);
const error = ref("");
const router = useRouter();

const loginForm = reactive({
    username: "",
    password: "",
});

function handleLogin() {
    if (!loginForm.username || !loginForm.password) {
        error.value = "Please enter your username and password.";
        return;
    }

    submitting.value = true;
    error.value = "";

    login(loginForm)
        .then((response) => {
            const role = response.data?.role ?? "CHW";
            authStore.login({
                username: loginForm.username,
                role,
            });

            if (role === "Admin") {
                router.push("/admin/dashboard");
            } else {
                router.push("/dashboard");
            }
        })
        .catch(() => {
            error.value = "Invalid credentials. Please try again.";
        })
        .finally(() => {
            submitting.value = false;
        });
}
</script>

<template>
    <section
        class="mx-auto w-full max-w-md rounded-2xl border border-gray-200 bg-white p-8 shadow-sm"
    >
        <header class="mb-6 text-center">
            <h2 class="text-2xl font-semibold text-gray-900">Login</h2>
            <p class="mt-2 text-sm text-gray-600">
                Secure access for CHWs and Admins
            </p>
        </header>

        <div
            v-if="error"
            class="mb-4 rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700"
        >
            {{ error }}
        </div>

        <form class="grid gap-5" @submit.prevent="handleLogin">
            <div class="grid gap-2">
                <label class="text-sm font-medium text-gray-700"
                    >Username</label
                >
                <input
                    v-model="loginForm.username"
                    type="text"
                    placeholder="e.g. chw_demo"
                    autocomplete="username"
                    class="rounded-lg border border-gray-300 px-4 py-2 text-sm text-gray-900 shadow-sm focus:border-[#10B981] focus:outline-none focus:ring-2 focus:ring-[#10B981]/20"
                />
            </div>

            <div class="grid gap-2">
                <label class="text-sm font-medium text-gray-700"
                    >Password</label
                >
                <input
                    v-model="loginForm.password"
                    type="password"
                    placeholder="Enter your password"
                    autocomplete="current-password"
                    class="rounded-lg border border-gray-300 px-4 py-2 text-sm text-gray-900 shadow-sm focus:border-[#10B981] focus:outline-none focus:ring-2 focus:ring-[#10B981]/20"
                />
            </div>

            <button
                class="w-full rounded-lg bg-[#10B981] px-4 py-2.5 text-sm font-semibold text-white shadow-sm transition hover:bg-[#0EA371] disabled:cursor-not-allowed disabled:opacity-70"
                type="submit"
                :disabled="submitting"
            >
                {{ submitting ? "Please wait..." : "Login" }}
            </button>
        </form>
    </section>
</template>
