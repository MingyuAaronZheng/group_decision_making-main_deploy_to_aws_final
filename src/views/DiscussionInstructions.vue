<template>
  <b-jumbotron header="Discussion Instructions" header-level="4" class="mb-4 fs-5">
    <div class="content-area"><div class="page-indicator text-center mb-1">Page: 4 / 9</div></div>
    <div class="content-area bg-light p-4 rounded">
      <h5 class="mt-3 mb-2">What to Expect</h5>
      <p class="mb-3">
        By using our chat platform, you will participate in a turn-based discussion about a policy that you previously answered in the questionnaire.
        Your randomly paired discussion partner may or may not share the same attitude as you regarding this policy.
        For anonymity, your name in the discussion will be randomly generated as an animal name.
      </p>
      <p class="mb-3">
        <b>AI Chatbot:</b> During the discussion, you may encounter AI chatbot(s) with different roles, such as participating or moderating the discussion.
        The AI chatbot's roles will be indicated by their names.
      </p>

      <h5 class="mt-4 mb-2">Discussion Rules</h5>
      <b-list-group class="mb-3">
        <b-list-group-item class="px-3 py-3 mb-3 bg-white border rounded"><strong>Explain Your Position:</strong> Begin by briefly explaining your stance on the policy.</b-list-group-item>
        <b-list-group-item class="px-3 py-3 mb-3 bg-white border rounded">
          <strong>Message Length:</strong>
          Each message must contain at least
          <span style="background-color: #ffe066; font-weight: bold;">10</span>
          meaningful words. Filler words (such as "um", "well", "like") and repeated words don't count toward this minimum.
        </b-list-group-item>
        <b-list-group-item class="px-3 py-3 mb-3 bg-white border rounded"><strong>Take Turns to Speak:</strong> If you see "<i>[Participant Name, e.g., pink tiger] is typing</i>" on the interface, wait until the indicator disappears before responding.</b-list-group-item>
        <b-list-group-item class="px-3 py-3 mb-3 bg-white border rounded">
          <strong>Duration:</strong> After taking <span style="background-color: #ffe066; font-weight: bold;">4</span> discussion turns, you may continue or proceed to the exit survey.
        </b-list-group-item>
        <b-list-group-item class="px-3 py-3 mb-3 bg-white border rounded"><strong>Exit Options:</strong> You may leave anytime without penalty.</b-list-group-item>
        <b-list-group-item class="px-3 py-3 mb-3 bg-white border rounded"><strong style="color: blue;">No Copy-Pasting:</strong> <span style="color: blue;">Copy-pasting is disabled to ensure original opinions.</span></b-list-group-item>
      </b-list-group>
    </div>

    <!-- Tutorial video (local .mp4) -->
    <h5 class="mt-4 mb-2 text-center">Tutorial Video</h5>
    <div class="content-area mb-4">
      <div class="video-container">
        <video
          ref="tutorialVideo"
          :src="dropboxRawUrl"
          preload="metadata"
          class="w-100 rounded"
          @ended="onVideoEnded"
        >
          Sorry, your browser doesn't support embedded videos.
        </video>
        <div class="custom-controls">
          <b-button
            variant="warning"
            @click="togglePlay"
            class="play-pause-btn"
            size="lg"
          >
            <b-icon :icon="isPlaying ? 'pause-fill' : 'play-fill'" class="mr-2"></b-icon>
            {{ isPlaying ? 'Pause' : 'Play' }}
          </b-button>
        </div>
      </div>
      <div v-show="!videoEnded" class="text-center mt-2 text-muted">
        Please watch the full tutorial to unlock the Next button.
      </div>
      <div v-if="this.$store.state.test==='Y'" class="button-area text-center mt-4">
      <b-button variant="primary" name="next" @click="enableNext">Enable Next (Test mode only)</b-button>
    </div>
    </div>
    <div class="button-area text-center mt-4">
      <b-button variant="primary" name="next" @click="goToWaitingRoom" :disabled="!videoEnded || !quizSubmitted">Next</b-button>
    </div>

    <!-- Quiz Modal -->
    <b-modal
      v-model="showQuiz"
      title="Quick Check"
      size="lg"
      hide-footer
      no-close-on-backdrop
      no-close-on-esc
      hide-header-close
      class="quiz-modal"
    >
      <div class="quiz-content">
        <p class="mb-4">Which of the following statements is incorrect?</p>
        <b-form-group>
          <b-form-radio-group
            v-model="selectedAnswer"
            :options="quizOptions"
            stacked
          ></b-form-radio-group>
        </b-form-group>
        <div class="text-center mt-4">
          <b-button
            variant="primary"
            @click="submitQuiz"
            :disabled="!selectedAnswer"
            size="lg"
          >
            Submit Answer
          </b-button>
        </div>
      </div>
    </b-modal>
  </b-jumbotron>
</template>

<script>
export default {
  data () {
    return {
      videoEnded: false,
      dropboxRawUrl: 'https://dl.dropboxusercontent.com/scl/fi/h1xnumflaz8ex9w249bul/tutorial.mp4?rlkey=o94vlehz5y03elpy2oqp3kvjr&st=qndk5bsj&dl=0',
      isPlaying: false,
      showQuiz: false,
      selectedAnswer: '',
      quizSubmitted: false,
      quizOptions: [
        'One turn requires all participants to post at least one message.',
        'I could proceed to the next survey only if all members agreed to end the discussion.',
        'The "End" button will appear after 3 discussion turns.'
      ]
    }
  },
  mounted () {
    window.scrollTo(0, 0)
    const video = this.$refs.tutorialVideo
    if (video) {
      video.addEventListener('play', this.handlePlay)
      video.addEventListener('pause', this.handlePause)
    }
  },
  beforeDestroy () {
    const video = this.$refs.tutorialVideo
    if (video) {
      video.removeEventListener('play', this.handlePlay)
      video.removeEventListener('pause', this.handlePause)
    }
  },
  methods: {
    onVideoEnded () {
      this.videoEnded = true
      this.isPlaying = false
      this.showQuiz = true
    },
    enableNext () {
      this.videoEnded = true
      this.quizSubmitted = true
    },
    goToWaitingRoom () {
      this.$router.push('/WaitingRoom')
    },
    togglePlay () {
      const video = this.$refs.tutorialVideo
      if (video) {
        if (video.paused) {
          video.play()
        } else {
          video.pause()
        }
      }
    },
    handlePlay () {
      this.isPlaying = true
    },
    handlePause () {
      this.isPlaying = false
    },
    async submitQuiz () {
      if (!this.$store.state.subject_id) {
        console.error('No subject ID found in store')
        this.$alert('Session error: No subject ID found. Please refresh the page.', 'Error', { icon: 'error' })
        return
      }

      if (!this.selectedAnswer) {
        this.$alert('Please select an answer before submitting.', 'Error', { icon: 'warning' })
        return
      }

      try {
        const body = new FormData()
        body.append('subject_id', this.$store.state.subject_id)
        body.append('answer', this.selectedAnswer)

        console.log('Submitting quiz with data:', {
          subject_id: this.$store.state.subject_id,
          answer: this.selectedAnswer
        })

        const response = await this.$axios.post(this.$server_url + 'submit_video_quiz/', body)

        console.log('Quiz submission response:', response)

        if (response.data.success) {
          this.quizSubmitted = true
          this.showQuiz = false
          this.$alert('Thank you for your response. You can now proceed to the next page.', 'Quiz Completed', { icon: 'success' })
        } else {
          console.error('Quiz submission failed. Response:', response.data)
          const errorMsg = response.data.error || response.data.message || 'Unknown error'
          this.$alert(`Failed to submit quiz: ${errorMsg}`, 'Error', { icon: 'error' })
        }
      } catch (error) {
        console.error('Error submitting quiz. Full error:', error)
        console.error('Error response data:', error.response?.data)
        console.error('Error status:', error.response?.status)

        let errorMsg = 'Network error'
        if (error.response?.data?.error) {
          errorMsg = error.response.data.error
        } else if (error.response?.data?.message) {
          errorMsg = error.response.data.message
        } else if (error.message) {
          errorMsg = error.message
        }

        this.$alert(`Failed to submit quiz: ${errorMsg}`, 'Error', { icon: 'error' })
      }
    }
  }
}
</script>

<style scoped>
.button-area {
  text-align: center;
  margin-top: 20px;
}

.video-container {
  position: relative;
  width: 100%;
  height: 95vh;
  margin: 0 auto;
}

/* Hide native video controls */
video::-webkit-media-controls {
  display: none !important;
}

video::-webkit-media-controls-enclosure {
  display: none !important;
}

video::-webkit-media-controls-panel {
  display: none !important;
}

/* Firefox */
video::-moz-media-controls {
  display: none !important;
}

.custom-controls {
  position: absolute;
  bottom: 20px;
  left: 0;
  right: 0;
  display: flex;
  justify-content: center;
  z-index: 2;
}

.play-pause-btn {
  min-width: 120px;
  opacity: 1;
  font-weight: bold;
  font-size: 1.1rem;
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.3);
  border: 3px solid #fff;
  background: linear-gradient(45deg, #ffc107, #ff8c00);
  color: #000;
  transition: all 0.3s ease;
}

.play-pause-btn:hover {
  transform: scale(1.05);
  box-shadow: 0 6px 12px rgba(0, 0, 0, 0.4);
  background: linear-gradient(45deg, #ff8c00, #ff6b00);
}

video {
  background: black;
  width: 100%;
  height: 100%;
  object-fit: contain;
}

.quiz-content {
  padding: 1rem;
}

/* Make quiz modal larger */
.quiz-modal .modal-dialog {
  max-width: 800px;
  width: 90%;
}

.quiz-modal .modal-content {
  min-height: 400px;
}

.quiz-modal .modal-body {
  padding: 2rem;
  font-size: 1.1rem;
}

.quiz-modal .modal-title {
  font-size: 1.5rem;
  font-weight: bold;
}

/* Style radio buttons */
.custom-control-label {
  padding: 0.5rem 0;
  cursor: pointer;
}

.custom-radio .custom-control-input:checked ~ .custom-control-label::before {
  background-color: #007bff;
  border-color: #007bff;
}
</style>
