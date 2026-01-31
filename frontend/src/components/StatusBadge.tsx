import React from 'react';

interface StatusBadgeProps {
  status: 'active' | 'standby' | 'offline' | 'unknown';
}

const statusConfig = {
  active: { bg: 'bg-green-100', text: 'text-green-800', label: 'Active' },
  standby: { bg: 'bg-yellow-100', text: 'text-yellow-800', label: 'Standby' },
  offline: { bg: 'bg-red-100', text: 'text-red-800', label: 'Offline' },
  unknown: { bg: 'bg-gray-100', text: 'text-gray-800', label: 'Unknown' },
};

export const StatusBadge: React.FC<StatusBadgeProps> = ({ status }) => {
  const config = statusConfig[status];
  return (
    <span className={`px-2 py-1 rounded-full text-xs font-medium ${config.bg} ${config.text}`}>
      {config.label}
    </span>
  );
};
