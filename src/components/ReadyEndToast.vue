<template>
  <div class="ready-end-toast">
    <span :style="{ color: 'black', fontWeight: 'bold' }">
      {{ subjectColor }} {{ subjectName }}
    </span>
    <div>
      has indicated they are ready to end the discussion.
    </div>
    <div>
      If you’re also ready, click the button to conclude the conversation.
    </div>
    <div>
      If not, feel free to continue sharing your thoughts.
    </div>
    <div>
      The discussion will only end when all participants have clicked to end it.
    </div>
  </div>
</template>

<script>
export default {
  name: 'ReadyEndToast',
  props: {
    subjectColor: {
      type: String,
      required: true
    },
    subjectName: {
      type: String,
      required: true
    }
  }
}
</script>

<style scoped>
.ready-end-toast {
  line-height: 1.4;
}
</style>
