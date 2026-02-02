import React from 'react';
import { Calendar, Power, Clock, Trash2 } from 'lucide-react';
import { Schedule } from '../types';

interface ScheduleCardProps {
  schedule: Schedule;
  onToggle?: (id: number, enabled: boolean) => void;
  onDelete?: (id: number) => void;
  isLoading?: boolean;
}

export const ScheduleCard: React.FC<ScheduleCardProps> = ({ 
  schedule, 
  onToggle,
  onDelete,
  isLoading = false 
}) => {
  const handleToggle = () => {
    if (onToggle && !isLoading) {
      onToggle(schedule.id, !schedule.enabled);
    }
  };

  const handleDelete = (e: React.MouseEvent) => {
    e.stopPropagation();
    if (onDelete) {
      onDelete(schedule.id);
    }
  };

  const formatCron = (cron: string) => {
    const parts = cron.split(' ');
    if (parts.length !== 5) return cron;
    
    const [minute, hour, , , dayOfWeek] = parts;
    const time = `${hour.padStart(2, '0')}:${minute.padStart(2, '0')}`;
    
    const dayMap: Record<string, string> = {
      '0': 'Sun',
      '1': 'Mon',
      '2': 'Tue',
      '3': 'Wed',
      '4': 'Thu',
      '5': 'Fri',
      '6': 'Sat',
      '*': 'Every day',
    };

    if (dayOfWeek === '*') {
      return `${time} - Every day`;
    }

    const days = dayOfWeek.split(',').map(d => dayMap[d] || d).join(', ');
    return `${time} - ${days}`;
  };

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow dark:shadow-gray-900 p-4 hover:shadow-lg dark:hover:shadow-gray-800 transition-shadow">
      <div className="flex items-start justify-between">
        <div className="flex items-center space-x-3 flex-1">
          <Calendar className="w-8 h-8 text-gray-600 dark:text-gray-400" />
          <div className="flex-1">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white">{schedule.name}</h3>
            <div className="flex items-center space-x-2 mt-1">
              <Clock className="w-4 h-4 text-gray-500 dark:text-gray-400" />
              <p className="text-sm text-gray-500 dark:text-gray-400">{formatCron(schedule.cron_expression)}</p>
            </div>
            <div className="flex items-center space-x-2 mt-1">
              <Power className={`w-4 h-4 ${schedule.action === 'on' ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400'}`} />
              <p className="text-sm text-gray-500 dark:text-gray-400">
                Power {schedule.action === 'on' ? 'On' : 'Off'}
              </p>
            </div>
          </div>
        </div>
        <div className="flex items-center space-x-2">
          {onToggle && (
            <button
              onClick={handleToggle}
              disabled={isLoading}
              className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 ${
                schedule.enabled 
                  ? 'bg-blue-600' 
                  : 'bg-gray-200 dark:bg-gray-700'
              } ${isLoading ? 'opacity-50 cursor-not-allowed' : ''}`}
            >
              <span
                className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                  schedule.enabled ? 'translate-x-6' : 'translate-x-1'
                }`}
              />
            </button>
          )}
          {onDelete && (
            <button
              onClick={handleDelete}
              className="p-2 text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/20 rounded-lg transition-colors"
              title="Delete schedule"
            >
              <Trash2 className="w-5 h-5" />
            </button>
          )}
        </div>
      </div>
    </div>
  );
};
