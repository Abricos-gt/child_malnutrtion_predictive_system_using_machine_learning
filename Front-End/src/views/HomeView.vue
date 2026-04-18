<script setup></script>

<template>
    <div class="min-h-screen bg-gray-50 text-gray-900">
        <!-- Hero -->
        <section class="relative w-full">
            <div class="absolute inset-0">
                <img
                    class="h-full w-full object-cover"
                    src="/src/assets/image.jpg"
                    alt="Community healthcare"
                />
                <div
                    class="absolute inset-0 bg-gradient-to-r from-[#0F172A]/80 via-[#0F172A]/60 to-transparent"
                ></div>
            </div>

            <div
                class="relative mx-auto flex min-h-[520px] max-w-7xl flex-col gap-12 px-6 py-28 md:flex-row md:items-center md:py-36"
            >
                <div class="max-w-2xl text-white">
                    <h1
                        class="text-5xl font-bold leading-[1.05] tracking-tight md:text-7xl"
                    >
                        Early Detection of Child
                        <span class="text-[#10B981]"> Malnutrition</span>
                    </h1>
                    <p class="mt-6 text-xl text-white/85 md:text-2xl">
                        AI-powered system to screen and identify nutritional
                        risk in children quickly and accurately.
                    </p>
                    <div class="mt-8 flex flex-wrap gap-4">
                        <button
                            class="rounded-full bg-[#10B981] px-8 py-4 text-lg font-semibold text-white shadow-md transition hover:opacity-95"
                            type="button"
                        >
                            Start Screening
                        </button>
                        <button
                            class="rounded-full border border-white/40 px-8 py-4 text-lg font-semibold text-white transition hover:border-white"
                            type="button"
                        >
                            Learn More
                        </button>
                    </div>
                </div>
                <div class="hidden md:block md:flex-1"></div>
            </div>
        </section>
    </div>
</template>
