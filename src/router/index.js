import Vue from 'vue'
import VueRouter from 'vue-router'
import VueSimpleAlert from 'vue-simple-alert'
/** Qualifications **/
import StarEntrance from '../views/StarEntrance.vue'
/** Common pages **/
/** Common pages - Instructions**/
import DiscussionInstructions from '../views/DiscussionInstructions.vue'
import WaitingRoom from '../views/WaitingRoom.vue'
/** Common pages - Exit pages**/
import EarlyExit from '../views/errors/EarlyExit.vue'
/** Errors **/
import FailPairing from '../views/errors/FailPairing.vue'
/** Without AI **/

import PreDSurvey from '@/views/PreDSurvey.vue'
import PostDOSurvey from '@/views/PostDOSurvey.vue'
import PostDFSurvey from '@/views/PostDFSurvey.vue'
import DemograSurvey from '@/views/DemograSurvey.vue'
import ChatRoom from '@/views/ChatRoom.vue'
import AvatarAssignment from '@/views/avatar-assignment.vue'
import DeBriefing from '@/views/DeBriefing.vue'
import GoBackTerminatedParticipation from '@/views/errors/GoBackTerminatedParticipation.vue'
import InactivityTerminatedParticipation from '@/views/errors/InactivityTerminatedParticipation.vue'

Vue.use(VueRouter)
Vue.use(VueSimpleAlert)

// Define the correct order of pages
const pageOrder = [
  'StarEntrance',
  'DemograSurvey',
  'PreDSurvey',
  'DiscussionInstructions',
  'WaitingRoom',
  'AvatarAssignment',
  'ChatRoom',
  'PostDOSurvey',
  'PostDFSurvey'
]

const routes = [
  {
    path: '/',
    redirect: '/StarEntrance'
  },
  {
    path: '/EarlyExit',
    name: 'EarlyExit',
    component: EarlyExit
  },
  {
    path: '/StarEntrance',
    name: 'StarEntrance',
    component: StarEntrance
  },
  {
    path: '/PreDSurvey',
    name: 'PreDSurvey',
    component: PreDSurvey
  },
  {
    path: '/FailPairing',
    name: 'FailPairing',
    component: FailPairing
  },
  {
    path: '/GoBackTerminatedParticipation',
    name: 'GoBackTerminatedParticipation',
    component: GoBackTerminatedParticipation
  },
  {
    path: '/InactivityTerminatedParticipation',
    name: 'InactivityTerminatedParticipation',
    component: InactivityTerminatedParticipation
  },
  {
    path: '/PreDSurvey',
    name: 'PreDSurvey',
    component: PreDSurvey
  },
  {
    path: '/PostDOSurvey',
    name: 'PostDOSurvey',
    component: PostDOSurvey
  },
  {
    path: '/PostDFSurvey',
    name: 'PostDFSurvey',
    component: PostDFSurvey
  },
  {
    path: '/DemograSurvey',
    name: 'DemograSurvey',
    component: DemograSurvey
  },
  {
    path: '/ChatRoom',
    name: 'ChatRoom',
    component: ChatRoom
  },
  {
    path: '/DiscussionInstructions',
    name: 'DiscussionInstructions',
    component: DiscussionInstructions
  },
  {
    path: '/WaitingRoom',
    name: 'WaitingRoom',
    component: WaitingRoom
  },
  {
    path: '/avatar-assignment',
    name: 'AvatarAssignment',
    component: AvatarAssignment
  },
  {
    path: '/deBriefing',
    name: 'DeBriefing',
    component: DeBriefing
  }
]

const router = new VueRouter({
  mode: 'history',
  base: process.env.BASE_URL,
  routes
})

router.beforeEach((to, from, next) => {
  // Get indices of current and target pages in the pageOrder array
  let fromIndex
  let toIndex

  // Define EndingPages as an array of pages that are not part of the study flow
  const EndingPages = ['KickOut', 'FailPairing', 'NoEntrance', 'GoBackTerminatedParticipation', 'InactivityTerminatedParticipation', 'DeBriefing', 'EarlyExit']
  // If the page is an ending page, set the index to 1000
  if (EndingPages.includes(from.name)) {
    fromIndex = 1000
  } else {
    fromIndex = pageOrder.indexOf(from.name)
  }

  if (EndingPages.includes(to.name)) {
    toIndex = 1000
  } else {
    toIndex = pageOrder.indexOf(to.name)
  }
  // Check if trying to go backwards in the study flow
  if (fromIndex !== -1 && toIndex !== -1 && toIndex < fromIndex) {
    VueSimpleAlert.confirm(
      'Warning: Going back will invalidate your participation.',
      'You will not be compensated if you leave. Do you really want to go back?',
      'warning'
    ).then((result) => {
      if (result) {
        next('/GoBackTerminatedParticipation')
      } else {
        next(false)
      }
    }).catch(() => {
      next(false)
    })
  } else {
    next()
  }
})

export default router
