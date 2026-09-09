import clsx from 'clsx'
import type { ReactNode } from 'react'

/**
 * A floating glass surface.
 *
 * Panels float over the map rather than sitting in a grid; that single decision is what
 * keeps the map the centerpiece and stops the layout reading as an admin dashboard.
 * Blur-on-blur turns to mud, so never stack more than two of these.
 */
export function GlassPanel({
  children,
  className,
  as: Tag = 'div',
}: {
  children: ReactNode
  className?: string
  as?: 'div' | 'aside' | 'section' | 'header' | 'footer'
}) {
  return <Tag className={clsx('cv-glass', className)}>{children}</Tag>
}
