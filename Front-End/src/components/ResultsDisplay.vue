  <script setup>
import { computed, ref } from "vue";
import html2pdf from "html2pdf.js";

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

const showLastVisit = ref(false);

const currentAssessment = computed(
    () => props.result?.current_assessment ?? {},
);
const previousAssessment = computed(
    () => props.result?.previous_assessment ?? {},
);
const previousDetails = computed(() => previousAssessment.value?.details ?? {});
const comparisonSummary = computed(
    () => props.result?.comparison_summary ?? {},
);
const chartData = computed(() => props.result?.chart_data ?? {});

const scorePercent = computed(() => {
    const rawScore = currentAssessment.value?.danger_score ?? 0;
    if (typeof rawScore === "string") {
        const cleaned = rawScore.replace("%", "");
        return Number(cleaned) || 0;
    }
    if (typeof rawScore === "number") {
        return rawScore;
    }
    return 0;
});

const riskLevel = computed(() => {
    const statusMap = {
        Critical: {
            label: "Critical",
            badge: "inline-flex items-center rounded-full bg-red-100 px-2.5 py-1 text-xs font-semibold text-red-700",
            color: "#ef4444",
        },
        "At Risk": {
            label: "At Risk",
            badge: "inline-flex items-center rounded-full bg-amber-100 px-2.5 py-1 text-xs font-semibold text-amber-700",
            color: "#f59e0b",
        },
        Stable: {
            label: "Stable",
            badge: "inline-flex items-center rounded-full bg-emerald-100 px-2.5 py-1 text-xs font-semibold text-emerald-700",
            color: "#22c55e",
        },
    };

    const status = currentAssessment.value?.danger_level;
    if (status && statusMap[status]) {
        return statusMap[status];
    }

    const score = scorePercent.value;
    if (score >= 70) return statusMap.Critical;
    if (score >= 40) return statusMap["At Risk"];
    return statusMap.Stable;
});

const riskPercentage = computed(() => scorePercent.value);

const zScores = computed(() => {
    const z = currentAssessment.value?.z_scores ?? {};
    return {
        haz: z.haz ?? z.HAZ ?? null,
        whz: z.whz ?? z.WHZ ?? null,
        waz: z.waz ?? z.WAZ ?? null,
    };
});

const recommendations = computed(() => {
    const rec = currentAssessment.value?.recommendations ?? {};
    return {
        immediate: rec.immediate_action ? [rec.immediate_action] : [],
        shortTerm: rec.treatment ? [rec.treatment] : [],
        preventive: rec.followup_days
            ? [`Follow-up in ${rec.followup_days} days`]
            : [],
    };
});

const chartPoints = computed(() => {
    const scores = chartData.value?.danger_scores ?? [];
    if (!scores.length) return "";
    const chartWidth = 260;
    const chartHeight = 120;
    const chartPadding = 8;
    const max = Math.max(...scores, 1);
    const min = Math.min(...scores, 0);
    const range = max - min || 1;

    return scores
        .map((score, index) => {
            const x =
                chartPadding +
                (index / Math.max(scores.length - 1, 1)) *
                    (chartWidth - chartPadding * 2);
            const y =
                chartPadding +
                (1 - (score - min) / range) * (chartHeight - chartPadding * 2);
            return `${x},${y}`;
        })
        .join(" ");
});

const reportRef = ref(null);

function downloadPdf() {
    if (!reportRef.value) return;
    const options = {
        margin: 8,
        filename: "nutriai-screening-report.pdf",
        image: { type: "jpeg", quality: 0.98 },
        html2canvas: { scale: 2 },
        jsPDF: { unit: "mm", format: "a4", orientation: "portrait" },
    };
    html2pdf().set(options).from(reportRef.value).save();
}
</script>

<template>
    <div
        class="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4"
    >
        <div
            ref="reportRef"
            class="w-full max-w-6xl rounded-2xl border border-gray-200 bg-white p-6 shadow-lg"
        >
            <div class="flex items-start justify-between">
                <div>
                    <h2 class="text-xl font-semibold text-gray-900">
                        AI Prediction Results
                    </h2>
                    <p class="mt-1 text-sm text-gray-600">
                        Risk assessment summary and clinical guidance.
                    </p>
                </div>
                <button
                    class="rounded-lg border border-gray-200 px-3 py-1 text-sm font-semibold text-gray-700 transition hover:text-gray-900"
                    type="button"
                    @click="emit('close')"
                >
                    Close
                </button>
            </div>

            <div class="mt-6 grid gap-6 lg:grid-cols-3">
                <!-- Left: Primary AI Alert -->
                <div class="rounded-xl border border-gray-200 p-5">
                    <p class="text-xs uppercase tracking-wide text-gray-500">
                        Current Status
                    </p>
                    <div class="mt-4 flex items-center justify-center">
                        <div
                            class="flex h-36 w-36 items-center justify-center rounded-full"
                            :style="{
                                background: `conic-gradient(${riskLevel.color} 0deg ${riskPercentage * 3.6}deg, #E5E7EB ${riskPercentage * 3.6}deg 360deg)`,
                            }"
                        >
                            <div
                                class="flex h-28 w-28 items-center justify-center rounded-full bg-white"
                            >
                                <div class="text-center">
                                    <p
                                        class="text-2xl font-semibold text-gray-900"
                                    >
                                        {{ riskPercentage }}%
                                    </p>
                                    <p class="text-xs text-gray-500">
                                        Danger Score
                                    </p>
                                </div>
                            </div>
                        </div>
                    </div>
                    <div class="mt-4 flex justify-center">
                        <span :class="riskLevel.badge">{{
                            riskLevel.label
                        }}</span>
                    </div>
                    <div class="mt-4 border-t border-gray-200 pt-4">
                        <h3 class="text-sm font-semibold text-gray-900">
                            XAI Explanation
                        </h3>
                        <p class="mt-2 text-sm text-gray-700">
                            {{ currentAssessment?.xai?.summary || "—" }}
                        </p>
                        <div class="mt-2 text-sm text-gray-700">
                            <span class="font-medium">Primary Factors:</span>
                            {{
                                (
                                    currentAssessment?.xai?.primary_factors ||
                                    []
                                ).join(", ") || "—"
                            }}
                        </div>
                    </div>
                </div>

                <!-- Center: Side-by-side comparison -->
                <div class="rounded-xl border border-gray-200 p-5">
                    <div class="flex items-center justify-between">
                        <h3 class="text-base font-semibold text-gray-900">
                            Clinical Comparison
                        </h3>
                        <button
                            class="rounded-lg border border-gray-200 px-3 py-1 text-xs font-semibold text-gray-700 transition hover:text-gray-900 disabled:cursor-not-allowed disabled:opacity-50"
                            type="button"
                            :disabled="!previousAssessment?.exists"
                            @click="showLastVisit = !showLastVisit"
                        >
                            {{
                                showLastVisit ? "Hide Last Visit" : "Last Visit"
                            }}
                        </button>
                    </div>

                    <div class="mt-4 grid gap-3 text-sm text-gray-700">
                        <div
                            class="grid grid-cols-3 gap-2 text-xs text-gray-500"
                        >
                            <span>Metric</span>
                            <span>Previous</span>
                            <span>Current</span>
                        </div>
                        <div class="grid grid-cols-3 gap-2">
                            <span>Weight</span>
                            <span>{{
                                showLastVisit && previousAssessment?.exists
                                    ? `${previousDetails.weight ?? "—"} kg`
                                    : "—"
                            }}</span>
                            <span>{{ patient.weight_kg }} kg</span>
                        </div>
                        <div class="grid grid-cols-3 gap-2">
                            <span>Height</span>
                            <span>{{
                                showLastVisit && previousAssessment?.exists
                                    ? `${previousDetails.height ?? "—"} cm`
                                    : "—"
                            }}</span>
                            <span>{{ patient.height_cm }} cm</span>
                        </div>
                        <div class="grid grid-cols-3 gap-2">
                            <span>Danger Score</span>
                            <span>{{
                                showLastVisit && previousAssessment?.exists
                                    ? `${previousDetails.danger_score ?? "—"}%`
                                    : "—"
                            }}</span>
                            <span>{{ riskPercentage }}%</span>
                        </div>
                        <div class="grid grid-cols-3 gap-2">
                            <span>Status</span>
                            <span>{{
                                showLastVisit && previousAssessment?.exists
                                    ? (previousDetails.status ?? "—")
                                    : "—"
                            }}</span>
                            <span>{{
                                currentAssessment?.danger_level || "—"
                            }}</span>
                        </div>
                        <div class="grid grid-cols-3 gap-2">
                            <span>Date</span>
                            <span>{{
                                showLastVisit && previousAssessment?.exists
                                    ? (previousDetails.date ?? "—")
                                    : "—"
                            }}</span>
                            <span>{{ props.result?.timestamp || "—" }}</span>
                        </div>
                        <div class="grid grid-cols-3 gap-2">
                            <span>HAZ</span>
                            <span>{{
                                showLastVisit && previousAssessment?.exists
                                    ? (previousDetails.z_scores?.HAZ ?? "—")
                                    : "—"
                            }}</span>
                            <span>{{ zScores.haz ?? "—" }}</span>
                        </div>
                        <div class="grid grid-cols-3 gap-2">
                            <span>WHZ</span>
                            <span>{{
                                showLastVisit && previousAssessment?.exists
                                    ? (previousDetails.z_scores?.WHZ ?? "—")
                                    : "—"
                            }}</span>
                            <span>{{ zScores.whz ?? "—" }}</span>
                        </div>
                        <div class="grid grid-cols-3 gap-2">
                            <span>WAZ</span>
                            <span>{{
                                showLastVisit && previousAssessment?.exists
                                    ? (previousDetails.z_scores?.WAZ ?? "—")
                                    : "—"
                            }}</span>
                            <span>{{ zScores.waz ?? "—" }}</span>
                        </div>
                    </div>

                    <div class="mt-4 text-xs text-gray-500">
                        {{ comparisonSummary?.label || "Initial Assessment" }} •
                        Trend: {{ comparisonSummary?.trend || "—" }} • Δ Weight:
                        {{ comparisonSummary?.weight_change_kg ?? 0 }}kg • Last
                        visit: {{ previousDetails.date || "—" }}
                    </div>
                </div>

                <!-- Right: Trend + Action -->
                <div class="rounded-xl border border-gray-200 p-5">
                    <h3 class="text-base font-semibold text-gray-900">
                        Growth Trend
                    </h3>
                    <div
                        class="mt-3 rounded-lg border border-gray-200 bg-gray-50 p-4 text-sm text-gray-600"
                    >
                        <svg
                            v-if="chartPoints"
                            :width="260"
                            :height="120"
                            viewBox="0 0 260 120"
                        >
                            <polyline
                                :points="chartPoints"
                                fill="none"
                                stroke="#10B981"
                                stroke-width="3"
                            />
                        </svg>
                        <span v-else
                            >Trend chart will appear after multiple
                            screenings.</span
                        >
                    </div>

                    <div
                        class="mt-6 rounded-lg border border-amber-200 bg-amber-50 p-4 text-sm text-amber-800"
                    >
                        <p class="font-semibold">Action</p>
                        <p class="mt-2">
                            <span class="font-medium">Immediate:</span>
                            {{ recommendations.immediate[0] || "—" }}
                        </p>
                        <p class="mt-1">
                            <span class="font-medium">Treatment:</span>
                            {{ recommendations.shortTerm[0] || "—" }}
                        </p>
                        <p class="mt-1">
                            <span class="font-medium">Follow-up:</span>
                            {{ recommendations.preventive[0] || "—" }}
                        </p>
                    </div>
                </div>
            </div>

            <div class="mt-8 flex flex-wrap justify-end gap-3">
                <button
                    class="rounded-lg border border-gray-200 px-4 py-2 text-sm font-semibold text-gray-700 transition hover:text-gray-900"
                    type="button"
                    @click="downloadPdf"
                >
                    Download PDF
                </button>
                <button
                    class="rounded-lg border border-gray-200 px-4 py-2 text-sm font-semibold text-gray-700 transition hover:text-gray-900"
                    type="button"
                    @click="emit('newScreening')"
                >
                    New Screening
                </button>
                <button
                    class="rounded-lg bg-[#10B981] px-4 py-2 text-sm font-semibold text-white transition hover:bg-[#0EA371]"
                    type="button"
                    @click="emit('close')"
                >
                    Close
                </button>
            </div>
        </div>
    </div>
</template>

