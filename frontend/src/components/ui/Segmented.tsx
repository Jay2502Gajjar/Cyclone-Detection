import clsx from 'clsx'

/** A two-or-three-way switch. Used for Explore | Verify in the header, and nowhere else. */
export function Segmented<T extends string>({
  options,
  value,
  onChange,
}: {
  options: { value: T; label: string }[]
  value: T
  onChange: (value: T) => void
}) {
  return (
    <div className="flex items-center gap-0.5 rounded-lg border border-cv-glass-border bg-cv-glass p-0.5">
      {options.map((option) => (
        <button
          key={option.value}
          type="button"
          onClick={() => onChange(option.value)}
          aria-pressed={value === option.value}
          className={clsx(
            'rounded-[6px] px-3 py-1 text-[12px] transition-colors duration-150',
            value === option.value
              ? 'bg-cv-accent-dim text-cv-accent'
              : 'text-cv-muted hover:text-cv-text',
          )}
        >
          {option.label}
        </button>
      ))}
    </div>
  )
}
