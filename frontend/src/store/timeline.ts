import { create } from 'zustand'

/**
 * The only global state in the application: which storm is selected, where the timeline
 * cursor sits, and which mode we are in.
 *
 * Three fields, deliberately. Everything else is either server state (TanStack Query) or
 * local component state. A store that grows past this is a sign something has been put
 * in the wrong place.
 */
export type Mode = 'explore' | 'verify'

interface TimelineState {
  selectedSid: string | null
  /** ISO instant of the scrubber cursor. Null until a storm's frames have loaded. */
  cursorTime: string | null
  mode: Mode
  /** In verify mode, the instant a forecast was issued for. */
  verifyFrom: string | null
  revealed: boolean

  selectStorm: (sid: string) => void
  setCursor: (t: string) => void
  setMode: (mode: Mode) => void
  setVerifyFrom: (t: string | null) => void
  setRevealed: (revealed: boolean) => void
}

export const useTimeline = create<TimelineState>((set) => ({
  selectedSid: null,
  cursorTime: null,
  mode: 'explore',
  verifyFrom: null,
  revealed: false,

  selectStorm: (sid) =>
    // Changing storm resets the cursor and any in-progress verification: carrying a
    // timestamp from one storm to another would silently show the wrong frame.
    set({ selectedSid: sid, cursorTime: null, verifyFrom: null, revealed: false }),
  setCursor: (t) => set({ cursorTime: t }),
  setMode: (mode) => set({ mode, revealed: false }),
  setVerifyFrom: (t) => set({ verifyFrom: t, revealed: false }),
  setRevealed: (revealed) => set({ revealed }),
}))
