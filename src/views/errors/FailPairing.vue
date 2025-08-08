<template>
  <b-jumbotron header-level="5">
    <template v-slot:header>
      <div class="center-lead-text">
        Fail to find group members for you.
      </div>
    </template>
    <template v-slot:lead>
      <div class="lead-boundary">
        <div class="center-lead-text">
          <p>Sorry, we could not find enough people to form a group for the discussion.</p>
          <p>You will be compensated based on your previous tasks' time and waiting time.</p>
          <p>We will bonus you <b>15 cents per minute</b> for your waiting time.</p>
        </div>
      </div>
    </template>

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
      <p>Please push the button below to redirect to prolific.</p>
      <b-button variant="primary" name="next" v-on:click="submit" :disabled="submitting">
        {{ submitting ? 'Submitting...' : 'Submit' }}
      </b-button>
    </div>
    <b-alert v-if="feedbackSubmitted" variant="info" class="mt-3">Thank you for your feedback!</b-alert>
  </b-jumbotron>
</template>
<script>
import axios from 'axios'
export default {
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
      body.append('status', 'failed_pairing')
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
.lead-boundary {
  border: 2px solid #138496;
  border-radius: 10px;
  padding: 16px 12px;
  margin: 0 auto 10px auto;
  background: #f8f9fa;
  display: block;
  max-width: 800px;
  width: 100%;
  text-align: center;
}
.center-lead-text {
  text-align: center;
}
.feedback-area {
  margin: 32px 0 16px 0;
}
</style>
