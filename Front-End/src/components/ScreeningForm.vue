<script setup>
import { computed, reactive, ref } from "vue";
import {
    registerPatient,
    getPatientDetails,
    searchPatients,
    predict,
} from "../services/api";

const emit = defineEmits(["close", "submitted"]);

const step = ref(1);
const submitting = ref(false);
const apiError = ref("");
const fieldErrors = reactive({});

const patientSearchQuery = ref("");
const searchResults = ref([]);
const searching = ref(false);
const lookingUpPatient = ref(false);
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
    age_months: "",
    weight_kg: "",
    height_cm: "",
    diarrhea: false,
    anemia: false,
    malaria: false,
});

const patientAgeMonths = computed(() => {
    if (screeningForm.age_months !== "") {
        return screeningForm.age_months;
    }

    const dob = selectedPatient.value?.dob;
    if (!dob) return "";

    return calculateAgeMonths(dob);
});

const patientDisplayName = computed(() => {
    return selectedPatient.value?.name ?? "";
});

function clearFieldErrors() {
    Object.keys(fieldErrors).forEach((key) => {
        delete fieldErrors[key];
    });
}

function calculateAgeMonths(dateOfBirth) {
    const dob = new Date(dateOfBirth);
    if (Number.isNaN(dob.getTime())) return "";

    const now = new Date();
    let months =
        (now.getFullYear() - dob.getFullYear()) * 12 +
        (now.getMonth() - dob.getMonth());

    if (now.getDate() < dob.getDate()) {
        months -= 1;
    }

    return Math.max(months, 0);
}

async function runSearch() {
    const query = patientSearchQuery.value.trim();

    if (!query) {
        searchResults.value = [];
        return;
    }

    searching.value = true;
    try {
        const { data } = await searchPatients(query);
        searchResults.value = Array.isArray(data) ? data : [];
    } catch {
        searchResults.value = [];
    } finally {
        searching.value = false;
    }
}

async function lookupPatient() {
    const patientId = patientSearchQuery.value.trim();

    if (!patientId) {
        apiError.value = "Enter a patient ID to load the child record.";
        return;
    }

    apiError.value = "";
    lookingUpPatient.value = true;

    try {
        const { data } = await getPatientDetails(patientId);
        selectedPatient.value = data;
        screeningForm.patient_id = patientId;
        screeningForm.age_months = calculateAgeMonths(data.dob);
        patientSearchQuery.value = data.name || patientId;
        searchResults.value = [];
    } catch (error) {
        apiError.value =
            error.response?.data?.message ||
            error.response?.data?.error ||
            "Unable to load patient details.";
    } finally {
        lookingUpPatient.value = false;
    }
}

async function selectPatient(patient) {
    apiError.value = "";
    patientSearchQuery.value = patient.full_name;
    searchResults.value = [];
    selectedPatient.value = {
        name: patient.full_name,
        dob: patient.dob,
        gender: patient.gender,
    };
    screeningForm.patient_id = patient.id;
    screeningForm.age_months = calculateAgeMonths(patient.dob);
}

async function registerNewPatient() {
    clearFieldErrors();
    apiError.value = "";
    registerSuccess.value = "";

    if (!patientForm.name.trim()) fieldErrors.name = "Child name is required.";
    if (!patientForm.parent_name.trim()) {
        fieldErrors.parent_name = "Parent name is required.";
    }
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
            patientSearchQuery.value = detail.data.name || patientId;
            screeningForm.patient_id = patientId;
            screeningForm.age_months = calculateAgeMonths(detail.data.dob);
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
        apiError.value = "Load or register a patient first.";
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

    const ageMonths = Number(screeningForm.age_months);
    const weight = Number(screeningForm.weight_kg);
    const height = Number(screeningForm.height_cm);

    if (!Number.isInteger(ageMonths) || ageMonths < 0 || ageMonths > 60) {
        fieldErrors.age_months =
            "Age must be a whole number between 0 and 60 months.";
    }

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
            age_months: ageMonths,
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
                age_months: ageMonths,
                gender: selectedPatient.value?.gender,
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
                        Register or load a child, then record screening
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

            <div v-if="step === 1" class="mt-6 grid gap-6 lg:grid-cols-2">
                <div class="rounded-xl border border-gray-200 bg-gray-50 p-4">
                    <div class="flex items-center justify-between">
                        <h3 class="text-sm font-semibold text-gray-900">
                            Load Existing Patient
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
                            v-model="patientSearchQuery"
                            type="text"
                            class="rounded-lg border border-gray-300 px-3 py-2 text-sm text-gray-900 focus:border-[#10B981] focus:outline-none focus:ring-2 focus:ring-[#10B981]/20"
                            placeholder="Search by child name, patient ID, or parent phone"
                            @input="runSearch"
                        />
                        <div v-if="searching" class="text-xs text-gray-500">
                            Searching...
                        </div>
                        <ul
                            v-else-if="searchResults.length"
                            class="max-h-56 overflow-auto rounded-lg border border-gray-200 bg-white text-sm"
                        >
                            <li
                                v-for="patient in searchResults"
                                :key="patient.id"
                                class="cursor-pointer border-b border-gray-100 px-3 py-3 hover:bg-gray-50"
                                @click="selectPatient(patient)"
                            >
                                <div class="font-medium text-gray-900">
                                    {{ patient.full_name }}
                                </div>
                                <div class="mt-1 text-xs text-gray-500">
                                    ID: {{ patient.id }} • {{ patient.gender }} •
                                    DOB: {{ patient.dob }}
                                </div>
                                <div class="mt-1 text-xs text-gray-500">
                                    Parent: {{ patient.parent_name || "-" }} •
                                    Phone: {{ patient.parent_phone || "-" }}
                                </div>
                                <div class="mt-1 text-xs text-gray-500">
                                    Last status: {{ patient.last_status || "New Patient" }}
                                </div>
                            </li>
                        </ul>
                        <button
                            v-if="!selectedPatient || patientSearchQuery === screeningForm.patient_id"
                            type="button"
                            class="rounded-lg border border-gray-200 px-4 py-2 text-sm font-semibold text-gray-700 transition hover:text-gray-900 disabled:opacity-70"
                            :disabled="lookingUpPatient"
                            @click="lookupPatient"
                        >
                            {{
                                lookingUpPatient
                                    ? "Loading patient..."
                                    : "Load By ID"
                            }}
                        </button>
                        <p class="text-xs text-gray-500">
                            Search by child name, patient ID, or parent phone.
                            You can also paste an exact patient ID and load it
                            directly.
                        </p>
                    </div>

                    <div
                        v-if="selectedPatient"
                        class="mt-4 rounded-lg border border-gray-200 bg-white p-3 text-sm text-gray-700"
                    >
                        <p class="font-semibold text-gray-900">
                            Selected Patient
                        </p>
                        <p class="mt-1">
                            {{ selectedPatient.name }} •
                            {{ selectedPatient.gender }} •
                            {{ patientAgeMonths }} months
                        </p>
                        <p class="text-xs text-gray-500">
                            ID: {{ screeningForm.patient_id }}
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
                                v-if="fieldErrors.name"
                                class="text-xs text-red-600"
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
                                v-if="fieldErrors.parent_name"
                                class="text-xs text-red-600"
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
                                    v-if="fieldErrors.dob"
                                    class="text-xs text-red-600"
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
                                    v-if="fieldErrors.gender"
                                    class="text-xs text-red-600"
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

            <div v-if="step === 2" class="mt-6 grid gap-6 lg:grid-cols-2">
                <div class="rounded-xl border border-gray-200 bg-gray-50 p-4">
                    <h3 class="text-sm font-semibold text-gray-900">
                        Selected Patient
                    </h3>
                    <p class="mt-2 text-sm text-gray-700">
                        {{ patientDisplayName || "-" }}
                    </p>
                    <p class="text-xs text-gray-500">
                        Age: {{ patientAgeMonths || "-" }} months • Gender:
                        {{ selectedPatient?.gender || "-" }}
                    </p>
                </div>

                <div class="rounded-xl border border-gray-200 bg-white p-4">
                    <h3 class="text-sm font-semibold text-gray-900">
                        Screening Measurements
                    </h3>
                    <div class="mt-3 grid gap-3">
                        <div>
                            <label class="text-xs font-medium text-gray-700"
                                >Age at Screening (months)</label
                            >
                            <input
                                v-model="screeningForm.age_months"
                                type="number"
                                min="0"
                                max="60"
                                class="mt-1 w-full rounded-lg border border-gray-300 px-3 py-2 text-sm"
                                placeholder="e.g. 18"
                            />
                            <small
                                v-if="fieldErrors.age_months"
                                class="text-xs text-red-600"
                                >{{ fieldErrors.age_months }}</small
                            >
                            <p class="mt-1 text-xs text-gray-500">
                                Auto-filled from date of birth. Adjust if needed
                                for the visit date.
                            </p>
                        </div>
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
                                v-if="fieldErrors.weight_kg"
                                class="text-xs text-red-600"
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
                                v-if="fieldErrors.height_cm"
                                class="text-xs text-red-600"
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
