import '@babel/polyfill'
import 'mutationobserver-shim'
import Vue from 'vue'
import './plugins/axios'
import { BootstrapVue, IconsPlugin } from './plugins/bootstrap-vue'
import VueSimpleAlert from './plugins/vue-simple-alert'
import App from './App.vue'
import router from './router'
import animal from 'vue-animals'
import './assets/style.css'
import Vuex from 'vuex'
import Amplify from 'aws-amplify'
import '@aws-amplify/ui-vue'
import aws_exports from './aws-exports'
import { useSound } from '@vueuse/sound'
import sound from './assets/alert.mp3'
import Toast from 'vue-toastification'
import 'vue-toastification/dist/index.css'
/* import the fontawesome core */
import { library } from '@fortawesome/fontawesome-svg-core'
/* import specific icons */
import { faCircleCheck, faCircleXmark, faCircle, faSkull, faGavel, faRobot } from '@fortawesome/free-solid-svg-icons'
/* import font awesome icon component */
import { FontAwesomeIcon } from '@fortawesome/vue-fontawesome'
import VueTour from 'vue-tour'
import axios from 'axios'
import { notifyReadyToEnd, clearReadyToEndNotification } from '@/plugins/notificationService.js'

Vue.use(BootstrapVue)
Vue.use(IconsPlugin)
console.log('Alarm sound URL:', sound)
require('vue-tour/dist/vue-tour.css')
Amplify.configure(aws_exports)
Vue.config.productionTip = false
Vue.use(Vuex)
Vue.use(VueSimpleAlert)
Vue.use(Toast, {
  transition: 'Vue-Toastification__bounce',
  maxToasts: 20,
  newestOnTop: true,
  dangerouslyUseHTMLString: true
})
Vue.use(VueTour)
Vue.component('v-animal', animal)
library.add(faCircleCheck)
library.add(faCircleXmark)
library.add(faCircle)
library.add(faSkull)
library.add(faGavel)
library.add(faRobot)
Vue.component('font-awesome-icon', FontAwesomeIcon)

// // Add global properties
// Vue.prototype.$server_url = 'https://gobackend.discussionexperiment.com/ccw/api/'
// Vue.prototype.$ws_url = 'wss://gobackend.discussionexperiment.com/ws/chat/'
// Vue.prototype.$chat_url = 'wss://gobackend.discussionexperiment.com/ws/chat/'
// Vue.prototype.$test_mode = false

// Vue.prototype.$server_url = 'http://127.0.0.1:8000/ccw/api/'
// Vue.prototype.$ws_url = 'ws://127.0.0.1:8000/ws/chat/'
// Vue.prototype.$chat_url = 'ws://127.0.0.1:8000/ws/chat/'
// Vue.prototype.$test_mode = true

const store = new Vuex.Store({
  // plugins: [createPersistedState({
  //   getItem: key => Cookies.get(key),
  //   setItem: (key, value) => Cookies.set(key, value, { expires: 3, secure: false }),
  //   removeItem: key => Cookies.remove(key)
  // })],
  data () {
    return {
      websock: null,
      alarm_sound: null,
      lastNotificationMessage: null
    }
  },
  created () {
    // Initialize sound
    try {
      this.alarm_sound = new Audio(require('@/assets/alert.mp3'))
      // Preload the sound
      this.alarm_sound.load()
    } catch (e) {
      console.error('Failed to load notification sound:', e)
    }
  },
  state () {
    return {
      subject_id: null,
      avatar_name: null,
      avatar_color: null,
      group_id: -1,
      messages: [],
      preDiscussionResponses: [], // Store pre-discussion responses
      participant_number_condition: -1,
      participant_condition: -1,
      moderator_condition: -1,
      masterStatements: [
        'Abortion should be legal.',
        'Governments should have the authority to censor online content.',
        'Tariffs on imported goods protect American jobs and industries from foreign competition.',
        'Unpredictability in U.S. foreign policy is an effective deterrent against hostile actions from other nations.',
        'The United States should implement a digital dollar system.',
        'Automation will crash democracy.'
      ], // Store master statements
      chat_statement_index: null,
      chat_statement: null,
      all_ready: false, // Tracks whether all human members are ready
      lastActivityTimestamp: Date.now(),
      inactivityWarningShown: false,
      inactivityCheckInterval: null,
      random_third_person_prompt: -1,
      is_third_person: false,
      websocket: null,
      websocketConnected: false,
      WebSocketOnMessageRunningTimes: 0,
      current_turn: 1,
      conversation_exit_turn_number: 4,
      test: 'N',
      test_moderator_code: -1,
      test_participant_code: -1,
      test_policy_number: -1,
      test_turn_number: -1,
      platform: '',
      all_confirmed: false,
      memberLeftChat: false,
      leftMemberMessage: ''
    }
  },
  mutations: {
    setAllReadyStatus (state, all_ready) {
      state.all_ready = all_ready
    },
    assign_random_third_person_prompt (state, random_third_person_prompt) {
      state.random_third_person_prompt = random_third_person_prompt
    },
    assign_is_third_person (state, is_third_person) {
      state.is_third_person = true
    },
    // Heartbeat functionality has been removed
    assign_participant_condition (state, participant_condition) {
      state.participant_condition = participant_condition
    },
    assign_moderator_condition (state, moderator_condition) {
      state.moderator_condition = moderator_condition
    },
    setPreDiscussionResponses (state, responses) {
      state.preDiscussionResponses = responses
    },
    setPostDiscussionResponses (state, responses) {
      state.postDiscussionResponses = responses
    },
    assign_subject_id (state, record) {
      state.subject_id = record.subject_id
    },
    assign_group_id (state, record) {
      state.group_id = record.group_id
    },
    new_message (state, message) {
      state.messages.push(message)
      console.log(`New message: ${message.content}`)
    },
    clear_messages (state) {
      state.messages = []
    },
    assign_group_chat_statement_indx (state, index) {
      state.chat_statement_index = index
      console.log('Updated chat statement index:', state.chat_statement_index)
    },
    assign_group_chat_statement (state, chat_statement_index) {
      state.chat_statement = state.masterStatements[chat_statement_index]
      console.log('Updated chat statement:', state.chat_statement)
    },
    update_avatar (state, payload) {
      state.avatar_name = payload.avatar_name
      state.avatar_color = payload.avatar_color
    },
    updateLastActivity (state) {
      state.lastActivityTimestamp = Date.now()
      state.inactivityWarningShown = false
    },
    setInactivityWarningShown (state, value) {
      state.inactivityWarningShown = value
    },
    startInactivityCheck (state) {
      if (!state.inactivityCheckInterval) {
        // Reset the activity timestamp when starting the check
        state.lastActivityTimestamp = Date.now()
        state.inactivityWarningShown = false

        state.inactivityCheckInterval = setInterval(() => {
          const currentTime = Date.now()
          const timeSinceLastActivity = currentTime - state.lastActivityTimestamp

          // Show warning after 45 seconds of inactivity
          if (timeSinceLastActivity >= 45000 && !state.inactivityWarningShown) {
            state.inactivityWarningShown = true
            // Emit a custom event that components can listen to
            window.dispatchEvent(new CustomEvent('show-inactivity-warning'))
          }

          // Remove user after 1.25 minute of inactivity
          if (timeSinceLastActivity >= 75000 && state.test !== 'Y') {
            // Clear the interval before removing user to prevent multiple triggers
            clearInterval(state.inactivityCheckInterval)
            state.inactivityCheckInterval = null
            window.dispatchEvent(new CustomEvent('remove-inactive-user'))
          }
        }, 1000) // Check every second
      }
    },
    stopInactivityCheck (state) {
      if (state.inactivityCheckInterval) {
        clearInterval(state.inactivityCheckInterval)
        state.inactivityCheckInterval = null
      }
    },
    setThirdPerson (state, is_third_person) {
      state.is_third_person = is_third_person
    },
    setWebSocket (state, websocket) {
      state.websocket = websocket
    },
    setWebSocketConnected (state, status) {
      state.websocketConnected = status
    },
    assign_test_variables (state, payload) {
      state.test = payload.test
      state.test_moderator_code = Number(payload.test_moderator_code)
      state.test_participant_code = Number(payload.test_participant_code)
      state.test_policy_number = Number(payload.test_policy_number)
      state.test_turn_number = Number(payload.test_turn_number)
      // update masterStatements based on policy number
      if (state.test_policy_number === 1) {
        console.log('Test policy number 1')
        state.masterStatements = [
          'Abortion should be legal.'
        ]
      } else if (state.test_policy_number === 3) {
        state.masterStatements = [
          'Abortion should be legal.',
          'Governments should have the authority to censor online content.',
          'The government should employ a stricter immigration/border policy.'
        ]
      } else if (state.test_policy_number === 0) {
        state.masterStatements = [
          'UK should apply to rejoin the European Union.'
        ]
      }
      // update conversation_exit_turn_number based on turn number
      state.conversation_exit_turn_number = state.test_turn_number
    },
    assign_platform (state, payload) {
      state.platform = payload.platform
      if (state.platform === 'localhost') {
        Vue.prototype.$server_url = 'http://127.0.0.1:8000/ccw/api/'
        Vue.prototype.$ws_url = 'ws://127.0.0.1:8000/ws/chat/'
        Vue.prototype.$chat_url = 'ws://127.0.0.1:8000/ws/chat/'
        Vue.prototype.$test_mode = true
      } else {
        Vue.prototype.$server_url = 'https://gobackend.discussionexperiment.com/ccw/api/'
        Vue.prototype.$ws_url = 'wss://gobackend.discussionexperiment.com/ws/chat/'
        Vue.prototype.$chat_url = 'wss://gobackend.discussionexperiment.com/ws/chat/'
        Vue.prototype.$test_mode = false
      }
    },
    setAllConfirmed (state, all_confirmed) {
      state.all_confirmed = all_confirmed
    },
    setMemberLeftChat (state, { message }) {
      state.memberLeftChat = true
      state.leftMemberMessage = message || 'A group member has left the chat'
    }
  },
  actions: {
    updatePreDiscussionResponses ({ commit }, responses) {
      commit('setPreDiscussionResponses', responses)
    },
    initWebSocket ({ commit, state }) {
      console.log('Initializing WebSocket connection in action main', state.$ws_url)
      return new Promise((resolve, reject) => {
        const ws = new WebSocket(state.$ws_url)

        ws.onopen = () => {
          commit('setWebSocket', ws)
          commit('setWebSocketConnected', true)
          resolve()
        }

        ws.onerror = (error) => {
          console.error('WebSocket error:', error)
          reject(error)
        }

        ws.onclose = () => {
          commit('setWebSocket', null)
          commit('setWebSocketConnected', false)
        }
      })
    },
    recordActivity ({ commit }) {
      commit('updateLastActivity')
    }
  },
  getters: {
    getSelectedStatements: (state) => state.masterStatements,
    getPreDiscussionResponses: (state) => state.preDiscussionResponses
  }
})

// Clear all toasts on navigation
router.afterEach(() => {
  if (Vue.prototype.$toast) {
    Vue.prototype.$toast.clear()
  }
})

new Vue({
  data: function () {
    return {
      server_url: Vue.prototype.$server_url,
      chat_url: Vue.prototype.$chat_url,
      test_mode: Vue.prototype.$test_mode,
      estimation: null,
      is_loading: false,
      fire_400: false,
      members: [],
      decisions: [],
      typingUsers: new Set() // Track who is currently typing
    }
  },
  watch: {
    '$store.state.all_ready': function (newVal) {
      if (newVal) {
        clearReadyToEndNotification(this.$toast)
        this.$router.push('/PostDOSurvey') // Redirect when all are ready
      }
    }
  },
  methods: {
    updateStore (data) {
      this.$store.commit('assign_group_id', { group_id: data.group_id })
      this.$store.commit('assign_participant_condition', data.participant_condition)
      this.$store.commit('assign_moderator_condition', data.moderator_condition)
      this.$store.commit('assign_group_chat_statement', data.chat_statement_indx)
      this.$store.commit('assign_group_chat_statement_indx', data.chat_statement_indx)

      console.log('third_person_id:', data.third_person_id)
      console.log('subject_id:', this.$store.state.subject_id)
      console.log('Type of third_person_id:', typeof data.third_person_id)
      console.log('Type of subject_id:', typeof this.$store.state.subject_id)
      console.log('Exact comparison:', data.third_person_id === this.$store.state.subject_id)
      if (data.third_person_id === this.$store.state.subject_id) {
        this.$store.commit('assign_is_third_person', true)
        console.log('subject_id:', this.$store.state.subject_id)
        console.log('random_third_person_prompt:', data.random_third_person_prompt)
        this.$store.commit('assign_random_third_person_prompt', data.random_third_person_prompt)
      }

      if (data.assigned_avatars && data.assigned_avatars.length > 0) {
        const subjectId = this.$store.state.subject_id
        const myAvatar = data.assigned_avatars.find(avatar => avatar.subject_id === subjectId)
        if (myAvatar) {
          const avatarColor = myAvatar.avatar_color || myAvatar.color
          const avatarName = myAvatar.avatar_name || myAvatar.name

          this.$store.commit('update_avatar', {
            avatar_color: avatarColor,
            avatar_name: avatarName
          })
        }
      }
    },
    initWebSocket () {
      console.log('Initializing WebSocket connection in main method', this.$store.state.group_id)
      const wsUrl = `${this.$chat_url}${this.$store.state.group_id}/`
      console.log('Connecting to WebSocket at:', wsUrl)

      this.websock = new WebSocket(wsUrl)
      this.websock.onmessage = this.webSocketOnMessage
      this.websock.onopen = this.webSocketOnOpen
      this.websock.onerror = this.webSocketOnError
      this.websock.onclose = this.webSocketOnClose
    },
    sendWebSocketMessage (msg) {
      console.log('WebSocket message sent:', msg)
      this.websock.send(JSON.stringify(msg))
    },
    playNotificationSound () {
      if (!this.alarm_sound) {
        console.log('Sound not initialized, skipping play')
        return
      }

      // Reset the sound to the beginning in case it's already playing
      this.alarm_sound.pause()
      this.alarm_sound.currentTime = 0

      // Play without using .catch() to prevent the error
      const playPromise = this.alarm_sound.play()
      if (playPromise !== undefined) {
        playPromise.catch(error => {
          console.log('Sound playback prevented:', error)
        })
      }
    },
    webSocketOnMessage (response) {
      const data = JSON.parse(response.data)
      const message = data.message || data
      console.log('WebSocket message received:', message)

      if (message.code === 101) {
        console.log('WebSocket message:', message)
        if (message.startable) {
          let data = {
            'is_third_person': message.is_third_person,
            'has_capacity': message.has_capacity,
            'third_person_id': message.third_person_id,
            'group_id': message.group_id,
            'group_capacity': message.group_capacity,
            'moderator_condition': message.moderator_condition,
            'participant_condition': message.participant_condition,
            'chat_statement_indx': message.chat_statement_indx,
            'assigned_avatars': message.assigned_avatars,
            'random_third_person_prompt': message.random_third_person_prompt
          }
          this.updateStore(data)
          this.alarm_sound.play()
          // show popup message based on the condition
          let countdown = 5
          let popup_message = `Your group is ready! You will redirect to avatar assignment in ${countdown} seconds`

          // Show the toast and keep its id
          const toastId = this.$toast(popup_message, {
            position: 'top-right',
            timeout: false, // We'll dismiss manually
            closeOnClick: false,
            pauseOnFocusLoss: false,
            pauseOnHover: false,
            draggable: false,
            draggablePercent: 0.6,
            showCloseButtonOnHover: false,
            hideProgressBar: true,
            closeButton: false,
            icon: true,
            rtl: false
          })

          const intervalId = setInterval(() => {
            countdown--
            if (countdown > 0) {
              this.$toast.update(toastId, {
                content: `Your group is ready! You will redirect to avatar assignment in ${countdown} seconds`
              })
            } else {
              clearInterval(intervalId)
              this.$toast.dismiss(toastId)
              this.setNotReadyToPair()
              let body = new FormData()
              body.append('subject_id', this.$store.state.subject_id)
              axios.post(this.$server_url + 'set_pipei_end_time', body)
                .then(response => {
                  console.log('Set pipei end time response:', response.data)
                })
                .catch(error => {
                  console.error('Error setting pipei end time:', error)
                })
              this.$router.push('/avatar-assignment')
            }
          }, 1000)
        }
      } else if (message.code === 201) { // Both human and AI messages
        let received_msg = message.message
        // Process human messages
        // 1. Add avatar info
        // 2. Update current turn
        if (received_msg.sender.subject_id > 0) {
          // Find the member with matching subject_id
          const member = this.$root.members.find(m => m.subject_id === parseInt(received_msg.sender.subject_id))
          if (member) {
            received_msg.sender.avatar_name = member.avatar_name
            received_msg.sender.avatar_color = member.avatar_color
            console.log(`Received message from ${received_msg.sender.subject_id}: ${member.avatar_name} (${member.avatar_color})`)
          } else {
            console.error('Member not found for subject_id:', received_msg.sender.subject_id, 'Available members:', this.$root.members)
          }
        }
        // Add to Vuex store
        this.$store.commit('new_message', received_msg)
      } else if (message.code === 210) { // Turn update
        this.$store.state.current_turn = message.current_turn
        console.log('Current turn:', this.$store.state.current_turn)
      } else if (message.code === 778) { // Devil's advocate message
        let received_msg = message.message
        this.$store.commit('new_message', received_msg)
      } else if (message.code === 203) { // Typing notification
        const typingInfo = message.typing_info
        // Skip if it's the current user's typing notification
        if (typingInfo.subject_id > 0) {
          console.log('Typing notification from human:', typingInfo.avatar_name, typingInfo.avatar_color, typingInfo.is_typing)
        }
        if (typingInfo.subject_id === this.$store.state.subject_id) {
          return
        }
        // Always dispatch 'user-typing' event, with is_typing true or false
        const typingEvent = new CustomEvent('user-typing', {
          detail: {
            subject_id: typingInfo.subject_id,
            avatar_name: typingInfo.avatar_name,
            avatar_color: typingInfo.avatar_color,
            is_typing: typingInfo.is_typing
          }
        })
        window.dispatchEvent(typingEvent)
      } else if (message.code === 903) { // Ready to end status update
        // Update ready status for members
        const readyMembers = message.ready_members
        this.$root.members.forEach(member => {
          member.is_ready_to_end = readyMembers.includes(member.subject_id)
        })
        // Store `all_ready` in Vuex so all components can reactively watch it
        this.$store.commit('setAllReadyStatus', message.all_ready)
        // Show yellow warning toast when a subject is ready (skip if all are ready)
        const subject_obj = message.message.sender
        const subject_id = subject_obj.subject_id
        const subject_name = subject_obj.avatar_name
        const subject_color = subject_obj.avatar_color
        // Only show the warning if the sender is not the current user
        if (!message.all_ready && subject_id !== this.$store.state.subject_id) {
          notifyReadyToEnd(this.$toast, subject_color, subject_name)
        }
      } else if (message.code === 300) { // All confirmed
        this.$store.commit('setAllConfirmed', message.all_confirmed)
        this.alarm_sound.play()
      } else if (message.code === 132) { // Inactive user notification
        console.log('[DEBUG] Received inactive user notification:', JSON.stringify(message, null, 2))

        // Extract the actual message text
        const notificationMessage = message.message || 'A group member has left the chat'

        // Play sound first
        this.playNotificationSound()

        // Show notification
        console.log('[DEBUG] Calling showMemberLeftNotification directly')
        this.$nextTick(() => {
          this.$store.commit('setMemberLeftChat', {
            message: notificationMessage
          })
        })
      }
    },
    webSocketOnOpen (e) {
      console.log('WebSocket connection opened')
      let enter_room = {
        'code': 100,
        'data': {
          'subject_id': this.$store.state.subject_id
        }
      }
      this.$root.sendWebSocketMessage(enter_room)
    },
    webSocketOnError (e) {
      console.error(e)
    },
    webSocketOnClose (e) {
      let leave_room = {
        'code': 130,
        'message': this.$store.state.subject_id
      }
      this.$root.sendWebSocketMessage(leave_room)
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
          console.log('Set not ready to pair response:', response.data)
        })
        .catch(error => {
          console.error('Error setting not ready to pair:', error)
        })
    }
  },
  setup () {
    const alarm_sound = useSound(sound)

    return {
      alarm_sound
    }
  },
  store: store,
  router,
  render: h => h(App)
}).$mount('#app')
