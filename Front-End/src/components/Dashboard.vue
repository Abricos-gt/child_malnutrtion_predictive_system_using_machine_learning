<script setup>
import { computed, onMounted, ref } from "vue";
import { createCHW, getAdminDashboard } from "../services/api";
import { authStore } from "../store";
import ScreeningForm from "./ScreeningForm.vue";
import ResultsDisplay from "./ResultsDisplay.vue";

const chwData = ref({
    tasks_overdue: [],
    recent_screenings: [],
});

const adminData = ref({
    total: 0,
    critical: 0,
    prevalence: {},
    chw_stats: [],
});

const isLoading = ref(true);
const loadingError = ref("");
const showScreeningForm = ref(false);
const showResults = ref(false);
const screeningResult = ref(null);
const screeningPatient = ref(null);
const activeReport = ref(null);
const showCreateChwModal = ref(false);
const chwForm = ref({
    username: "",
    email: "",
    password: "",
});
const creatingChw = ref(false);
const chwCreateError = ref("");
const chwCreateSuccess = ref("");

const statusPalette = {
    Critical: "#ef4444",
    "At Risk": "#f59e0b",
    Borderline: "#f59e0b",
    Stable: "#22c55e",
};

const prevalenceSegments = computed(() => {
    const summary = adminData.value.prevalence ?? {};
    const entries = Object.entries(summary).map(([label, value]) => ({
        label,
        value: Number(value ?? 0),
        color: statusPalette[label] ?? "#94a3b8",
    }));
    const total = entries.reduce((acc, entry) => acc + entry.value, 0);

    if (!total) {
        return [];
    }

    return entries.map((entry) => ({
        ...entry,
        percent: Math.round((entry.value / total) * 100),
    }));
});

const earlyWarningFlags = computed(() => {
    const flags = activeReport.value?.result?.early_warning_flags;
    return Array.isArray(flags) ? flags : [];
});

const recommendationEntries = computed(() => {
    const recommendation = activeReport.value?.result?.recommendation;
    if (!recommendation || typeof recommendation !== "object") {
        return [];
    }

    return Object.entries(recommendation).map(([key, value]) => ({
        key,
        label: key
            .replace(/_/g, " ")
            .replace(/\b\w/g, (char) => char.toUpperCase()),
        value: Array.isArray(value) ? value.join(", ") : value,
    }));
});

async function loadDashboard() {
    isLoading.value = true;
    loadingError.value = "";

    try {
        if (authStore.user?.role === "CHW") {
            chwData.value = {
                tasks_overdue: [],
                recent_screenings: [],
            };
        } else if (authStore.user?.role === "Admin") {
            const { data } = await getAdminDashboard();
            adminData.value = {
                ...data,
                chw_stats: adminData.value.chw_stats || [],
            };
        }
    } catch (error) {
        loadingError.value = "Surveillance data could not be loaded right now.";
    } finally {
        isLoading.value = false;
    }
}

function openScreeningForm() {
    showScreeningForm.value = true;
}

function closeScreeningForm() {
    showScreeningForm.value = false;
}

function handleScreeningSubmitted(data) {
    screeningResult.value = data.result;
    screeningPatient.value = data.patient;
    showScreeningForm.value = false;
    showResults.value = true;
    activeReport.value = data;
}

function closeResults() {
    showResults.value = false;
    activeReport.value = null;
    screeningResult.value = null;
    screeningPatient.value = null;
}

function startNewScreening() {
    showResults.value = false;
    screeningResult.value = null;
    screeningPatient.value = null;
    openScreeningForm();
}

function badgeClass(status) {
    return (
        {
            Critical:
                "inline-flex items-center rounded-full bg-red-100 px-2.5 py-1 text-xs font-semibold text-red-700",
            "At Risk":
                "inline-flex items-center rounded-full bg-amber-100 px-2.5 py-1 text-xs font-semibold text-amber-700",
            Borderline:
                "inline-flex items-center rounded-full bg-amber-100 px-2.5 py-1 text-xs font-semibold text-amber-700",
            Stable: "inline-flex items-center rounded-full bg-emerald-100 px-2.5 py-1 text-xs font-semibold text-emerald-700",
        }[status] ??
        "inline-flex items-center rounded-full bg-slate-100 px-2.5 py-1 text-xs font-semibold text-slate-700"
    );
}

function openCreateChwModal() {
    showCreateChwModal.value = true;
    chwCreateError.value = "";
    chwCreateSuccess.value = "";
}

function closeCreateChwModal() {
    showCreateChwModal.value = false;
}

function generatePassword() {
    const chars =
        "ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz23456789!@#$";
    let pwd = "";
    for (let i = 0; i < 10; i += 1) {
        pwd += chars.charAt(Math.floor(Math.random() * chars.length));
    }
    chwForm.value.password = pwd;
}

async function submitCreateChw() {
    chwCreateError.value = "";
    chwCreateSuccess.value = "";
    creatingChw.value = true;

    try {
        await createCHW({
            username: chwForm.value.username,
            email: chwForm.value.email,
            password: chwForm.value.password,
        });
        chwCreateSuccess.value = "CHW created successfully.";
        chwForm.value = { username: "", email: "", password: "" };
        showCreateChwModal.value = false;
        await loadDashboard();
    } catch (error) {
        chwCreateError.value =
            error.response?.data?.error ||
            error.response?.data?.message ||
            "Unable to create CHW. Please try again.";
    } finally {
        creatingChw.value = false;
    }
}

onMounted(loadDashboard);
</script>

<template>
    <div class="mx-auto w-full max-w-7xl px-6 py-12 text-gray-900">
        <section
            class="rounded-2xl border border-gray-200 bg-white p-6 shadow-sm"
        >
            <div
                class="flex flex-col gap-4 md:flex-row md:items-center md:justify-between"
            >
                <div>
                    <h1 class="text-2xl font-semibold">
                        {{
                            authStore.user?.role === "Admin"
                                ? "Admin Dashboard"
                                : "CHW Dashboard"
                        }}
                    </h1>
                    <p class="mt-1 text-sm text-gray-600">
                        {{
                            authStore.user?.role === "Admin"
                                ? "High-level monitoring, analytics, and operations."
                                : "Daily screening, follow-ups, and case tracking."
                        }}
                    </p>
                </div>
                <div class="flex flex-wrap gap-3">
                    <button
                        class="rounded-lg border border-gray-200 px-4 py-2 text-sm font-semibold text-gray-700 transition hover:text-gray-900"
                        type="button"
                        @click="loadDashboard"
                    >
                        Refresh
                    </button>
                    <button
                        v-if="authStore.user?.role === 'CHW'"
                        class="rounded-lg bg-[#10B981] px-4 py-2 text-sm font-semibold text-white transition hover:bg-[#0EA371]"
                        type="button"
                        @click="openScreeningForm"
                    >
                        New Screening
                    </button>
                </div>
            </div>
        </section>

        <div
            v-if="loadingError"
            class="mt-6 rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700"
        >
            {{ loadingError }}
        </div>

        <div
            v-if="isLoading"
            class="mt-6 rounded-2xl border border-gray-200 bg-white p-6 shadow-sm"
        >
            <p class="text-sm text-gray-600">Loading dashboard data...</p>
        </div>

        <template v-else>
            <section
                v-if="authStore.user?.role === 'CHW'"
                class="mt-8 grid gap-6"
            >
                <div
                    class="rounded-2xl border border-gray-200 bg-white p-6 shadow-sm"
                >
                    <h2 class="text-lg font-semibold">
                        Welcome, Health Worker
                    </h2>
                    <p class="mt-1 text-sm text-gray-600">
                        Review overdue tasks and recent screenings.
                    </p>
                </div>

                <div
                    class="rounded-2xl border border-gray-200 bg-white p-6 shadow-sm"
                >
                    <h2 class="text-lg font-semibold">Overdue Tasks</h2>
                    <p class="mt-1 text-sm text-gray-600">
                        Prioritize urgent follow-ups.
                    </p>

                    <div
                        v-if="!chwData.tasks_overdue?.length"
                        class="mt-4 text-sm text-gray-600"
                    >
                        No overdue tasks detected.
                    </div>

                    <ul v-else class="mt-4 space-y-2 text-sm text-gray-700">
                        <li
                            v-for="(task, index) in chwData.tasks_overdue"
                            :key="index"
                            class="flex flex-wrap items-center gap-2"
                        >
                            <span class="font-medium">{{
                                task.patient || `Child ${index + 1}`
                            }}</span>
                            <span class="text-gray-500">—</span>
                            <span>
                                {{
                                    task.reason ||
                                    task.follow_up_reason ||
                                    "Follow-up required"
                                }}
                            </span>
                        </li>
                    </ul>
                </div>

                <div
                    class="rounded-2xl border border-gray-200 bg-white p-6 shadow-sm"
                >
                    <h2 class="text-lg font-semibold">Recent Screenings</h2>
                    <div class="mt-4 overflow-x-auto">
                        <table class="w-full border-collapse text-sm">
                            <thead>
                                <tr
                                    class="text-left text-xs font-semibold uppercase tracking-wider text-gray-500"
                                >
                                    <th class="pb-3">Patient Name</th>
                                    <th class="pb-3">Status</th>
                                    <th class="pb-3">Date</th>
                                </tr>
                            </thead>
                            <tbody class="border-t border-gray-100">
                                <tr
                                    v-for="(
                                        screening, index
                                    ) in chwData.recent_screenings"
                                    :key="index"
                                    class="border-b border-gray-100"
                                >
                                    <td class="py-3">
                                        {{
                                            screening.name ||
                                            `Screening ${index + 1}`
                                        }}
                                    </td>
                                    <td class="py-3">
                                        <span
                                            :class="
                                                badgeClass(screening.status)
                                            "
                                        >
                                            {{ screening.status || "Tracked" }}
                                        </span>
                                    </td>
                                    <td class="py-3">
                                        {{ screening.date || "—" }}
                                    </td>
                                </tr>
                            </tbody>
                        </table>
                    </div>
                </div>

                <!-- Inline Report -->
                <ResultsDisplay
                    v-if="activeReport && screeningResult && screeningPatient"
                    :result="screeningResult"
                    :patient="screeningPatient"
                    :inline="true"
                    @close="closeResults"
                    @newScreening="startNewScreening"
                />
            </section>

            <section v-else class="mt-8 grid gap-6">
                <div class="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
                    <div
                        class="rounded-xl border border-gray-200 bg-white p-4 shadow-sm"
                    >
                        <p
                            class="text-xs uppercase tracking-wide text-gray-500"
                        >
                            Total Screenings
                        </p>
                        <p class="mt-2 text-2xl font-semibold text-gray-900">
                            {{ adminData.total ?? 0 }}
                        </p>
                    </div>
                    <div
                        class="rounded-xl border border-gray-200 bg-white p-4 shadow-sm"
                    >
                        <p
                            class="text-xs uppercase tracking-wide text-gray-500"
                        >
                            Critical Cases
                        </p>
                        <p class="mt-2 text-2xl font-semibold text-gray-900">
                            {{ adminData.critical ?? 0 }}
                        </p>
                    </div>
                    <div
                        class="rounded-xl border border-gray-200 bg-white p-4 shadow-sm"
                    >
                        <p
                            class="text-xs uppercase tracking-wide text-gray-500"
                        >
                            At Risk
                        </p>
                        <p class="mt-2 text-2xl font-semibold text-gray-900">
                            {{ adminData.prevalence?.["At Risk"] ?? 0 }}
                        </p>
                    </div>
                    <div
                        class="rounded-xl border border-gray-200 bg-white p-4 shadow-sm"
                    >
                        <p
                            class="text-xs uppercase tracking-wide text-gray-500"
                        >
                            Stable
                        </p>
                        <p class="mt-2 text-2xl font-semibold text-gray-900">
                            {{ adminData.prevalence?.Stable ?? 0 }}
                        </p>
                    </div>
                </div>

                <div
                    class="rounded-2xl border border-gray-200 bg-white p-6 shadow-sm"
                >
                    <h2 class="text-lg font-semibold">Prevalence Summary</h2>
                    <div
                        v-if="!prevalenceSegments.length"
                        class="mt-4 text-sm text-gray-600"
                    >
                        No prevalence data available.
                    </div>
                    <div v-else class="mt-4 space-y-4">
                        <div
                            v-for="segment in prevalenceSegments"
                            :key="segment.label"
                            class="space-y-2"
                        >
                            <div
                                class="flex items-center justify-between text-sm text-gray-600"
                            >
                                <span>{{ segment.label }}</span>
                                <span>{{ segment.percent }}%</span>
                            </div>
                            <div class="h-2 w-full rounded-full bg-gray-100">
                                <div
                                    :style="{
                                        width: segment.percent + '%',
                                        background: segment.color,
                                    }"
                                    class="h-2 rounded-full"
                                ></div>
                            </div>
                        </div>
                    </div>
                </div>

                <div
                    class="rounded-2xl border border-gray-200 bg-white p-6 shadow-sm"
                >
                    <h2 class="text-lg font-semibold">CHW Performance</h2>
                    <div class="mt-4 overflow-x-auto">
                        <table class="w-full border-collapse text-sm">
                            <thead>
                                <tr
                                    class="text-left text-xs font-semibold uppercase tracking-wider text-gray-500"
                                >
                                    <th class="pb-3">CHW Name</th>
                                    <th class="pb-3">Total Screenings</th>
                                    <th class="pb-3">Avg Risk Score</th>
                                </tr>
                            </thead>
                            <tbody class="border-t border-gray-100">
                                <tr
                                    v-for="(chw, index) in adminData.chw_stats"
                                    :key="index"
                                    class="border-b border-gray-100"
                                >
                                    <td class="py-3">
                                        {{ chw.chw || `CHW ${index + 1}` }}
                                    </td>
                                    <td class="py-3">{{ chw.total ?? 0 }}</td>
                                    <td class="py-3">
                                        {{ chw.avg_risk ?? "—" }}
                                    </td>
                                </tr>
                            </tbody>
                        </table>
                    </div>
                </div>

                <div
                    class="rounded-2xl border border-gray-200 bg-white p-6 shadow-sm"
                >
                    <h2 class="text-lg font-semibold">Create CHW Account</h2>
                    <p class="mt-1 text-sm text-gray-600">
                        Add a new community health worker.
                    </p>
                    <div class="mt-4">
                        <button
                            type="button"
                            class="rounded-lg bg-[#10B981] px-4 py-2 text-sm font-semibold text-white transition hover:bg-[#0EA371]"
                            @click="openCreateChwModal"
                        >
                            New CHW
                        </button>
                    </div>
                </div>
            </section>

            <div
                v-if="showCreateChwModal"
                class="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4"
                @click.self="closeCreateChwModal"
            >
                <div
                    class="w-full max-w-lg rounded-2xl border border-gray-200 bg-white p-6 shadow-lg"
                >
                    <div class="flex items-start justify-between">
                        <div>
                            <h3 class="text-lg font-semibold text-gray-900">
                                Create CHW Account
                            </h3>
                            <p class="mt-1 text-sm text-gray-600">
                                Provide CHW credentials and generate a password.
                            </p>
                        </div>
                        <button
                            type="button"
                            class="rounded-lg border border-gray-200 px-3 py-1 text-sm font-semibold text-gray-700 transition hover:text-gray-900"
                            @click="closeCreateChwModal"
                        >
                            Close
                        </button>
                    </div>

                    <div
                        v-if="chwCreateError"
                        class="mt-4 rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700"
                    >
                        {{ chwCreateError }}
                    </div>
                    <div
                        v-if="chwCreateSuccess"
                        class="mt-4 rounded-lg border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm text-emerald-700"
                    >
                        {{ chwCreateSuccess }}
                    </div>

                    <form
                        class="mt-4 grid gap-4"
                        @submit.prevent="submitCreateChw"
                    >
                        <div class="grid gap-2">
                            <label class="text-sm font-medium text-gray-700"
                                >Username</label
                            >
                            <input
                                v-model="chwForm.username"
                                type="text"
                                class="rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-[#10B981] focus:outline-none focus:ring-2 focus:ring-[#10B981]/20"
                                placeholder="chw_username"
                            />
                        </div>
                        <div class="grid gap-2">
                            <label class="text-sm font-medium text-gray-700"
                                >Email</label
                            >
                            <input
                                v-model="chwForm.email"
                                type="email"
                                class="rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-[#10B981] focus:outline-none focus:ring-2 focus:ring-[#10B981]/20"
                                placeholder="chw@clinic.org"
                            />
                        </div>
                        <div class="grid gap-2">
                            <label class="text-sm font-medium text-gray-700"
                                >Password</label
                            >
                            <div class="flex gap-2">
                                <input
                                    v-model="chwForm.password"
                                    type="text"
                                    class="flex-1 rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-[#10B981] focus:outline-none focus:ring-2 focus:ring-[#10B981]/20"
                                    placeholder="Generate or enter password"
                                />
                                <button
                                    type="button"
                                    class="rounded-lg border border-gray-200 px-3 py-2 text-sm font-semibold text-gray-700 transition hover:text-gray-900"
                                    @click="generatePassword"
                                >
                                    Generate
                                </button>
                            </div>
                        </div>

                        <div class="flex justify-end">
                            <button
                                type="submit"
                                class="rounded-lg bg-[#10B981] px-4 py-2 text-sm font-semibold text-white transition hover:bg-[#0EA371] disabled:cursor-not-allowed disabled:opacity-70"
                                :disabled="creatingChw"
                            >
                                {{ creatingChw ? "Creating..." : "Create CHW" }}
                            </button>
                        </div>
                    </form>
                </div>
            </div>


        </template>

        <ScreeningForm
            v-if="showScreeningForm"
            @close="closeScreeningForm"
            @submitted="handleScreeningSubmitted"
        />
    </div>
</template>
