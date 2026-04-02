import './style.css'

const app = document.querySelector('#app')

app.innerHTML = `
  <div class="min-h-screen bg-slate-100 px-4 py-8 text-slate-900 sm:px-6">
    <div class="mx-auto max-w-5xl">
      <header class="mb-8 rounded-[28px] border border-slate-200 bg-white p-6 shadow-sm sm:p-8">
        <div class="flex flex-col gap-6 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <div class="inline-flex items-center gap-2 rounded-full bg-sky-50 px-3 py-1 text-sm font-semibold text-sky-700">
              <i class="fa-solid fa-heart-pulse"></i>
              Child Nutrition Care
            </div>
            <h1 class="mt-4 font-['Plus_Jakarta_Sans'] text-3xl font-bold tracking-tight text-slate-950 sm:text-4xl">
              Proactive Child Malnutrition Early Warning System
            </h1>
            <p class="mt-3 max-w-2xl text-base leading-7 text-slate-600">
              A simple website for screening risk, understanding the reason behind the score, and getting a clear next recommendation.
            </p>
          </div>

          <div class="flex flex-col gap-3 sm:w-[220px]">
            <button class="rounded-2xl bg-slate-900 px-5 py-3 font-semibold text-white transition hover:bg-slate-800">
              Sign In
            </button>
            <button class="rounded-2xl border border-slate-200 bg-white px-5 py-3 font-semibold text-slate-700 transition hover:bg-slate-50">
              Register
            </button>
          </div>
        </div>
      </header>

      <main class="grid gap-6 lg:grid-cols-[0.95fr,1.05fr]">
        <section class="rounded-[28px] border border-slate-200 bg-white p-6 shadow-sm">
          <div class="mb-6">
            <h2 class="font-['Plus_Jakarta_Sans'] text-2xl font-bold text-slate-950">Patient Input</h2>
            <p class="mt-2 text-sm leading-6 text-slate-500">
              Enter a few key details to get a quick risk estimate.
            </p>
          </div>

          <form id="risk-form" class="grid gap-4">
            <label class="block">
              <span class="mb-2 block text-sm font-semibold text-slate-700">Age (months)</span>
              <input name="age" type="number" min="0" max="60" value="18" class="w-full rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 outline-none transition focus:border-sky-400 focus:bg-white focus:ring-4 focus:ring-sky-100" />
            </label>

            <label class="block">
              <span class="mb-2 block text-sm font-semibold text-slate-700">Weight (kg)</span>
              <input name="weight" type="number" min="1" max="30" step="0.1" value="7.2" class="w-full rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 outline-none transition focus:border-sky-400 focus:bg-white focus:ring-4 focus:ring-sky-100" />
            </label>

            <label class="block">
              <span class="mb-2 block text-sm font-semibold text-slate-700">Height (cm)</span>
              <input name="height" type="number" min="30" max="140" step="0.1" value="74" class="w-full rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 outline-none transition focus:border-sky-400 focus:bg-white focus:ring-4 focus:ring-sky-100" />
            </label>

            <label class="block">
              <span class="mb-2 block text-sm font-semibold text-slate-700">Previous Score</span>
              <input name="previousScore" type="number" min="0" max="100" value="34" class="w-full rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 outline-none transition focus:border-sky-400 focus:bg-white focus:ring-4 focus:ring-sky-100" />
            </label>

            <div class="grid gap-4 sm:grid-cols-2">
              <fieldset class="rounded-3xl border border-slate-200 p-4">
                <legend class="px-2 text-sm font-semibold text-slate-700">Malaria</legend>
                <div class="mt-3 flex gap-4">
                  <label class="flex items-center gap-2 text-sm text-slate-700">
                    <input type="radio" name="malaria" value="yes" />
                    Yes
                  </label>
                  <label class="flex items-center gap-2 text-sm text-slate-700">
                    <input type="radio" name="malaria" value="no" checked />
                    No
                  </label>
                </div>
              </fieldset>

              <fieldset class="rounded-3xl border border-slate-200 p-4">
                <legend class="px-2 text-sm font-semibold text-slate-700">Diarrhea</legend>
                <div class="mt-3 flex gap-4">
                  <label class="flex items-center gap-2 text-sm text-slate-700">
                    <input type="radio" name="diarrhea" value="yes" checked />
                    Yes
                  </label>
                  <label class="flex items-center gap-2 text-sm text-slate-700">
                    <input type="radio" name="diarrhea" value="no" />
                    No
                  </label>
                </div>
              </fieldset>
            </div>

            <button type="submit" class="mt-2 rounded-2xl bg-sky-600 px-5 py-3 font-semibold text-white transition hover:bg-sky-500">
              Check Risk
            </button>
          </form>
        </section>

        <section class="grid gap-6">
          <article class="rounded-[28px] border border-slate-200 bg-white p-6 shadow-sm">
            <div class="flex items-center justify-between gap-4">
              <div>
                <h2 class="font-['Plus_Jakarta_Sans'] text-2xl font-bold text-slate-950">Result</h2>
                <p class="mt-2 text-sm text-slate-500">Current screening outcome.</p>
              </div>
              <div id="status-badge" class="rounded-full bg-emerald-50 px-4 py-2 text-sm font-semibold text-emerald-700">
                Stable
              </div>
            </div>

            <div class="mt-6 rounded-3xl bg-slate-50 p-6 text-center">
              <p class="text-sm font-semibold uppercase tracking-[0.18em] text-slate-400">Danger Score</p>
              <p id="score-value" class="mt-3 font-['Plus_Jakarta_Sans'] text-6xl font-bold text-slate-950">12</p>
              <p id="score-range" class="mt-3 text-sm text-slate-500">0-14: Stable</p>
            </div>
          </article>

          <article class="rounded-[28px] border border-slate-200 bg-white p-6 shadow-sm">
            <h3 class="font-['Plus_Jakarta_Sans'] text-xl font-bold text-slate-950">Explanation</h3>
            <p class="mt-2 text-sm text-slate-500">Why the model gave this score.</p>
            <div id="drivers-list" class="mt-4 flex flex-wrap gap-3">
              <span class="rounded-full bg-slate-100 px-4 py-2 text-sm text-slate-700">Low age vulnerability</span>
              <span class="rounded-full bg-slate-100 px-4 py-2 text-sm text-slate-700">Diarrhea present</span>
            </div>
          </article>

          <article class="rounded-[28px] border border-slate-200 bg-white p-6 shadow-sm">
            <h3 class="font-['Plus_Jakarta_Sans'] text-xl font-bold text-slate-950">Recommendation</h3>
            <p class="mt-2 text-sm text-slate-500">Suggested next step based on the current score.</p>
            <div class="mt-4 rounded-3xl bg-amber-50 p-5">
              <p id="recommendation-text" class="text-sm leading-7 text-amber-900">
                Continue routine follow-up, support feeding guidance, and monitor progress at the next visit.
              </p>
            </div>
          </article>
        </section>
      </main>
    </div>
  </div>
`

const form = document.querySelector('#risk-form')
const scoreValue = document.querySelector('#score-value')
const scoreRange = document.querySelector('#score-range')
const statusBadge = document.querySelector('#status-badge')
const driversList = document.querySelector('#drivers-list')
const recommendationText = document.querySelector('#recommendation-text')

const statusConfig = {
  Stable: {
    badge: 'bg-emerald-50 text-emerald-700',
    range: '0-14: Stable',
    recommendation:
      'Continue routine follow-up, support feeding guidance, and monitor progress at the next visit.',
  },
  Monitor: {
    badge: 'bg-yellow-50 text-yellow-700',
    range: '15-39: Monitor',
    recommendation:
      'Increase follow-up frequency, review diet intake, and monitor symptoms closely.',
  },
  Warning: {
    badge: 'bg-orange-50 text-orange-700',
    range: '40-84: Warning',
    recommendation:
      'Begin proactive nutrition support, review for infection burden, and arrange prompt clinical follow-up.',
  },
  Critical: {
    badge: 'bg-rose-50 text-rose-700',
    range: '85-100: Critical',
    recommendation:
      'Start urgent therapeutic support and refer immediately for clinical management.',
  },
}

function clamp(value, min, max) {
  return Math.min(Math.max(value, min), max)
}

function getStatus(score) {
  if (score <= 14) return 'Stable'
  if (score <= 39) return 'Monitor'
  if (score <= 84) return 'Warning'
  return 'Critical'
}

function calculateModelOutput(values) {
  const heightInMeters = values.height / 100
  const bmi = values.weight / (heightInMeters * heightInMeters)

  let score = 10
  const drivers = []

  if (values.age <= 12) {
    score += 16
    drivers.push('Low age vulnerability')
  } else if (values.age <= 24) {
    score += 10
    drivers.push('Age under 24 months')
  }

  if (bmi < 12.5) {
    score += 38
    drivers.push('Very low BMI')
  } else if (bmi < 14) {
    score += 26
    drivers.push('Low BMI')
  }

  if (values.malaria) {
    score += 18
    drivers.push('Malaria present')
  }

  if (values.diarrhea) {
    score += 14
    drivers.push('Diarrhea present')
  }

  const trend = score - values.previousScore
  if (trend >= 15) drivers.push('Risk increased since last visit')
  if (trend <= -10) drivers.push('Risk improved since last visit')

  const finalScore = clamp(Math.round(score), 0, 100)

  return {
    danger_score: finalScore,
    status: getStatus(finalScore),
    top_drivers: drivers.slice(0, 3),
  }
}

function readFormValues() {
  const formData = new FormData(form)

  return {
    age: Number(formData.get('age')),
    previousScore: clamp(Number(formData.get('previousScore')), 0, 100),
    weight: Number(formData.get('weight')),
    height: Number(formData.get('height')),
    malaria: formData.get('malaria') === 'yes',
    diarrhea: formData.get('diarrhea') === 'yes',
  }
}

function updateUI(result) {
  const config = statusConfig[result.status]

  scoreValue.textContent = String(result.danger_score)
  scoreRange.textContent = config.range
  statusBadge.className = `rounded-full px-4 py-2 text-sm font-semibold ${config.badge}`
  statusBadge.textContent = result.status
  recommendationText.textContent = config.recommendation

  const items = result.top_drivers.length
    ? result.top_drivers
    : ['Current indicators remain within safer range']

  driversList.innerHTML = items
    .map(
      (driver) =>
        `<span class="rounded-full bg-slate-100 px-4 py-2 text-sm text-slate-700">${driver}</span>`,
    )
    .join('')
}

form.addEventListener('submit', (event) => {
  event.preventDefault()
  const values = readFormValues()
  const result = calculateModelOutput(values)
  updateUI(result)
})
