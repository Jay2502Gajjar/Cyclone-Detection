import * as Dialog from '@radix-ui/react-dialog'
import type { ReactNode } from 'react'

/**
 * A right-hand drawer for progressive disclosure.
 *
 * Grad-CAM, structural metrics, SHAP attributions and analogue detail all live behind
 * one of these. The map stays visible behind the blur, so opening a drawer reads as
 * looking closer at the same thing rather than navigating somewhere else — which is why
 * these are drawers and not routes.
 */
export function Drawer({
  open,
  onOpenChange,
  title,
  subtitle,
  children,
}: {
  open: boolean
  onOpenChange: (open: boolean) => void
  title: string
  subtitle?: string
  children: ReactNode
}) {
  return (
    <Dialog.Root open={open} onOpenChange={onOpenChange}>
      <Dialog.Portal>
        <Dialog.Overlay className="fixed inset-0 z-40 bg-cv-ground/40" />
        <Dialog.Content
          className="cv-glass fixed top-3 right-3 bottom-3 z-50 flex w-[min(52vw,720px)] flex-col overflow-hidden focus:outline-none"
          aria-describedby={undefined}
        >
          <div className="flex items-start justify-between border-b border-cv-glass-border px-5 py-4">
            <div>
              <Dialog.Title className="text-[15px] font-medium text-cv-text">
                {title}
              </Dialog.Title>
              {subtitle ? (
                <p className="mt-0.5 text-[11px] text-cv-muted">{subtitle}</p>
              ) : null}
            </div>
            <Dialog.Close
              className="rounded px-2 py-1 text-[12px] text-cv-muted transition-colors duration-150 hover:text-cv-text"
              aria-label="Close"
            >
              Esc
            </Dialog.Close>
          </div>
          <div className="flex-1 overflow-y-auto px-5 py-4">{children}</div>
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  )
}
