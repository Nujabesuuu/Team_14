import type { CapacitorConfig } from '@capacitor/cli'

const config: CapacitorConfig = {
  appId: 'dev.teamate.app',
  appName: 'Teamate',
  webDir: 'dist',
  server: {
    // The MVP talks to a plain-HTTP API on the local network.
    cleartext: true,
  },
  android: {
    backgroundColor: '#0A0A0A',
  },
}

export default config
