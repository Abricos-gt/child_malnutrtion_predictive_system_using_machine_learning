<script setup>
import { computed, reactive, ref } from "vue";
import { predict } from "../services/api";

const emit = defineEmits(["close", "submitted"]);

const step = ref(1);
const submitting = ref(false);
const apiError = ref("");
const fieldErrors = reactive({});

const form = reactive({
    patient_name: "",
    age_months: "",
    weight_kg: "",
    height_cm: "",
    gender: "",
    diarrhea: false,
    anemia: false,
    malaria: false,
});

const progress = computed(() => (step.value === 1 ? 50 : 100));

const numericPayload = computed(() => ({
    patient_name: form.patient_name.trim(),
    age_months: Number(form.age_months),
    weight_kg: Number(form.weight_kg),
    height_cm: Number(form.height_cm),
    gender: form.gender,
    diarrhea: form.diarrhea ? 1 : 0,
    anemia: form.anemia ? 1 : 0,
    malaria: form.malaria ? 1 : 0,
}));

function clearFieldErrors() {
    Object.keys(fieldErrors).forEach((key) => {
        delete fieldErrors[key];
    });
}

function validateStep(currentStep) {
    clearFieldErrors();
    apiError.value = "";

    if (currentStep === 1) {
        if (!form.patient_name.trim()) {
            fieldErrors.patient_name = "Patient name is required.";
        }

        const age = Number(form.age_months);
        const weight = Number(form.weight_kg);
        const height = Number(form.height_cm);

        if (!Number.isFinite(age) || age < 0 || age > 60) {
            fieldErrors.age_months = "Age must be between 0 and 60 months.";
        }

        if (!Number.isFinite(weight) || weight < 1.5 || weight > 30) {
            fieldErrors.weight_kg = "Weight must be between 1.5 kg and 30 kg.";
        }

        if (!Number.isFinite(height) || height < 45 || height > 125) {
            fieldErrors.height_cm = "Height must be between 45 cm and 125 cm.";
        }

        if (!form.gender) {
            fieldErrors.gender = "Gender is required.";
        }
    }

    return Object.keys(fieldErrors).length === 0;
}

function nextStep() {
    if (validateStep(1)) {
        step.value = 2;
    }
}

function previousStep() {
    clearFieldErrors();
    apiError.value = "";
    step.value = 1;
}

async function submitScreening() {
    if (!validateStep(1)) {
        step.value = 1;
        return;
    }

    submitting.value = true;
    apiError.value = "";

    try {
        const { data } = await predict(numericPayload.value);
        emit("submitted", {
            patient: numericPayload.value,
            result: data,
        });
    } catch (error) {
        if (error.response?.status === 400) {
            const backendMessages = error.response?.data?.messages;
            const joinedMessages = Array.isArray(backendMessages)
                ? backendMessages.join(" ")
                : "";
            const backendMessage =
                error.response?.data?.message ??
                error.response?.data?.error ??
                "";
            apiError.value =
                joinedMessages ||
                backendMessage ||
                "The screening data is outside accepted limits. Please review age, weight, and height.";
        } else {
            apiError.value =
                "The prediction request could not be completed. Please try again.";
        }
    } finally {
        submitting.value = false;
    }
}
</script>

<template>
    <div
        class="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4"
    >
        <div
            class="w-full max-w-3xl rounded-2xl border border-gray-200 bg-white p-6 shadow-lg"
        >
            <div class="flex items-start justify-between">
                <div>
                    <h2 class="text-xl font-semibold text-gray-900">
                        Child Screening (WHO-aligned)
                    </h2>
                    <p class="mt-1 text-sm text-gray-600">
                        Enter basic measurements and clinical flags to run AI
                        prediction.
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
                class="mt-4 rounded-lg border border-gray-200 bg-gray-50 px-4 py-3 text-sm text-gray-700"
            >
                <span v-if="step === 1">Step 1 of 2: Basic Information</span>
                <span v-else>Step 2 of 2: Clinical Factors</span>
                <span class="ml-2 text-gray-500"
                    >Progress: {{ progress }}%</span
                >
            </div>

            <form class="mt-6 grid gap-5" @submit.prevent="submitScreening">
                <template v-if="step === 1">
                    <div class="grid gap-2">
                        <label class="text-sm font-medium text-gray-700"
                            >Patient Name</label
                        >
                        <input
                            v-model="form.patient_name"
                            type="text"
                            placeholder="Full name"
                            class="rounded-lg border border-gray-300 px-4 py-2 text-sm text-gray-900 focus:border-[#10B981] focus:outline-none focus:ring-2 focus:ring-[#10B981]/20"
                        />
                        <small
                            class="text-sm text-red-600"
                            v-if="fieldErrors.patient_name"
                            >{{ fieldErrors.patient_name }}</small
                        >
                    </div>

                    <div class="grid gap-2">
                        <label class="text-sm font-medium text-gray-700"
                            >Age (months)</label
                        >
                        <input
                            v-model="form.age_months"
                            type="number"
                            min="0"
                            max="60"
                            placeholder="0 - 60"
                            class="rounded-lg border border-gray-300 px-4 py-2 text-sm text-gray-900 focus:border-[#10B981] focus:outline-none focus:ring-2 focus:ring-[#10B981]/20"
                        />
                        <small
                            class="text-sm text-red-600"
                            v-if="fieldErrors.age_months"
                            >{{ fieldErrors.age_months }}</small
                        >
                    </div>

                    <div class="grid gap-2">
                        <label class="text-sm font-medium text-gray-700"
                            >Gender</label
                        >
                        <select
                            v-model="form.gender"
                            class="rounded-lg border border-gray-300 px-4 py-2 text-sm text-gray-900 focus:border-[#10B981] focus:outline-none focus:ring-2 focus:ring-[#10B981]/20"
                        >
                            <option value="" disabled>Select</option>
                            <option value="Male">Male</option>
                            <option value="Female">Female</option>
                        </select>
                        <small
                            class="text-sm text-red-600"
                            v-if="fieldErrors.gender"
                            >{{ fieldErrors.gender }}</small
                        >
                    </div>

                    <div class="grid gap-2">
                        <label class="text-sm font-medium text-gray-700"
                            >Weight (kg)</label
                        >
                        <input
                            v-model="form.weight_kg"
                            type="number"
                            min="1.5"
                            max="30"
                            step="0.1"
                            placeholder="e.g. 11.4"
                            class="rounded-lg border border-gray-300 px-4 py-2 text-sm text-gray-900 focus:border-[#10B981] focus:outline-none focus:ring-2 focus:ring-[#10B981]/20"
                        />
                        <small
                            class="text-sm text-red-600"
                            v-if="fieldErrors.weight_kg"
                            >{{ fieldErrors.weight_kg }}</small
                        >
                    </div>

                    <div class="grid gap-2">
                        <label class="text-sm font-medium text-gray-700"
                            >Height (cm)</label
                        >
                        <input
                            v-model="form.height_cm"
                            type="number"
                            min="45"
                            max="125"
                            step="0.1"
                            placeholder="e.g. 83.2"
                            class="rounded-lg border border-gray-300 px-4 py-2 text-sm text-gray-900 focus:border-[#10B981] focus:outline-none focus:ring-2 focus:ring-[#10B981]/20"
                        />
                        <small
                            class="text-sm text-red-600"
                            v-if="fieldErrors.height_cm"
                            >{{ fieldErrors.height_cm }}</small
                        >
                    </div>
                </template>

                <template v-else>
                    <div class="grid gap-2">
                        <label class="text-sm font-medium text-gray-700"
                            >Clinical Risk Factors</label
                        >
                        <div class="flex flex-wrap gap-4 text-sm text-gray-700">
                            <label class="inline-flex items-center gap-2">
                                <input
                                    v-model="form.diarrhea"
                                    type="checkbox"
                                    class="h-4 w-4 rounded border-gray-300 text-[#10B981]"
                                />
                                Diarrhea
                            </label>
                            <label class="inline-flex items-center gap-2">
                                <input
                                    v-model="form.anemia"
                                    type="checkbox"
                                    class="h-4 w-4 rounded border-gray-300 text-[#10B981]"
                                />
                                Anemia
                            </label>
                            <label class="inline-flex items-center gap-2">
                                <input
                                    v-model="form.malaria"
                                    type="checkbox"
                                    class="h-4 w-4 rounded border-gray-300 text-[#10B981]"
                                />
                                Malaria
                            </label>
                        </div>
                    </div>

                    <div
                        class="rounded-xl border border-gray-200 bg-gray-50 p-4"
                    >
                        <h3 class="text-sm font-semibold text-gray-900">
                            Screening Summary
                        </h3>
                        <p class="mt-1 text-sm text-gray-600">
                            {{ form.patient_name || "Child" }} •
                            {{ form.gender || "Gender" }} •
                            {{ form.age_months || "--" }} months
                        </p>
                        <div class="mt-4 grid gap-3 sm:grid-cols-3">
                            <div
                                class="rounded-lg border border-gray-200 bg-white p-3"
                            >
                                <p class="text-xs text-gray-500">Weight</p>
                                <p class="text-sm font-semibold text-gray-900">
                                    {{ form.weight_kg || "--" }} kg
                                </p>
                            </div>
                            <div
                                class="rounded-lg border border-gray-200 bg-white p-3"
                            >
                                <p class="text-xs text-gray-500">Height</p>
                                <p class="text-sm font-semibold text-gray-900">
                                    {{ form.height_cm || "--" }} cm
                                </p>
                            </div>
                            <div
                                class="rounded-lg border border-gray-200 bg-white p-3"
                            >
                                <p class="text-xs text-gray-500">BMI</p>
                                <p class="text-sm font-semibold text-gray-900">
                                    {{
                                        form.weight_kg && form.height_cm
                                            ? (
                                                  form.weight_kg /
                                                  Math.pow(
                                                      form.height_cm / 100,
                                                      2,
                                                  )
                                              ).toFixed(1)
                                            : "--"
                                    }}
                                </p>
                            </div>
                        </div>
                    </div>
                </template>

                <div
                    v-if="apiError"
                    class="rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700"
                >
                    {{ apiError }}
                </div>

                <div class="flex flex-wrap justify-end gap-3">
                    <button
                        v-if="step === 2"
                        class="rounded-lg border border-gray-200 px-4 py-2 text-sm font-semibold text-gray-700 transition hover:text-gray-900"
                        type="button"
                        @click="previousStep"
                    >
                        Back
                    </button>
                    <button
                        v-if="step === 1"
                        class="rounded-lg bg-[#10B981] px-4 py-2 text-sm font-semibold text-white transition hover:bg-[#0EA371]"
                        type="button"
                        @click="nextStep"
                    >
                        Continue
                    </button>
                    <button
                        v-else
                        class="rounded-lg bg-[#10B981] px-4 py-2 text-sm font-semibold text-white transition hover:bg-[#0EA371] disabled:cursor-not-allowed disabled:opacity-70"
                        type="submit"
                        :disabled="submitting"
                    >
                        {{ submitting ? "Running..." : "Run AI Prediction" }}
                    </button>
                </div>
            </form>
        </div>
    </div>
</template>
