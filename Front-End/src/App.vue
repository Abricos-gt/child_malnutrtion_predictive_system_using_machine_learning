<script setup>
import Navbar from "./components/Navbar.vue";
</script>

<template>
    <div class="min-h-screen bg-gray-50 text-gray-900">
        <Navbar />

        <main class="pt-[70px]">
            <router-view />
        </main>

        <footer class="border-t border-gray-200 bg-white">
            <div
                class="mx-auto flex max-w-7xl flex-col items-center justify-between gap-4 px-6 py-8 text-sm text-gray-600 md:flex-row"
            >
                <div class="flex flex-wrap gap-4">
                    <router-link
                        to="/"
                        class="cursor-pointer transition hover:text-gray-900 hover:underline"
                        >Home</router-link
                    >
                    <router-link
                        to="/features"
                        class="cursor-pointer transition hover:text-gray-900 hover:underline"
                        >Features</router-link
                    >
                    <router-link
                        to="/how-it-works"
                        class="cursor-pointer transition hover:text-gray-900 hover:underline"
                        >How It Works</router-link
                    >
                    <router-link
                        to="/about"
                        class="cursor-pointer transition hover:text-gray-900 hover:underline"
                        >About</router-link
                    >
                    <router-link
                        to="/login"
                        class="cursor-pointer transition hover:text-gray-900 hover:underline"
                        >Login</router-link
                    >
                </div>
                <div>AI for public health impact</div>
            </div>
        </footer>
    </div>
</template>
