import { motion, AnimatePresence } from 'framer-motion'
import { AlertTriangle, ShieldAlert, CheckCircle, X } from 'lucide-react'

const Notification = ({ type, message, onClose, id }) => {
  const icons = {
    warning: AlertTriangle,
    error: ShieldAlert,
    success: CheckCircle
  }

  const colors = {
    warning: 'bg-amber-500/10 border-amber-500/20 text-amber-400',
    error: 'bg-red-500/10 border-red-500/20 text-red-400',
    success: 'bg-emerald-500/10 border-emerald-500/20 text-emerald-400'
  }

  const Icon = icons[type] || AlertTriangle

  return (
    <motion.div
      initial={{ opacity: 0, x: 300, scale: 0.9 }}
      animate={{ opacity: 1, x: 0, scale: 1 }}
      exit={{ opacity: 0, x: 300, scale: 0.9 }}
      className={`glass-card p-4 flex items-start gap-3 min-w-[320px] max-w-[400px] ${colors[type]}`}
    >
      <Icon size={20} className="mt-0.5 flex-shrink-0" />
      <div className="flex-1">
        <p className="text-sm font-medium leading-tight">{message}</p>
      </div>
      <button
        onClick={() => onClose(id)}
        className="p-1 rounded-full hover:bg-white/10 transition-colors"
      >
        <X size={14} />
      </button>
    </motion.div>
  )
}

const NotificationContainer = ({ notifications, onClose }) => {
  return (
    <div className="fixed top-6 right-6 z-50 space-y-3">
      <AnimatePresence>
        {notifications.map((notification) => (
          <Notification
            key={notification.id}
            {...notification}
            onClose={onClose}
          />
        ))}
      </AnimatePresence>
    </div>
  )
}

export default NotificationContainer