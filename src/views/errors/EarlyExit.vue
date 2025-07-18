<template>
  <b-jumbotron header-level="5">
    <template v-slot:lead>
      Early Exit Feedback
    </template>
    <div class="content-area">
      <div class="alert alert-info">
        <h4>Thank you for your participation in our study.</h4>
        <p>Since you have chosen to exit early, we would greatly appreciate your feedback to help us improve future studies.</p>
        <h5><strong>Why did you choose to exit the study early?</strong></h5>
        <p><em>(Please select all that apply or provide additional comments.)</em></p>
        <b-form-group>
          <b-form-checkbox-group v-model="reasons" stacked>
            <b-form-checkbox value="rude_participants">The other participants are too rude.</b-form-checkbox>
            <b-form-checkbox value="difficult_tasks">The tasks were too difficult or time-consuming.</b-form-checkbox>
            <b-form-checkbox value="not_expected">The study was not what I expected.</b-form-checkbox>
            <b-form-checkbox value="technical_issues">Technical issues prevented me from continuing.</b-form-checkbox>
          </b-form-checkbox-group>
          <b-form-group label="Other (please specify):">
            <b-form-input v-model="otherReason" placeholder="Your comments..."></b-form-input>
          </b-form-group>
        </b-form-group>

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

        <p>Your feedback is entirely optional and will remain confidential. Thank you for helping us improve!</p>
        <div class="button-area">
          <b-button variant="primary" name="next" @click="submit">Submit Feedback</b-button>
        </div>
      </div>
    </div>
  </b-jumbotron>
</template>

<script>
import axios from 'axios'
export default {
  name: 'EarlyExit',
  data () {
    return {
      reasons: [],
      otherReason: '',
      feedback: '',
      isSubmitting: false
    }
  },
  methods: {
    async submit (event) {
      if (event) {
        event.preventDefault()
        event.stopPropagation()
      }

      if (this.isSubmitting) return

      this.isSubmitting = true

      try {
        // First terminate the participation
        const terminateBody = new FormData()
        terminateBody.append('subject_id', this.$store.state.subject_id)
        await axios.post(this.$server_url + 'terminate_participation', terminateBody)

        // Submit the feedback
        const feedbackBody = new FormData()
        feedbackBody.append('subject_id', this.$store.state.subject_id)
        // Combine structured reasons, other reason, and detailed feedback into feedback text
        const feedbackText = `Early Exit Reasons: ${this.reasons.join(', ')}${this.otherReason ? '\nOther Reason: ' + this.otherReason : ''}${this.feedback ? '\n\nOptional Detailed Feedback:\n' + this.feedback : ''}`
        feedbackBody.append('feedback_text', feedbackText)
        try {
          await axios.post(this.$server_url + 'submit_feedback', feedbackBody)
        } catch (e) {
          // Feedback is optional, so just log error
          console.error('Feedback submission failed', e)
        }

        // Then submit to Prolific
        const body = new FormData()
        body.append('subject_id', this.$store.state.subject_id)
        body.append('status', 'early_exit')
        body.append('reasons', JSON.stringify(this.reasons))
        body.append('other_reason', this.otherReason)

        const response = await axios.post(this.$server_url + 'submit_to_prolific', body)

        if (response.data.success === true) {
          // Redirect to Prolific URL in current tab
          window.location.href = response.data.prolific_url
        } else {
          throw new Error('Failed to submit to Prolific')
        }
      } catch (error) {
        console.error('Error in submit:', error)
        this.isSubmitting = false
        alert('An error occurred. Please submit the HIT on Prolific manually.')
      }
    }
  }
}
</script>

<style scoped>
.content-area {
  max-width: 600px;
  margin: 0 auto;
  padding: 2rem;
}
.alert {
  text-align: left;
}
.button-area {
  margin-top: 24px;
  text-align: center;
}
.feedback-area {
  margin: 32px 0 16px 0;
}
</style>
