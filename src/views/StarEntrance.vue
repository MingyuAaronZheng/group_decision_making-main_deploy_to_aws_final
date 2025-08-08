<template>
  <div class="star-entrance-bg">
    <b-jumbotron header="Welcome to our group discussion study!" header-level="4" class="mb-4 shadow-lg entrance-jumbotron">
      <div class="page-indicator text-center mb-1">Page: 1 / 9</div>
      <div class="content-area bg-white p-4 rounded-lg entrance-content">
        <p class="entrance-section-title">
          In this study, you will be asked to complete a series of tasks, including:
        </p>
        <b-list-group class="mb-4 entrance-step-list">
          <b-list-group-item class="px-3 py-3 mb-3 bg-light border-0 rounded-lg d-flex align-items-center entrance-step">
            <b-icon icon="1-circle" variant="primary" class="mr-3 entrance-step-icon" />
            <span>Sharing your attitudes and perspectives on specific topics.</span>
          </b-list-group-item>
          <b-list-group-item class="px-3 py-3 mb-3 bg-light border-0 rounded-lg d-flex align-items-center entrance-step">
            <b-icon icon="2-circle" variant="success" class="mr-3 entrance-step-icon" />
            <span>Participating in a discussion task using a customized chat interface.</span>
          </b-list-group-item>
          <b-list-group-item class="px-3 py-3 mb-3 bg-light border-0 rounded-lg d-flex align-items-center entrance-step">
            <b-icon icon="3-circle" variant="warning" class="mr-3 entrance-step-icon" />
            <span>Reflecting on your experience and providing feedback in a post-discussion survey.</span>
          </b-list-group-item>
        </b-list-group>
        <p class="entrance-section-title">
          The entire process is expected to take approximately <b>20 minutes</b>. Your responses will remain confidential and will be used exclusively for research purposes to ensure the integrity and impact of the findings.
          <br>
          <span class="text-info entrance-section-subline">You are only allowed to participate in this study once.</span>
        </p>
        <b-alert variant="warning" show class="my-4 p-4 font-weight-bold entrance-alert d-flex align-items-center shadow-sm">
          <b-icon icon="info-circle-fill" font-scale="1.7" class="mr-3 text-info" />
          <div class="entrance-alert-text">
            <span class="h5 entrance-alert-title">Important Inactivity Rule:</span><br>
            If you are inactive for <strong>45 seconds</strong>, you will see a warning. If inactivity continues for another <strong>30 seconds</strong> (total <strong>75 seconds</strong>), your study will be terminated.<br>
            <ul class="mb-0">
              <li class="text-dark">Even if you are terminated, you will still be paid for the tasks you have completed up to that point.</li>
              <li class="text-dark">To stay active, interact with the website, such as clicking on option buttons of the surveys, entering text in input boxes.</li>
            </ul>
          </div>
        </b-alert>
        <p class="entrance-section-title mb-4">
          <b-icon icon="arrow-right-circle" class="mr-2 text-primary" />
          Sounds interesting? Click the button below to start the study!
        </p>
        <div class="button-area text-center mt-4">
          <b-button variant="primary" name="next" v-on:click="next" class="entrance-btn shadow-sm">Start the Study</b-button>
        </div>
      </div>

    </b-jumbotron>
  </div>
</template>

<script>
import axios from 'axios'
export default {
  data: function () {
    return {
      platform: null,
      worker_id: null,
      study_id: null,
      session_id: null,
      test_moderator_code: null,
      test_participant_code: null,
      test_policy_number: null,
      test_turn_number: null
    }
  },
  mounted () { // get the worker id, study id, and session id from the URL
    this.prolific_processor(location.href)
  },
  methods: {
    prolific_processor: function (url) {
      // https://dev.d1uau7ss3lp78y.amplifyapp.com/qualificationentrance/?PROLIFIC_PID={{%PROLIFIC_PID%}}&STUDY_ID={{%STUDY_ID%}}&SESSION_ID={{%SESSION_ID%}}&TEST={{%TEST%}}&TEST_MODERATOR_CODE={{%TEST_MODERATOR%}}&TEST_PARTICIPANT_CODE={{%TEST_PARTICIPANT%}}&TEST_POLICY_NUMBER={{%TEST_POLICY%}}&TEST_TURN_NUMBER={{%TEST_TURN%}}
      if (url.includes('localhost')) {
        this.platform = 'localhost'
      } else {
        this.platform = 'aws'
      }

      this.$store.commit('assign_platform', {platform: this.platform})
      let prolificArray = url.split('?')[1].split('&')
      this.worker_id = prolificArray[0].split('=')[1]
      this.study_id = prolificArray[1].split('=')[1]
      this.session_id = prolificArray[2].split('=')[1]
      this.test = prolificArray[3] ? prolificArray[3].split('=')[1] : 'N'
      console.log('Test:', this.test)
      if (this.test === 'Y') {
        this.test_moderator_code = prolificArray[4] ? prolificArray[4].split('=')[1] : 0
        this.test_participant_code = prolificArray[5] ? prolificArray[5].split('=')[1] : 1
        this.test_policy_number = prolificArray[6] ? prolificArray[6].split('=')[1] : 1
        this.test_turn_number = prolificArray[7] ? prolificArray[7].split('=')[1] : 1
      }
    },

    next: function () {
      // update store
      if (this.test === 'Y') {
        this.$store.commit('assign_test_variables', {
          test: this.test,
          test_moderator_code: this.test_moderator_code,
          test_participant_code: this.test_participant_code,
          test_policy_number: this.test_policy_number,
          test_turn_number: this.test_turn_number
        })
        console.log('Test variables assigned:', this.test_moderator_code, this.test_participant_code, this.test_policy_number, this.test_turn_number)
      }

      // update backend and create subject
      let body = new FormData()
      if (this.$store.state.subject_id === null) { // If no subject id is stored in state, it means this is a new login
        if (typeof this.worker_id === 'undefined' || this.worker_id === null || this.worker_id === '') {
          this.$alert('We could not get your Prolific ID information, please return the HIT.', '', 'warning')
          return
        }
        body.append('worker_id', this.worker_id)
        body.append('study_id', this.study_id)
        body.append('session_id', this.session_id)
        body.append('test', this.test)
        if (this.test === 'Y') {
          body.append('test_moderator_code', this.test_moderator_code)
          body.append('test_participant_code', this.test_participant_code)
          body.append('test_policy_number', this.test_policy_number)
          body.append('test_turn_number', this.test_turn_number)
        }
        console.log(this.$server_url)
        axios.post(this.$server_url + 'create_subject', body)
          .then(response => {
            if (response.data.success === true) {
              this.$store.commit('assign_subject_id', {subject_id: response.data.subject_id})
              this.$router.push('/DemograSurvey')
            } else {
              this.$alert(response.data.message || 'Error creating subject', '', 'warning')
            }
          })
          .catch(e => {
            this.$alert(e.response.data.detail)
          })
      }
    }
  }
}
</script>

<style scoped>
.star-entrance-bg {
  min-height: 100vh;
  background: linear-gradient(135deg, #e3f0ff 0%, #f9f9f9 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 0;
}
.entrance-jumbotron {
  background: rgba(255,255,255,0.92);
  border-radius: 1.5rem;
  box-shadow: 0 4px 32px rgba(80,120,200,0.08);
  padding: 2.5rem 1.5rem;
  max-width: 1100px;
  margin: 2rem auto;
}
.entrance-content {
  background: #fff;
  border-radius: 1.25rem;
  box-shadow: 0 2px 16px rgba(80,120,200,0.08);
}
.entrance-welcome {
  font-size: 1.25rem;
  font-weight: 600;
  color: #3b3b6d;
  display: flex;
  align-items: center;
  margin-bottom: 1.5rem;
}
.entrance-icon {
  color: #4f8cff;
  font-size: 2rem;
}
.entrance-section-title {
  font-size: 1.08rem;
  color: #3b3b6d;
  font-weight: 500;
  margin-bottom: 0.75rem;
  margin-top: 0.7rem;
  line-height: 1.8;
}
.entrance-step-list .entrance-step:last-child {
  margin-bottom: 0 !important;
  padding-bottom: 0 !important;
}
.entrance-step-list {
  margin-bottom: 0 !important;
}
.entrance-step-list .entrance-step:last-child {
  margin-bottom: 0 !important;
}
.entrance-step-list {
  margin-bottom: 0.3rem;
}
.entrance-section-subline {
  display: inline-block;
  margin-top: 0.6em;
  margin-bottom: 0.1em;
  font-size: 1.02rem;
  letter-spacing: 0.01em;
}
.entrance-step-list {
  margin-bottom: 0.8rem;
}
.entrance-step {
  background: #f7faff !important;
  border: none !important;
  box-shadow: 0 1px 6px rgba(80,120,200,0.04);
  font-size: 1.07rem;
  transition: box-shadow 0.2s;
}
.entrance-step:hover {
  box-shadow: 0 4px 16px rgba(80,120,200,0.11);
  background: #e9f3ff !important;
}
.entrance-step-icon {
  font-size: 1.6rem;
  min-width: 2.2rem;
}
.entrance-alert {
  background: #fffbe6 !important;
  border: 1.5px solid #ffe066 !important;
  color: #8a6d3b !important;
  border-radius: 1rem !important;
  box-shadow: 0 2px 12px rgba(255,224,102,0.12);
  font-size: 1.08rem;
}
.entrance-alert-text {
  line-height: 2.05;
  margin-top: 0.1em;
  margin-bottom: 0.1em;
}
.entrance-alert-title {
  background: #ffe066;
  color: #a35b00;
  padding: 0.22em 0.85em 0.22em 0.85em;
  border-radius: 0.7em;
  font-weight: 700;
  font-size: 1.13em;
  box-shadow: 0 1px 6px rgba(255,224,102,0.07);
  display: inline-block;
  letter-spacing: 0.01em;
}
.entrance-btn {
  font-size: 1.15rem;
  padding: 0.85rem 2.5rem;
  border-radius: 2rem;
  font-weight: 600;
  letter-spacing: 0.02em;
  transition: background 0.18s, box-shadow 0.18s, transform 0.12s;
}
.entrance-btn:hover {
  background: #1b6be0 !important;
  box-shadow: 0 4px 18px rgba(27,107,224,0.13);
  transform: translateY(-1px) scale(1.03);
}
@media (max-width: 768px) {
  .entrance-jumbotron {
    padding: 1.2rem 0.2rem;
    max-width: 98vw;
  }
  .entrance-content {
    padding: 1.1rem 0.3rem;
  }
  .entrance-welcome {
    font-size: 1.09rem;
  }
  .entrance-step {
    font-size: 1rem;
  }
  .entrance-btn {
    font-size: 1rem;
    padding: 0.7rem 1.5rem;
  }
}
.page-indicator {
  font-size: 1.1rem;
  font-weight: 500;
  color: #333;
  background: #f2f2f2;
  border-radius: 6px;
  padding: 6px 18px;
  display: inline-block;
  margin-bottom: 12px;
}
</style>

<script>
import axios from 'axios'
export default {
  data: function () {
    return {
      platform: null,
      worker_id: null,
      study_id: null,
      session_id: null,
      test_moderator_code: null,
      test_participant_code: null,
      test_policy_number: null,
      test_turn_number: null
    }
  },
  mounted () { // get the worker id, study id, and session id from the URL
    this.prolific_processor(location.href)
  },
  methods: {
    prolific_processor: function (url) {
      // https://dev.d1uau7ss3lp78y.amplifyapp.com/qualificationentrance/?PROLIFIC_PID={{%PROLIFIC_PID%}}&STUDY_ID={{%STUDY_ID%}}&SESSION_ID={{%SESSION_ID%}}&TEST={{%TEST%}}&TEST_MODERATOR_CODE={{%TEST_MODERATOR%}}&TEST_PARTICIPANT_CODE={{%TEST_PARTICIPANT%}}&TEST_POLICY_NUMBER={{%TEST_POLICY%}}&TEST_TURN_NUMBER={{%TEST_TURN%}}
      if (url.includes('localhost')) {
        this.platform = 'localhost'
      } else {
        this.platform = 'aws'
      }

      this.$store.commit('assign_platform', {platform: this.platform})
      let prolificArray = url.split('?')[1].split('&')
      this.worker_id = prolificArray[0].split('=')[1]
      this.study_id = prolificArray[1].split('=')[1]
      this.session_id = prolificArray[2].split('=')[1]
      this.test = prolificArray[3] ? prolificArray[3].split('=')[1] : 'N'
      console.log('Test:', this.test)
      if (this.test === 'Y') {
        this.test_moderator_code = prolificArray[4] ? prolificArray[4].split('=')[1] : 0
        this.test_participant_code = prolificArray[5] ? prolificArray[5].split('=')[1] : 1
        this.test_policy_number = prolificArray[6] ? prolificArray[6].split('=')[1] : 1
        this.test_turn_number = prolificArray[7] ? prolificArray[7].split('=')[1] : 1
      }
    },

    next: function () {
      // update store
      if (this.test === 'Y') {
        this.$store.commit('assign_test_variables', {
          test: this.test,
          test_moderator_code: this.test_moderator_code,
          test_participant_code: this.test_participant_code,
          test_policy_number: this.test_policy_number,
          test_turn_number: this.test_turn_number
        })
        console.log('Test variables assigned:', this.test_moderator_code, this.test_participant_code, this.test_policy_number, this.test_turn_number)
      }

      // update backend and create subject
      let body = new FormData()
      if (this.$store.state.subject_id === null) { // If no subject id is stored in state, it means this is a new login
        if (typeof this.worker_id === 'undefined' || this.worker_id === null || this.worker_id === '') {
          this.$alert('We could not get your Prolific ID information, please return the HIT.', '', 'warning')
          return
        }
        body.append('worker_id', this.worker_id)
        body.append('study_id', this.study_id)
        body.append('session_id', this.session_id)
        body.append('test', this.test)
        if (this.test === 'Y') {
          body.append('test_moderator_code', this.test_moderator_code)
          body.append('test_participant_code', this.test_participant_code)
          body.append('test_policy_number', this.test_policy_number)
          body.append('test_turn_number', this.test_turn_number)
        }
        console.log(this.$server_url)
        axios.post(this.$server_url + 'create_subject', body)
          .then(response => {
            if (response.data.success === true) {
              this.$store.commit('assign_subject_id', {subject_id: response.data.subject_id})
              this.$router.push('/DemograSurvey')
            } else {
              this.$alert(response.data.message || 'Error creating subject', '', 'warning')
            }
          })
          .catch(e => {
            this.$alert(e.response.data.detail)
          })
      }
    }
  }
}
</script>

<style scoped>
.warning-box {
  background-color: #f8f9fa;
  border: 1px solid #dee2e6;
  border-radius: 0.25rem;
  padding: 1rem;
  margin-bottom: 1rem;
}
.page-indicator {
  font-size: 1.1rem;
  font-weight: 500;
  color: #333;
  background: #f2f2f2;
  border-radius: 6px;
  padding: 6px 18px;
  display: inline-block;
  margin-bottom: 12px;
}
</style>

<style scoped>
.button-area {
  text-align: center;
  margin-top: 20px;
}
.page-indicator {
  font-size: 1.1rem;
  font-weight: 500;
  color: #333;
  background: #f2f2f2;
  border-radius: 6px;
  padding: 6px 18px;
  display: inline-block;
  margin-bottom: 12px;
}
</style>
