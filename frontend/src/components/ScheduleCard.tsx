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
    <div className="bg-white rounded-lg shadow p-4 hover:shadow-lg transition-shadow">
      <div className="flex items-start justify-between">
        <div className="flex items-center space-x-3 flex-1">
          <Clock className="w-8 h-8 text-purple-600" />
          <div className="flex-1">
            <h3 className="text-lg font-semibold text-gray-900">{schedule.name}</h3>
            <p className="text-sm text-gray-600 mt-1 font-mono">{schedule.cron_expression}</p>
            <div className="flex items-center space-x-2 mt-2">
              <Power className={`w-4 h-4 ${schedule.action === 'on' ? 'text-green-600' : 'text-gray-400'}`} />
              <span className="text-xs text-gray-500">
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
                ? 'bg-green-100 text-green-800 hover:bg-green-200'
                : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
            } ${isLoading ? 'opacity-50 cursor-not-allowed' : ''}`}
          >
            {schedule.enabled ? 'Enabled' : 'Disabled'}
          </button>
        )}
      </div>
    </div>
  );
};
