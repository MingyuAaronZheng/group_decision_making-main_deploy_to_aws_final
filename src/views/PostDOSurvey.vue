<template>
  <div class="centered-survey-wrapper">
    <div class="page-indicator text-center mb-1">Page: 7 / 9</div>
    <div class="intro-center-frame">
      <div class="highlighted-lead">
        <div class="intro-title">Post-Discussion Questionnaire</div>
        Thank you for participating in the discussion task. In this section, you will complete an Exit Survey, designed to gather your feedback and reflections on the discussion experience.
      </div>
    </div>
    <b-jumbotron header-level="5" class="questions-area">
      <div class="content-area">
      <!-- Policy Attitudes Section -->
      <div class="section">
        <h4>Please indicate your current stance on the following discussion topics.</h4>
        <p></p>
        <p></p>
        <div v-for="(statement, index) in randomizedStatements" :key="index" class="policy-statement mb-4">
          <p><strong>Statement {{ index + 1 }}:</strong> {{ statement.text }}</p>

          <!-- Agreement Question -->
          <div class="question-block">
            <p>To what extent do you agree with this statement?</p>
            <b-form-radio-group
              v-model="policyResponses[index].agreement"
              :name="'agreement_' + index"
              buttons
              button-variant="outline-black"
              size="md"
              class="agreement-options custom-radio-button"
              @change="onFormInteraction"
            >
              <div class="agreement-wrapper">
                <div v-for="(option, optIndex) in opinionAgreementScale" :key="optIndex" class="option-label-wrapper">
                  <div class="option-label">{{ option.text || getAgreementLabel(option.value) }}</div>
                  <b-form-radio :value="option.value" class="custom-radio-button"></b-form-radio>
                </div>
              </div>
            </b-form-radio-group>
          </div>

          <!-- Importance Question -->
          <div class="question-block">
            <p>How personally important is this issue to you?</p>
            <b-form-radio-group
              v-model="policyResponses[index].importance"
              :name="'importance_' + index"
              buttons
              button-variant="outline-black"
              size="md"
              class="agreement-options custom-radio-button"
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
        </div>
      </div>

      <!-- Conversation Quality Section -->
      <div class="section">
        <h4>Based on your experience in the previous group discussion, please answer the following questions.</h4>
        <p></p>
        <p></p>
        <div class="question-block">
          <p>How would you grade the quality of the discussion you just had?</p>
          <b-form-radio-group
            v-model="conversationQuality"
            :name="'conversationQuality'"
            buttons
            button-variant="outline-black"
            size="md"
            class="agreement-options custom-radio-button"
            @change="onFormInteraction"
          >
            <div class="agreement-wrapper">
              <div v-for="(option, optIndex) in qualityScale" :key="optIndex" class="option-label-wrapper">
                <div class="option-label">{{ option.text }}</div>
                <b-form-radio :value="option.value" class="custom-radio-button"></b-form-radio>
              </div>
            </div>
          </b-form-radio-group>
        </div>
        <p class="mt-3">To what extent do you agree with the following statements regarding the discussion?</p>
        <table class="table agreement-table">
          <thead>
            <tr>
              <th>Statement</th>
              <th v-for="option in agreementScale" :key="option.value" class="text-center align-middle">{{ option.text || getAgreementLabel(option.value) }}</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="(statement, index) in conversationStatements" :key="index">
              <td>{{ statement }}</td>
              <td v-for="option in agreementScale" :key="option.value" class="text-center align-middle">
                <b-form-radio
                  v-model="conversationResponses[index]"
                  :name="'conversation_' + index"
                  :value="option.value"
                  class="custom-radio-button"
                  @change="onFormInteraction"
                >
                  <span class="square-dot"></span>
                </b-form-radio>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- Democratic Reciprocity Section -->
      <div class="section">
        <h4>To what extent do you agree with the following statements?</h4>
        <table class="table agreement-table">
          <thead>
            <tr>
              <th>Statement</th>
              <th v-for="option in agreementScale" :key="option.value" class="text-center align-middle">
                {{ option.text || getAgreementLabel(option.value) }}
              </th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="(statement, index) in reciprocityStatements" :key="index">
              <td>{{ statement }}</td>
              <td v-for="option in agreementScale" :key="option.value" class="text-center align-middle">
                <b-form-radio
                  v-model="reciprocityResponses[index]"
                  :name="'reciprocity_' + index"
                  :value="option.value"
                  class="custom-radio-button"
                  @change="onFormInteraction"
                >
                  <span class="square-dot"></span>
                </b-form-radio>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- Submit Button -->
      <div class="button-area mt-4">
        <b-button
          variant="primary"
          size="lg"
          @click="submitSurvey"
        >
          Submit Survey
        </b-button>
      </div>
    </div>
    </b-jumbotron>
  </div>
</template>

<script>
import axios from 'axios'
import { notifyInactivity } from '@/plugins/notificationService.js'

export default {
  data () {
    return {
      statements: [], // Will be populated from store
      randomizedStatements: [],
      policyResponses: [],
      conversationQuality: null,
      conversationResponses: Array(4).fill(null),
      reciprocityResponses: Array(4).fill(null),
      // Scales
      opinionAgreementScale: [
        { text: 'Strongly Disagree', value: -3 },
        { text: 'Disagree', value: -2 },
        { text: 'Somewhat Disagree', value: -1 },
        { text: 'Somewhat Agree', value: 1 },
        { text: 'Agree', value: 2 },
        { text: 'Strongly Agree', value: 3 }
      ],
      agreementScale: [
        { text: 'Strongly Disagree', value: 1 },
        { text: 'Disagree', value: 2 },
        { text: 'Somewhat Disagree', value: 3 },
        { text: 'Neutral', value: 4 },
        { text: 'Somewhat Agree', value: 5 },
        { text: 'Agree', value: 6 },
        { text: 'Strongly Agree', value: 7 }
      ],
      importanceScale: [
        { text: 'Not at all important to me', value: 1 },
        { text: 'Slightly important to me', value: 2 },
        { text: 'Somewhat important to me', value: 3 },
        { text: 'Moderately important to me', value: 4 },
        { text: 'Important to me', value: 5 },
        { text: 'Very important to me', value: 6 },
        { text: 'Extremely important to me', value: 7 }
      ],
      qualityScale: [
        { text: 'Very poor', value: 1 },
        { text: 'Poor', value: 2 },
        { text: 'Somewhat poor', value: 3 },
        { text: 'Average', value: 4 },
        { text: 'Somewhat good', value: 5 },
        { text: 'Good', value: 6 },
        { text: 'Very good', value: 7 }
      ],
      conversationStatements: [
        'I felt heard and understood by others in the discussion.',
        'I treated others with respect in the discussion.',
        'The other(s) in the discussion was(were) disrespectful to me.',
        'I was able to communicate my values and beliefs to others in the discussion.'
      ],
      reciprocityStatements: [
        'I find it difficult to see things from the perspective of people who disagree with me on the policy of discussion.',
        'It is important to understand people who disagree with me on the policy of discussion by imagining how things look from their perspective.',
        'Even if I don\'t agree with them, I understand people have good reasons for voting for candidates who disagree with me on the policy of discussion.',
        'I respect the opinions of people who disagree with me on the policy of discussion.'
      ]
    }
  },
  computed: {
    isFormValid () {
      // Check if all required fields are filled
      const policyComplete = this.policyResponses.every(
        response => response.agreement !== null && response.importance !== null
      )
      const conversationComplete = this.conversationQuality !== null &&
        this.conversationResponses.every(response => response !== null)
      const reciprocityComplete = this.reciprocityResponses.every(
        response => response !== null
      )
      return policyComplete && conversationComplete && reciprocityComplete
    }
  },
  created () {
    // Wrap statements with IDs and shuffle
    const selectedStatements = this.$store.state.masterStatements.map((text, idx) => ({ id: idx, text }))
    this.randomizedStatements = this.shuffleArray(selectedStatements)
    this.policyResponses = this.randomizedStatements.map(() => ({
      agreement: null,
      importance: null
    }))
  },
  methods: {
    getAgreementLabel (value) {
      switch (value) {
        case 1: return 'Strongly Disagree'
        case 2: return 'Disagree'
        case 3: return 'Somewhat Disagree'
        case 4: return 'Neutral'
        case 5: return 'Somewhat Agree'
        case 6: return 'Agree'
        case 7: return 'Strongly Agree'
        default: return ''
      }
    },
    shuffleArray (array) {
      const arr = array.slice()
      for (let i = arr.length - 1; i > 0; i--) {
        const j = Math.floor(Math.random() * (i + 1))
        ;[arr[i], arr[j]] = [arr[j], arr[i]]
      }
      return arr
    },
    // Track activity on form interactions
    onFormInteraction () {
      this.$store.dispatch('recordActivity')
    },
    showInactivityWarning () {
      notifyInactivity(this.$bvToast, this.$store.state.test)
    },
    handleInactiveUser () {
      // Redirect to timeout page
      this.$router.push('/InactivityTerminatedParticipation')
    },
    async submitSurvey () {
      // Record activity when submitting
      this.$store.dispatch('recordActivity')
      if (!this.isFormValid) {
        this.$alert('Please complete all required fields.')
        return
      }

      // Map responses to include statement IDs
      const mappedResponses = this.randomizedStatements.map((s, i) => ({
        statement_id: s.id,
        agreement: this.policyResponses[i].agreement,
        importance: this.policyResponses[i].importance
      }))

      const formData = new FormData()
      formData.append('subject_id', this.$store.state.subject_id)
      formData.append('policy_responses', JSON.stringify(mappedResponses))
      formData.append('conversation_quality', this.conversationQuality)
      formData.append('conversation_responses', JSON.stringify(this.conversationResponses))
      formData.append('reciprocity_responses', JSON.stringify(this.reciprocityResponses))
      axios
        .post(this.$server_url + 'post_do_survey', formData)
        .then((response) => {
          if (response.data.success) {
            this.$store.commit('setPostDiscussionResponses', mappedResponses)
            this.$router.push('/PostDFSurvey')
          } else {
            alert(response.data.message)
          }
        })
        .catch(() => {
          alert('An error occurred while submitting. Please try again.')
        })
    }
  },
  mounted () {
    // Scroll to top when component is mounted
    window.scrollTo(0, 0)

    this.$store.commit('startInactivityCheck')
    window.addEventListener('show-inactivity-warning', this.showInactivityWarning)
    window.addEventListener('remove-inactive-user', this.handleInactiveUser)
  },
  beforeDestroy () {
    window.removeEventListener('show-inactivity-warning', this.showInactivityWarning)
    window.removeEventListener('remove-inactive-user', this.handleInactiveUser)
    this.$store.commit('stopInactivityCheck')
  }
}
</script>

<style scoped>
  .centered-survey-wrapper {
    min-height: 100vh;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: flex-start;
    background: #f5f7fa;
    width: 100vw;
  }
  .intro-center-frame {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    min-height: 10vh;
    width: 100vw;
  }
  .highlighted-lead {
    background: #fffbe6;
    border: 2px solid #ffe066;
    border-radius: 12px;
    padding: 1.25rem 2rem;
    margin-top: 4rem;
    margin-bottom: 1rem;
    font-size: 1.15rem;
    color: #7c6700;
    box-shadow: 0 2px 8px rgba(255, 217, 0, 0.08);
    text-align: center;
    font-weight: 500;
    letter-spacing: 0.01em;
    max-width: 900px;
  }
  .intro-title {
    font-size: 1.3rem;
    font-weight: bold;
    margin-bottom: 0.5rem;
    color: #7c6700;
  }
  .questions-area {
    margin-top: 1rem;
    width: 100vw;
    display: flex;
    flex-direction: column;
    align-items: center;
  }
  .content-area {
    padding: 1.25rem 2rem;
    width: 100%;
    max-width: 2000px;
  }

.section {
  margin-bottom: 2rem;
  padding: 1rem;
  border: 1px solid #dee2e6;
  border-radius: 0.25rem;
}

.question-block {
  margin-bottom: 1.5rem;
}

.policy-statement {
  padding: 1rem;
  background-color: #f8f9fa;
  border-radius: 0.25rem;
  text-align: center;
}

.policy-statement > p,
.question-block > p,
.section > p {
  font-size: 1.25rem;
  text-align: center;
}
.section > h4 {
  font-size: 1.35rem;
  text-align: center;
}

.mb-3 > p {
  font-size: 1.2rem;
  text-align: center !important;
}
.agreement-wrapper {
  display: flex;
  flex-direction: row;
  justify-content: center;
  flex-wrap: wrap;
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
  font-size: 1rem;
  color: #495057;
  margin-bottom: 4px;
  height: 2.5em;
  display: flex;
  align-items: center;
  justify-content: center;
  text-align: center;
}

.agreement-options {
  display: flex;
  justify-content: center;
  width: 100%;
  margin-top: 0.5rem;
}

.agreement-table {
  width: 100%;
  margin-top: 1rem;
  border-collapse: collapse;
}

.agreement-table th, .agreement-table td {
  border: 1px solid #dee2e6;
  padding: 0.5rem;
  text-align: center;
}

.agreement-table th {
  background-color: #f8f9fa;
}
</style>
