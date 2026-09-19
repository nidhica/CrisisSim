interface Props { level: string; size?: 'sm' | 'md' }

const colors: Record<string, string> = {
  low: 'bg-green-100 text-green-800',
  medium: 'bg-yellow-100 text-yellow-800',
  moderate: 'bg-yellow-100 text-yellow-800',
  high: 'bg-orange-100 text-orange-800',
  critical: 'bg-red-100 text-red-800',
}

export function SeverityBadge({ level, size = 'sm' }: Props) {
  const cls = colors[level] || 'bg-gray-100 text-gray-800'
  const sz = size === 'md' ? 'px-3 py-1 text-sm' : 'px-2 py-0.5 text-xs'
  return (
    <span className={`${cls} ${sz} font-semibold rounded-full uppercase`}>
      {level}
    </span>
  )
}
