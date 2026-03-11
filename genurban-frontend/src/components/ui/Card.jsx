// src/components/ui/Card.jsx
export function Card({ children, className = '' }) {
  return (
    <div className={`bg-white rounded-2xl border border-gray-200 p-6 ${className}`}>
      {children}
    </div>
  )
}

export function CardHeader({ children, className = '' }) {
  return (
    <div className={`mb-6 ${className}`}>
      {children}
    </div>
  )
}

export function CardTitle({ children, className = '' }) {
  return (
    <h3 className={`text-lg font-semibold text-gray-900 ${className}`}>
      {children}
    </h3>
  )
}

export function CardDescription({ children, className = '' }) {
  return (
    <p className={`text-gray-600 text-sm ${className}`}>
      {children}
    </p>
  )
}

export function CardContent({ children, className = '' }) {
  return (
    <div className={className}>
      {children}
    </div>
  )
}