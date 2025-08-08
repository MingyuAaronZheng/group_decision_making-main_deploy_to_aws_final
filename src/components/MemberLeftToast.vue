<template>
  <div class="member-left-toast">
    <div class="toast-message">{{ message }}</div>
    <b-button
      class="mt-2 w-100"
      variant="primary"
      size="sm"
      @click="proceed"
    >
      Proceed to Next Survey
    </b-button>
  </div>
</template>

<script>
export default {
  name: 'MemberLeftToast',
  props: {
    message: {
      type: String,
      required: true
    },
    onProceed: {
      type: Function,
      required: true
    }
  },
  methods: {
    proceed () {
      this.onProceed()
    }
  }
}
</script>

<style scoped>
.member-left-toast {
  text-align: left;
}

.toast-message {
  margin-bottom: 8px;
  line-height: 1.4;
}
</style>
