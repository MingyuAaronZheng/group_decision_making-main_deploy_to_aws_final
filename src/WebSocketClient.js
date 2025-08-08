export default class WebSocketClient {
  constructor (url) {
    this.url = url
    this.client = null
    this.reconnectInterval = 5000 // 5 seconds
  }

  connect () {
    this.client = new WebSocket(this.url)

    this.client.onopen = () => {
      console.log('WebSocket connected')
    }

    this.client.onmessage = (event) => {
      if (this.onMessageCallback) {
        this.onMessageCallback(JSON.parse(event.data))
      }
    }

    this.client.onerror = (error) => {
      console.error('WebSocket error:', error)
    }

    this.client.onclose = () => {
      console.log('WebSocket disconnected, attempting reconnect...')
      setTimeout(() => this.connect(), this.reconnectInterval)
    }
  }

  onMessage (callback) {
    this.onMessageCallback = callback
  }

  send (message) {
    if (this.client && this.client.readyState === WebSocket.OPEN) {
      this.client.send(JSON.stringify(message))
    }
  }
}
