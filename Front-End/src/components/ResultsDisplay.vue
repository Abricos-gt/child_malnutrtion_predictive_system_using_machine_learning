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

const scorePercent = computed(() => {
    const rawScore =
        props.result?.danger_score ?? props.result?.prediction ?? 0;
    if (typeof rawScore === "string") {
        const cleaned = rawScore.replace("%", "");
        return Number(cleaned) || 0;
    }
    if (typeof rawScore === "number") {
        return rawScore <= 1 ? Math.round(rawScore * 100) : rawScore;
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
        Borderline: {
            label: "Borderline",
            badge: "inline-flex items-center rounded-full bg-amber-100 px-2.5 py-1 text-xs font-semibold text-amber-700",
            color: "#f59e0b",
        },
        Stable: {
            label: "Stable",
            badge: "inline-flex items-center rounded-full bg-emerald-100 px-2.5 py-1 text-xs font-semibold text-emerald-700",
            color: "#22c55e",
        },
    };

    const status = props.result?.status;
    if (status && statusMap[status]) {
        return statusMap[status];
    }

    const score = scorePercent.value;
    if (score >= 70) return statusMap.Critical;
    if (score >= 40) return statusMap["At Risk"];
    if (score >= 20) return statusMap.Borderline;
    return statusMap.Stable;
});

const riskPercentage = computed(() => scorePercent.value);

const primaryRisk = computed(() => {
    return (
        props.result?.primary_risk ||
        props.result?.primary_driver ||
        "No immediate risk identified"
    );
});

const zScores = computed(() => {
    const z = props.result?.z_scores ?? {};
    return {
        haz: z.haz ?? z.HAZ ?? null,
        whz: z.whz ?? z.WHZ ?? null,
        waz: z.waz ?? z.WAZ ?? null,
    };
});

const recommendations = computed(() => {
    const level = riskLevel.value.label;
    const base = {
        Critical: {
            immediate: [
                "Refer to nearest facility for urgent assessment",
                "Initiate therapeutic feeding under supervision",
            ],
            shortTerm: [
                "Follow-up within 24–48 hours",
                "Monitor hydration and vital signs closely",
            ],
            preventive: [
                "Caregiver counseling on danger signs",
                "Coordinate transport plan and escalation contact",
            ],
            proactive:
                "High probability of acute malnutrition. Escalate immediately.",
        },
        "High Risk": {
            immediate: [
                "Schedule clinical assessment within 72 hours",
                "Start supplementary feeding if available",
            ],
            shortTerm: [
                "Weekly monitoring for 4 weeks",
                "Nutrition counseling for caregivers",
            ],
            preventive: [
                "Vaccination status check and follow-up",
                "Sanitation and clean water guidance",
            ],
            proactive: "Risk rising. Intervene early to prevent deterioration.",
        },
        "Moderate Risk": {
            immediate: ["Community health worker review within 7 days"],
            shortTerm: ["Monthly growth monitoring", "Dietary counseling"],
            preventive: [
                "Household nutrition education",
                "Routine deworming check",
            ],
            proactive: "Moderate risk. Maintain close follow-up.",
        },
        "Low Risk": {
            immediate: ["Continue routine growth monitoring"],
            shortTerm: ["Nutrition counseling as needed"],
            preventive: ["Ensure age-appropriate vaccinations"],
            proactive: "Low risk. Keep scheduled follow-ups.",
        },
        Stable: {
            immediate: ["Maintain routine wellness checks"],
            shortTerm: ["Monitor growth at standard intervals"],
            preventive: ["Continue balanced diet and hygiene guidance"],
            proactive: "Stable condition. Maintain preventive care.",
        },
    };

    return base[level] || base.Stable;
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
            class="w-full max-w-5xl rounded-2xl border border-gray-200 bg-white p-6 shadow-lg"
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

            <div
                class="mt-6 grid gap-4 rounded-xl border border-gray-200 p-4 md:grid-cols-3"
            >
                <div class="p-2">
                    <p class="text-xs uppercase tracking-wide text-gray-500">
                        Risk Score
                    </p>
                    <p class="mt-2 text-2xl font-semibold text-gray-900">
                        {{ riskPercentage }}%
                    </p>
                </div>
                <div class="p-2">
                    <p class="text-xs uppercase tracking-wide text-gray-500">
                        Status
                    </p>
                    <div class="mt-2">
                        <span :class="riskLevel.badge">{{
                            riskLevel.label
                        }}</span>
                    </div>
                </div>
                <div class="p-2">
                    <p class="text-xs uppercase tracking-wide text-gray-500">
                        Primary Risk Factor
                    </p>
                    <p class="mt-2 text-sm font-semibold text-gray-900">
                        {{ primaryRisk }}
                    </p>
                </div>
            </div>

            <div class="mt-8">
                <h3 class="text-lg font-semibold text-gray-900">
                    Patient Snapshot
                </h3>
                <div class="mt-4 grid gap-3 sm:grid-cols-2 lg:grid-cols-5">
                    <div class="p-2">
                        <p class="text-xs text-gray-500">Name</p>
                        <p class="text-sm font-semibold text-gray-900">
                            {{ patient.patient_name }}
                        </p>
                    </div>
                    <div class="p-2">
                        <p class="text-xs text-gray-500">Age</p>
                        <p class="text-sm font-semibold text-gray-900">
                            {{ patient.age_months }} months
                        </p>
                    </div>
                    <div class="p-2">
                        <p class="text-xs text-gray-500">Gender</p>
                        <p class="text-sm font-semibold text-gray-900">
                            {{ patient.gender }}
                        </p>
                    </div>
                    <div class="p-2">
                        <p class="text-xs text-gray-500">Weight</p>
                        <p class="text-sm font-semibold text-gray-900">
                            {{ patient.weight_kg }} kg
                        </p>
                    </div>
                    <div class="p-2">
                        <p class="text-xs text-gray-500">Height</p>
                        <p class="text-sm font-semibold text-gray-900">
                            {{ patient.height_cm }} cm
                        </p>
                    </div>
                </div>
            </div>

            <div class="mt-8">
                <h3 class="text-lg font-semibold text-gray-900">Z-Scores</h3>
                <div class="mt-4 grid gap-3 sm:grid-cols-3">
                    <div class="p-2">
                        <p class="text-xs text-gray-500">HAZ</p>
                        <p class="text-sm font-semibold text-gray-900">
                            {{ zScores.haz ?? "—" }}
                        </p>
                    </div>
                    <div class="p-2">
                        <p class="text-xs text-gray-500">WHZ</p>
                        <p class="text-sm font-semibold text-gray-900">
                            {{ zScores.whz ?? "—" }}
                        </p>
                    </div>
                    <div class="p-2">
                        <p class="text-xs text-gray-500">WAZ</p>
                        <p class="text-sm font-semibold text-gray-900">
                            {{ zScores.waz ?? "—" }}
                        </p>
                    </div>
                </div>
            </div>

            <div class="mt-8">
                <h3 class="text-lg font-semibold text-gray-900">
                    Recommendations
                </h3>
                <div class="mt-4 grid gap-4 md:grid-cols-3">
                    <div class="p-2">
                        <h4 class="text-sm font-semibold text-gray-900">
                            Immediate
                        </h4>
                        <ul class="mt-2 space-y-1 text-sm text-gray-600">
                            <li
                                v-for="(
                                    item, index
                                ) in recommendations.immediate"
                                :key="index"
                            >
                                {{ item }}
                            </li>
                        </ul>
                    </div>
                    <div class="p-2">
                        <h4 class="text-sm font-semibold text-gray-900">
                            Short-term
                        </h4>
                        <ul class="mt-2 space-y-1 text-sm text-gray-600">
                            <li
                                v-for="(
                                    item, index
                                ) in recommendations.shortTerm"
                                :key="index"
                            >
                                {{ item }}
                            </li>
                        </ul>
                    </div>
                    <div class="p-2">
                        <h4 class="text-sm font-semibold text-gray-900">
                            Preventive
                        </h4>
                        <ul class="mt-2 space-y-1 text-sm text-gray-600">
                            <li
                                v-for="(
                                    item, index
                                ) in recommendations.preventive"
                                :key="index"
                            >
                                {{ item }}
                            </li>
                        </ul>
                    </div>
                </div>

                <div
                    class="mt-6 rounded-lg border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-800"
                >
                    <strong>Proactive Warning:</strong>
                    {{ recommendations.proactive }}
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
