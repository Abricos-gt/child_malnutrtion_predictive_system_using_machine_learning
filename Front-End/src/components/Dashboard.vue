<script setup>
import { computed, onMounted, ref } from "vue";
import {
    createCHW,
    getAdminStats,
    getChwUpcomingTasks,
    resetChwPassword,
} from "../services/api";
import { authStore } from "../store";
import ScreeningForm from "./ScreeningForm.vue";
import ResultsDisplay from "./ResultsDisplay.vue";

const chwData = ref({
    upcoming_tasks: [],
    pagination: {
        total_items: 0,
        current_page: 1,
        total_pages: 1,
        has_next: false,
    },
});

const adminData = ref({
    summary: {
        total_children: 0,
        total_chws: 0,
        total_screenings: 0,
    },
    monthly_activity: {},
    patient_outcomes: {
        stable_to_critical: 0,
        critical_to_stable: 0,
        remained_stable: 0,
        remained_critical: 0,
    },
});

const isLoading = ref(true);
const loadingError = ref("");
const showScreeningForm = ref(false);
const showResults = ref(false);
const screeningResult = ref(null);
const screeningPatient = ref(null);
const activeReport = ref(null);
const showCreateChwModal = ref(false);
const showResetPasswordModal = ref(false);
const expandedTaskIds = ref([]);
const chwForm = ref({
    username: "",
    email: "",
    password: "",
});
const resetPasswordForm = ref({
    username: "",
    new_password: "",
});
const creatingChw = ref(false);
const resettingPassword = ref(false);
const chwCreateError = ref("");
const chwCreateSuccess = ref("");
const resetPasswordError = ref("");
const resetPasswordSuccess = ref("");

const monthLabels = [
    "Jan",
    "Feb",
    "Mar",
    "Apr",
    "May",
    "Jun",
    "Jul",
    "Aug",
    "Sep",
    "Oct",
    "Nov",
    "Dec",
];

const summaryCards = computed(() => {
    const summary = adminData.value.summary ?? {};

    return [
        {
            label: "Registered Children",
            value: summary.total_children ?? 0,
            accent: "from-emerald-500 to-emerald-600",
            note: "Children currently tracked in the platform",
        },
        {
            label: "Active CHWs",
            value: summary.total_chws ?? 0,
            accent: "from-sky-500 to-cyan-600",
            note: "Frontline workers using the system",
        },
        {
            label: "Total Screenings",
            value: summary.total_screenings ?? 0,
            accent: "from-amber-500 to-orange-500",
            note: "All screenings captured across the program",
        },
    ];
});

const monthlyActivity = computed(() => {
    const source = adminData.value.monthly_activity ?? {};

    return monthLabels.map((label, index) => {
        const monthNumber = index + 1;
        const value = Number(
            source[monthNumber] ?? source[String(monthNumber)] ?? 0,
        );

        return {
            label,
            value,
        };
    });
});

const maxMonthlyValue = computed(() => {
    return Math.max(...monthlyActivity.value.map((item) => item.value), 1);
});

const totalTransitions = computed(() => {
    const outcomes = adminData.value.patient_outcomes ?? {};

    return Object.values(outcomes).reduce(
        (total, value) => total + Number(value ?? 0),
        0,
    );
});

const outcomeCards = computed(() => {
    const outcomes = adminData.value.patient_outcomes ?? {};
    const total = totalTransitions.value || 1;

    return [
        {
            key: "critical_to_stable",
            label: "Recovered to Stable",
            value: Number(outcomes.critical_to_stable ?? 0),
            tone: "border-emerald-200 bg-emerald-50 text-emerald-900",
            bar: "bg-emerald-500",
            description: "Children whose latest screening improved out of critical status.",
            percent: Math.round(
                (Number(outcomes.critical_to_stable ?? 0) / total) * 100,
            ),
        },
        {
            key: "stable_to_critical",
            label: "Escalated to Critical",
            value: Number(outcomes.stable_to_critical ?? 0),
            tone: "border-red-200 bg-red-50 text-red-900",
            bar: "bg-red-500",
            description: "Children whose condition worsened between the last two visits.",
            percent: Math.round(
                (Number(outcomes.stable_to_critical ?? 0) / total) * 100,
            ),
        },
        {
            key: "remained_stable",
            label: "Remained Stable",
            value: Number(outcomes.remained_stable ?? 0),
            tone: "border-slate-200 bg-slate-50 text-slate-900",
            bar: "bg-slate-500",
            description: "Children with stable outcomes across consecutive screenings.",
            percent: Math.round(
                (Number(outcomes.remained_stable ?? 0) / total) * 100,
            ),
        },
        {
            key: "remained_critical",
            label: "Remained Critical",
            value: Number(outcomes.remained_critical ?? 0),
            tone: "border-amber-200 bg-amber-50 text-amber-900",
            bar: "bg-amber-500",
            description: "Children still needing sustained intensive follow-up.",
            percent: Math.round(
                (Number(outcomes.remained_critical ?? 0) / total) * 100,
            ),
        },
    ];
});

const strongestSignal = computed(() => {
    return [...outcomeCards.value].sort((a, b) => b.value - a.value)[0];
});

const chwTaskCards = computed(() => {
    const today = new Date();
    today.setHours(0, 0, 0, 0);

    return (chwData.value.upcoming_tasks ?? []).map((task) => {
        const dueDate = new Date(task.due_date);
        dueDate.setHours(0, 0, 0, 0);

        const diffDays = Math.round(
            (dueDate.getTime() - today.getTime()) / (1000 * 60 * 60 * 24),
        );

        let urgencyLabel = "Upcoming";
        let urgencyTone =
            "border-sky-200 bg-sky-50 text-sky-900";

        if (diffDays <= 0) {
            urgencyLabel = "Due Today";
            urgencyTone = "border-red-200 bg-red-50 text-red-900";
        } else if (diffDays === 1) {
            urgencyLabel = "Due Tomorrow";
            urgencyTone = "border-amber-200 bg-amber-50 text-amber-900";
        }

        return {
            ...task,
            diffDays,
            urgencyLabel,
            urgencyTone,
        };
    });
});

async function loadDashboard() {
    await loadDashboardPage(1);
}

async function loadDashboardPage(page = 1) {
    isLoading.value = true;
    loadingError.value = "";

    try {
        if (authStore.user?.role === "CHW") {
            const { data } = await getChwUpcomingTasks({
                page,
                per_page: 5,
            });
            chwData.value = {
                upcoming_tasks: Array.isArray(data?.tasks) ? data.tasks : [],
                pagination: {
                    total_items: data?.pagination?.total_items ?? 0,
                    current_page: data?.pagination?.current_page ?? 1,
                    total_pages: data?.pagination?.total_pages ?? 1,
                    has_next: Boolean(data?.pagination?.has_next),
                },
            };
        } else if (authStore.user?.role === "Admin") {
            const { data } = await getAdminStats();
            adminData.value = {
                summary: {
                    total_children: data.summary?.total_children ?? 0,
                    total_chws: data.summary?.total_chws ?? 0,
                    total_screenings: data.summary?.total_screenings ?? 0,
                },
                monthly_activity: data.monthly_activity ?? {},
                patient_outcomes: {
                    stable_to_critical:
                        data.patient_outcomes?.stable_to_critical ?? 0,
                    critical_to_stable:
                        data.patient_outcomes?.critical_to_stable ?? 0,
                    remained_stable:
                        data.patient_outcomes?.remained_stable ?? 0,
                    remained_critical:
                        data.patient_outcomes?.remained_critical ?? 0,
                },
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

function toggleTaskExpansion(taskId) {
    if (expandedTaskIds.value.includes(taskId)) {
        expandedTaskIds.value = expandedTaskIds.value.filter(
            (id) => id !== taskId,
        );
        return;
    }

    expandedTaskIds.value = [...expandedTaskIds.value, taskId];
}

function isTaskExpanded(taskId) {
    return expandedTaskIds.value.includes(taskId);
}

function goToTaskPage(page) {
    if (
        page < 1 ||
        page > (chwData.value.pagination?.total_pages ?? 1) ||
        isLoading.value
    ) {
        return;
    }

    loadDashboardPage(page);
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

function openResetPasswordModal() {
    showResetPasswordModal.value = true;
    resetPasswordError.value = "";
    resetPasswordSuccess.value = "";
}

function closeCreateChwModal() {
    showCreateChwModal.value = false;
}

function closeResetPasswordModal() {
    showResetPasswordModal.value = false;
    resetPasswordError.value = "";
    resetPasswordSuccess.value = "";
    resetPasswordForm.value = { username: "", new_password: "" };
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

async function submitResetPassword() {
    resetPasswordError.value = "";
    resetPasswordSuccess.value = "";
    resettingPassword.value = true;

    try {
        const { data } = await resetChwPassword({
            username: resetPasswordForm.value.username,
            new_password: resetPasswordForm.value.new_password,
        });
        resetPasswordSuccess.value =
            data?.message || "Password updated successfully.";
    } catch (error) {
        resetPasswordError.value =
            error.response?.data?.message ||
            "Unable to reset password. Please try again.";
    } finally {
        resettingPassword.value = false;
    }
}

onMounted(loadDashboard);
</script>

<template>
    <div class="mx-auto w-full max-w-7xl px-6 py-12 text-gray-900">
        <section
            class="overflow-hidden rounded-[28px] border border-slate-200 bg-white shadow-sm"
        >
            <div
                class="bg-[radial-gradient(circle_at_top_left,_rgba(16,185,129,0.18),_transparent_35%),linear-gradient(135deg,#0f172a,#111827_55%,#1f2937)] px-6 py-8 text-white"
            >
                <div
                    class="flex flex-col gap-5 lg:flex-row lg:items-end lg:justify-between"
                >
                    <div class="max-w-3xl">
                        <p
                            class="text-xs font-semibold uppercase tracking-[0.28em] text-emerald-300"
                        >
                            {{ authStore.user?.role === "Admin" ? "Regional Control Center" : "Field Operations" }}
                        </p>
                        <h1 class="mt-3 text-3xl font-semibold tracking-tight">
                            {{
                                authStore.user?.role === "Admin"
                                    ? "Program Analytics Dashboard"
                                    : "CHW Dashboard"
                            }}
                        </h1>
                        <p class="mt-3 max-w-2xl text-sm text-slate-300">
                            {{
                                authStore.user?.role === "Admin"
                                    ? "Monitor workforce capacity, screening volume, and patient outcome transitions from a single operational view."
                                    : "Daily screening, follow-ups, and case tracking."
                            }}
                        </p>
                    </div>

                    <div class="flex flex-wrap gap-3">
                        <button
                            class="rounded-xl border border-white/15 bg-white/10 px-4 py-2 text-sm font-semibold text-white transition hover:bg-white/15"
                            type="button"
                            @click="loadDashboard"
                        >
                            Refresh
                        </button>
                        <button
                            v-if="authStore.user?.role === 'CHW'"
                            class="rounded-xl bg-emerald-500 px-4 py-2 text-sm font-semibold text-slate-950 transition hover:bg-emerald-400"
                            type="button"
                            @click="openScreeningForm"
                        >
                            New Screening
                        </button>
                        <button
                            v-if="authStore.user?.role === 'Admin'"
                            class="rounded-xl bg-emerald-500 px-4 py-2 text-sm font-semibold text-slate-950 transition hover:bg-emerald-400"
                            type="button"
                            @click="openCreateChwModal"
                        >
                            Create CHW
                        </button>
                    </div>
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
                        Review follow-ups due in the next three days and prioritize community outreach.
                    </p>
                </div>

                <div class="grid gap-4 md:grid-cols-3">
                    <article
                        class="rounded-[24px] border border-emerald-200 bg-gradient-to-br from-emerald-50 to-white p-5 shadow-sm"
                    >
                        <p class="text-xs font-semibold uppercase tracking-[0.22em] text-emerald-700">
                            Upcoming Follow-Ups
                        </p>
                        <p class="mt-3 text-4xl font-semibold text-emerald-700">
                            {{ chwTaskCards.length }}
                        </p>
                        <p class="mt-2 text-sm text-emerald-900/80">
                            {{
                                chwData.pagination.total_items
                            }}
                            children scheduled for review within the next three
                            days.
                        </p>
                    </article>

                    <article
                        class="rounded-[24px] border border-red-200 bg-gradient-to-br from-red-50 to-white p-5 shadow-sm"
                    >
                        <p class="text-xs font-semibold uppercase tracking-[0.22em] text-red-700">
                            Due Today
                        </p>
                        <p class="mt-3 text-4xl font-semibold text-red-700">
                            {{
                                chwTaskCards.filter((task) => task.diffDays <= 0)
                                    .length
                            }}
                        </p>
                        <p class="mt-2 text-sm text-red-900/80">
                            Cases needing same-day attention or immediate follow-up.
                        </p>
                    </article>

                    <article
                        class="rounded-[24px] border border-sky-200 bg-gradient-to-br from-sky-50 to-white p-5 shadow-sm"
                    >
                        <p class="text-xs font-semibold uppercase tracking-[0.22em] text-sky-700">
                            Reachable Caregivers
                        </p>
                        <p class="mt-3 text-4xl font-semibold text-sky-700">
                            {{
                                chwTaskCards.filter((task) => task.phone).length
                            }}
                        </p>
                        <p class="mt-2 text-sm text-sky-900/80">
                            Upcoming tasks with a caregiver phone number available.
                        </p>
                    </article>
                </div>

                <div
                    class="rounded-[28px] border border-gray-200 bg-white p-6 shadow-sm"
                >
                    <div class="flex flex-col gap-2 sm:flex-row sm:items-end sm:justify-between">
                        <div>
                            <p class="text-xs font-semibold uppercase tracking-[0.22em] text-emerald-600">
                                Follow-Up Queue
                            </p>
                            <h2 class="mt-2 text-xl font-semibold text-slate-900">
                                Upcoming Tasks
                            </h2>
                        </div>
                        <p class="text-sm text-slate-500">
                            Sorted by due date from your new CHW task endpoint
                        </p>
                    </div>

                    <div
                        v-if="!chwTaskCards.length"
                        class="mt-6 rounded-2xl border border-dashed border-slate-200 bg-slate-50 p-6 text-sm text-slate-600"
                    >
                        No follow-ups are due in the next three days.
                    </div>

                    <div v-else class="mt-6 space-y-4">
                        <article
                            v-for="task in chwTaskCards"
                            :key="`${task.patient_id}-${task.due_date}`"
                            class="rounded-[24px] border border-slate-200 bg-slate-50 shadow-sm"
                        >
                            <button
                                type="button"
                                class="flex w-full flex-col gap-4 p-5 text-left transition hover:bg-slate-100/70 md:flex-row md:items-center md:justify-between"
                                @click="toggleTaskExpansion(task.patient_id)"
                            >
                                <div class="min-w-0">
                                    <p class="text-lg font-semibold text-slate-900">
                                        {{ task.name || task.patient_id }}
                                    </p>
                                    <p class="mt-1 text-xs uppercase tracking-[0.2em] text-slate-500">
                                        Patient ID: {{ task.patient_id }}
                                    </p>
                                </div>

                                <div class="flex flex-wrap items-center gap-3">
                                    <div class="rounded-2xl bg-white px-4 py-3">
                                        <p class="text-xs uppercase tracking-[0.18em] text-slate-500">
                                            Upcoming Follow-Up
                                        </p>
                                        <p class="mt-1 text-sm font-semibold text-slate-900">
                                            {{ task.due_date || "-" }}
                                        </p>
                                    </div>
                                    <span
                                        class="inline-flex rounded-full border px-3 py-1 text-xs font-semibold"
                                        :class="task.urgencyTone"
                                    >
                                        {{ task.urgencyLabel }}
                                    </span>
                                    <span class="text-sm font-semibold text-emerald-700">
                                        {{
                                            isTaskExpanded(task.patient_id)
                                                ? "Hide record"
                                                : "View past record"
                                        }}
                                    </span>
                                </div>
                            </button>

                            <div
                                v-if="isTaskExpanded(task.patient_id)"
                                class="border-t border-slate-200 bg-white px-5 py-5"
                            >
                                <div class="grid gap-4 md:grid-cols-[0.9fr_1.1fr]">
                                    <div class="space-y-4">
                                        <div class="rounded-2xl bg-slate-50 p-4">
                                            <p class="text-xs uppercase tracking-[0.18em] text-slate-500">
                                                Current Status
                                            </p>
                                            <div class="mt-2">
                                                <span :class="badgeClass(task.current_status)">
                                                    {{ task.current_status || "Tracked" }}
                                                </span>
                                            </div>
                                        </div>

                                        <div class="rounded-2xl bg-slate-50 p-4">
                                            <p class="text-xs uppercase tracking-[0.18em] text-slate-500">
                                                Caregiver Contact
                                            </p>
                                            <p class="mt-2 text-sm font-semibold text-slate-900">
                                                {{ task.phone || "No phone number recorded" }}
                                            </p>
                                        </div>

                                        <a
                                            v-if="task.screen_button_url"
                                            :href="task.screen_button_url"
                                            class="inline-flex rounded-xl bg-emerald-500 px-4 py-2 text-sm font-semibold text-slate-950 transition hover:bg-emerald-400"
                                        >
                                            Open Screening
                                        </a>
                                    </div>

                                    <div class="rounded-2xl bg-slate-50 p-4">
                                        <p class="text-xs uppercase tracking-[0.18em] text-slate-500">
                                            Previous Screening History
                                        </p>

                                        <div
                                            v-if="!task.history_table?.length"
                                            class="mt-3 text-sm text-slate-600"
                                        >
                                            No previous screenings found.
                                        </div>

                                        <div v-else class="mt-3 overflow-x-auto">
                                            <table class="w-full min-w-[360px] border-collapse text-sm">
                                                <thead>
                                                    <tr class="border-b border-slate-200 text-left text-xs uppercase tracking-[0.16em] text-slate-500">
                                                        <th class="pb-2 font-semibold">Date</th>
                                                        <th class="pb-2 font-semibold">Weight</th>
                                                        <th class="pb-2 font-semibold">Height</th>
                                                        <th class="pb-2 font-semibold">Status</th>
                                                    </tr>
                                                </thead>
                                                <tbody>
                                                    <tr
                                                        v-for="history in task.history_table"
                                                        :key="`${task.patient_id}-${history.date}-${history.status}`"
                                                        class="border-b border-slate-100 text-slate-700 last:border-b-0"
                                                    >
                                                        <td class="py-2">{{ history.date }}</td>
                                                        <td class="py-2">{{ history.weight }}</td>
                                                        <td class="py-2">{{ history.height }}</td>
                                                        <td class="py-2">{{ history.status }}</td>
                                                    </tr>
                                                </tbody>
                                            </table>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </article>
                    </div>

                    <div
                        v-if="chwData.pagination.total_pages > 1"
                        class="mt-6 flex flex-col gap-3 border-t border-slate-200 pt-5 sm:flex-row sm:items-center sm:justify-between"
                    >
                        <p class="text-sm text-slate-500">
                            Page {{ chwData.pagination.current_page }} of
                            {{ chwData.pagination.total_pages }} •
                            {{ chwData.pagination.total_items }} total tasks
                        </p>

                        <div class="flex gap-3">
                            <button
                                type="button"
                                class="rounded-xl border border-slate-200 px-4 py-2 text-sm font-semibold text-slate-700 transition hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-50"
                                :disabled="chwData.pagination.current_page <= 1"
                                @click="
                                    goToTaskPage(
                                        chwData.pagination.current_page - 1,
                                    )
                                "
                            >
                                Previous
                            </button>
                            <button
                                type="button"
                                class="rounded-xl border border-slate-200 px-4 py-2 text-sm font-semibold text-slate-700 transition hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-50"
                                :disabled="!chwData.pagination.has_next"
                                @click="
                                    goToTaskPage(
                                        chwData.pagination.current_page + 1,
                                    )
                                "
                            >
                                Next
                            </button>
                        </div>
                    </div>
                </div>

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
                <div class="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
                    <article
                        v-for="card in summaryCards"
                        :key="card.label"
                        class="relative overflow-hidden rounded-[24px] border border-slate-200 bg-white p-5 shadow-sm"
                    >
                        <div
                            class="absolute right-0 top-0 h-24 w-24 rounded-full bg-slate-100 blur-2xl"
                        ></div>
                        <div
                            :class="`inline-flex rounded-full bg-gradient-to-r ${card.accent} px-3 py-1 text-xs font-semibold uppercase tracking-[0.18em] text-white`"
                        >
                            {{ card.label }}
                        </div>
                        <p class="mt-5 text-4xl font-semibold tracking-tight text-slate-900">
                            {{ card.value }}
                        </p>
                        <p class="mt-2 text-sm text-slate-600">
                            {{ card.note }}
                        </p>
                    </article>
                </div>

                <div class="grid gap-6 xl:grid-cols-[1.5fr_1fr]">
                    <section
                        class="rounded-[28px] border border-slate-200 bg-white p-6 shadow-sm"
                    >
                        <div
                            class="flex flex-col gap-2 sm:flex-row sm:items-end sm:justify-between"
                        >
                            <div>
                                <p class="text-xs font-semibold uppercase tracking-[0.22em] text-emerald-600">
                                    Monthly Activity
                                </p>
                                <h2 class="mt-2 text-xl font-semibold text-slate-900">
                                    Screening Volume Trend
                                </h2>
                            </div>
                            <p class="text-sm text-slate-500">
                                Total screenings captured by month
                            </p>
                        </div>

                        <div class="mt-8">
                            <div class="flex h-72 items-end gap-3">
                                <div
                                    v-for="month in monthlyActivity"
                                    :key="month.label"
                                    class="flex flex-1 flex-col items-center justify-end gap-3"
                                >
                                    <span class="text-xs font-medium text-slate-500">
                                        {{ month.value }}
                                    </span>
                                    <div
                                        class="flex w-full items-end rounded-t-2xl bg-slate-100"
                                        style="height: 220px"
                                    >
                                        <div
                                            class="w-full rounded-t-2xl bg-gradient-to-t from-emerald-500 via-teal-500 to-cyan-400 transition-all"
                                            :style="{
                                                height: `${Math.max((month.value / maxMonthlyValue) * 100, month.value ? 12 : 4)}%`,
                                            }"
                                        ></div>
                                    </div>
                                    <span class="text-xs font-semibold uppercase tracking-wide text-slate-500">
                                        {{ month.label }}
                                    </span>
                                </div>
                            </div>
                        </div>
                    </section>

                    <section
                        class="rounded-[28px] border border-slate-200 bg-white p-6 shadow-sm"
                    >
                        <p class="text-xs font-semibold uppercase tracking-[0.22em] text-emerald-600">
                            Executive Signal
                        </p>
                        <h2 class="mt-2 text-xl font-semibold text-slate-900">
                            Outcome Snapshot
                        </h2>
                        <p class="mt-2 text-sm leading-relaxed text-slate-600">
                            {{
                                strongestSignal
                                    ? `${strongestSignal.label} is currently the most visible transition pattern in the latest patient comparisons.`
                                    : "Outcome transitions will appear after patients have at least two screenings."
                            }}
                        </p>

                        <div class="mt-6 rounded-2xl bg-slate-950 p-5 text-white">
                            <p class="text-sm uppercase tracking-[0.18em] text-slate-400">
                                Transition Records
                            </p>
                            <p class="mt-3 text-4xl font-semibold">
                                {{ totalTransitions }}
                            </p>
                            <p class="mt-2 text-sm text-slate-300">
                                Patient comparisons based on the last two screenings.
                            </p>
                        </div>

                        <div class="mt-5 space-y-4">
                            <div
                                v-for="item in outcomeCards"
                                :key="item.key"
                                class="rounded-2xl border p-4"
                                :class="item.tone"
                            >
                                <div class="flex items-center justify-between gap-4">
                                    <div>
                                        <p class="text-sm font-semibold">
                                            {{ item.label }}
                                        </p>
                                        <p class="mt-1 text-xs opacity-80">
                                            {{ item.description }}
                                        </p>
                                    </div>
                                    <div class="text-right">
                                        <p class="text-2xl font-semibold">
                                            {{ item.value }}
                                        </p>
                                        <p class="text-xs opacity-80">
                                            {{ item.percent }}%
                                        </p>
                                    </div>
                                </div>
                                <div class="mt-3 h-2 rounded-full bg-white/50">
                                    <div
                                        class="h-2 rounded-full"
                                        :class="item.bar"
                                        :style="{ width: `${item.percent}%` }"
                                    ></div>
                                </div>
                            </div>
                        </div>
                    </section>
                </div>

                <section
                    class="rounded-[28px] border border-slate-200 bg-white p-6 shadow-sm"
                >
                    <div
                        class="flex flex-col gap-2 sm:flex-row sm:items-end sm:justify-between"
                    >
                        <div>
                            <p class="text-xs font-semibold uppercase tracking-[0.22em] text-emerald-600">
                                Patient Outcomes
                            </p>
                            <h2 class="mt-2 text-xl font-semibold text-slate-900">
                                Improvement vs Deterioration
                            </h2>
                        </div>
                        <p class="text-sm text-slate-500">
                            Transition logic based on each child's last two screenings
                        </p>
                    </div>

                    <div class="mt-6 grid gap-4 lg:grid-cols-2">
                        <div
                            class="rounded-3xl border border-emerald-200 bg-gradient-to-br from-emerald-50 to-white p-5"
                        >
                            <p class="text-sm font-semibold text-emerald-900">
                                Improvement Pathway
                            </p>
                            <p class="mt-3 text-4xl font-semibold text-emerald-700">
                                {{ adminData.patient_outcomes.critical_to_stable }}
                            </p>
                            <p class="mt-2 text-sm text-emerald-900/80">
                                Children who moved from critical to stable between the previous and latest screening.
                            </p>
                        </div>

                        <div
                            class="rounded-3xl border border-red-200 bg-gradient-to-br from-red-50 to-white p-5"
                        >
                            <p class="text-sm font-semibold text-red-900">
                                Escalation Pathway
                            </p>
                            <p class="mt-3 text-4xl font-semibold text-red-700">
                                {{ adminData.patient_outcomes.stable_to_critical }}
                            </p>
                            <p class="mt-2 text-sm text-red-900/80">
                                Children whose latest screening indicates deterioration into critical status.
                            </p>
                        </div>
                    </div>
                </section>

                <section
                    class="rounded-[28px] border border-slate-200 bg-white p-6 shadow-sm"
                >
                    <div class="flex flex-col gap-6 lg:grid lg:grid-cols-2">
                        <div class="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
                            <div>
                                <h2 class="text-lg font-semibold text-slate-900">
                                    Workforce Management
                                </h2>
                                <p class="mt-1 text-sm text-slate-600">
                                    Add a new community health worker account for field deployment.
                                </p>
                            </div>
                            <button
                                type="button"
                                class="rounded-xl bg-emerald-500 px-4 py-2 text-sm font-semibold text-slate-950 transition hover:bg-emerald-400"
                                @click="openCreateChwModal"
                            >
                                New CHW
                            </button>
                        </div>

                        <div class="rounded-[24px] border border-amber-200 bg-amber-50 p-5">
                            <div class="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
                                <div>
                                    <h3 class="text-base font-semibold text-amber-900">
                                        Reset CHW Password
                                    </h3>
                                    <p class="mt-1 text-sm text-amber-900/80">
                                        Admins can issue a new password when a CHW is locked out or onboarding to a new device.
                                    </p>
                                </div>
                                <button
                                    type="button"
                                    class="rounded-xl border border-amber-300 bg-white px-4 py-2 text-sm font-semibold text-amber-900 transition hover:bg-amber-100"
                                    @click="openResetPasswordModal"
                                >
                                    Reset Password
                                </button>
                            </div>
                        </div>
                    </div>
                </section>
            </section>

            <div
                v-if="showResetPasswordModal"
                class="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4"
                @click.self="closeResetPasswordModal"
            >
                <div
                    class="w-full max-w-lg rounded-2xl border border-gray-200 bg-white p-6 shadow-lg"
                >
                    <div class="flex items-start justify-between">
                        <div>
                            <h3 class="text-lg font-semibold text-gray-900">
                                Reset CHW Password
                            </h3>
                            <p class="mt-1 text-sm text-gray-600">
                                Enter the CHW username and assign a new password.
                            </p>
                        </div>
                        <button
                            type="button"
                            class="rounded-lg border border-gray-200 px-3 py-1 text-sm font-semibold text-gray-700 transition hover:text-gray-900"
                            @click="closeResetPasswordModal"
                        >
                            Close
                        </button>
                    </div>

                    <div
                        v-if="resetPasswordError"
                        class="mt-4 rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700"
                    >
                        {{ resetPasswordError }}
                    </div>
                    <div
                        v-if="resetPasswordSuccess"
                        class="mt-4 rounded-lg border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm text-emerald-700"
                    >
                        {{ resetPasswordSuccess }}
                    </div>

                    <form
                        class="mt-4 grid gap-4"
                        @submit.prevent="submitResetPassword"
                    >
                        <div class="grid gap-2">
                            <label class="text-sm font-medium text-gray-700"
                                >CHW Username</label
                            >
                            <input
                                v-model="resetPasswordForm.username"
                                type="text"
                                class="rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-[#10B981] focus:outline-none focus:ring-2 focus:ring-[#10B981]/20"
                                placeholder="chw_username"
                            />
                        </div>
                        <div class="grid gap-2">
                            <label class="text-sm font-medium text-gray-700"
                                >New Password</label
                            >
                            <input
                                v-model="resetPasswordForm.new_password"
                                type="text"
                                class="rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-[#10B981] focus:outline-none focus:ring-2 focus:ring-[#10B981]/20"
                                placeholder="Enter the new password"
                            />
                        </div>

                        <div class="flex justify-end">
                            <button
                                type="submit"
                                class="rounded-lg bg-amber-500 px-4 py-2 text-sm font-semibold text-slate-950 transition hover:bg-amber-400 disabled:cursor-not-allowed disabled:opacity-70"
                                :disabled="resettingPassword"
                            >
                                {{
                                    resettingPassword
                                        ? "Updating..."
                                        : "Reset Password"
                                }}
                            </button>
                        </div>
                    </form>
                </div>
            </div>

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
                            <p class="mt-1 text-sm text-slate-600">
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
