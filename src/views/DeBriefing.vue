<template>
  <div class="debriefing">
    <div class="page-indicator text-center mb-1">Page: 9 / 9</div>
    <h1>Debriefing</h1>
    <p>Thank you for participating in the earlier group discussion. We understand that some topics may feel sensitive or polarizing.</p>
    <p>If you ever need support, please explore these mental health resources:</p>
    <ul>
      <li><strong>CDC Mental Health Resources</strong> – Access <a href="https://www.cdc.gov/mental-health/caring/index.html#:~:text=Treatment%20and%20support&text=Visit%20findtreatment.gov%20%E2%80%93%20a%20confidential,Code%20to%20435748%20(HELP4U)" target="_blank" rel="noopener">cdc.gov/mental-health</a> for more information.</li>
      <li><strong>Local Services</strong> – Contact your primary care physician or local health department for referrals in your area.</li>
    </ul>
    <p>Your well-being matters to us. Don’t hesitate to reach out if you need assistance.</p>

    <div class="feedback-area">
      <h5>Optional: Share any feedback about your experience (optional)</h5>
      <b-form-textarea
        v-model="feedback"
        placeholder="Your feedback (optional)"
        rows="4"
        max-rows="8"
        class="mb-3"
      />
    </div>

    <div class="button-area">
      <h5>Please push the button below to submit the study!</h5>
      <b-button variant="primary" name="next" v-on:click="submit" :disabled="submitting">
        {{ submitting ? 'Submitting...' : 'Submit Study' }}
      </b-button>
    </div>
    <b-alert v-if="feedbackSubmitted" variant="success" class="mt-3">Thank you for your feedback!</b-alert>
  </div>
</template>

<script>
import axios from 'axios'
export default {
  name: 'DeBriefing',
  data () {
    return {
      feedback: '',
      feedbackSubmitted: false,
      submitting: false
    }
  },
  methods: {
    async submit (event) {
      this.submitting = true
      // Submit feedback if provided
      if (this.feedback && this.feedback.trim().length > 0) {
        try {
          const feedbackBody = new FormData()
          feedbackBody.append('subject_id', this.$store.state.subject_id)
          feedbackBody.append('feedback_text', this.feedback)
          await axios.post(this.$server_url + 'submit_feedback', feedbackBody)
          this.feedbackSubmitted = true
        } catch (e) {
          // Feedback is optional, so just log error
          console.error('Feedback submission failed', e)
        }
      }
      // Continue with Prolific submission
      const body = new FormData()
      body.append('subject_id', this.$store.state.subject_id)
      body.append('status', 'success')
      axios.post(this.$server_url + 'submit_to_prolific', body)
        .then(response => {
          if (response.data.success === true) {
            window.location.href = response.data.prolific_url
          } else {
            alert('Some error happened! Please submit the HIT on Prolific manually.')
          }
        })
        .catch(e => { alert('Some error happened! Please submit the HIT on Prolific manually.' + e) })
        .finally(() => { this.submitting = false })
    }
  }
}
</script>

<style scoped>
.debriefing {
  max-width: 800px;
  margin: 40px auto;
  padding: 30px;
  background: #f9f9f9;
  border-radius: 10px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  line-height: 1.6;
}
.debriefing h1 {
  text-align: center;
  margin-bottom: 20px;
}
.debriefing p {
  margin-bottom: 16px;
}
.debriefing ul {
  padding-left: 1.2em;
  margin-bottom: 20px;
}
.debriefing li {
  margin-bottom: 8px;
}
.debriefing a {
  color: #1a0dab;
  text-decoration: none;
}
.debriefing a:hover {
  text-decoration: underline;
}
.feedback-area {
  margin: 32px 0 16px 0;
}
</style>
