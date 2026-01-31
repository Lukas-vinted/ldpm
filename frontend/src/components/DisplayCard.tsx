import React from 'react';
import { Monitor } from 'lucide-react';
import { Display } from '../types';
import { StatusBadge } from './StatusBadge';
import { PowerButton } from './PowerButton';

interface DisplayCardProps {
  display: Display;
  onPowerToggle?: (id: number, state: 'on' | 'off') => void;
  isLoading?: boolean;
}

export const DisplayCard: React.FC<DisplayCardProps> = ({ 
  display, 
  onPowerToggle, 
  isLoading = false 
}) => {
  const handleToggle = () => {
    if (onPowerToggle) {
      const newState = display.status === 'active' ? 'off' : 'on';
      onPowerToggle(display.id, newState);
    }
  };

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow dark:shadow-gray-900 p-4 hover:shadow-lg dark:hover:shadow-gray-800 transition-shadow">
      <div className="flex items-start justify-between">
        <div className="flex items-center space-x-3 flex-1">
          <Monitor className="w-8 h-8 text-gray-600 dark:text-gray-400" />
          <div className="flex-1">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white">{display.name}</h3>
            <p className="text-sm text-gray-500 dark:text-gray-400">{display.ip_address}</p>
            {display.location && (
              <p className="text-xs text-gray-400 dark:text-gray-500 mt-1">{display.location}</p>
            )}
          </div>
        </div>
        <div className="flex items-center space-x-2">
          <StatusBadge status={display.status} />
          {onPowerToggle && (
            <PowerButton
              isOn={display.status === 'active'}
              isLoading={isLoading}
              onToggle={handleToggle}
            />
          )}
        </div>
      </div>
    </div>
  );
};
