import ReadyEndToast from '@/components/ReadyEndToast.vue'

let activeReadyToEndToast = null

export function notifyInactivity (bvToast, testFlag = 'N') {
  const baseMsg = 'Warning: You appear to be inactive. Please respond within 30 seconds or you may be removed from the discussion.'
  const msg = testFlag === 'Y'
    ? `${baseMsg} [TEST MODE: inactivity removal disabled]`
    : baseMsg
  bvToast.toast(msg, {
    title: 'Inactivity Warning',
    variant: 'warning',
    solid: true,
    autoHideDelay: 10000
  })
}

export function notifyReadyToEnd (toast, subjectColor, subjectName) {
  // Clear any existing toast first
  if (activeReadyToEndToast) {
    toast.dismiss(activeReadyToEndToast)
  }
  activeReadyToEndToast = 'ready-to-end-warning'
  toast(
    { component: ReadyEndToast, props: { subjectColor, subjectName } },
    {
      type: 'warning',
      position: 'top-left',
      timeout: false, // persistent
      closeOnClick: false,
      closeButton: 'button', // Ensure close button is always visible
      hideProgressBar: true,
      toastId: activeReadyToEndToast
    }
  )
}

export function clearReadyToEndNotification (toast) {
  if (activeReadyToEndToast) {
    toast.dismiss(activeReadyToEndToast)
    activeReadyToEndToast = null
  }
}
