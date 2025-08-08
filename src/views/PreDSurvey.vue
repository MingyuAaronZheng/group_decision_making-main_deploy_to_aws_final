<template>
  <b-jumbotron header-level="5" class="survey-container">
    <div class="content-area"><div class="page-indicator text-center mb-1">Page: 3 / 9</div></div>
    <template v-slot:header>
      <h2 class="survey-title">Policy Statement Survey</h2>
    </template>

    <div class="content-area">
      <div v-for="(statement, index) in randomizedStatements" :key="statement.id" class="policy-statement-box mb-4">
        <b-card class="w-100">
          <div class="statement-header mb-2">
            <div class="statement-text highlight-statement">{{ statement.text }}</div>
          </div>
          <!-- Question 1: Extent of agreement -->
          <div class="question-block mb-3">
            <p class="mb-1 font-weight-bold">To what extent do you agree with this statement?</p>
            <b-form-radio-group
              v-model="responses[index].agreement"
              :name="'agreement_' + index"
              buttons
              button-variant="outline-black"
              size="md"
              class="agreement-options"
              @change="onFormInteraction"
            >
              <div class="agreement-wrapper">
                <div
                  v-for="(option, optIndex) in agreementScale"
                  :key="optIndex"
                  class="option-label-wrapper"
                >
                  <div class="option-label">
                    {{ getAgreementLabel(option.value) }}
                  </div>
                  <b-form-radio :value="option.value" class="custom-radio-button">
                    <!-- Empty text since we're only showing labels -->
                  </b-form-radio>
                </div>
              </div>
            </b-form-radio-group>
          </div>
          <!-- Importance Question -->
          <div class="question-block">
            <p class="mb-1 font-weight-bold">How personally important is this issue to you?</p>
            <b-form-radio-group
              v-model="responses[index].importance"
              :name="'importance_' + index"
              buttons
              button-variant="outline-black"
              size="md"
              class="agreement-options"
              @change="onFormInteraction"
            >
              <div class="agreement-wrapper">
                <div v-for="(option, optIndex) in importanceScale" :key="optIndex" class="option-label-wrapper">
                  <div class="option-label">{{ option.text }}</div>
                  <b-form-radio :value="option.value" class="custom-radio-button"></b-form-radio>
                </div>
              </div>
            </b-form-radio-group>
          </div>
        </b-card>
      </div>
    </div>
    <!-- Final submit button -->
    <div class="button-area">
      <b-button variant="primary" size="lg" @click="finalSubmit">
        <font-awesome-icon :icon="['fas', 'circle-check']" class="mr-2" />
        Submit
      </b-button>
    </div>

  </b-jumbotron>
</template>

<script>
import axios from 'axios'
import { notifyInactivity } from '@/plugins/notificationService.js'

export default {
  data () {
    const initialResponses = this.$store.state.masterStatements.map(() => ({
      agreement: null,
      importance: null
    }))
    return {
      // selected statements = master statements mapped to objects with id and text
      selectedStatements: this.$store.state.masterStatements.map((text, idx) => ({
        id: idx,
        text
      })),

      // Response data for each statement
      responses: initialResponses,

      // Agreement scale options
      agreementScale: [
        {text: '', value: -3},
        {text: '', value: -2},
        {text: '', value: -1},
        {text: '', value: 1},
        {text: '', value: 2},
        {text: '', value: 3}
      ],

      // Importance scale options
      importanceScale: [
        {text: 'Not at all important to me', value: 1},
        {text: 'Slightly important to me', value: 2},
        {text: 'Somewhat important to me', value: 3},
        {text: 'Moderately important to me', value: 4},
        {text: 'Important to me', value: 5},
        {text: 'Very important to me', value: 6},
        {text: 'Extremely important to me', value: 7}
      ],
      // Will hold randomized statements
      randomizedStatements: []
    }
  },
  mounted () {
    window.scrollTo(0, 0)
    // Initialize responses array with empty objects for each statement
    this.responses = this.selectedStatements.map(() => ({
      agreement: null,
      importance: null
    }))
    this.$store.commit('startInactivityCheck')
    window.addEventListener('show-inactivity-warning', this.showInactivityWarning)
    window.addEventListener('remove-inactive-user', this.handleInactiveUser)
  },
  watch: {
    selectedStatements: {
      handler (newVal) {
        if (newVal && newVal.length > 0) {
          this.randomizedStatements = this.shuffleArray(newVal)
          this.responses = newVal.map(() => ({ agreement: null, importance: null }))
        }
      },
      immediate: true,
      deep: true
    }
  },
  methods: {
    // Fisher-Yates shuffle
    shuffleArray (array) {
      const arr = array.slice()
      for (let i = arr.length - 1; i > 0; i--) {
        const j = Math.floor(Math.random() * (i + 1));
        [arr[i], arr[j]] = [arr[j], arr[i]]
      }
      return arr
    },
    getAgreementLabel (value) {
      switch (value) {
        case -3: return 'Strongly Disagree'
        case -2: return 'Disagree'
        case -1: return 'Somewhat Disagree'
        case 1: return 'Somewhat Agree'
        case 2: return 'Agree'
        case 3: return 'Strongly Agree'
        default: return ''
      }
    },

    // Final submit logic
    finalSubmit () {
      const incomplete = this.responses.some(r => r.agreement === null || r.importance === null)
      if (incomplete) {
        this.$alert('Please answer all questions before submitting.')
        return
      }
      // Prepare mapped responses: [{id, agreement, importance}]
      const mappedResponses = this.randomizedStatements.map((s, i) => ({
        statement_id: s.id,
        agreement: this.responses[i].agreement,
        importance: this.responses[i].importance
      }))
      const body = new FormData()
      body.append('subject_id', this.$store.state.subject_id)
      body.append('responses', JSON.stringify(mappedResponses))
      console.log('PreDSurvey responses:', mappedResponses)
      // Store the responses in frontend for later comparison with post-discussion survey
      this.$store.commit('setPreDiscussionResponses', mappedResponses)
      // Submit the data to the server
      axios
        .post(this.$server_url + 'Update_pre_discussion_survey', body)
        .then((response) => {
          if (response.data.success) {
            this.$router.push('/DiscussionInstructions')
          } else {
            alert(response.data.message)
          }
        })
        .catch(() => {
          alert('An error occurred while submitting. Please try again.')
        })
    },

    // Track activity on form interactions
    onFormInteraction () {
      this.$store.dispatch('recordActivity')
    },
    showInactivityWarning () {
      notifyInactivity(this.$bvToast, this.$store.state.test)
    },
    handleInactiveUser () {
      const body = new FormData()
      body.append('subject_id', this.$store.state.subject_id)
      axios.post(this.$server_url + 'terminate_participation', body)
        .then(() => {
          this.$router.push('/InactivityTerminatedParticipation')
        })
        .catch(error => {
          console.error('Error terminating participation:', error)
        })
    }
  },
  beforeDestroy () {
    window.removeEventListener('show-inactivity-warning', this.showInactivityWarning)
    window.removeEventListener('remove-inactive-user', this.handleInactiveUser)
    this.$store.commit('stopInactivityCheck')
  }
}
</script>

<style scoped>

.agreement-wrapper {
  display: flex;
  justify-content: space-between;
  flex-wrap: nowrap;
  gap: 12px;
  margin-top: 0.5rem;
}

.option-label-wrapper {
  display: flex;
  flex-direction: column;
  align-items: center;
  flex: 1;
  min-width: 90px;
  text-align: center;
}

.option-label {
  font-size: 0.8rem;
  color: #495057;
  margin-bottom: 4px;
  height: 2.5em; /* keeps all labels same height */
  display: flex;
  align-items: center;
  justify-content: center;
  text-align: center;
}

.custom-radio-button >>> .btn {
  width: 100%;
  padding: 0.6rem 1rem;
  border: none !important;
  background: transparent !important;
  box-shadow: none !important;
}

/* Custom black radio button style: use with button-variant="outline-black" (see usage hint below) */
.btn-outline-black {
  color: #000 !important;
  background-color: transparent !important;
  background-image: none !important;
  border-color: #000 !important;
}
.btn-outline-black:hover,
.btn-outline-black:focus,
.btn-outline-black.active,
.btn-outline-black:active,
.btn-outline-black:checked {
  color: #fff !important;
  background-color: #888 !important;
  border-color: #888 !important;
}
/* BootstrapVue deep selectors for custom-radio-button using outline-black */
::v-deep .custom-radio-button .btn-outline-black,
::v-deep .custom-radio-button .btn-outline-black.active,
::v-deep .custom-radio-button .btn-outline-black:active,
::v-deep .custom-radio-button .btn-outline-black:focus,
::v-deep .custom-radio-button .btn-outline-black:checked {
  color: #fff !important;
  background: #888 !important;
  border-color: #888 !important;
  box-shadow: none !important;
}
/* Usage: <b-form-radio-group ... button-variant="outline-black" ...> */

/* Remove border and background for active/checked state as well */
/* Strongest override for BootstrapVue radio button background */
::v-deep .custom-radio-button .btn,
::v-deep .custom-radio-button .btn.active,
::v-deep .custom-radio-button .btn:active,
::v-deep .custom-radio-button .btn:focus,
::v-deep .custom-radio-button .btn:checked,
::v-deep .custom-radio-button .btn-primary,
::v-deep .custom-radio-button .btn-outline-primary,
::v-deep .custom-radio-button .btn-primary.active,
::v-deep .custom-radio-button .btn-primary:active,
::v-deep .custom-radio-button .btn-primary:focus,
::v-deep .custom-radio-button .btn-primary:checked,
::v-deep .custom-radio-button .btn-outline-primary.active,
::v-deep .custom-radio-button .btn-outline-primary:active,
::v-deep .custom-radio-button .btn-outline-primary:focus,
::v-deep .custom-radio-button .btn-outline-primary:checked {
  background: #ccc !important;
  border-color: #ccc !important;
  color: #fff !important;
  box-shadow: none !important;
}

/* Update CSS variable block for grey */
::v-deep .custom-radio-button .btn,
::v-deep .custom-radio-button .btn-primary,
::v-deep .custom-radio-button .btn-outline-primary {
  --bs-btn-bg: #ccc !important;
  --bs-btn-border-color: #ccc !important;
  --bs-btn-hover-bg: #b3b3b3 !important;
  --bs-btn-active-bg: #ccc !important;
  --bs-btn-active-border-color: #ccc !important;
}

/* Remove border radius if you want fully flat look */
.custom-radio-button >>> .btn {
  border-radius: 0 !important;
}

.survey-container {
  font-family: 'Arial', sans-serif;
  line-height: 1.6;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  border-radius: 8px;
  background-color: #ffffff;
}

.survey-title {
  color: #2c3e50;
  margin-bottom: 1rem;
  text-align: center;
}

.jumbotron >>> .lead {
  font-size: 1.5rem;
  margin-bottom: 1.5rem;
  text-align: center;
  color: #495057;
}

.content-area {
  font-size: 1.2rem;
  max-width: 900px;
  margin: 0 auto;
  padding: 1rem;
}

.policy-statement {
  margin-bottom: 3rem;
  padding: 1.5rem;
  background: #f8f9fa;
  border-radius: 8px;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.05);
  transition: transform 0.2s;
}

.policy-statement:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
}

.statement-header {
  margin-bottom: 1.5rem;
}

.statement-number {
  font-size: 1.3rem;
  color: #000 !important; /* Black for 'Statement 1' */
  margin-bottom: 0.5rem;
}

.statement-text.highlight-statement {
  font-size: 1.5rem;
  line-height: 1.7;
  color: #000 !important; /* Black for the statement text */
  font-weight: bold;
  background: #fffbe6;
  border-radius: 8px;
  padding: 1.1rem 1.5rem;
  margin: 0.8rem 0 1.5rem 0;
  box-shadow: 0 2px 8px rgba(255, 217, 0, 0.08);
  border: 1.5px solid #ffe066;
  transition: background 0.2s, box-shadow 0.2s;
}

/* If you want to keep the original class for other uses: */
.statement-text {
  font-size: 1.2rem;
  line-height: 1.6;
  color: #343a40;
}

.scale-labels {
  display: flex;
  justify-content: space-between;
  margin-bottom: 0.5rem;
  font-size: 0.9rem;
  color: #6c757d;
}

.flex-grow {
  flex-grow: 1;
}

.agreement-options {
  display: flex;
  justify-content: space-between;
  width: 100%;
  margin-top: 0.5rem;
}

.agreement-options >>> .btn-group {
  width: 100%;
  display: flex;
  justify-content: space-between;
}

.agreement-options >>> .btn {
  flex: 1;
  margin: 0 4px;
  border-radius: 10px;
  border-width: 0;
  font-weight: 500;
  transition: all 0.2s;
}

.agreement-options >>> .btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 2px 5px rgba(0, 0, 0, 0.1);
}

.agreement-options >>> .active {
  font-weight: bold;
  box-shadow: 0 2px 5px rgba(0, 0, 0, 0.2);
}

.button-area {
  margin-top: 3rem;
  text-align: center;
}

.button-area .btn {
  padding: 0.75rem 2rem;
  font-weight: bold;
  transition: all 0.3s;
  border-radius: 30px;
}

.button-area .btn:hover:not(:disabled) {
  transform: translateY(-3px);
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
}

.progress-label {
  color: white;
  font-weight: bold;
  text-shadow: 1px 1px 2px rgba(0, 0, 0, 0.3);
}

</style>
