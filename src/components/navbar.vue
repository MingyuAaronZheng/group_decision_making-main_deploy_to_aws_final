<template>
  <b-navbar id="nav-bar" toggleable="lg" type="dark" variant="dark">
    <b-navbar-brand>Parole Judgement Test</b-navbar-brand>
    <b-nav class="ml-auto">
      <b-navbar-brand :class="avatarShowed" class="avatar-area">
        <v-animal size="40px" :name="avatarNamechanged" :color="avatarColorchanged" class="avatar-icon"/>
        {{avatarColorchanged}} {{avatarNamechanged}}
      </b-navbar-brand>
    </b-nav>
  </b-navbar>
</template>
<script>
import { colors } from '@/components/constants'
export default {
  name: 'nav-bar',
  data: function () {
    return {
    }
  },
  computed: {
    avatarNamechanged () {
      return this.$store.state.avatar_name
    },
    avatarColorchanged () {
      return this.$store.state.avatar_color
    },
    avatarColorHexchanged () {
      return colors[this.$store.state.avatar_color] || this.$store.state.avatar_color || '#000000'
    },
    avatarShowed () {
      return (this.avatarNamechanged != null) ? 'show_avatar' : 'hide_avatar'
    }
  }
}
</script>
<style>
  .show_avatar {
    display: block;
  }
  .hide_avatar {
    display: none;
  }
  .avatar-area {
    display: flex;
    align-items: center;
  }
  .avatar-icon {
    display: inline-block !important;
    margin-right: 10px;
  }

  .avatar-icon svg {
    fill: inherit !important;
  }

  .avatar-icon svg path {
    fill: inherit !important;
  }

  .avatar-icon svg circle {
    fill: inherit !important;
  }
</style>
