<script setup>
import { computed } from "vue";
import { authStore } from "../store";

const dashboardRoute = computed(() =>
    authStore.user?.role === "Admin" ? "/admin/dashboard" : "/dashboard",
);
</script>

<template>
    <div class="min-h-screen bg-white text-slate-900 selection:bg-emerald-100 selection:text-emerald-900">
        <section id="hero" class="relative w-full overflow-hidden">
            <div class="absolute inset-0 z-0">
                <img
                    class="h-full w-full object-cover object-center"
                    src="/src/assets/image.jpg"
                    alt="Community healthcare"
                />
                <div class="absolute inset-0 bg-gradient-to-r from-slate-950 via-slate-950/80 to-transparent"></div>
            </div>

            <div class="relative z-10 flex min-h-[650px] w-full items-center px-6 md:px-16 lg:px-24">
                <div class="w-full text-left">
                    <h1 class="max-w-4xl text-4xl font-extrabold leading-[1.1] tracking-tight text-white sm:text-5xl md:text-6xl lg:text-7xl">
                        Early Detection of <br class="hidden md:block" />
                        Child <span class="text-emerald-500">Malnutrition</span>
                    </h1>
                    
                    <p class="mt-8 max-w-lg text-lg leading-relaxed text-slate-300 md:text-xl">
                        AI-powered system to screen and identify nutritional risk in children quickly and accurately.
                    </p>

                    <div class="mt-10 flex flex-wrap justify-start gap-5">
                        <router-link
                            :to="authStore.user ? dashboardRoute : '/login'"
                            class="rounded-xl bg-emerald-600 px-10 py-4 text-lg font-bold text-white shadow-2xl transition-all hover:bg-emerald-500 active:scale-95"
                        >
                            {{ authStore.user ? "Return to Dashboard" : "Start Screening" }}
                        </router-link>
                        <a
                            href="#how-it-works"
                            class="rounded-xl border border-white/20 bg-white/5 px-10 py-4 text-lg font-bold text-white backdrop-blur-md transition hover:bg-white/10"
                        >
                            Methodology
                        </a>
                    </div>
                </div>
            </div>
        </section>

         <div class="bg-slate-950 py-6 border-y border-slate-800">
    <div class="mx-auto max-w-7xl px-6 flex flex-col md:flex-row items-center justify-between gap-4">
        
        <div class="flex items-center">
            <p class="text-white font-bold uppercase tracking-[0.2em] text-xs md:text-sm">
                Proactive Intervention: 
                <span class="text-slate-400 font-medium normal-case ml-2">
                    Actionable data for immediate care.
                </span>
            </p>
        </div>
        
        <div class="hidden md:block h-px w-24 bg-slate-800"></div>
        
        <div class="flex items-center">
            <p class="text-emerald-500 font-bold text-xs md:text-sm uppercase tracking-widest">
                Screen early. Protect every child.
            </p>
        </div>
        
    </div>
</div>

        <section id="user-ecosystem" class="bg-white py-24 border-b border-slate-100">
            <div class="mx-auto max-w-7xl px-6">
                <div class="text-center mb-16">
                    <h2 class="text-emerald-600 font-black uppercase tracking-[0.2em] text-xs">The User Ecosystem</h2>
                    <h3 class="mt-3 text-4xl font-bold text-slate-900 md:text-5xl tracking-tight">Built for the frontlines.</h3>
                </div>

                <div class="grid md:grid-cols-2 gap-8">
                    <div class="group relative rounded-[2rem] bg-slate-50 p-10 transition-all hover:bg-emerald-600">
                        <div class="mb-8 flex h-14 w-14 items-center justify-center rounded-2xl bg-emerald-600 text-white transition-colors group-hover:bg-white group-hover:text-emerald-600 shadow-lg">
                            <svg class="h-8 w-8" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0z"/></svg>
                        </div>
                        <h4 class="text-2xl font-bold text-slate-900 group-hover:text-white transition-colors">Community Health Workers</h4>
                        <p class="mt-4 text-slate-600 leading-relaxed group-hover:text-emerald-50 transition-colors">Equipping field teams in remote regions with mobile AI tools to calculate Z-scores and malnutrition danger levels instantly.</p>
                    </div>

                    <div class="group relative rounded-[2rem] bg-slate-50 p-10 transition-all hover:bg-slate-900">
                        <div class="mb-8 flex h-14 w-14 items-center justify-center rounded-2xl bg-slate-900 text-white transition-colors group-hover:bg-emerald-500 group-hover:text-slate-900 shadow-lg">
                            <svg class="h-8 w-8" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6m6 0h6m0 0v-6a2 2 0 012-2h2a2 2 0 012 2v6m-6 0h-6"/></svg>
                        </div>
                        <h4 class="text-2xl font-bold text-slate-900 group-hover:text-white transition-colors">Program Administrators</h4>
                        <p class="mt-4 text-slate-600 leading-relaxed group-hover:text-slate-400 transition-colors">Monitoring regional prevalence trends and resource distribution through high-level analytics to ensure interventions reach the most vulnerable.</p>
                    </div>
                </div>
            </div>
        </section>

    </div>
</template>

<style scoped>
.landing-dark-section {
    background: linear-gradient(135deg, #020617 0%, #0f172a 50%, #064e3b 100%);
}
</style>
