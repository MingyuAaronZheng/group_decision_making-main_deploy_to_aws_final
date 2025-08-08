<template>
  <div class="chat-room">
    <!-- Hidden iframe for finish_chat during unload -->
    <iframe id="finish-chat-frame" style="display: none;"></iframe>
    <div class="page-indicator text-center mb-1">Page: 6 / 9</div>
    <!-- Chat Statement, User's Stance, and User's Name with Instructions -->
    <b-row class="align-items-start mb-3 mx-0 no-gutters">
      <!-- Left Column: User Info -->
      <b-col md="7" class="statement-area">
        <p class="chat-statement">
          <strong>Discussion Topic:</strong> {{ chat_statement }}
        </p>
        <div class="user-info">
          <v-animal size="45px" :name="$store.state.avatar_name" :color="$store.state.avatar_color" class="avatar-icon"/>
          <span class="info-item"><strong>Your Name:</strong> {{ avatar_full_name }}</span>
          <span class="info-divider">|</span>
          <span class="info-item"><strong>Your Stance:</strong> {{ user_stance }}</span>
        </div>
      </b-col>

      <!-- Right Column: Special Instructions for Third Person -->
      <b-col v-if="$store.state.participant_condition === 3 && $store.state.is_third_person" md="5">
        <div class="third-person-instructions p-3" style="background-color: #f8f9fa; border-radius: 8px; border-left: 4px solid #ffc107; height: 100%; font-size: 1.2rem;">
          <h3 class="mb-3" style="font-size: 1.4rem;">Special Instructions for You</h3>
          <div class="mb-3" style="font-size: 1.15rem;">We will bonus you if you do well in this task.</div>
          <div v-if="$store.state.random_third_person_prompt === 0" class="advocating-prompt mt-2">
            <h4 class="text-center p-2" style="background-color: #fff3cd; border-radius: 4px; display: inline-block; margin: 0 auto; display: block; width: fit-content; font-size: 1.4rem; margin-bottom: 0.8rem !important;">Advocating Role</h4>
            <p style="font-size: 1.2rem; margin-bottom: 0.8rem;">Your specific task is to <strong style="background-color: #fff3cd; padding: 0 6px; border-radius: 3px; font-size: 1.25rem;">ALWAYS advocate</strong> your own position. Try to:</p>
            <ul class="text-left pl-3" style="margin-bottom: 0; font-size: 1.15rem; padding-left: 1.5rem;">
              <li><strong>Champion your stance:</strong> Consistently highlight its benefits, principles, and supporting evidence—use facts, logic, and real-world examples to build a clear, positive case.</li>
              <li><strong>Stay in your own lane:</strong> Do not mention, quote, or critique the opposing side's arguments, examples, or wording; keep every statement focused solely on strengthening your position.</li>
              <li><strong>Advance, don't rebut:</strong> When the other side speaks, ignore their points and offer fresh reasons or illustrations that reinforce your stance rather than responding to or comparing with theirs.</li>
            </ul>
          </div>
          <div v-else class="disputing-prompt mt-2">
            <h4 class="text-center p-2" style="background-color: #fff3cd; border-radius: 4px; display: inline-block; margin: 0 auto; display: block; width: fit-content; font-size: 1.4rem; margin-bottom: 0.8rem !important;">Disputing Role</h4>
            <p style="font-size: 1.2rem; margin-bottom: 0.8rem;">Your specific task is to <strong style="background-color: #fff3cd; padding: 0 6px; border-radius: 3px; font-size: 1.25rem;">ALWAYS dispute</strong> the position of others who hold opposite views to yours. Try to:</p>
            <ul class="text-left pl-3" style="margin-bottom: 0; font-size: 1.15rem; padding-left: 1.5rem;">
              <li><strong>Zero-in on others' position:</strong> Use evidence, logic, and real-world examples to expose weaknesses, gaps, or harmful implications in the opponent's stance—every statement should chip away at their argument.</li>
              <li><strong>Don't bring up your own side:</strong> Do not mention or praise your own preferred view; avoid presenting its benefits, solutions, or supporting data—focus solely on why the opponent's idea falls short.</li>
              <li><strong>Counter, don't cultivate:</strong> When the other side speaks, reply with fresh critiques that undermine their point rather than offering alternative proposals or positive cases for any viewpoint.</li>
            </ul>
          </div>
        </div>
      </b-col>
    </b-row>

    <!-- Ready to End Button in Top Panel -->
    <div v-if="canExit" class="ready-to-end-area d-flex justify-content-center my-2">
      <div :style="isReadyToEnd ? 'max-width: 250px; width: 100%;' : 'max-width: 400px; width: 100%;'">
        <b-button
          @click="handleReadyToEnd"
          :variant="isReadyToEnd ? 'success' : 'warning'"
          class="exit-button w-100"
          :disabled="isReadyToEnd"
          style="white-space: normal;"
        >
          <span style="padding: 2px 6px; border-radius: 4px; font-weight: bold;">
            {{ isReadyToEnd ? 'You indicated you are ready to end the discussion. We are waiting for other participants to do the same.' : 'When you are ready to end the discussion, click this button' }}
          </span>
        </b-button>
      </div>
    </div>

    <!-- System Messages Display Area -->
    <div class="chat-container">
      <div class="messages-wrapper">
        <!-- System Messages Display Area and Chat -->
        <div class="room-area" ref="roomarea">
          <!-- System Messages always show at the top, scroll up with chat -->
          <div v-for="(sysMsg, idx) in systemMessages" :key="'sysmsg-' + idx" class="message-card system-message">
            <b-row>
              <b-col cols="12">
                <div class="system-message-content">
                  <span v-html="sysMsg"></span>
                </div>
              </b-col>
            </b-row>
          </div>
          <!-- Chat Messages Display Area -->
          <div v-for="message in messages" :key="message.id" class="message-card">
            <!-- AI Messages -->
            <b-row v-if="message.sender.subject_id < -1">
              <b-col cols="1" class="vertical-align">
                <div class="message-avatar-icon">
                  <!-- Different icons for different AI roles -->
                  <div class="ai-icon-container" :style="{ backgroundColor: getAIColorHex(message.sender.subject_id) }">
                    <img :src="getAIIcon(message.sender.subject_id)" class="circle-icon" style="color: white; width: 30px; height: 30px;"/>
                  </div>
                </div>
              </b-col>
              <b-col cols="9" style="padding-left: 0;">
                <b-row>
                  <b-col class="message-avatar-name">
                <span :style="{ color: message.sender.avatar_color }">
                  {{ message.sender.avatar_color }} {{ message.sender.avatar_name }}
                </span>
              </b-col>
                </b-row>
                <b-row>
                  <b-col>
                    <div class="message-content">
                      <span>{{ message.content }}</span>
                    </div>
                  </b-col>
                </b-row>
              </b-col>
            </b-row>

            <!-- Other Users' Messages -->
            <b-row v-else-if="message.sender.subject_id !== $store.state.subject_id">
              <b-col cols="1" class="vertical-align">
                <div class="message-avatar-icon">
                  <v-animal size="30px" :name="message.sender.avatar_name"
                            :color="message.sender.avatar_color"
                            class="avatar-icon"/>
                </div>
              </b-col>
              <b-col cols="9" style="padding-left: 0;">
                <b-row>
                  <b-col class="message-avatar-name" :style="{ color: message.sender.avatar_color }">{{message.sender.avatar_color }} {{ message.sender.avatar_name }}</b-col>
                </b-row>
                <b-row>
                  <b-col>
                    <div class="message-content">
                      <span>{{ message.content }}</span>
                    </div>
                  </b-col>
                </b-row>
              </b-col>
            </b-row>

            <!-- Current User's Messages -->
            <b-row v-else class="own_message">
              <b-col cols="2"/>
              <b-col cols="9" style="padding-right: 15px;">
                <b-row style="margin-right: 0;" class="justify-content-end">
                  <b-col class="current-user-avatar-name text-end" style="text-align: right; width: 100%;" >{{ avatar_full_name }} (You)</b-col>
                </b-row>
                <b-row style="margin-left: 0;">
                  <b-col>
                    <div class="message-content">
                      <span>{{ message.content }}</span>
                    </div>
                  </b-col>
                </b-row>
              </b-col>
              <b-col cols="1" class="vertical-align" style="text-align: left; padding-right: 0; padding-left: 10px;">
                <div class="message-avatar-icon">
                  <v-animal size="30px" :name="$store.state.avatar_name"
                            :color="$store.state.avatar_color"
                            class="avatar-icon"/>
                </div>
              </b-col>
            </b-row>
          </div>
        </div>
      </div>
    </div>

    <!-- Typing Notifications -->
    <div v-if="typingNotification" class="typing-notifications">
      <p class="typing-indicator">
        <span :style="{ color: avatarColorHex(typingNotification.avatar_color) }">
          {{ typingNotification.avatar_color }} {{ typingNotification.avatar_name }}
        </span> is typing...
      </p>
      <p v-if="isAITyping" class="typing-disabled-note">
        Send button is disabled while AI is typing.
      </p>
    </div>

    <!-- Chat Input Area -->
    <div class="message-area">
      <b-input-group>
        <b-form-textarea
          placeholder="Type a message..."
          v-model="send_out_message"
          class="message-input-area"
          rows="1"
          max-rows="5"
          resize="none"
          @keydown.enter.native.exact.prevent="sendMessage"
          @paste="handlePaste"
          @copy="handleCopy"
          @cut="handleCut"
          :disabled="isAITyping"
        />
        <b-button
          variant='success'
          class="message-send-button"
          v-on:click="sendMessage"
          :disabled="isAITyping"
        >
          Send
        </b-button>
      </b-input-group>
    </div>

    <!-- Ready to End Button moved to top panel -->
  </div>
</template>

<script>
import { colors } from '@/components/constants'
import axios from 'axios'
import { notifyInactivity } from '@/plugins/notificationService.js'
import MemberLeftToast from '@/components/MemberLeftToast.vue'

const CUSTOM_FILLER_WORDS = new Set([
  'um', 'uh', 'er', 'ah', 'like', 'okay', 'right', 'you know', 'i mean',
  'well', 'so', 'anyway', 'basically', 'actually', 'literally', 'just'
])

export default {
  components: {
    MemberLeftToast // eslint-disable-line vue/no-unused-components
  },
  data () {
    return {
      send_out_message: '',
      typingTimeout: null,
      isReadyToEnd: false,
      typingNotification: null,
      typingNotificationTimeout: null,
      systemMessages: [], // system messages like "joined" with agreement
      memberAgreements: [], // raw API data
      memberLeftToastId: null,
      shouldFinishChat: false, // Flag to track if we should call finishChat on unload
      isNavigating: false // Flag to track if we're navigating away normally
    }
  },
  computed: {
    avatar_full_name () {
      return this.$store.state.avatar_color + ' ' + this.$store.state.avatar_name
    },
    avatar_part_name () {
      return this.$store.state.avatar_name
    },
    chat_statement () {
      return this.$store.state.chat_statement || 'No discussion topic available'
    },
    user_stance () {
      const masterStatements = this.$store.state.masterStatements || []
      const chatStatement = this.$store.state.chat_statement

      const statementIndex = masterStatements.indexOf(chatStatement)
      if (statementIndex === -1) return 'No stance recorded'

      // Get the user's response for this statement
      const response = this.$store.state.preDiscussionResponses.find(r => r.statement_id === statementIndex)
      if (!response) return 'No stance recorded'

      // Convert agreement value to corresponding text from the scale
      const agreementScale = [
        {text: 'Strongly disagree', value: -3},
        {text: 'Disagree', value: -2},
        {text: 'Somewhat disagree', value: -1},
        {text: 'Neutral', value: 0},
        {text: 'Somewhat agree', value: 1},
        {text: 'Agree', value: 2},
        {text: 'Strongly agree', value: 3}
      ]

      const scaleItem = agreementScale.find(item => item.value === response.agreement)
      return scaleItem ? scaleItem.text : 'No stance recorded'
    },
    messages () {
      return this.$store.state.messages
    },
    typingNotifications () {
      // Filter out current user from typing notifications
      return Array.from(this.$root.typingUsers)
        .filter(user => user.subject_id !== this.$store.state.subject_id)
    },
    // ***** TODO: Currently, can exit only when it is the 5th turn (i.e., one person sends a message after finishing 4th turn),
    //        but it should be after 4th turn and before 5th turn (i.e., no one needs to send a message for the 5th turn)
    canExit () {
      return this.$store.state.current_turn > this.$store.state.conversation_exit_turn_number
    },
    // readyMembers () {
    //   return this.$root.members.filter(m => m.is_ready_to_end && m.subject_id > 0)
    // },
    // humanMemberCount () {
    //   return this.$root.members.filter(m => m.subject_id > 0).length
    // },
    isAITyping () {
      return this.typingNotification && this.typingNotification.subject_id < 0
    }
  },
  methods: {
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
    bumpActivityOnClick () {
      this.$store.commit('updateLastActivity')
    },
    avatarColorHex (avatar_color) {
      return colors[avatar_color] || avatar_color || '#000000'
    },
    getAIColorHex (subjectId) {
      switch (subjectId) {
        case -2: return '#2196F3' // Blue for moderator
        case -3: return '#4CAF50' // Green for participant
        case -4: return '#4CAF50' // Green for dispute
        default: return '#9E9E9E' // Grey for default
      }
    },
    getAIIcon (subjectId) {
      switch (subjectId) {
        case -2: return require('@/assets/AI_moderator.png') // AI Moderator
        case -3: return require('@/assets/AI_participant.jpg') // Advocating AI
        case -4: return require('@/assets/AI_participant.jpg') // Disputing AI
        default: return ['fas', 'robot']
      }
    },
    getAIName (subjectId) {
      switch (subjectId) {
        case -2: return 'AI Moderator'
        case -3: return 'AI Participant'
        case -4: return 'AI Participant'
        default: return 'AI'
      }
    },
    getAvatarName (subjectId) {
      // Find the member with matching subject_id in the root members list
      const member = this.$root.members.find(m => m.subject_id === parseInt(subjectId))
      if (member) {
        return member.avatar_name
      }
      // Fallback to the message's avatar name if member not found
      const message = this.messages.find(m => m.sender.subject_id === subjectId)
      return message ? message.sender.avatar_name : 'Unknown'
    },
    getAvatarColor (subjectId) {
      // Find the member with matching subject_id in the root members list
      const member = this.$root.members.find(m => m.subject_id === parseInt(subjectId))
      if (member) {
        return member.avatar_color
      }
      // Fallback to the message's avatar color if member not found
      const message = this.messages.find(m => m.sender.subject_id === subjectId)
      return message ? message.sender.avatar_color : 'blue'
    },
    updateChatStatus () {
      const formData = new FormData()
      formData.append('group_id', this.$store.state.group_id)
      formData.append('chatting', true)
      axios.post(this.$server_url + 'update_chat_status', formData)
        .then(response => {
          console.log('Chat status updated:', response.data)
        })
        .catch(error => {
          console.error('Error updating chat status:', error)
        })
    },
    finishChat () {
      const subjectId = this.$store.state.subject_id
      const serverUrl = this.$server_url

      // 1. First try: sendBeacon (most reliable for page unload)
      try {
        console.log('Attempting sendBeacon for finish_chat...')
        const url = new URL('finish_chat', serverUrl).toString()
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
        const iframe = document.getElementById('finish-chat-frame')
        if (iframe && iframe.contentWindow) {
          const form = document.createElement('form')
          form.method = 'POST'
          const actionUrl = new URL('finish_chat', serverUrl).toString()
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

      // 3. Third try: Hidden form submission
      try {
        console.log('Attempting hidden form submission...')
        const form = document.createElement('form')
        form.method = 'POST'
        form.action = new URL('finish_chat', serverUrl).toString()

        const input = document.createElement('input')
        input.type = 'hidden'
        input.name = 'subject_id'
        input.value = subjectId
        form.appendChild(input)

        // Create a hidden iframe to handle the form submission
        const iframe = document.createElement('iframe')
        iframe.name = 'finish-chat-iframe-' + Date.now()
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

      // 4. Last resort: fetch with keepalive
      try {
        const url = new URL('finish_chat', serverUrl).toString()
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
        })
      } catch (e) {
        const errorData = {
          error: e.toString(),
          stack: e.stack,
          timestamp: new Date().toISOString(),
          status: 'setup_error'
        }
        console.error('Error in fetch keepalive setup:', errorData)
      }
    },
    countMeaningfulWords (message) {
      const words = message.toLowerCase().trim().split(/\s+/)
      // Remove custom filler words
      const filtered = words.filter(word => !CUSTOM_FILLER_WORDS.has(word))
      // Count only unique words
      const uniqueWords = new Set(filtered)
      return uniqueWords.size
    },
    sendMessage () {
      this.$store.dispatch('recordActivity')
      // Also bump activity on send
      this.$store.commit('updateLastActivity')
      const trimmedMessage = this.send_out_message.trim()
      // console.log('Trimmed message:', trimmedMessage)

      if (trimmedMessage !== '') {
        const meaningfulWordCount = this.countMeaningfulWords(trimmedMessage)
        // console.log('Meaningful word count:', meaningfulWordCount)
        // Set required meaningful word count based on test state
        const requiredMeaningfulWords = this.$store.state.test === 'Y' ? 3 : 10
        if (meaningfulWordCount < requiredMeaningfulWords) {
          // Show error message
          this.$bvToast.toast(
            `Your message must contain at least ${requiredMeaningfulWords} meaningful words. Filler words don't count. (Currently: ${meaningfulWordCount})`,
            {
              title: 'Message Too Short',
              variant: 'warning',
              solid: true
            }
          )
          return
        }

        let send_chat_message = {
          'code': 200,
          'data': {
            'subject_id': this.$store.state.subject_id,
            'group_id': this.$store.state.group_id,
            'msg': this.send_out_message
          }
        }
        this.$root.sendWebSocketMessage(send_chat_message)
        this.send_out_message = ''
      }
    },
    notifyTyping (isTyping) {
      const data = {
        code: 202,
        data: {
          event: isTyping ? 'user_typing' : 'user_stopped_typing',
          subject_id: this.$store.state.subject_id,
          group_id: this.$store.state.group_id,
          avatar_name: this.$store.state.avatar_name,
          avatar_color: this.$store.state.avatar_color
        }
      }

      this.$root.sendWebSocketMessage(data)
      console.log('human typing notifyTyping called with:', data)
    },
    handleReadyToEnd () {
      this.isReadyToEnd = true
      let ready_message = {
        'code': 902, // code for ready to end
        'data': {
          'subject_id': this.$store.state.subject_id,
          'group_id': this.$store.state.group_id
        }
      }
      this.$root.sendWebSocketMessage(ready_message)
    },
    showInactivityWarning () {
      if (this.$store.state.test === 'N') {
        notifyInactivity(this.$bvToast, this.$store.state.test)
      }
    },
    handleInactiveUser () {
      // Send websocket message to notify server
      let inactive_message = {
        'code': 131, // new code for inactivity
        'data': {
          'subject_id': this.$store.state.subject_id,
          'group_id': this.$store.state.group_id
        }
      }
      this.$root.sendWebSocketMessage(inactive_message)
      // Redirect to a timeout page
      this.$router.push('/InactivityTerminatedParticipation')
    },
    handleTypingEvent (event) {
      console.log('user-typing event received:', event.detail)
      this.handleTyping(event.detail)
    },
    handleTyping (user) {
      console.log('handleTyping called with:', user)

      // Handle both typing and stopped typing for AI
      if (user.subject_id < 0) {
        console.log('AI typing detected before is_typing:', user)
        if (user.is_typing) {
          this.typingNotification = user
          console.log('AI typing detected after is_typing:', user)
          console.log('isAITyping:', this.isAITyping)
          console.log('typingNotification:', this.typingNotification)
          console.log('typingNotification.subject_id < 0:', this.typingNotification && this.typingNotification.subject_id < 0)
        } else {
          // Only clear if this is the same AI
          if (this.typingNotification && this.typingNotification.subject_id === user.subject_id) {
            this.typingNotification = null
          }
        }
        return
      }

      // Human typing logic: show and auto-clear after 3 seconds
      if (user.subject_id > 0 && user.is_typing) {
        this.typingNotification = user
      }

      if (this.typingNotificationTimeout) {
        clearTimeout(this.typingNotificationTimeout)
      }
      this.typingNotificationTimeout = setTimeout(() => {
        this.typingNotification = null
      }, 3000) // Show typing indicator for 3 seconds
    },
    handlePaste (e) {
      if (this.$store.state.test !== 'Y') {
        e.preventDefault()
      }
    },
    handleCopy (e) {
      if (this.$store.state.test !== 'Y') {
        e.preventDefault()
      }
    },
    handleCut (e) {
      if (this.$store.state.test !== 'Y') {
        e.preventDefault()
      }
    },
    handleBeforeUnload (event) {
      // Only show confirmation if this is a tab close/page refresh
      // and not a normal navigation
      if (!this.isNavigating) {
        // Set flag to indicate we should finish chat if unload happens
        this.shouldFinishChat = true

        // Show the browser's native dialog
        const message = 'Are you sure you want to leave the chat? Your participation may be affected.'

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
      if (this.shouldFinishChat) {
        console.log('Page unloading, calling finishChat...')
        this.finishChat()
      }
    },
    saveSystemMessage () {
      axios.post(`${this.$server_url}update_system_message`, {
        group_id: this.$store.state.group_id,
        system_message: this.editedSystemMessage
      })
        .then(() => {
          this.$bvToast.toast('System prompt saved', 'Saved', {variant: 'success'})
        })
    },
    showMemberLeftNotification (message = 'Due to certain reasons, a group member has left the chat. However, the study will continue. Please click the button to proceed to the next survey.') {
      console.log('Showing member left notification with message:', message)

      // Create a unique ID for this toast
      const toastId = `member-left-${Date.now()}`
      this.memberLeftToastId = toastId

      // Hide any existing member left toasts
      if (this.memberLeftToastId && this.memberLeftToastId !== toastId) {
        this.$bvToast.hide(this.memberLeftToastId)
      }

      // Create the toast using the Vue component
      const h = this.$createElement
      this.$bvToast.toast(
        h(MemberLeftToast, {
          props: {
            message: message,
            onProceed: () => this.proceedToNextSurvey(toastId)
          }
        }),
        {
          id: toastId,
          title: 'Member Left',
          variant: 'warning',
          solid: true,
          noAutoHide: true,
          noCloseButton: true,
          noHoverPause: true,
          toaster: 'b-toaster-top-center'
        }
      )

      console.log('Member left notification shown with ID:', toastId)
      return toastId
    }
  },
  watch: {
    '$store.state.memberLeftChat': {
      handler (newVal, oldVal) {
        console.group('memberLeftChat watcher triggered')
        console.log('New value:', newVal)
        console.log('Old value:', oldVal)
        console.log('leftMemberMessage:', this.$store.state.leftMemberMessage)
        console.log('Call stack:')
        console.trace()
        console.groupEnd()

        if (newVal === true) {
          const message = this.$store.state.leftMemberMessage || 'Due to certain reasons, a group member has left the chat. However, the study will continue. Please click the button to proceed to the next survey.'
          console.log('Member left chat detected - showing notification:', message)
          this.showMemberLeftNotification(message)
        }
      }
    },
    messages: {
      handler () {
        this.$nextTick(() => {
          const el = this.$refs.roomarea
          if (el) {
            el.scrollTop = el.scrollHeight
          }
        })
      },
      deep: true
    },
    canExit: {
      handler (newVal) {
        if (newVal) {
          this.$nextTick(() => {
            const el = this.$refs.roomarea
            if (el) {
              const buttonContainer = document.querySelector('.ready-to-end-area')
              const buttonHeight = buttonContainer?.offsetHeight || 0
              const buttonMargin = 24 // From my-4
              const messageAreaPadding = 0 // From .message-area
              const totalScroll = buttonHeight + buttonMargin + messageAreaPadding
              el.style.scrollBehavior = 'smooth'
              el.scrollTop += totalScroll
              setTimeout(() => {
                el.style.scrollBehavior = 'auto'
              }, 500)
            }
          })
        }
      },
      immediate: true
    },
    send_out_message (newMessage) {
      // Bump activity on typing
      this.$store.commit('updateLastActivity')
      // Clear any existing timeout
      if (this.typingTimeout) {
        clearTimeout(this.typingTimeout)
      }

      if (newMessage.trim() !== '') {
        // Send typing notification
        this.notifyTyping(true)
        // Set timeout to clear typing status after 1 second of no changes
        this.typingTimeout = setTimeout(() => {
          this.notifyTyping(false)
        }, 1000)
      } else {
        // If message is empty, immediately send stopped typing
        this.notifyTyping(false)
      }
    }
  },
  beforeRouteLeave (to, from, next) {
    // Set isNavigating to true to indicate normal navigation
    this.isNavigating = true
    next()
  },

  mounted () {
    // Scroll to top when component is mounted
    window.scrollTo(0, 0)

    // Ensure WebSocket is initialized
    if (!this.$root.websock || this.$root.websock.readyState !== WebSocket.OPEN) {
      this.$root.initWebSocket()
    }

    // Add unload event listeners
    window.addEventListener('beforeunload', this.handleBeforeUnload)
    window.addEventListener('unload', this.handleUnload)

    // Listen for inactivity events
    // window.addEventListener('show-inactivity-warning', this.showInactivityWarning)
    // window.addEventListener('remove-inactive-user', this.handleInactiveUser)

    // Bump activity on any click in the chat room
    this.$el.addEventListener('click', this.bumpActivityOnClick)

    // Fetch group member agreements and generate system messages
    const groupId = this.$store.state.group_id
    const formData = new FormData()
    formData.append('group_id', groupId)
    axios.post(`${this.$server_url}get_group_member_agreements`, formData)
      .then(response => {
        console.log('Group member agreements response:', response.data)
        if (response.data && response.data.members) {
          // Initialize root members list for message processing
          this.$root.members = response.data.members.map(member => ({
            subject_id: member.subject_id,
            avatar_name: member.avatar_name,
            avatar_color: member.avatar_color,
            is_ready_to_end: false
          }))
          this.memberAgreements = response.data.members
          // Build system messages for each member
          const messages = response.data.members
            .filter(member => member.avatar_name !== this.$store.state.avatar_name || member.avatar_color !== this.$store.state.avatar_color)
            .map(member => {
              let agreementText = 'No response'
              if (member.agreement_level !== null && member.agreement_level !== undefined) {
                const scale = [
                  {text: 'Strongly disagree', value: -3},
                  {text: 'Disagree', value: -2},
                  {text: 'Somewhat disagree', value: -1},
                  {text: 'Neutral', value: 0},
                  {text: 'Somewhat agree', value: 1},
                  {text: 'Agree', value: 2},
                  {text: 'Strongly agree', value: 3}
                ]
                const found = scale.find(item => item.value === member.agreement_level)
                agreementText = found ? found.text : member.agreement_level
              }
              const styledName = `<span>${member.avatar_color} ${member.avatar_name}</span>`
              return `${styledName}'s Stance: "${agreementText}"`
            })
          const header = messages.length === 1 ? 'Your discussion partner:' : 'Your discussion partners:'
          this.systemMessages = messages.length > 0
            ? [header, ...messages]
            : []
        }
      }).catch(error => {
        console.error('Error loading group member agreements:', error)
        this.systemMessages = ['Failed to load group member agreements.' + error]
      })

    // Load saved system prompt
    // axios.get(`${this.$server_url}get_system_message`, { params: { group_id: this.$store.state.group_id } })
    //   .then(res => { this.currentSystemMessage = res.data.system_message })
    //   .catch(e => { console.error('load prompt', e) })

    // Listen for typing events
    window.addEventListener('user-typing', this.handleTypingEvent)
    // Remove this conflicting listener - all typing logic is in handleTyping now
    // window.addEventListener('user-stopped-typing', () => { this.typingNotification = null })

    // Existing mounted code...
    this.updateChatStatus()
    this.$store.commit('startInactivityCheck')
  },
  beforeDestroy () {
    if (this.$toast) {
      this.$toast.clear()
    }
    // Dismiss ready-to-end-warning toast if present
    if (this.$toast && typeof this.$toast.dismiss === 'function') {
      this.$toast.dismiss('ready-to-end-warning')
    }
    // Clean up event listeners
    // window.removeEventListener('show-inactivity-warning', this.showInactivityWarning)
    // window.removeEventListener('remove-inactive-user', this.handleInactiveUser)
    window.removeEventListener('user-typing', this.handleTypingEvent)
    window.removeEventListener('beforeunload', this.handleBeforeUnload)
    window.removeEventListener('unload', this.handleUnload)
    // Remove this conflicting listener - all typing logic is in handleTyping now
    // window.removeEventListener('user-stopped-typing', () => { this.typingNotification = null })
    if (this.$el) {
      this.$el.removeEventListener('click', this.bumpActivityOnClick)
    }
    // Clear any existing timeouts
    if (this.typingTimeout) {
      clearTimeout(this.typingTimeout)
    }

    if (this.typingNotificationTimeout) {
      clearTimeout(this.typingNotificationTimeout)
    }

    // Deactivate chat status of group
    this.finishChat()
    // Optionally, send a WebSocket message to inform the server
    let leave_room = {
      'code': 130,
      'data': this.$store.state.subject_id
    }
    this.$root.sendWebSocketMessage(leave_room)
    // TODO There is currently no handling for code 130 in consumers.py
    // Clean up listeners and intervals
    this.$store.commit('stopInactivityCheck')
  }
}
</script>

<style scoped>
.chat-room {
  display: flex;
  flex-direction: column;
  height: 100vh;
  padding: 20px;
  background: #f5f7fa;
  box-sizing: border-box;
  position: relative;
  overflow: hidden;
}

.statement-area {
  background: white;
  padding: 20px;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
  margin: 0 auto 20px;
  max-width: 600px;
  width: 100%;
  flex-shrink: 0;
}

.chat-statement {
  margin: 0 0 30px 0;
  padding: 8px 0;
  color: #2c3e50;
  font-size: 1.6em;
  font-weight: 500;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 12px;
  margin: 0;
  padding: 8px 0;
  color: #2c3e50;
}

.info-item {
  white-space: nowrap;
}

.info-divider {
  color: #6c757d;
  font-weight: bold;
  padding: 0 8px;
  font-size: 1.1em;
  opacity: 0.7;
}

.chat-container {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-height: 0;
  position: relative;
}

.messages-wrapper {
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;
}

.room-area {
  flex: 1;
  overflow-y: auto;
  padding: 20px 0;
  min-height: 0;
}

.message-card {
  margin-bottom: 16px;
  animation: fadeIn 0.3s ease;
}

.system-message-content {
  text-align: center;
  color: #6c757d;
  font-size: 1.05rem;
  font-style: italic;
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
}

.message-content {
  padding: 12px 16px;
  border-radius: 12px;
  background: white;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
  max-width: 80%;
  word-wrap: break-word;
}

.own_message .message-content {
  background: #007bff;
  color: white;
  margin-left: auto;
}

.message-avatar-icon {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #e9ecef;
}

.typing-notifications {
  margin: 8px 0;
}

.typing-indicator {
  display: flex;
  align-items: center;
  color: #6c757d;
  font-size: 0.9em;
}

.typing-indicator::before {
  content: '';
  display: inline-block;
  width: 8px;
  height: 8px;
  margin-right: 8px;
  border-radius: 50%;
  background: #007bff;
  animation: typing 1s infinite;
}

@keyframes typing {
  0%, 100% { transform: scale(1); }
  50% { transform: scale(1.2); }
}

.message-area {
  background: white;
  padding: 16px;
  border-radius: 12px;
  box-shadow: 0 -2px 8px rgba(0,0,0,0.1);
  margin-top: 20px;
  flex-shrink: 0;
  position: relative;
  z-index: 10;
  width: 100%;
}

.message-input-area {
  border: 1px solid #e9ecef;
  border-radius: 8px;
  padding: 12px;
  margin-right: 8px;
}

.message-send-button {
    border-radius: 8px;
    padding: 12px 24px;
    background-color: #0342a1 !important;
    border-color: #0342a1 !important;
}

.exit-button {
  position: static;
  box-shadow: none;
}

.ready-status {
  position: static;
  background-color: transparent;
  border: none;
  padding: 0;
}

.ready-to-end-area {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0;
  margin: 2;
  background: transparent;
  border: none;
  box-shadow: none;
}

.avatar-icon {
  display:inline-block !important;
  color: inherit !important;
}

.avatar-icon svg {
  fill: currentColor !important;
}

.avatar-icon path {
  fill: currentColor !important;
}

.ready-instructions {
  margin: 15px 0;
  padding: 10px;
  background-color: #f8f9fa;
  border-radius: 5px;
}

.instruction-text {
  font-size: 0.9rem;
  color: #6c757d;
  margin: 0;
  font-style: italic;
}

.button-container {
  text-align: right;
}

.current-user-avatar-name {
  text-align: right;
  width: 100%;
}

@media (max-width: 768px) {
  .chat-room {
    padding: 10px;
  }

  .message-content {
    max-width: 90%;
  }
}

.system-panel-container {
  margin-top: 20px;
}

.ai-role-label {
  font-size: 0.9em;
  color: #666;
  margin-left: 6px;
  font-style: italic;
}
</style>
