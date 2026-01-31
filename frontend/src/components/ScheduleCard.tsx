import React from 'react';
import { Clock, Power } from 'lucide-react';
import { Schedule } from '../types';

interface ScheduleCardProps {
  schedule: Schedule;
  onToggleEnabled?: (id: number, enabled: boolean) => void;
  isLoading?: boolean;
}

export const ScheduleCard: React.FC<ScheduleCardProps> = ({ 
  schedule, 
  onToggleEnabled,
  isLoading = false 
}) => {
  const handleToggle = () => {
    if (onToggleEnabled) {
      onToggleEnabled(schedule.id, !schedule.enabled);
    }
  };

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow dark:shadow-gray-900 p-4 hover:shadow-lg dark:hover:shadow-gray-800 transition-shadow">
      <div className="flex items-start justify-between">
        <div className="flex items-center space-x-3 flex-1">
          <Clock className="w-8 h-8 text-purple-600 dark:text-purple-400" />
          <div className="flex-1">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white">{schedule.name}</h3>
            <p className="text-sm text-gray-600 dark:text-gray-400 mt-1 font-mono">{schedule.cron_expression}</p>
            <div className="flex items-center space-x-2 mt-2">
              <Power className={`w-4 h-4 ${schedule.action === 'on' ? 'text-green-600 dark:text-green-400' : 'text-gray-400 dark:text-gray-500'}`} />
              <span className="text-xs text-gray-500 dark:text-gray-400">
                Power {schedule.action === 'on' ? 'ON' : 'OFF'}
              </span>
            </div>
          </div>
        </div>
        {onToggleEnabled && (
          <button
            onClick={handleToggle}
            disabled={isLoading}
            className={`px-3 py-1 rounded text-sm font-medium transition-colors ${
              schedule.enabled
                ? 'bg-green-100 dark:bg-green-900 text-green-800 dark:text-green-300 hover:bg-green-200 dark:hover:bg-green-800'
                : 'bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-600'
            } ${isLoading ? 'opacity-50 cursor-not-allowed' : ''}`}
          >
            {schedule.enabled ? 'Enabled' : 'Disabled'}
          </button>
        )}
      </div>
    </div>
  );
};
