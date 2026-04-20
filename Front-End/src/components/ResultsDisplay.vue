<script setup>
import { computed, nextTick, onMounted, ref, watch } from "vue";
import html2pdf from "html2pdf.js";
import { getVhwPatientDashboard } from "../services/api";

const props = defineProps({
    result: {
        type: Object,
        required: true,
    },
    patient: {
        type: Object,
        required: true,
    },
});

const emit = defineEmits(["close", "newScreening"]);

const reportRef = ref(null);
const historyLoading = ref(false);
const historyError = ref("");
const childDashboard = ref(null);

const childInfo = computed(() => props.result?.child_information ?? {});
const assessment = computed(() => props.result?.assessment ?? {});
const actionPlan = computed(() => props.result?.action_plan ?? {});
const growthTrajectory = computed(
    () =>
        props.result?.growth_trajectory ??
        props.result?.growthTrajectory ??
        {},
);

const scorePercent = computed(() => {
    const rawScore = assessment.value?.danger_score ?? 0;
    if (typeof rawScore === "string") {
        return Number(rawScore.replace("%", "")) || 0;
    }
    return Number(rawScore) || 0;
});

const triageMeta = computed(() => {
    const level = assessment.value?.triage_level ?? "";

    if (level.includes("Critical") || level.includes("Emergency")) {
        return {
            label: level || "Critical",
            color: "#dc2626",
            soft: "border-red-200 bg-red-50 text-red-900",
            badge: "inline-flex items-center rounded-full bg-red-100 px-3 py-1 text-xs font-semibold text-red-700",
        };
    }

    if (level.includes("Risk") || level.includes("MAM")) {
        return {
            label: level || "At Risk",
            color: "#d97706",
            soft: "border-amber-200 bg-amber-50 text-amber-900",
            badge: "inline-flex items-center rounded-full bg-amber-100 px-3 py-1 text-xs font-semibold text-amber-700",
        };
    }

    return {
        label: level || "Stable",
        color: "#059669",
        soft: "border-emerald-200 bg-emerald-50 text-emerald-900",
        badge: "inline-flex items-center rounded-full bg-emerald-100 px-3 py-1 text-xs font-semibold text-emerald-700",
    };
});

const growthMeta = computed(() => {
    const status = String(growthTrajectory.value?.status ?? "");

    if (/declin|deterior|critical/i.test(status)) {
        return {
            badge: "inline-flex items-center rounded-full bg-red-100 px-3 py-1 text-xs font-semibold text-red-700",
            soft: "border-red-200 bg-red-50 text-red-900",
        };
    }

    if (/watch|mixed|risk/i.test(status)) {
        return {
            badge: "inline-flex items-center rounded-full bg-amber-100 px-3 py-1 text-xs font-semibold text-amber-700",
            soft: "border-amber-200 bg-amber-50 text-amber-900",
        };
    }

    return {
        badge: "inline-flex items-center rounded-full bg-emerald-100 px-3 py-1 text-xs font-semibold text-emerald-700",
        soft: "border-emerald-200 bg-emerald-50 text-emerald-900",
    };
});

const zScores = computed(() => {
    const z = assessment.value?.z_scores ?? {};
    return [
        { label: "WHZ", meaning: "Wasting", value: z.WHZ ?? "-" },
        { label: "HAZ", meaning: "Stunting", value: z.HAZ ?? "-" },
        { label: "WAZ", meaning: "Underweight", value: z.WAZ ?? "-" },
    ];
});

const childSummaryRows = computed(() => [
    ["Child Name", childInfo.value.full_name || props.patient.patient_name || "-"],
    ["Patient ID", childInfo.value.patient_id || props.patient.patient_id || "-"],
    [
        "Age at Screening",
        childInfo.value.age_at_screening ||
            `${props.patient.age_months ?? "-"} months`,
    ],
    ["Date of Birth", childInfo.value.date_of_birth || "-"],
    ["Gender", childInfo.value.gender || props.patient.gender || "-"],
    ["Report Status", props.result?.status || "success"],
]);

const actionRows = computed(() => [
    ["Immediate Action", actionPlan.value.immediate_action || "-"],
    ["Treatment Regimen", actionPlan.value.treatment_regimen || "-"],
    ["Follow-Up Schedule", actionPlan.value.follow_up_schedule || "-"],
    ["Next Visit Date", actionPlan.value.next_visit_date || "-"],
]);

const growthRows = computed(() => [
    ["Trajectory Status", growthTrajectory.value.status || "-"],
    ["Weight Change", `${growthTrajectory.value.weight_change_kg ?? "-"} kg`],
]);

const medicalHistory = computed(() => {
    const records = childDashboard.value?.complete_medical_record;
    return Array.isArray(records) ? records : [];
});

async function loadChildDashboard() {
    if (!props.patient?.patient_id) return;

    historyLoading.value = true;
    historyError.value = "";

    try {
        const { data } = await getVhwPatientDashboard(props.patient.patient_id);
        childDashboard.value = data;
    } catch (error) {
        historyError.value =
            error.response?.data?.message ||
            error.response?.data?.error ||
            "Child dashboard history could not be loaded.";
    } finally {
        historyLoading.value = false;
    }
}

async function downloadPdf() {
    if (!reportRef.value) return;

    const reportNode = reportRef.value;
    const originalStyles = {
        maxHeight: reportNode.style.maxHeight,
        height: reportNode.style.height,
        overflowY: reportNode.style.overflowY,
        overflow: reportNode.style.overflow,
    };

    reportNode.style.maxHeight = "none";
    reportNode.style.height = "auto";
    reportNode.style.overflowY = "visible";
    reportNode.style.overflow = "visible";

    await nextTick();

    const options = {
        margin: 8,
        filename: `${props.patient.patient_id || "screening"}-report.pdf`,
        image: { type: "jpeg", quality: 0.98 },
        html2canvas: {
            scale: 2,
            useCORS: true,
            scrollY: 0,
            windowWidth: reportNode.scrollWidth,
            windowHeight: reportNode.scrollHeight,
        },
        jsPDF: { unit: "mm", format: "a4", orientation: "portrait" },
        pagebreak: {
            mode: ["css", "legacy"],
        },
    };

    try {
        await html2pdf().set(options).from(reportNode).save();
    } finally {
        reportNode.style.maxHeight = originalStyles.maxHeight;
        reportNode.style.height = originalStyles.height;
        reportNode.style.overflowY = originalStyles.overflowY;
        reportNode.style.overflow = originalStyles.overflow;
    }
}

onMounted(loadChildDashboard);

watch(
    () => props.patient?.patient_id,
    () => {
        loadChildDashboard();
    },
);
</script>

<template>
    <div
        class="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4"
    >
        <div
            ref="reportRef"
            class="max-h-[92vh] w-full max-w-5xl overflow-y-auto rounded-[28px] border border-stone-300 bg-[#fcfbf8] shadow-2xl"
        >
            <section class="border-b border-stone-300 bg-white px-8 py-8">
                <div class="flex flex-col gap-6 md:flex-row md:items-start md:justify-between">
                    <div class="max-w-3xl">
                        <p class="text-xs font-semibold uppercase tracking-[0.32em] text-stone-500">
                            Nutritional Screening Report
                        </p>
                        <h2 class="mt-3 text-3xl font-semibold tracking-tight text-stone-900">
                            Child Clinical Assessment
                        </h2>
                        <p class="mt-3 text-sm leading-relaxed text-stone-600">
                            Structured report summarizing the child profile, AI-supported assessment,
                            growth trajectory, and recommended follow-up plan.
                        </p>
                    </div>

                    <div class="flex flex-wrap gap-3">
                        <span :class="triageMeta.badge">
                            {{ triageMeta.label }}
                        </span>
                        <button
                            class="rounded-xl border border-stone-300 bg-white px-4 py-2 text-sm font-semibold text-stone-700 transition hover:bg-stone-50"
                            type="button"
                            @click="emit('close')"
                        >
                            Close
                        </button>
                    </div>
                </div>
            </section>

            <div class="space-y-8 px-8 py-8">
                <section class="grid gap-8 lg:grid-cols-[1.05fr_1.25fr]">
                    <article class="rounded-[24px] border border-stone-300 bg-white p-6">
                        <div class="flex items-start justify-between gap-4">
                            <div>
                                <p class="text-xs font-semibold uppercase tracking-[0.24em] text-stone-500">
                                    Assessment
                                </p>
                                <h3 class="mt-2 text-xl font-semibold text-stone-900">
                                    Current Clinical Risk
                                </h3>
                            </div>
                            <span :class="triageMeta.badge">
                                {{ assessment.triage_level || "Not Available" }}
                            </span>
                        </div>

                        <div class="mt-8 flex items-center gap-6">
                            <div
                                class="flex h-36 w-36 shrink-0 items-center justify-center rounded-full"
                                :style="{
                                    background: `conic-gradient(${triageMeta.color} 0deg ${scorePercent * 3.6}deg, #e7e5e4 ${scorePercent * 3.6}deg 360deg)`,
                                }"
                            >
                                <div class="flex h-26 w-26 items-center justify-center rounded-full bg-white">
                                    <div class="text-center">
                                        <p class="text-3xl font-semibold tracking-tight text-stone-900">
                                            {{ scorePercent }}%
                                        </p>
                                        <p class="text-xs uppercase tracking-[0.18em] text-stone-500">
                                            Danger
                                        </p>
                                    </div>
                                </div>
                            </div>

                            <div class="min-w-0">
                                <p class="text-sm font-medium text-stone-500">
                                    AI Interpretation
                                </p>
                                <p class="mt-2 text-base leading-relaxed text-stone-800">
                                    {{ assessment.ai_interpretation || "-" }}
                                </p>
                            </div>
                        </div>

                        <div class="mt-8 border-t border-stone-200 pt-6">
                            <p class="text-sm font-semibold text-stone-900">
                                WHO Z-Score Summary
                            </p>
                            <div class="mt-4 grid gap-4 sm:grid-cols-3">
                                <div
                                    v-for="score in zScores"
                                    :key="score.label"
                                    class="rounded-2xl bg-stone-50 px-4 py-4"
                                >
                                    <p class="text-xs font-semibold uppercase tracking-[0.18em] text-stone-500">
                                        {{ score.label }}
                                    </p>
                                    <p class="mt-2 text-3xl font-semibold tracking-tight text-stone-900">
                                        {{ score.value }}
                                    </p>
                                    <p class="mt-1 text-sm text-stone-600">
                                        {{ score.meaning }}
                                    </p>
                                </div>
                            </div>
                        </div>
                    </article>

                    <article class="rounded-[24px] border border-stone-300 bg-white p-6">
                        <p class="text-xs font-semibold uppercase tracking-[0.24em] text-stone-500">
                            Child Summary
                        </p>
                        <h3 class="mt-2 text-xl font-semibold text-stone-900">
                            Identity and Screening Details
                        </h3>

                        <dl class="mt-6 divide-y divide-stone-200">
                            <div
                                v-for="[label, value] in childSummaryRows"
                                :key="label"
                                class="grid gap-2 py-4 sm:grid-cols-[180px_1fr]"
                            >
                                <dt class="text-sm font-medium text-stone-500">
                                    {{ label }}
                                </dt>
                                <dd class="text-sm font-semibold text-stone-900">
                                    {{ value }}
                                </dd>
                            </div>
                        </dl>
                    </article>
                </section>

                <section
                    class="rounded-[24px] border bg-white p-6"
                    :class="growthMeta.soft"
                >
                    <div class="flex flex-col gap-4 md:flex-row md:items-start md:justify-between">
                        <div class="max-w-3xl">
                            <p class="text-xs font-semibold uppercase tracking-[0.24em] opacity-80">
                                Growth Trajectory
                            </p>
                            <h3 class="mt-2 text-xl font-semibold">
                                {{ growthTrajectory.status || "Growth Signal Not Returned" }}
                            </h3>
                            <p class="mt-3 text-sm leading-relaxed opacity-90">
                                {{
                                    growthTrajectory.description ||
                                    "The predict response did not include a growth trajectory description for this screening."
                                }}
                            </p>
                        </div>
                        <span :class="growthMeta.badge">
                            {{ growthTrajectory.status || "Growth trajectory" }}
                        </span>
                    </div>

                    <dl class="mt-6 divide-y divide-white/40 rounded-2xl bg-white/80 px-4">
                        <div
                            v-for="[label, value] in growthRows"
                            :key="label"
                            class="grid gap-2 py-4 sm:grid-cols-[180px_1fr]"
                        >
                            <dt class="text-sm font-medium opacity-70">
                                {{ label }}
                            </dt>
                            <dd class="text-sm font-semibold">
                                {{ value }}
                            </dd>
                        </div>
                    </dl>
                </section>

                <section class="grid gap-8 lg:grid-cols-[1.15fr_0.95fr]">
                    <article class="rounded-[24px] border border-stone-300 bg-white p-6">
                        <p class="text-xs font-semibold uppercase tracking-[0.24em] text-stone-500">
                            Care Plan
                        </p>
                        <h3 class="mt-2 text-xl font-semibold text-stone-900">
                            Recommended Follow-Up Actions
                        </h3>

                        <dl class="mt-6 divide-y divide-stone-200">
                            <div
                                v-for="[label, value] in actionRows"
                                :key="label"
                                class="grid gap-2 py-4 sm:grid-cols-[180px_1fr]"
                            >
                                <dt class="text-sm font-medium text-stone-500">
                                    {{ label }}
                                </dt>
                                <dd class="text-sm leading-relaxed text-stone-900">
                                    {{ value }}
                                </dd>
                            </div>
                        </dl>
                    </article>

                    <article class="rounded-[24px] border border-stone-300 bg-white p-6">
                        <p class="text-xs font-semibold uppercase tracking-[0.24em] text-stone-500">
                            Clinical Impression
                        </p>
                        <h3 class="mt-2 text-xl font-semibold text-stone-900">
                            Case Summary
                        </h3>

                        <div class="mt-6 space-y-4 text-sm leading-relaxed text-stone-700">
                            <p>
                                The child is currently classified as
                                <span class="font-semibold text-stone-900">
                                    {{ assessment.triage_level || "not available" }}
                                </span>
                                with a recorded danger score of
                                <span class="font-semibold text-stone-900">
                                    {{ assessment.danger_score || "-" }}
                                </span>.
                            </p>
                            <p>
                                {{
                                    growthTrajectory.description ||
                                    "No growth trajectory narrative was returned in the response."
                                }}
                            </p>
                            <p>
                                Next scheduled review:
                                <span class="font-semibold text-stone-900">
                                    {{ actionPlan.next_visit_date || "-" }}
                                </span>
                            </p>
                        </div>
                    </article>
                </section>

                <section class="rounded-[24px] border border-stone-300 bg-white p-6">
                    <div class="flex flex-col gap-2 sm:flex-row sm:items-end sm:justify-between">
                        <div>
                            <p class="text-xs font-semibold uppercase tracking-[0.24em] text-stone-500">
                                Longitudinal History
                            </p>
                            <h3 class="mt-2 text-xl font-semibold text-stone-900">
                                Previous Visit Timeline
                            </h3>
                        </div>
                        <p class="text-sm text-stone-500">
                            {{ childDashboard?.history_count ?? medicalHistory.length }} recorded visits
                        </p>
                    </div>

                    <div
                        v-if="historyLoading"
                        class="mt-6 text-sm text-stone-600"
                    >
                        Loading child history...
                    </div>
                    <div
                        v-else-if="historyError"
                        class="mt-6 rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700"
                    >
                        {{ historyError }}
                    </div>
                    <div
                        v-else-if="!medicalHistory.length"
                        class="mt-6 rounded-2xl border border-dashed border-stone-200 bg-stone-50 p-6 text-sm text-stone-600"
                    >
                        No screening history is available yet.
                    </div>
                    <div v-else class="mt-6 space-y-4">
                        <article
                            v-for="(visit, index) in medicalHistory"
                            :key="`${visit.visit_date}-${index}`"
                            class="rounded-2xl border border-stone-200 bg-stone-50 p-5"
                        >
                            <div class="flex flex-col gap-2 md:flex-row md:items-start md:justify-between">
                                <div>
                                    <p class="text-base font-semibold text-stone-900">
                                        Visit {{ index + 1 }} - {{ visit.visit_date || "-" }}
                                    </p>
                                    <p class="mt-1 text-sm text-stone-500">
                                        Recorded by {{ visit.recorded_by || "-" }} • {{ visit.clinical_age || "-" }}
                                    </p>
                                </div>
                                <span :class="triageMeta.badge">
                                    {{ visit.ai_assessment?.triage_status || "Tracked" }}
                                </span>
                            </div>

                            <div class="mt-4 overflow-x-auto">
                                <table class="w-full min-w-[620px] border-collapse text-sm">
                                    <thead>
                                        <tr class="border-b border-stone-200 text-left text-xs uppercase tracking-[0.16em] text-stone-500">
                                            <th class="pb-3 font-semibold">Weight</th>
                                            <th class="pb-3 font-semibold">Height</th>
                                            <th class="pb-3 font-semibold">Danger Score</th>
                                            <th class="pb-3 font-semibold">WHZ</th>
                                            <th class="pb-3 font-semibold">HAZ</th>
                                            <th class="pb-3 font-semibold">WAZ</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        <tr class="text-stone-800">
                                            <td class="py-3">{{ visit.physical_stats?.weight_kg ?? "-" }} kg</td>
                                            <td class="py-3">{{ visit.physical_stats?.height_cm ?? "-" }} cm</td>
                                            <td class="py-3">{{ visit.ai_assessment?.danger_score ?? "-" }}</td>
                                            <td class="py-3">{{ visit.who_z_scores?.["WHZ (Wasting)"] ?? "-" }}</td>
                                            <td class="py-3">{{ visit.who_z_scores?.["HAZ (Stunting)"] ?? "-" }}</td>
                                            <td class="py-3">{{ visit.who_z_scores?.["WAZ (Underweight)"] ?? "-" }}</td>
                                        </tr>
                                    </tbody>
                                </table>
                            </div>
                        </article>
                    </div>
                </section>

                <div class="flex flex-wrap justify-end gap-3 border-t border-stone-200 pt-2">
                    <button
                        class="rounded-xl border border-stone-300 bg-white px-4 py-2 text-sm font-semibold text-stone-700 transition hover:bg-stone-50"
                        type="button"
                        @click="downloadPdf"
                    >
                        Download PDF
                    </button>
                    <button
                        class="rounded-xl border border-stone-300 bg-white px-4 py-2 text-sm font-semibold text-stone-700 transition hover:bg-stone-50"
                        type="button"
                        @click="emit('newScreening')"
                    >
                        New Screening
                    </button>
                    <button
                        class="rounded-xl bg-emerald-600 px-4 py-2 text-sm font-semibold text-white transition hover:bg-emerald-500"
                        type="button"
                        @click="emit('close')"
                    >
                        Close
                    </button>
                </div>
            </div>
        </div>
    </div>
</template>
