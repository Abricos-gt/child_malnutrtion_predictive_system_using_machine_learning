<script setup>
import { computed, reactive, ref } from "vue";
import {
    registerPatient,
    getPatientDetails,
    searchPatients,
    predict,
} from "../services/api";

const emit = defineEmits(["close", "submitted"]);

const step = ref(1); // 1: Patient, 2: Screening
const submitting = ref(false);
const apiError = ref("");
const fieldErrors = reactive({});

const searchQuery = ref("");
const searchResults = ref([]);
const searching = ref(false);
const selectedPatient = ref(null);

const registerMode = ref(false);
const registering = ref(false);
const registerSuccess = ref("");

const patientForm = reactive({
    name: "",
    parent_name: "",
    dob: "",
    gender: "",
    address: "",
    phone: "",
});

const screeningForm = reactive({
    patient_id: "",
    weight_kg: "",
    height_cm: "",
    diarrhea: false,
    anemia: false,
    malaria: false,
});

const patientAgeMonths = computed(() => {
    return selectedPatient.value?.identity?.current_age_months ?? "";
});

const patientDisplayName = computed(() => {
    return selectedPatient.value?.identity?.name ?? "";
});

function clearFieldErrors() {
    Object.keys(fieldErrors).forEach((key) => {
        delete fieldErrors[key];
    });
}

async function runSearch() {
    if (!searchQuery.value.trim()) {
        searchResults.value = [];
        return;
    }

    searching.value = true;
    try {
        const { data } = await searchPatients(searchQuery.value.trim());
        searchResults.value = Array.isArray(data) ? data : [];
    } catch {
        searchResults.value = [];
    } finally {
        searching.value = false;
    }
}

async function selectPatient(patient) {
    searchResults.value = [];
    searchQuery.value = "";
    try {
        const { data } = await getPatientDetails(patient.id);
        selectedPatient.value = data;
        screeningForm.patient_id = data.identity.id;
    } catch (error) {
        apiError.value =
            error.response?.data?.message || "Unable to load patient details.";
    }
}

async function registerNewPatient() {
    clearFieldErrors();
    apiError.value = "";
    registerSuccess.value = "";

    if (!patientForm.name.trim()) fieldErrors.name = "Child name is required.";
    if (!patientForm.parent_name.trim())
        fieldErrors.parent_name = "Parent name is required.";
    if (!patientForm.dob) fieldErrors.dob = "Date of birth is required.";
    if (!patientForm.gender) fieldErrors.gender = "Gender is required.";

    if (Object.keys(fieldErrors).length) return;

    registering.value = true;
    try {
        const { data } = await registerPatient({
            name: patientForm.name.trim(),
            parent_name: patientForm.parent_name.trim(),
            dob: patientForm.dob,
            gender: patientForm.gender,
            address: patientForm.address.trim(),
            phone: patientForm.phone.trim(),
        });
        registerSuccess.value = "Patient registered successfully.";
        const patientId = data.patient_id;
        if (patientId) {
            const detail = await getPatientDetails(patientId);
            selectedPatient.value = detail.data;
            screeningForm.patient_id = patientId;
            step.value = 2;
        }
    } catch (error) {
        apiError.value =
            error.response?.data?.message ||
            error.response?.data?.error ||
            "Patient registration failed.";
    } finally {
        registering.value = false;
    }
}

function goToScreening() {
    apiError.value = "";
    if (!screeningForm.patient_id) {
        apiError.value = "Select or register a patient first.";
        return;
    }
    step.value = 2;
}

function goBackToPatient() {
    apiError.value = "";
    step.value = 1;
}

async function submitScreening() {
    clearFieldErrors();
    apiError.value = "";

    if (!screeningForm.patient_id) {
        apiError.value = "Missing patient ID.";
        return;
    }

    const weight = Number(screeningForm.weight_kg);
    const height = Number(screeningForm.height_cm);

    if (!Number.isFinite(weight) || weight < 2 || weight > 30) {
        fieldErrors.weight_kg = "Weight must be between 2 and 30 kg.";
    }

    if (!Number.isFinite(height) || height < 45 || height > 125) {
        fieldErrors.height_cm = "Height must be between 45 and 125 cm.";
    }

    if (Object.keys(fieldErrors).length) return;

    submitting.value = true;
    try {
        const { data } = await predict({
            patient_id: screeningForm.patient_id,
            weight_kg: weight,
            height_cm: height,
            diarrhea: screeningForm.diarrhea ? 1 : 0,
            anemia: screeningForm.anemia ? 1 : 0,
            malaria: screeningForm.malaria ? 1 : 0,
        });

        emit("submitted", {
            patient: {
                patient_id: screeningForm.patient_id,
                patient_name: patientDisplayName.value,
                age_months: patientAgeMonths.value,
                gender: selectedPatient.value?.identity?.gender,
                weight_kg: weight,
                height_cm: height,
            },
            result: data,
        });
    } catch (error) {
        apiError.value =
            error.response?.data?.message ||
            error.response?.data?.error ||
            "The prediction request failed. Please try again.";
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
            class="w-full max-w-4xl rounded-2xl border border-gray-200 bg-white p-6 shadow-lg"
        >
            <div class="flex items-start justify-between">
                <div>
                    <h2 class="text-xl font-semibold text-gray-900">
                        Child Screening
                    </h2>
                    <p class="mt-1 text-sm text-gray-600">
                        Register or select a child, then record screening
                        measurements.
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
                v-if="apiError"
                class="mt-4 rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700"
            >
                {{ apiError }}
            </div>

            <div class="mt-4 flex gap-3 text-sm font-medium text-gray-600">
                <button
                    type="button"
                    class="rounded-full border px-4 py-1"
                    :class="
                        step === 1
                            ? 'border-[#10B981] text-[#10B981]'
                            : 'border-gray-200'
                    "
                >
                    Patient
                </button>
                <button
                    type="button"
                    class="rounded-full border px-4 py-1"
                    :class="
                        step === 2
                            ? 'border-[#10B981] text-[#10B981]'
                            : 'border-gray-200'
                    "
                >
                    Screening
                </button>
            </div>

            <!-- Step 1: Patient -->
            <div v-if="step === 1" class="mt-6 grid gap-6 lg:grid-cols-2">
                <div class="rounded-xl border border-gray-200 bg-gray-50 p-4">
                    <div class="flex items-center justify-between">
                        <h3 class="text-sm font-semibold text-gray-900">
                            Search Patient
                        </h3>
                        <button
                            type="button"
                            class="text-xs font-semibold text-[#1E3A8A]"
                            @click="registerMode = !registerMode"
                        >
                            {{
                                registerMode
                                    ? "Hide Registration"
                                    : "Register New"
                            }}
                        </button>
                    </div>

                    <div class="mt-3 grid gap-2">
                        <input
                            v-model="searchQuery"
                            type="text"
                            class="rounded-lg border border-gray-300 px-3 py-2 text-sm text-gray-900 focus:border-[#10B981] focus:outline-none focus:ring-2 focus:ring-[#10B981]/20"
                            placeholder="Search by name or patient ID"
                            @input="runSearch"
                        />
                        <div v-if="searching" class="text-xs text-gray-500">
                            Searching...
                        </div>
                        <ul
                            v-if="searchResults.length"
                            class="max-h-40 overflow-auto rounded-lg border border-gray-200 bg-white text-sm"
                        >
                            <li
                                v-for="patient in searchResults"
                                :key="patient.id"
                                class="cursor-pointer border-b border-gray-100 px-3 py-2 hover:bg-gray-50"
                                @click="selectPatient(patient)"
                            >
                                <div class="font-medium text-gray-900">
                                    {{ patient.name }}
                                </div>
                                <div class="text-xs text-gray-500">
                                    {{ patient.id }} • {{ patient.gender }} •
                                    {{ patient.dob }}
                                </div>
                            </li>
                        </ul>
                    </div>

                    <div
                        v-if="selectedPatient"
                        class="mt-4 rounded-lg border border-gray-200 bg-white p-3 text-sm text-gray-700"
                    >
                        <p class="font-semibold text-gray-900">
                            Selected Patient
                        </p>
                        <p class="mt-1">
                            {{ selectedPatient.identity.name }} •
                            {{ selectedPatient.identity.gender }} •
                            {{
                                selectedPatient.identity.current_age_months
                            }}
                            months
                        </p>
                        <p class="text-xs text-gray-500">
                            ID: {{ selectedPatient.identity.id }}
                        </p>
                    </div>
                </div>

                <div
                    v-if="registerMode"
                    class="rounded-xl border border-gray-200 bg-white p-4"
                >
                    <h3 class="text-sm font-semibold text-gray-900">
                        Register New Patient
                    </h3>
                    <div class="mt-3 grid gap-3">
                        <div>
                            <label class="text-xs font-medium text-gray-700"
                                >Child Name</label
                            >
                            <input
                                v-model="patientForm.name"
                                type="text"
                                class="mt-1 w-full rounded-lg border border-gray-300 px-3 py-2 text-sm"
                                placeholder="Child full name"
                            />
                            <small
                                class="text-xs text-red-600"
                                v-if="fieldErrors.name"
                                >{{ fieldErrors.name }}</small
                            >
                        </div>
                        <div>
                            <label class="text-xs font-medium text-gray-700"
                                >Parent Name</label
                            >
                            <input
                                v-model="patientForm.parent_name"
                                type="text"
                                class="mt-1 w-full rounded-lg border border-gray-300 px-3 py-2 text-sm"
                                placeholder="Parent/guardian name"
                            />
                            <small
                                class="text-xs text-red-600"
                                v-if="fieldErrors.parent_name"
                                >{{ fieldErrors.parent_name }}</small
                            >
                        </div>
                        <div class="grid gap-3 sm:grid-cols-2">
                            <div>
                                <label class="text-xs font-medium text-gray-700"
                                    >Date of Birth</label
                                >
                                <input
                                    v-model="patientForm.dob"
                                    type="date"
                                    class="mt-1 w-full rounded-lg border border-gray-300 px-3 py-2 text-sm"
                                />
                                <small
                                    class="text-xs text-red-600"
                                    v-if="fieldErrors.dob"
                                    >{{ fieldErrors.dob }}</small
                                >
                            </div>
                            <div>
                                <label class="text-xs font-medium text-gray-700"
                                    >Gender</label
                                >
                                <select
                                    v-model="patientForm.gender"
                                    class="mt-1 w-full rounded-lg border border-gray-300 px-3 py-2 text-sm"
                                >
                                    <option value="" disabled>Select</option>
                                    <option value="Male">Male</option>
                                    <option value="Female">Female</option>
                                </select>
                                <small
                                    class="text-xs text-red-600"
                                    v-if="fieldErrors.gender"
                                    >{{ fieldErrors.gender }}</small
                                >
                            </div>
                        </div>
                        <div>
                            <label class="text-xs font-medium text-gray-700"
                                >Address</label
                            >
                            <input
                                v-model="patientForm.address"
                                type="text"
                                class="mt-1 w-full rounded-lg border border-gray-300 px-3 py-2 text-sm"
                                placeholder="Address or village"
                            />
                        </div>
                        <div>
                            <label class="text-xs font-medium text-gray-700"
                                >Phone</label
                            >
                            <input
                                v-model="patientForm.phone"
                                type="text"
                                class="mt-1 w-full rounded-lg border border-gray-300 px-3 py-2 text-sm"
                                placeholder="Phone number"
                            />
                        </div>

                        <button
                            class="mt-2 w-full rounded-lg bg-[#10B981] px-4 py-2 text-sm font-semibold text-white transition hover:bg-[#0EA371] disabled:opacity-70"
                            type="button"
                            :disabled="registering"
                            @click="registerNewPatient"
                        >
                            {{
                                registering
                                    ? "Registering..."
                                    : "Register Patient"
                            }}
                        </button>

                        <p
                            v-if="registerSuccess"
                            class="text-xs text-emerald-700"
                        >
                            {{ registerSuccess }}
                        </p>
                    </div>
                </div>
            </div>

            <!-- Step 2: Screening -->
            <div v-if="step === 2" class="mt-6 grid gap-6 lg:grid-cols-2">
                <div class="rounded-xl border border-gray-200 bg-gray-50 p-4">
                    <h3 class="text-sm font-semibold text-gray-900">
                        Selected Patient
                    </h3>
                    <p class="mt-2 text-sm text-gray-700">
                        {{ patientDisplayName || "—" }}
                    </p>
                    <p class="text-xs text-gray-500">
                        Age: {{ patientAgeMonths || "—" }} months • Gender:
                        {{ selectedPatient?.identity?.gender || "—" }}
                    </p>
                </div>

                <div class="rounded-xl border border-gray-200 bg-white p-4">
                    <h3 class="text-sm font-semibold text-gray-900">
                        Screening Measurements
                    </h3>
                    <div class="mt-3 grid gap-3">
                        <div>
                            <label class="text-xs font-medium text-gray-700"
                                >Weight (kg)</label
                            >
                            <input
                                v-model="screeningForm.weight_kg"
                                type="number"
                                class="mt-1 w-full rounded-lg border border-gray-300 px-3 py-2 text-sm"
                                placeholder="e.g. 9.8"
                            />
                            <small
                                class="text-xs text-red-600"
                                v-if="fieldErrors.weight_kg"
                                >{{ fieldErrors.weight_kg }}</small
                            >
                        </div>
                        <div>
                            <label class="text-xs font-medium text-gray-700"
                                >Height (cm)</label
                            >
                            <input
                                v-model="screeningForm.height_cm"
                                type="number"
                                class="mt-1 w-full rounded-lg border border-gray-300 px-3 py-2 text-sm"
                                placeholder="e.g. 82"
                            />
                            <small
                                class="text-xs text-red-600"
                                v-if="fieldErrors.height_cm"
                                >{{ fieldErrors.height_cm }}</small
                            >
                        </div>
                        <div>
                            <label class="text-xs font-medium text-gray-700"
                                >Clinical Flags</label
                            >
                            <div
                                class="mt-2 flex flex-wrap gap-4 text-sm text-gray-700"
                            >
                                <label class="inline-flex items-center gap-2">
                                    <input
                                        v-model="screeningForm.diarrhea"
                                        type="checkbox"
                                        class="h-4 w-4 rounded border-gray-300 text-[#10B981]"
                                    />
                                    Diarrhea
                                </label>
                                <label class="inline-flex items-center gap-2">
                                    <input
                                        v-model="screeningForm.anemia"
                                        type="checkbox"
                                        class="h-4 w-4 rounded border-gray-300 text-[#10B981]"
                                    />
                                    Anemia
                                </label>
                                <label class="inline-flex items-center gap-2">
                                    <input
                                        v-model="screeningForm.malaria"
                                        type="checkbox"
                                        class="h-4 w-4 rounded border-gray-300 text-[#10B981]"
                                    />
                                    Malaria
                                </label>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            <div class="mt-6 flex flex-wrap justify-end gap-3">
                <button
                    v-if="step === 1"
                    class="rounded-lg border border-gray-200 px-4 py-2 text-sm font-semibold text-gray-700 transition hover:text-gray-900"
                    type="button"
                    @click="goToScreening"
                >
                    Continue to Screening
                </button>
                <button
                    v-if="step === 2"
                    class="rounded-lg border border-gray-200 px-4 py-2 text-sm font-semibold text-gray-700 transition hover:text-gray-900"
                    type="button"
                    @click="goBackToPatient"
                >
                    Back
                </button>
                <button
                    v-if="step === 2"
                    class="rounded-lg bg-[#10B981] px-4 py-2 text-sm font-semibold text-white transition hover:bg-[#0EA371] disabled:opacity-70"
                    type="button"
                    :disabled="submitting"
                    @click="submitScreening"
                >
                    {{ submitting ? "Running..." : "Run Prediction" }}
                </button>
            </div>
        </div>
    </div>
</template>
