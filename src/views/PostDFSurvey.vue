<template>
  <div class="centered-survey-wrapper">
    <div class="page-indicator text-center mb-1">Page: 8 / 9</div>
    <div class="intro-center-frame">
      <b-jumbotron header-level="5" class="highlighted-lead">
        <template v-slot:lead>
          <div class="intro-title">Final Reflection</div>
          After selecting your position for all the statements, please take a moment to reflect on your response.
        </template>
      </b-jumbotron>
    </div>
    <b-jumbotron header-level="5" class="questions-area">
      <div class="content-area">
        <!-- Reflection Section -->
        <div class="section">
          <p v-if="allResponsesSame" class="reflection-prompt">
            We notice that your agreement levels of all statements remained the same following the discussion.
            In the text box below, describe what specific aspects of the discussion influenced you to maintain your position.
            Please provide as much detail as you feel is necessary.
          </p>
          <p v-else-if="allResponsesChanged" class="reflection-prompt">
            We notice that your agreement levels of all statements changed following the discussion.
            In the text box below, describe what specific aspects of the discussion caused the change in your perspectives.
            Please provide as much detail as you feel is necessary.
          </p>
          <p v-else class="reflection-prompt">
            {{ generateChangeSummary() }}
            In the text box below, describe what specific aspects of the discussion caused the change in your perspectives on certain statements,
            and explain why your perspectives on other statements remained unchanged. Please provide as much detail as you feel is necessary.
          </p>

          <b-form-textarea
            v-model="reflection"
            rows="6"
            max-rows="8"
            placeholder="Enter your reflection here..."
            @input="onFormInteraction"
          />
        </div>

        <!-- Attention Check 1 -->
        <div class="section">
          <p>If July 2, 2025 is a Wednesday, what day of the week is July 7, 2025?</p>
          <b-form-radio-group v-model="attentionCheck1" :name="'attentionCheck1'" buttons button-variant="outline-black" size="md" class="agreement-options custom-radio-button" @change="onFormInteraction">
            <div class="agreement-wrapper">
              <div v-for="(option, optIndex) in attentionCheck1Options" :key="optIndex" class="option-label-wrapper">
                <div class="option-label">{{ option.text }}</div>
                <b-form-radio :value="option.value" class="custom-radio-button"></b-form-radio>
              </div>
            </div>
          </b-form-radio-group>
        </div>

        <!-- Critical Thinking -->
        <div class="section">
  <div class="text-center">
    <h4>To what extent do you agree with the following statements regarding your experience?</h4>
  </div>
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
      <tr v-for="(statement, index) in criticalThinkingStatements" :key="index">
        <td>{{ statement }}</td>
        <td v-for="option in agreementScale" :key="option.value" class="text-center align-middle">
          <b-form-radio
            v-model="criticalThinkingResponses[index]"
            :name="'critical_' + index"
            :value="option.value"
            class="custom-radio-button"
            required
            @change="onFormInteraction"
          >
            <span class="square-dot"></span>
          </b-form-radio>
        </td>
      </tr>
    </tbody>
  </table>
</div>

        <!-- Attention Check 2 -->
        <div class="section">
          <p>Please select 'Agree' for this statement.</p>
          <p>Statement: I have read the instructions carefully.</p>
          <b-form-radio-group v-model="attentionCheck2" :name="'attentionCheck2'" buttons button-variant="outline-black" size="md" class="agreement-options custom-radio-button" @change="onFormInteraction">
            <div class="agreement-wrapper">
              <div v-for="(option, optIndex) in agreementScale" :key="optIndex" class="option-label-wrapper">
                <div class="option-label">{{ option.text || getAgreementLabel(option.value) }}</div>
                <b-form-radio :value="option.value" class="custom-radio-button"></b-form-radio>
              </div>
            </div>
          </b-form-radio-group>
        </div>

        <!-- AI Tool Usage -->
        <div class="section">
          <p>We'd like to know if you have used a generative AI tool (e.g., ChatGPT, Gemini, Claude) to assist in writing your response for this study.
             Please let us know. You will be compensated regardless.</p>
          <b-form-radio-group v-model="usedAITool" :name="'usedAITool'" buttons button-variant="outline-black" size="md" class="agreement-options custom-radio-button" @change="onFormInteraction">
            <div class="agreement-wrapper">
              <div v-for="(option, optIndex) in aiToolOptions" :key="optIndex" class="option-label-wrapper">
                <div class="option-label">{{ option.text }}</div>
                <b-form-radio :value="option.value" class="custom-radio-button"></b-form-radio>
              </div>
            </div>
          </b-form-radio-group>
        </div>

        <!-- AI Interaction Quality (Conditional) -->
        <div v-if="hasAIParticipant || hasAIModerator" class="section">
          <h5 class="instruction-text mb-4">Please indicate how much you agree or disagree with the following statements about your previous experience in the group discussion:</h5>
          <div v-if="hasAIParticipant">
            <div v-for="(statement, index) in aiParticipantStatements" :key="index" class="mb-3">
              <p>{{ statement }}</p>
              <b-form-radio-group v-model="aiParticipantResponses[index]" :name="'aiParticipant_' + index" buttons button-variant="outline-black" size="md" class="agreement-options custom-radio-button" required @change="onFormInteraction">
                <div class="agreement-wrapper">
                  <div v-for="(option, optIndex) in agreementScale" :key="optIndex" class="option-label-wrapper">
                    <div class="option-label">{{ option.text || getAgreementLabel(option.value) }}</div>
                    <b-form-radio :value="option.value" class="custom-radio-button"></b-form-radio>
                  </div>
                </div>
              </b-form-radio-group>
            </div>
          </div>

          <div v-if="hasAIModerator">
            <div v-for="(statement, index) in aiModeratorStatements" :key="index" class="mb-3">
              <p>{{ statement }}</p>
              <b-form-radio-group v-model="aiModeratorResponses[index]" :name="'aiModerator_' + index" buttons button-variant="outline-black" size="md" class="agreement-options custom-radio-button" required @change="onFormInteraction">
                <div class="agreement-wrapper">
                  <div v-for="(option, optIndex) in agreementScale" :key="optIndex" class="option-label-wrapper">
                    <div class="option-label">{{ option.text || getAgreementLabel(option.value) }}</div>
                    <b-form-radio :value="option.value" class="custom-radio-button"></b-form-radio>
                  </div>
                </div>
              </b-form-radio-group>
            </div>
          </div>
        </div>

        <!-- Cost of Communication -->
        <div class="section">
  <div class="survey-prompt">{{ generateCostPrompt() }}</div>
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
      <tr v-for="(statement, index) in costStatements" :key="index">
        <td><span v-html="statement"></span></td>
        <td v-for="option in agreementScale" :key="option.value" class="text-center align-middle">
          <b-form-radio
            v-model="costResponses[index]"
            :name="'cost_' + index"
            :value="option.value"
            class="custom-radio-button"
            required
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

<style scoped>
.agreement-table {
  width: 100%;
  margin-top: 1rem;
  border-collapse: collapse;
}
.agreement-table th,
.agreement-table td {
  text-align: center;
  vertical-align: middle;
  border: 1px solid #dee2e6;
  padding: 0.5rem;
}
.agreement-table th {
  background-color: #f8f9fa;
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
  margin-bottom: 4px;
  height: 2.5em;
  display: flex;
  align-items: center;
  justify-content: center;
}
.agreement-wrapper {
  display: flex;
  justify-content: center;
  gap: 12px;
  margin-top: 0.5rem;
}
.agreement-options {
  width: 100%;
  display: flex;
  justify-content: center;
  margin-top: 0.5rem;
}
</style>

<script>
import axios from 'axios'
import { notifyInactivity } from '@/plugins/notificationService.js'

export default {
  data () {
    return {
      preDiscussionResponses: this.$store.state.preDiscussionResponses,
      postDiscussionResponses: this.$store.state.postDiscussionResponses,
      reflection: '',
      attentionCheck1: null,
      attentionCheck2: null,
      criticalThinkingResponses: Array(6).fill(null),
      usedAITool: null,
      aiParticipantResponses: Array(3).fill(null),
      aiModeratorResponses: Array(3).fill(null),
      costResponses: Array(4).fill(null),
      selectedStatements: this.$store.state.masterStatements,
      role: '',

      // Options and statements
      attentionCheck1Options: [
        { text: 'Monday', value: 1 },
        { text: 'Tuesday', value: 2 },
        { text: 'Wednesday', value: 3 },
        { text: 'Thursday', value: 4 },
        { text: 'Friday', value: 5 },
        { text: 'Saturday', value: 6 },
        { text: 'Sunday', value: 7 }
      ],
      agreementScale: [
        { text: 'Strongly disagree', value: 1 },
        { text: 'Disagree', value: 2 },
        { text: 'Somewhat disagree', value: 3 },
        { text: 'Neutral', value: 4 },
        { text: 'Somewhat agree', value: 5 },
        { text: 'Agree', value: 6 },
        { text: 'Strongly agree', value: 7 }
      ],
      aiToolOptions: [
        { text: 'Yes, I have used a generative AI tool', value: 1 },
        { text: 'No, I have not used a generative AI tool', value: 2 }
      ],
      criticalThinkingStatements: [
        'The discussion earlier made me examine the values rooted in the information presented.',
        'The discussion earlier made me examine the interrelationships among concepts or opinions posed.',
        'I examined the logical reasoning of an objection made by others to the opinion I posed.',
        'After the discussion, I analyze my thinking before jumping to conclusions.',
        'The discussion helped me anticipate reasonable criticisms one might raise against my viewpoints.',
        'After the discussion, I examine my values, thoughts/beliefs based on reasons and evidence.'
      ],
      aiParticipantStatements: [
        'The AI participant understood what I was thinking and feeling.',
        'I feel connected to the AI participant.',
        'I trust the AI participant.'
      ],
      aiModeratorStatements: [
        'The AI moderator understood what I was thinking and feeling.',
        'I feel connected to the AI moderator.',
        'I trust the AI moderator.'
      ],
      costStatements: [
        'I feel <strong>MORE</strong> guilty if I don\'t respond to a message from others when interacting on the new platform.',
        'I feel <strong>SADDER</strong> when others don\'t pay enough attention to me when interacting on the new platform.',
        'I am <strong>MORE</strong> concerned about my privacy when using the new platform.',
        'I worry <strong>MORE</strong> about lacking companionship when using the new platform.'
      ]
    }
  },
  created () {
    this.role = Math.random() < 0.5 ? 'moderator' : 'participant'
  },
  computed: {
    hasAIParticipant () {
      return this.$store.state.participant_condition === 1 || this.$store.state.participant_condition === 2
    },
    hasAIModerator () {
      return this.$store.state.moderator_condition === 1
    },
    allResponsesSame () {
      // Compare pre and post responses
      return this.compareResponses() === 'same'
    },
    allResponsesChanged () {
      return this.compareResponses() === 'changed'
    },
    isFormValid () {
      const basicFieldsValid = this.reflection &&
        this.attentionCheck1 &&
        this.attentionCheck2 &&
        this.criticalThinkingResponses.every(r => r !== null) &&
        this.usedAITool &&
        this.costResponses.every(r => r !== null)

      if (!basicFieldsValid) return false

      // Check AI-specific responses if applicable
      if (this.hasAIParticipant && !this.aiParticipantResponses.every(r => r !== null)) {
        return false
      }
      if (this.hasAIModerator && !this.aiModeratorResponses.every(r => r !== null)) {
        return false
      }

      return true
    }
  },
  methods: {
    compareResponses () {
      const postResponses = this.postDiscussionResponses || []
      const preResponses = this.preDiscussionResponses || []
      if (!postResponses.length || !preResponses.length) return 'invalid'

      // Build lookup by statement_id
      const postById = new Map(postResponses.map(r => [r.statement_id, r]))
      const preById = new Map(preResponses.map(r => [r.statement_id, r]))

      // Ensure same set of statements
      if (postById.size !== preById.size) return 'invalid'
      for (const id of preById.keys()) {
        if (!postById.has(id)) return 'invalid'
      }

      let allSame = true
      let allChanged = true

      for (const [id, pre] of preById.entries()) {
        const post = postById.get(id)
        // Compare by sign only
        const preSign = Math.sign(pre.agreement)
        const postSign = Math.sign(post.agreement)

        if (preSign === postSign) {
          allChanged = false
        } else {
          allSame = false
        }
      }

      if (allSame) return 'same'
      if (allChanged) return 'changed'
      return 'mixed'
    },
    generateChangeSummary () {
      // Generate summary of which statements changed/stayed same
      const changes = []
      const masters = this.$store.state.masterStatements
      this.preDiscussionResponses.forEach(pre => {
        const post = this.postDiscussionResponses.find(p => p.statement_id === pre.statement_id)
        if (post && pre.agreement * post.agreement < 0) {
          changes.push(masters[pre.statement_id])
        }
      })
      // If more than 3 changes, randomly select 3 and add "and extra" note
      if (changes.length > 3) {
        // Shuffle array and take first 3
        const shuffled = changes.sort(() => 0.5 - Math.random())
        const selected = shuffled.slice(0, 3)
        return `We notice that your agreement level on the statement(s) '${selected.join(', ')}' and extra changed following the discussion, while your agreement levels on the other statements remained unchanged.`
      }
      return `We notice that your agreement level on the statement(s) '${changes.join(', ')}' changed following the discussion, while your agreement levels on the other statements remained unchanged.`
    },
    generateCostPrompt () {
      if (!this.hasAIParticipant && !this.hasAIModerator) {
        const description = this.role === 'moderator'
          ? 'The AI moderator can moderate and coordinate the group discussion.'
          : 'The AI participant can actively participate in the discussion and express its stance or opinions.'
        return `Imagine using a new platform designed to provide a discussion experience where there exists an AI ${this.role}. ${description}.

Reflect on your typical discussion experiences on platforms without AI agents. Compared to those experiences, please indicate the extent to which you agree or disagree with the following statements:`
      } else {
        const options = ['AI moderator', 'AI participant', 'AI moderator and an AI participant']

        // Randomly select one of the available options
        const randomIndex = Math.floor(Math.random() * options.length)
        const selectedRole = options[randomIndex]

        return `Imagine using a new platform designed to facilitate discussions with the involvement of an ${selectedRole}, similar to the previous discussion you just experienced.

Reflect on your typical discussion experiences on platforms without AI agents. Compared to those experiences, please indicate the extent to which you agree or disagree with the following statements:`
      }
    },
    async submitSurvey () {
      if (!this.isFormValid) {
        this.$alert('Please complete all required fields.')
        return
      }

      try {
        const formData = new FormData()
        formData.append('subject_id', this.$store.state.subject_id)
        formData.append('reflection', this.reflection)
        formData.append('attention_check_1', this.attentionCheck1)
        formData.append('attention_check_2', this.attentionCheck2)
        formData.append('critical_thinking_responses', JSON.stringify(this.criticalThinkingResponses))
        formData.append('used_ai_tool', this.usedAITool)
        formData.append('ai_participant_responses', JSON.stringify(this.aiParticipantResponses))
        formData.append('ai_moderator_responses', JSON.stringify(this.aiModeratorResponses))
        formData.append('cost_responses', JSON.stringify(this.costResponses))
        const response = await axios.post(
          this.$server_url + 'post_df_survey',
          formData
        )
        if (response.data.success) {
          this.$router.push('/DeBriefing')
        }
      } catch (error) {
        console.error('Error submitting survey:', error)
        this.$bvToast.toast(`An error occurred. Please try again.\n${error && error.message ? error.message : ''}`, {
          title: 'Error',
          variant: 'danger'
        })
      }
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
    }
  },
  mounted () {
    // this.$store.commit('startInactivityCheck')
    // window.addEventListener('show-inactivity-warning', this.showInactivityWarning)
    // window.addEventListener('remove-inactive-user', this.handleInactiveUser)
    window.scrollTo(0, 0)
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
  transition: box-shadow 0.2s, transform 0.2s;
  margin-bottom: 2rem;
  padding: 1rem;
  border: 1px solid #dee2e6;
  border-radius: 0.25rem;
}
.section:hover,
.section:focus-within {
  box-shadow: 0 8px 24px rgba(80, 80, 80, 0.12), 0 1.5px 8px rgba(80,80,80,0.10);
  transform: translateY(-4px) scale(1.02);
  z-index: 2;
}

.reflection-prompt {
  font-style: italic;
  color: #495057;
  margin-bottom: 1rem;
}

.questions-area ::v-deep .btn-group {
  display: flex !important;
  flex-direction: row !important;
  flex-wrap: wrap !important;
  justify-content: center;
  gap: 0.5rem;
}

.questions-area ::v-deep .btn-group-vertical {
  flex-direction: row !important;
  flex-wrap: wrap;
  gap: 0.5rem;
}

.questions-area ::v-deep .btn-outline-black {
  position: relative;
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

.square-dot {
  display: inline-block;
}

.custom-radio-button {
  display: inline-flex !important;
  justify-content: center;
  align-items: center;
}

.survey-prompt {
  white-space: pre-line;
  margin-bottom: 1rem;
  font-size: 1.35rem;
  text-align: left;
  font-weight: bold;
}
</style>
