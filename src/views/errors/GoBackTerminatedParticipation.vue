<template>
  <b-jumbotron header-level="5">
    <template v-slot:lead>
      Study Terminated
    </template>
    <div class="content-area">
      <div class="alert alert-danger">
        <h4>Your participation has been terminated</h4>
        <p>
          Since you have chosen to go backwards, your participation has been terminated. As mentioned in the consent form,
          the compensation will be decreased for participants who do not complete the entire study.
        </p>
        <p>
          If you believe this is an error, please contact the study administrators with your
          participant ID: {{ $store.state.subject_id }}
        </p>
        <p>Please provide a reason for termination (optional):</p>
        <b-form-checkbox-group v-model="reasons" :options="reasonOptions" />
        <b-form-input v-model="otherReason" placeholder="Other reason" />
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
        <p>Please push the button below to redirect to prolific.</p>
        <b-button
          variant="primary"
          @click="submit"
          :disabled="submitting"
        >
          {{ submitting ? 'Submitting...' : 'Redirect to Prolific' }}
        </b-button>
        <b-alert v-if="feedbackSubmitted" variant="info" class="mt-3">Thank you for your feedback!</b-alert>
      </div>
    </div>
  </b-jumbotron>
</template>

<script>
import axios from 'axios'

export default {
  name: 'GoBackTerminatedParticipation',
  data () {
    return {
      reasons: [],
      otherReason: '',
      reasonOptions: [
        { text: 'Technical issues', value: 'technical_issues' },
        { text: 'Difficulty understanding the task', value: 'difficulty_understanding' },
        { text: 'Other', value: 'other' }
      ],
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
      let body = new FormData()
      body.append('subject_id', this.$store.state.subject_id)
      body.append('status', 'go_back_terminate')
      body.append('reasons', JSON.stringify(this.reasons))
      body.append('other_reason', this.otherReason)
      axios.post(this.$server_url + 'submit_to_prolific', body)
        .then(response => {
          if (response.data.success === true) {
            window.location.href = response.data.prolific_url
          } else {
            alert('Some error happened!! Please leave comments and submit the study on Prolific.')
          }
        })
        .catch(e => {
          alert('Some error happened!! Please leave comments and submit the study on Prolific.' + e)
        })
        .finally(() => { this.submitting = false })
    }
  },
  created () {
    // Optionally notify server about termination
    if (this.$store.state.subject_id) {
      const body = new FormData()
      body.append('subject_id', this.$store.state.subject_id)
      axios.post(this.$server_url + 'terminate_participation', body)
        .catch(error => {
          console.error('Error notifying termination:', error)
        })
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
.feedback-area {
  margin: 32px 0 16px 0;
}
</style>
