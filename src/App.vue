<template>
  <div id="app">
    <!-- Hidden iframe for termination requests -->
    <iframe id="termination-frame" style="display: none;"></iframe>
    <div v-if="!isErrorPage" class="early-exit-btn" style="position:absolute; top:1rem; right:1rem; background-color:white; color:black;">
      <b-button size="sm" style="background-color: white; color: black; border: 1px solid #ccc;" @click="confirmEarlyExit">Early Exit</b-button>
    </div>
    <b-modal
      id="early-exit-modal"
      v-model="showEarlyExitModal"
      title="Confirm Early Exit"
      hide-footer
      centered
    >
      <div class="my-3">
        <p>Are you sure you want to exit early? <br>This will terminate your participation in the study.</p>
      </div>
      <div class="d-flex justify-content-end">
        <b-button variant="secondary" class="mr-2" @click="showEarlyExitModal = false">Cancel</b-button>
        <b-button variant="danger" @click="handleEarlyExitConfirm">Yes, Exit</b-button>
      </div>
    </b-modal>
    <router-view :key="$route.fullPath" />
  </div>
</template>

<script>
export default {
  name: 'App',
  computed: {
    isErrorPage () {
      return ['FailPairing', 'GoBackTerminatedParticipation', 'InactivityTerminatedParticipation', 'EarlyExit', 'DeBriefing', 'StarEntrance'].includes(this.$route.name)
    }
  },
  data () {
    return {
      showEarlyExitModal: false,
      isNavigating: false,
      shouldTerminate: false,
      terminationSubjectId: null
    }
  },
  methods: {
    logToServer (logData) {
      // Use sendBeacon for reliability during page unload
      try {
        const url = new URL('client_logs', this.$server_url).toString()
        const data = new FormData()
        data.append('logs', JSON.stringify({
          ...logData,
          timestamp: logData.timestamp || new Date().toISOString(),
          url: window.location.href,
          userAgent: navigator.userAgent
        }))
        navigator.sendBeacon(url, data)
      } catch (e) {
        console.error('Error sending log to server:', e)
      }
    },
    storeLog (level, ...args) {
      if (!window.appLogs) {
        window.appLogs = []
      }
      const timestamp = new Date().toISOString()
      const message = args.map(arg =>
        typeof arg === 'object' ? JSON.stringify(arg) : String(arg)
      ).join(' ')

      window.appLogs.push({ timestamp, level, message })

      // Keep only the last 100 logs to prevent memory issues
      if (window.appLogs.length > 100) {
        window.appLogs = window.appLogs.slice(-100)
      }
    },

    handleUnloadLogs () {
      try {
        if (window.appLogs && window.appLogs.length > 0) {
          const logsToSend = window.appLogs.map(entry =>
            `[${entry.timestamp}] ${entry.level.toUpperCase()}: ${entry.message}`
          ).join('\n')

          // Send logs to server
          const formData = new FormData()
          formData.append('logs', logsToSend)
          formData.append('page', window.location.pathname)
          formData.append('timestamp', new Date().toISOString())

          // Use sendBeacon as it's more reliable during page unload
          navigator.sendBeacon(this.$server_url + 'client_logs', formData)

          // Also log to console for debugging
          window.originalConsole.log('Sending logs before unload:', logsToSend)
        }
      } catch (e) {
        window.originalConsole.error('Error in handleUnloadLogs:', e)
      }
    },
    confirmEarlyExit () {
      this.showEarlyExitModal = true
    },
    handleEarlyExitConfirm () {
      this.showEarlyExitModal = false
      this.$router.push('/EarlyExit')
    },
    handleBeforeUnload (event) {
      // Only show confirmation if this is a tab close/page refresh
      // and not a normal navigation
      if (!this.isNavigating) {
        // Store the subject ID for the unload handler
        this.terminationSubjectId = this.$store.state.subject_id

        // Set flag to indicate we should terminate if unload happens
        this.shouldTerminate = true

        // Show the browser's native dialog
        const message = 'Are you sure you want to leave? You may lose all records and not be compensated.'

        // Standard for most browsers
        event.returnValue = message

        // For browsers that support the modern approach
        if (event.cancelable) {
          event.preventDefault()
        }

        return message // For older browsers
      }
      // For normal navigation, don't show any dialog
      return undefined
    },

    handleUnload () {
      if (this.shouldTerminate && this.terminationSubjectId) {
        console.log('Page unloading, sending termination request for subject:', this.terminationSubjectId)
        const subjectId = this.terminationSubjectId
        const serverUrl = this.$server_url

        // 1. First try: sendBeacon (most reliable for page unload)
        try {
          console.log('Attempting sendBeacon...')
          const url = new URL('terminate_participation', serverUrl).toString()
          const formData = new FormData()
          formData.append('subject_id', subjectId)
          const beaconSent = navigator.sendBeacon(url, formData)
          console.log('sendBeacon result - success:', beaconSent, 'url:', url, 'method: POST (FormData)')
        } catch (e) {
          console.error('Error with sendBeacon:', e)
        }

        // 2. Second try: iframe form submission (works when sendBeacon is blocked)
        try {
          console.log('Attempting iframe form submission...')
          const iframe = document.getElementById('termination-frame')
          if (iframe && iframe.contentWindow) {
            const form = document.createElement('form')
            form.method = 'POST'
            const actionUrl = new URL('terminate_participation', serverUrl).toString()
            form.action = actionUrl

            const input = document.createElement('input')
            input.type = 'hidden'
            input.name = 'subject_id'
            input.value = subjectId

            form.appendChild(input)
            iframe.contentDocument.body.appendChild(form)
            form.submit()
            console.log('iframe form submitted - method: POST, url:', actionUrl)
          } else {
            console.log('Iframe not available for form submission')
          }
        } catch (e) {
          console.error('Error with iframe form method:', e)
        }

        // 3. Third try: Hidden form submission (replaces image beacon)
        try {
          console.log('Attempting hidden form submission...')
          const form = document.createElement('form')
          form.method = 'POST'
          form.action = new URL('terminate_participation', serverUrl).toString()

          const input = document.createElement('input')
          input.type = 'hidden'
          input.name = 'subject_id'
          input.value = subjectId
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

          console.log('Hidden form submitted - method: POST, url:', form.action)
        } catch (e) {
          console.error('Error with hidden form submission:', e)
        }

        // 4. Last resort: fetch with keepalive (works in modern browsers)
        try {
          const url = new URL('terminate_participation', serverUrl).toString()
          const formData = new FormData()
          formData.append('subject_id', subjectId)

          const requestId = 'req_' + Date.now()
          const startTime = performance.now()
          const logData = {
            requestId,
            url,
            method: 'POST',
            timestamp: new Date().toISOString(),
            subjectId,
            status: 'attempting',
            startTime: startTime
          }

          // Log the attempt
          console.log(`[${requestId}] Attempting fetch with keepalive...`, logData)

          // Send initial log to server
          this.logToServer({
            type: 'keepalive_attempt',
            ...logData
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
            const success = response.ok
            const status = response.status

            // Prepare success/error data
            const resultData = {
              ...logData,
              status: success ? 'success' : 'error',
              responseTime: `${responseTime}ms`,
              httpStatus: status,
              response: responseData,
              timestamp: new Date().toISOString()
            }

            // Log to console
            if (success) {
              console.log(`[${requestId}] Fetch with keepalive succeeded`, resultData)
            } else {
              console.error(`[${requestId}] Fetch with keepalive failed with status ${status}`, resultData)
            }

            // Send result to server
            this.logToServer({
              type: success ? 'keepalive_success' : 'keepalive_error',
              ...resultData
            })

            if (!success) {
              throw new Error(`HTTP error! status: ${status}`)
            }
            return responseData
          }).catch(e => {
            const errorTime = Math.round(performance.now() - startTime)
            const errorData = {
              ...logData,
              status: 'error',
              error: e.toString(),
              stack: e.stack,
              responseTime: `${errorTime}ms`,
              timestamp: new Date().toISOString()
            }
            console.error(`[${requestId}] Fetch with keepalive failed after ${errorTime}ms`, errorData)

            // Send error to server
            this.logToServer({
              type: 'keepalive_error',
              ...errorData
            })
          })
        } catch (e) {
          const errorData = {
            error: e.toString(),
            stack: e.stack,
            timestamp: new Date().toISOString(),
            status: 'setup_error'
          }
          console.error('Error in fetch keepalive setup:', errorData)

          // Send setup error to server
          this.logToServer({
            type: 'keepalive_setup_error',
            ...errorData
          })
        }
      }
    },

    handlePageHide (event) {
      // Handle pagehide event (for mobile browsers)
      if (this.shouldTerminate && this.terminationSubjectId) {
        this.handleUnload()
      }
    },
    setupNavigationGuards () {
      // Set flag when navigation starts
      this.$router.beforeEach((to, from, next) => {
        this.isNavigating = true
        next()
      })

      // Reset flag after navigation is complete
      this.$router.afterEach(() => {
        // Use nextTick to ensure the navigation is complete
        // before resetting the flag
        this.$nextTick(() => {
          this.isNavigating = false
        })
      })
    }
  },
  mounted () {
    // Store original console methods
    if (!window.originalConsole) {
      window.originalConsole = {
        log: console.log,
        error: console.error,
        warn: console.warn,
        info: console.info
      }

      // Override console methods to store logs
      console.log = (...args) => {
        this.storeLog('log', ...args)
        window.originalConsole.log(...args)
      }
      console.error = (...args) => {
        this.storeLog('error', ...args)
        window.originalConsole.error(...args)
      }
      console.warn = (...args) => {
        this.storeLog('warn', ...args)
        window.originalConsole.warn(...args)
      }
      console.info = (...args) => {
        this.storeLog('info', ...args)
        window.originalConsole.info(...args)
      }
    }

    // Initialize logs array if it doesn't exist
    if (!window.appLogs) {
      window.appLogs = []
    }

    this.setupNavigationGuards()
    window.addEventListener('beforeunload', this.handleBeforeUnload)
    window.addEventListener('unload', this.handleUnloadLogs)
    window.addEventListener('unload', this.handleUnload)
    // Add pagehide event for mobile browsers
    window.addEventListener('pagehide', this.handlePageHide)
  },
  beforeDestroy () {
    window.removeEventListener('beforeunload', this.handleBeforeUnload)
    window.removeEventListener('unload', this.handleUnload)
    window.removeEventListener('pagehide', this.handlePageHide)
  }
}
</script>

<style>
/* Add global styles if needed */
</style>
