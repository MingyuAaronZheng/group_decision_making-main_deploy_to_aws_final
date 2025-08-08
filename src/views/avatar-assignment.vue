<template>
  <b-container class="avatar-container">
    <b-row class="justify-content-center">
      <b-col md="12" class="text-center">
        <h2>Welcome to Your Discussion</h2>
      </b-col>
    </b-row>
    <template v-if="participantCondition === 3">
      <b-row class="main-content">
        <b-col md="8" class="left-column">
          <p>You have been assigned the following discussion identity:</p>

          <!-- Avatar Display -->
          <div class="avatar-display">
            <div v-if="assignedAvatar.animal && assignedAvatar.color">
              <v-animal :size="'80px'"
                        :name="assignedAvatar.animal || 'penguin'"
                        :color="assignedAvatar.color"
                        class="avatar-icon"/>
              <p class="mt-2">
                Your discussion name: <strong>{{ assignedAvatar.color }} {{ assignedAvatar.animal }}</strong>
              </p>
            </div>
            <div v-else>
              <p>Loading avatar information...</p>
              <b-spinner label="Loading..." class="mt-2"></b-spinner>
              <p class="mt-2">
                <small>Debug info: animal={{ assignedAvatar.animal }}, color={{ assignedAvatar.color }}</small>
              </p>
            </div>
          </div>

          <!-- Discussion Topic -->
          <div class="discussion-topic mt-4">
            <h5>Discussion Topic:</h5>
            <p class="statement-text">
              {{ chatStatement }}
            </p>
          </div>

          <!-- Your Agreement Level -->
          <div v-if="yourAgreementLevel !== null" class="agreement-level mt-3">
            <h5>Your Position:</h5>
            <div class="agreement-display">
              <p>Your agreement level: <strong>{{ agreementLevelText }}</strong></p>
              <div class="agreement-scale">
                <div class="scale-labels">
                  <span>Strongly disagree</span>
                  <span>Strongly agree</span>
                </div>
                <div class="scale-bar">
                  <div class="scale-marker" :style="{ left: agreementMarkerPosition + '%' }"></div>
                </div>
              </div>
            </div>
          </div>
          <!-- Countdown Timer -->
        </b-col>
        <b-col md="4" class="right-column">
          <div v-if="participantCondition === 3 && isThirdPerson" class="third-person-instructions">
            <h5>Special Instructions for You</h5>
            <h5><strong>We will bonus you if you do well in this task.</strong></h5>
            <div v-if="random_third_person_prompt === 0" class="advocating-prompt mt-3">
              <h6>Advocating Role:</h6>
              <p>Your specific task is to ALWAYS advocate your own position. Try to:</p>
              <ul class="text-left">
                <li><strong>Champion your stance:</strong> Consistently highlight its benefits, principles, and supporting evidence—use facts, logic, and real-world examples to build a clear, positive case.</li>
                <li><strong>Stay in your own lane:</strong> Do not mention, quote, or critique the opposing side's arguments, examples, or wording; keep every statement focused solely on strengthening your position.</li>
                <li><strong>Advance, don't rebut:</strong> When the other side speaks, ignore their points and offer fresh reasons or illustrations that reinforce your stance rather than responding to or comparing with theirs.</li>
              </ul>
            </div>
            <div v-if="random_third_person_prompt === 1" class="disputing-prompt mt-3">
              <h6>Disputing Role:</h6>
              <p>Your specific task is to ALWAYS dispute the position of others who hold opposite views to yours. Try to:</p>
              <ul class="text-left">
                <li><strong>Zero-in on others' position:</strong> Use evidence, logic, and real-world examples to expose weaknesses, gaps, or harmful implications in the opponent's stance—every statement should chip away at their argument.</li>
                <li><strong>Don’t bring up your own side:</strong> Do not mention or praise your own preferred view; avoid presenting its benefits, solutions, or supporting data—focus solely on why the opponent's idea falls short.</li>
                <li><strong>Counter, don't cultivate:</strong> When the other side speaks, reply with fresh critiques that undermine their point rather than offering alternative proposals or positive cases for any viewpoint.</li>
              </ul>
            </div>
            <b-button
              variant="primary"
              class="mt-3"
              :disabled="!hasReadInstructions"
              @click="confirmInstructions"
            >
              I have read and understand these instructions
            </b-button>
            <div v-if="!hasReadInstructions" class="text-muted mt-2">
              Please read the instructions carefully. Button enabled in {{ readTimer }}s
            </div>
          </div>
          <div v-if="participantCondition === 3 && !isThirdPerson && !allConfirmed" class="waiting-message">
            <p>We are finalizing the discussion environment, which won't take long.</p>
            <strong style="color: blue;">Please turn on audio on your device.</strong>
            <p>Once the environment is ready, we will notify you with a sound and redirect you to the next page.</p>
            <b-spinner label="Loading..." class="mt-2"></b-spinner>
          </div>
          <div v-if="participantCondition === 3 && allConfirmed" class="countdown-section mt-4">
            <p class="countdown-text">
              The environment is ready. Redirecting to the discussion room in <strong>{{ formattedCountdown }}</strong>...
            </p>
            <b-spinner label="Loading..." class="mt-2"></b-spinner>
          </div>
        </b-col>
      </b-row>
    </template>
    <template v-else>
      <b-row class="justify-content-center">
        <b-col md="8" class="single-column">
          <p>You have been assigned the following discussion identity:</p>

          <!-- Avatar Display -->
          <div class="avatar-display">
            <div v-if="assignedAvatar.animal && assignedAvatar.color">
              <v-animal :size="'80px'"
                        :name="assignedAvatar.animal || 'penguin'"
                        :color="assignedAvatar.color"
                        class="avatar-icon"/>
              <p class="mt-2">
                Your discussion name: <strong>{{ assignedAvatar.color }} {{ assignedAvatar.animal }}</strong>
              </p>
            </div>
            <div v-else>
              <p>Loading avatar information...</p>
              <b-spinner label="Loading..." class="mt-2"></b-spinner>
              <p class="mt-2">
                <small>Debug info: animal={{ assignedAvatar.animal }}, color={{ assignedAvatar.color }}</small>
              </p>
            </div>
          </div>

          <!-- Discussion Topic -->
          <div class="discussion-topic mt-4">
            <h5>Discussion Topic:</h5>
            <p class="statement-text">
              {{ chatStatement }}
            </p>
          </div>

          <!-- Your Agreement Level -->
          <div v-if="yourAgreementLevel !== null" class="agreement-level mt-3">
            <h5>Your Position:</h5>
            <div class="agreement-display">
              <p>Your agreement level: <strong>{{ agreementLevelText }}</strong></p>
              <div class="agreement-scale">
                <div class="scale-labels">
                  <span>Strongly disagree</span>
                  <span>Strongly agree</span>
                </div>
                <div class="scale-bar">
                  <div class="scale-marker" :style="{ left: agreementMarkerPosition + '%' }"></div>
                </div>
              </div>
            </div>
          </div>
          <!-- Countdown Timer -->
          <div v-if="(participantCondition === 3 && allConfirmed) || participantCondition !== 3" class="countdown-section mt-4">
            <p class="countdown-text">
              The environment is ready. Redirecting to the discussion room in <strong>{{ formattedCountdown }}</strong>...
            </p>
            <b-spinner label="Loading..." class="mt-2"></b-spinner>
          </div>
        </b-col>
      </b-row>
    </template>
  </b-container>
</template>

<script>
import { mapState } from 'vuex'
import { colors } from '@/components/constants'
import axios from 'axios'

export default {
  data () {
    return {
      countdown: this.$store.state.test === 'Y' ? 5 : 20, // 5s if 'Y', 20s if 'N'
      hasReadInstructions: false,
      readTimer: 5,
      readTimerInterval: null,
      random_third_person_prompt: this.$store.state.random_third_person_prompt
    }
  },
  computed: {
    ...mapState({
      assignedAvatar: state => {
        return {
          color: state.avatar_color,
          animal: state.avatar_name
        }
      },
      chatStatement: state => {
        return state.chat_statement
      },
      isThirdPerson: state => {
        return state.is_third_person
      },
      participantCondition: state => {
        return state.participant_condition
      },
      preDiscussionResponses: state => state.preDiscussionResponses,
      chatStatementIndex: state => state.chat_statement_index,
      allConfirmed: state => state.all_confirmed
    }),
    yourAgreementLevel () {
      // Get the agreement level for the current chat statement
      if (!this.preDiscussionResponses || this.chatStatementIndex === null) {
        return null
      }
      const targetId = this.chatStatementIndex
      const resp = this.preDiscussionResponses.find(r => r.statement_id === targetId)
      return resp ? resp.agreement : null
    },
    agreementLevelText () {
      // Convert numerical agreement level to text
      const level = this.yourAgreementLevel
      if (level === null) return 'Not available'

      const agreementMap = {
        '-3': 'Strongly disagree',
        '-2': 'Disagree',
        '-1': 'Somewhat disagree',
        '1': 'Somewhat agree',
        '2': 'Agree',
        '3': 'Strongly agree'
      }

      return agreementMap[level.toString()] || 'Neutral'
    },
    agreementMarkerPosition () {
      // Convert agreement level (-3 to 3) to percentage position (0 to 100)
      const level = this.yourAgreementLevel
      if (level === null) return 50 // Center position if no data

      // Map from -3...3 to 0...100
      // Note: We skip 0 in the scale (as in the PreDSurvey)
      // So we need to map -3,-2,-1,1,2,3 to positions on the scale
      if (level < 0) {
        // Map -3,-2,-1 to 0,16.7,33.3
        return (level + 3) * 16.7
      } else {
        // Map 1,2,3 to 66.7,83.3,100
        return 50 + (level * 16.7)
      }
    },
    formattedCountdown () {
      const minutes = Math.floor(this.countdown / 60)
      const seconds = this.countdown % 60
      return `${minutes}:${seconds.toString().padStart(2, '0')}`
    }
  },
  watch: {
    allConfirmed (newVal) {
      if (newVal) {
        this.startCountdown()
      }
    }
  },
  methods: {
    avatarColorHex (colorName) {
      if (!colorName) {
        console.warn('No color name provided')
        return '#006CFE' // Default to blue
      }

      // If colorName is already a hex code, return it directly
      if (colorName.startsWith('#')) {
        return colorName
      }

      const colorLower = colorName.toLowerCase()
      const colorHex = colors[colorLower]

      if (!colorHex) {
        console.warn(`Color "${colorName}" not found in colors map, using default`)
        return colorName || '#006CFE' // Return the color name or default to blue
      }

      return colorHex
    },
    startCountdown () {
      const countdownInterval = setInterval(() => {
        this.countdown--
        if (this.countdown <= 0) {
          clearInterval(countdownInterval)
          this.$router.push('/ChatRoom')
        }
      }, 1000)
    },
    async confirmInstructions () {
      try {
        const formData = new FormData()
        formData.append('subject_id', this.$store.state.subject_id)
        formData.append('group_id', this.$store.state.group_id)
        const response = await axios.post(this.$server_url + 'confirm_instructions', formData)

        if (response.data.success) {
          console.log('Instructions confirmed')
        }
      } catch (error) {
        console.error('Error confirming instructions:', error)
      }
    }
  },
  mounted () {
    // Scroll to top when component is mounted
    window.scrollTo(0, 0)

    // Start countdown for instruction-reading lock
    this.readTimerInterval = setInterval(() => {
      if (this.readTimer > 0) {
        this.readTimer--
      }
      if (this.readTimer <= 0) {
        clearInterval(this.readTimerInterval)
        this.hasReadInstructions = true
      }
    }, 1000)
    if (this.participantCondition !== 3) {
      this.startCountdown()
    }
  },
  beforeDestroy () {
    if (this.readTimerInterval) {
      clearInterval(this.readTimerInterval)
    }
    clearTimeout(this.timeout)
  }
}
</script>

<style scoped>
.avatar-container {
  text-align: center;
  padding: 40px;
}

.avatar-display {
  margin: 20px 0;
  padding: 15px;
  background-color: #f8f9fa;
  border-radius: 8px;
}

.avatar-icon {
  margin: 10px 0;
  display: inline-block !important;
}

.avatar-icon svg {
  fill: inherit !important;
}

.avatar-icon svg path {
  fill: inherit !important;
}

.avatar-icon svg circle {
  fill: inherit !important;
}

.statement-text {
  font-size: 1.1em;
  font-weight: 500;
  color: #2c3e50;
  padding: 10px;
  background-color: #f8f9fa;
  border-radius: 5px;
  margin-top: 10px;
}

.countdown-text {
  font-size: 1.2em;
  font-weight: bold;
  color: #d9534f; /* Bootstrap danger color */
}

.main-content {
  margin-top: 20px;
}

.left-column {
  padding-right: 30px;
  border-right: 1px solid #eee;
}

.right-column {
  padding-left: 30px;
  display: flex;
  flex-direction: column;
  justify-content: center;
}

.third-person-instructions {
  background-color: #f8f9fa;
  border-radius: 8px;
  padding: 20px;
}

.third-person-instructions ul {
  text-align: left;
  margin: 0 auto;
  max-width: 500px;
}

.third-person-instructions li {
  margin-bottom: 10px;
}

.waiting-message {
  text-align: center;
}

/* New styles for agreement level display */
.agreement-level {
  background-color: #f8f9fa;
  border-radius: 8px;
  padding: 15px;
  margin-top: 20px;
}

.agreement-display {
  margin: 10px 0;
}

.agreement-scale {
  width: 100%;
  max-width: 500px;
  margin: 15px auto;
}

.scale-labels {
  display: flex;
  justify-content: space-between;
  margin-bottom: 5px;
  font-size: 0.8em;
  color: #6c757d;
}

.scale-bar {
  position: relative;
  height: 10px;
  background: linear-gradient(to right, #dc3545, #e9ecef, #28a745);
  border-radius: 5px;
}

.scale-marker {
  position: absolute;
  top: -5px;
  width: 20px;
  height: 20px;
  background-color: #007bff;
  border-radius: 50%;
  transform: translateX(-50%);
}

.single-column {
  margin-top: 20px;
  text-align: center;
}

.page-indicator {
  color: #6c757d;
  font-size: 0.9em;
  margin-top: 5px;
  margin-bottom: 15px;
}
</style>
