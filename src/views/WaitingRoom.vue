<template>
  <div>
    <!-- Hidden iframe for termination requests -->
    <iframe id="termination-frame" style="display: none;"></iframe>
    <b-jumbotron header-level="5">
    <div class="content-area"><div class="page-indicator text-center mb-1">Page: 5 / 9</div></div>
    <template v-slot:header>
      Pairing You with Other Participants
    </template>

    <div class="content-area">
      <p>
        We are pairing you with other participants to start the discussion task.
        <strong style="color: blue;">Please turn on audio on your device.</strong>
        Once all of the group members arrive, we will notify you with a sound and redirect you to the next page.
      </p>
      <p>
        If no other group member is paired in 5 minutes, we will redirect you back to Prolific. <br>
        <strong style="color: blue;">But don't worry, you will still be paid for your time.</strong>
      </p>
      <p>
        We will bonus you <b>15 cents per minute</b> for your waiting time.<br>
        The average waiting time is <b>{{ displayWaitingTime }}</b> seconds.
      </p>

      <CountdownTimer :remain_time="remainingTime" /> <!-- ⏳ Countdown Timer -->
    </div>

    <div class="pairing-info">
      <p v-if="isPairing"><b>Finding a suitable group...</b></p>
      <p v-else-if="pairingFailed" class="text-danger"><b>Pairing failed. Redirecting...</b></p>
      <p v-else-if="!has_capacity" class="text-success"><b>Pairing successful! Redirecting...</b></p>

      <!-- Test button for debugging unload behavior -->
      <b-button
        v-if="!isProduction"
        @click="testUnloadHandler"
        variant="outline-danger"
        size="sm"
        class="mt-3">
        Test Unload Handler
      </b-button>
    </div>

    <b-spinner v-if="isPairing" label="Loading..."></b-spinner>

    <b-alert v-if="pairingFailed" variant="danger" dismissible>
      We couldn't find a suitable group. You will be redirected shortly.
    </b-alert>

    <div v-if="!isPairing && !isTimedOut" class="text-center mt-4">
    </div>

    </b-jumbotron>
  </div>
</template>

<script>
import axios from 'axios'
import CountdownTimer from '@/components/CountdownTimer.vue'

export default {
  components: {
    CountdownTimer
  },
  data () {
    return {
      isPairing: true,
      pairingFailed: false,
      pollInterval: null,
      timeout: null,
      remainingTime: 300, // 5 minutes countdown
      average_waiting_time: 10,
      has_capacity: false,
      memberLeftToastId: null,
      isNavigating: false,
      shouldTerminate: false,
      isProduction: this.$store.state.test === 'N' // Hide test button in production
    }
  },
  computed: {
    displayWaitingTime () {
      // Ensure we're displaying a valid number
      const waitTime = this.average_waiting_time - 5
      return typeof waitTime === 'number' && !isNaN(waitTime) && waitTime > 0 ? waitTime : 5
    }
  },
  methods: {
    // Test method to simulate unload behavior
    async testUnloadHandler () {
      console.log('Testing unload handler...')
      try {
        // Show a toast notification
        this.$bvToast.toast('Testing unload handler. Check console for details.', {
          title: 'Test Mode',
          variant: 'info',
          solid: true,
          autoHideDelay: 5000
        })

        // Call the same method that's called during unload
        await this.sendNotReady()

        // Log success
        console.log('Test unload handler completed successfully')
      } catch (error) {
        console.error('Error in testUnloadHandler:', error)
      }
    },

    proceedToNextSurvey (toastId) {
      // Hide the notification
      if (toastId) {
        this.$bvToast.hide(toastId)
      } else if (this.memberLeftToastId) {
        this.$bvToast.hide(this.memberLeftToastId)
      }
      // Navigate to the next survey
      this.$router.push('/PostDOSurvey')
    },

    showMemberLeftNotification (message = 'Due to certain reasons, a group member has left the chat. However, the study will continue. Please click the button to proceed to the next survey.') {
      console.log('Showing member left notification with message:', message)

      // Show initial notification
      this.$bvToast.toast('You were successfully grouped, but before finalizing the environment, one group member has left.', {
        title: 'Grouping Update',
        variant: 'info',
        solid: true,
        noAutoHide: true,
        noCloseButton: true
      })

      // Show member left notification after a short delay
      setTimeout(() => {
        const toastId = `member-left-${Date.now()}`
        this.memberLeftToastId = toastId

        // Create a simple toast with just the message first
        this.$bvToast.toast(message, {
          id: toastId,
          title: 'Member Left',
          variant: 'warning',
          solid: true,
          noAutoHide: true,
          noCloseButton: true,
          noHoverPause: true
        })

        // After a short delay, find the toast and add our button
        this.setupMemberLeftToast(toastId, message)
      }, 10000) // 10 second delay before showing member left notification
    },

    setupMemberLeftToast (toastId, message) {
      setTimeout(() => {
        // Hide any existing member left toasts
        if (this.memberLeftToastId && this.memberLeftToastId !== toastId) {
          this.$bvToast.hide(this.memberLeftToastId)
        }

        // Find the toast element
        const toastElement = document.getElementById(toastId)
        if (toastElement) {
          // Create the button
          const button = document.createElement('button')
          button.className = 'btn btn-primary btn-sm mt-2'
          button.textContent = 'Proceed to Next Survey'
          button.onclick = () => this.proceedToNextSurvey(toastId)

          // Find the toast body and append the button
          const toastBody = toastElement.querySelector('.toast-body')
          if (toastBody) {
            toastBody.appendChild(button)
          }
        }
      }, 100) // Small delay to ensure toast is in the DOM

      return toastId
    },

    startPairing () {
      this.startCountdown()
      this.setReadyToPair()
      this.checkPairingStatus()
      this.pollInterval = setInterval(this.checkPairingStatus, 5000) // Poll every 5s
      this.timeout = setTimeout(this.failPairing, 300000) // Redirect after 5 minutes
    },
    updateAverageWaitingTime (averageWaitingTime) {
      // Ensure we have a valid number
      this.average_waiting_time = typeof averageWaitingTime === 'number' && !isNaN(averageWaitingTime) ? averageWaitingTime : 10
    },
    checkPairingStatus () {
      const subjectId = this.$store.state.subject_id
      if (!subjectId || subjectId === -1) {
        console.error('No subject ID found')
        this.failPairing()
        return
      }
      let body = new FormData()
      body.append('subject_id', subjectId)
      axios.post(this.$server_url + 'pairing', body)
        .then(response => {
          console.log('Pairing response:', response.data)
          this.updateAverageWaitingTime(response.data.average_waiting_time)
          if (response.data.success) {
            clearInterval(this.pollInterval) // Stop polling on success
            this.$store.commit('assign_group_id', { group_id: response.data.group_id })
            this.$root.initWebSocket()
          }
        })
        .catch(error => {
          console.error('Error during pairing:', error)
        })
    },

    failPairing () {
      clearInterval(this.pollInterval)
      clearTimeout(this.timeout)
      this.isPairing = false
      this.pairingFailed = true
      this.setNotReadyToPair()
      this.$root.alarm_sound.play() // 🔊 Play failure sound
      setTimeout(() => {
        this.$router.push('/FailPairing') // ❌ Redirect to fail page
      }, 3000)
    },

    startCountdown () {
      const countdownInterval = setInterval(() => {
        if (this.remainingTime > 0) {
          this.remainingTime--
        } else {
          clearInterval(countdownInterval)
        }
      }, 1000) // Decrease timer every second
    },

    setReadyToPair () {
      const subjectId = this.$store.state.subject_id
      if (!subjectId || subjectId === -1) {
        console.error('No subject ID found for setting ready_to_pair')
        return
      }
      let body = new FormData()
      body.append('subject_id', subjectId)
      axios.post(this.$server_url + 'set_pipei', body)
        .then(response => {
          // console.log('Set ready to pair response:', response.data)
        })
        .catch(error => {
          console.error('Error setting ready to pair:', error)
        })
    },
    setNotReadyToPair () {
      const subjectId = this.$store.state.subject_id
      if (!subjectId || subjectId === -1) {
        console.error('No subject ID found for setting not ready_to_pair')
        return
      }
      let body = new FormData()
      body.append('subject_id', subjectId)
      axios.post(this.$server_url + 'set-not-ready', body)
        .then(response => {
          // console.log('Set not ready to pair response:', response.data)
        })
        .catch(error => {
          console.error('Error setting not ready to pair:', error)
        })
    },
    sendNotReadyBeacon () {
      const subjectId = this.$store.state.subject_id
      if (!subjectId || subjectId === -1) {
        console.log('No valid subject ID, skipping set-not-ready')
        return
      }

      const serverUrl = this.$server_url
      const endpoint = 'set-not-ready'
      const subjectIdStr = String(subjectId)

      console.log('Attempting to send set-not-ready for subject:', subjectIdStr)

      // 1. First try: sendBeacon (most reliable for page unload)
      try {
        console.log('Attempting sendBeacon for set-not-ready...')
        const url = new URL(endpoint, serverUrl).toString()
        const formData = new FormData()
        formData.append('subject_id', subjectIdStr)
        const beaconSent = navigator.sendBeacon(url, formData)
        console.log('sendBeacon result for set-not-ready - success:', beaconSent, 'url:', url, 'method: POST (FormData)')
      } catch (e) {
        console.error('Error with sendBeacon for set-not-ready:', e)
      }

      // 2. Second try: iframe form submission (works when sendBeacon is blocked)
      try {
        console.log('Attempting iframe form submission for set-not-ready...')
        const iframe = document.getElementById('termination-frame')
        if (iframe && iframe.contentWindow) {
          const form = document.createElement('form')
          form.method = 'POST'
          const actionUrl = new URL(endpoint, serverUrl).toString()
          form.action = actionUrl

          const input = document.createElement('input')
          input.type = 'hidden'
          input.name = 'subject_id'
          input.value = subjectIdStr

          form.appendChild(input)
          iframe.contentDocument.body.appendChild(form)
          form.submit()
          console.log('iframe form submitted for set-not-ready - method: POST, url:', actionUrl)
        } else {
          console.log('Iframe not available for form submission')
        }
      } catch (e) {
        console.error('Error with iframe form method for set-not-ready:', e)
      }

      // 3. Third try: Hidden form submission (replaces image beacon)
      try {
        console.log('Attempting hidden form submission for set-not-ready...')
        const form = document.createElement('form')
        form.method = 'POST'
        form.action = new URL(endpoint, serverUrl).toString()

        const input = document.createElement('input')
        input.type = 'hidden'
        input.name = 'subject_id'
        input.value = subjectIdStr
        form.appendChild(input)

        // Create a hidden iframe to handle the form submission
        const iframe = document.createElement('iframe')
        iframe.name = 'post-iframe-' + Date.now()
        iframe.style.display = 'none'
        form.target = iframe.name

        // Add to document and submit
        document.body.appendChild(iframe)
        document.body.appendChild(form)
        form.submit()

        // Clean up after a short delay
        setTimeout(() => {
          if (document.body.contains(iframe)) {
            document.body.removeChild(iframe)
          }
          if (document.body.contains(form)) {
            document.body.removeChild(form)
          }
        }, 1000)

        console.log('Hidden form submitted for set-not-ready - method: POST, url:', form.action)
      } catch (e) {
        console.error('Error with hidden form submission for set-not-ready:', e)
      }

      // 4. Last resort: fetch with keepalive (works in modern browsers)
      try {
        const url = new URL(endpoint, serverUrl).toString()
        const formData = new FormData()
        formData.append('subject_id', subjectIdStr)

        const requestId = 'req_' + Date.now()
        const startTime = performance.now()

        console.log(`[${requestId}] Attempting fetch with keepalive for set-not-ready...`, {
          url,
          method: 'POST',
          timestamp: new Date().toISOString(),
          subjectId: subjectIdStr
        })

        // Use fetch with keepalive for better reliability during page unload
        fetch(url, {
          method: 'POST',
          body: formData,
          keepalive: true,
          headers: {
            'X-Requested-With': 'XMLHttpRequest',
            'X-Request-ID': requestId
          }
        }).then(async response => {
          const responseTime = Math.round(performance.now() - startTime)
          const responseData = await response.text()

          if (!response.ok) {
            console.error(`[${requestId}] Fetch with keepalive for set-not-ready completed with error`, {
              status: response.status,
              statusText: response.statusText,
              response: responseData,
              responseTime: `${responseTime}ms`,
              url
            })
            throw new Error(`HTTP error! status: ${response.status}`)
          }

          console.log(`[${requestId}] Fetch with keepalive for set-not-ready succeeded`, {
            status: response.status,
            response: responseData,
            responseTime: `${responseTime}ms`,
            url
          })
          return responseData
        }).catch(e => {
          const errorTime = Math.round(performance.now() - startTime)
          console.error(`[${requestId}] Fetch with keepalive for set-not-ready failed after ${errorTime}ms`, {
            error: e.toString(),
            url,
            stack: e.stack
          })
        })
      } catch (e) {
        console.error('Error in fetch keepalive setup for set-not-ready:', {
          error: e.toString(),
          stack: e.stack,
          timestamp: new Date().toISOString()
        })
      }
    },

    // Send not ready using all available methods
    sendNotReady () {
      this.sendNotReadyBeacon()
    },

    setupNavigationGuards () {
      // Set flag when navigation starts
      this.$router.beforeEach((to, from, next) => {
        this.isNavigating = true
        if (from.path === this.$route.path && to.path !== this.$route.path) {
          this.setNotReadyToPair()
        }
        next()
      })

      // Reset flag after navigation is complete
      this.$router.afterEach(() => {
        this.$nextTick(() => {
          this.isNavigating = false
        })
      })
    },

    handleBeforeUnload (event) {
      // Only show confirmation if this is a tab close/page refresh
      if (!this.isNavigating) {
        // Don't set any flags here, just show the confirmation
        const message = 'Are you sure you want to leave? You may lose your place in the queue.'
        event.returnValue = message
        if (event.cancelable) {
          event.preventDefault()
        }
        return message
      }
      return undefined
    },

    handlePageHide (event) {
      // Only send not-ready if this is not a page navigation and the page is not being restored from bfcache
      if (!this.isNavigating && !event.persisted) {
        console.log('Page is being hidden, sending not-ready')
        this.sendNotReady()
      }
    },

    // Keep handleUnload for older browsers that don't support pagehide
    handleUnload () {
      // This is a fallback and will only run if pagehide didn't fire
      if (!this.isNavigating && !window.performance.getEntriesByType('navigation').some(nav => nav.type === 'back_forward')) {
        console.log('Page is unloading (fallback), sending not-ready')
        this.sendNotReady()
      }
    }
  },

  mounted () {
    // Scroll to top when component is mounted
    window.scrollTo(0, 0)
    this.startPairing()

    // Set up navigation guards
    this.setupNavigationGuards()

    // Set up unload handlers
    window.addEventListener('beforeunload', this.handleBeforeUnload)
    window.addEventListener('pagehide', this.handlePageHide)
    window.addEventListener('unload', this.handleUnload) // Fallback for older browsers
  },

  watch: {
    '$store.state.memberLeftChat': {
      handler (newVal) {
        console.group('memberLeftChat watcher triggered in WaitingRoom')
        console.log('New value:', newVal)
        console.log('leftMemberMessage:', this.$store.state.leftMemberMessage)
        console.groupEnd()

        if (newVal === true) {
          const message = this.$store.state.leftMemberMessage || 'Due to certain reasons, a group member has left the chat. However, the study will continue. Please click the button to proceed to the next survey.'
          console.log('Member left chat detected in WaitingRoom - showing notification:', message)
          this.showMemberLeftNotification(message)
        }
      }
    }
  },

  beforeDestroy () {
    console.log('WaitingRoom component destroying, sending not-ready')
    // Only send not-ready if this is not a normal navigation
    if (!this.isNavigating) {
      this.sendNotReady()
    }

    // Clean up intervals and timeouts
    clearInterval(this.pollInterval)
    clearTimeout(this.timeout)

    // Remove event listeners
    window.removeEventListener('beforeunload', this.handleBeforeUnload)
    window.removeEventListener('pagehide', this.handlePageHide)
    window.removeEventListener('unload', this.handleUnload)

    // Clear any member left notifications
    if (this.memberLeftToastId) {
      this.$bvToast.hide(this.memberLeftToastId)
    }
  }
}
</script>

<style scoped>
.content-area {
  font-size: 1rem;
  line-height: 1.5;
}

.highlight {
  color: red;
  font-weight: bold;
}

.pairing-info {
  margin-top: 20px;
}

.text-danger {
  color: red;
}

.text-success {
  color: green;
}
</style>
