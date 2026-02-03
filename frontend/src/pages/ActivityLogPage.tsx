import { useState } from 'react';
import { useActivityLogs, useDisplays } from '../hooks/useApi';
import { Activity, Power, Clock, Filter, ChevronDown } from 'lucide-react';
import { formatDistanceToNow } from 'date-fns';

export default function ActivityLogPage() {
  const [timeFilter, setTimeFilter] = useState<number | undefined>(24);
  const [displayFilter, setDisplayFilter] = useState<number | undefined>(undefined);
  const [actionFilter, setActionFilter] = useState<'on' | 'off' | undefined>(undefined);
  
  const { data: logs, isLoading, error } = useActivityLogs({
    hours: timeFilter,
    display_id: displayFilter,
    action: actionFilter,
    limit: 200,
  });
  
  const { data: displays } = useDisplays();

  const formatTimestamp = (timestamp: string) => {
    const date = new Date(timestamp);
    const timeStr = date.toLocaleTimeString('en-US', {
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
      hour12: false,
    });
    const dateStr = date.toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
    });
    return `${timeStr} - ${dateStr}`;
  };

  const getActionColor = (action: 'on' | 'off') => {
    return action === 'on' 
      ? 'text-green-600 dark:text-green-400 bg-green-50 dark:bg-green-900/20' 
      : 'text-gray-600 dark:text-gray-400 bg-gray-50 dark:bg-gray-900/20';
  };

  const getSourceBadge = (source: string) => {
    const styles = {
      manual: 'bg-blue-50 dark:bg-blue-900/20 text-blue-700 dark:text-blue-400',
      schedule: 'bg-purple-50 dark:bg-purple-900/20 text-purple-700 dark:text-purple-400',
      api: 'bg-orange-50 dark:bg-orange-900/20 text-orange-700 dark:text-orange-400',
    };
    
    return (
      <span className={`px-2 py-0.5 rounded text-xs font-medium ${styles[source as keyof typeof styles] || styles.api}`}>
        {source}
      </span>
    );
  };

  if (isLoading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="text-gray-500 dark:text-gray-400">Loading activity logs...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 dark:bg-red-950 border border-red-200 dark:border-red-800 rounded-lg p-4">
        <p className="text-red-800 dark:text-red-300">Failed to load activity logs. Please try again.</p>
      </div>
    );
  }

  return (
    <div>
      <div className="flex justify-between items-center mb-6">
        <div className="flex items-center space-x-3">
          <Activity className="w-8 h-8 text-blue-600 dark:text-blue-400" />
          <div>
            <h2 className="text-2xl font-bold text-gray-900 dark:text-white">Activity Log</h2>
            <p className="text-sm text-gray-600 dark:text-gray-400">Power state changes for all displays</p>
          </div>
        </div>
      </div>

      <div className="bg-white dark:bg-gray-800 rounded-lg shadow dark:shadow-gray-900 p-4 mb-6">
        <div className="flex items-center space-x-2 mb-3">
          <Filter className="w-4 h-4 text-gray-600 dark:text-gray-400" />
          <span className="text-sm font-medium text-gray-700 dark:text-gray-300">Filters</span>
        </div>
        
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Time Range
            </label>
            <div className="relative">
              <select
                value={timeFilter || ''}
                onChange={(e) => setTimeFilter(e.target.value ? parseInt(e.target.value) : undefined)}
                className="w-full px-3 py-2 bg-gray-50 dark:bg-gray-900 border border-gray-300 dark:border-gray-700 rounded-lg text-gray-900 dark:text-white appearance-none cursor-pointer"
              >
                <option value="1">Last 1 hour</option>
                <option value="6">Last 6 hours</option>
                <option value="24">Last 24 hours</option>
                <option value="168">Last 7 days</option>
                <option value="">All time</option>
              </select>
              <ChevronDown className="absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-500 pointer-events-none" />
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Display
            </label>
            <div className="relative">
              <select
                value={displayFilter || ''}
                onChange={(e) => setDisplayFilter(e.target.value ? parseInt(e.target.value) : undefined)}
                className="w-full px-3 py-2 bg-gray-50 dark:bg-gray-900 border border-gray-300 dark:border-gray-700 rounded-lg text-gray-900 dark:text-white appearance-none cursor-pointer"
              >
                <option value="">All displays</option>
                {displays?.map((display) => (
                  <option key={display.id} value={display.id}>
                    {display.name}
                  </option>
                ))}
              </select>
              <ChevronDown className="absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-500 pointer-events-none" />
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Action
            </label>
            <div className="relative">
              <select
                value={actionFilter || ''}
                onChange={(e) => setActionFilter(e.target.value as 'on' | 'off' | undefined || undefined)}
                className="w-full px-3 py-2 bg-gray-50 dark:bg-gray-900 border border-gray-300 dark:border-gray-700 rounded-lg text-gray-900 dark:text-white appearance-none cursor-pointer"
              >
                <option value="">All actions</option>
                <option value="on">Power On</option>
                <option value="off">Power Off</option>
              </select>
              <ChevronDown className="absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-500 pointer-events-none" />
            </div>
          </div>
        </div>
      </div>

      {!logs || logs.length === 0 ? (
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow dark:shadow-gray-900 p-8 text-center">
          <Activity className="w-16 h-16 text-gray-400 dark:text-gray-600 mx-auto mb-4" />
          <p className="text-gray-600 dark:text-gray-400">No activity logs found for the selected filters.</p>
          <p className="text-sm text-gray-500 dark:text-gray-500 mt-2">
            Try adjusting the time range or removing filters.
          </p>
        </div>
      ) : (
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow dark:shadow-gray-900 overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-gray-50 dark:bg-gray-900 border-b border-gray-200 dark:border-gray-700">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-600 dark:text-gray-400 uppercase tracking-wider">
                    Display
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-600 dark:text-gray-400 uppercase tracking-wider">
                    Action
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-600 dark:text-gray-400 uppercase tracking-wider">
                    Source
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-600 dark:text-gray-400 uppercase tracking-wider">
                    Timestamp
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-600 dark:text-gray-400 uppercase tracking-wider">
                    Relative
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200 dark:divide-gray-700">
                {logs.map((log) => (
                  <tr key={log.id} className="hover:bg-gray-50 dark:hover:bg-gray-900/50 transition-colors">
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="flex items-center">
                        <div className="text-sm font-medium text-gray-900 dark:text-white">
                          {log.display_name}
                        </div>
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="flex items-center space-x-2">
                        <Power 
                          className={`w-4 h-4 ${log.action === 'on' ? 'text-green-600 dark:text-green-400' : 'text-gray-600 dark:text-gray-400'}`}
                        />
                        <span className={`px-3 py-1 rounded-full text-xs font-medium ${getActionColor(log.action)}`}>
                          {log.action === 'on' ? 'Power On' : 'Power Off'}
                        </span>
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      {getSourceBadge(log.source)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="flex items-center space-x-2 text-sm text-gray-600 dark:text-gray-400">
                        <Clock className="w-4 h-4" />
                        <span>{formatTimestamp(log.timestamp)}</span>
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-500">
                      {formatDistanceToNow(new Date(log.timestamp), { addSuffix: true })}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          
          {logs.length >= 200 && (
            <div className="px-6 py-3 bg-yellow-50 dark:bg-yellow-900/20 border-t border-yellow-200 dark:border-yellow-800">
              <p className="text-sm text-yellow-800 dark:text-yellow-400">
                Showing the most recent 200 events. Use filters to narrow down results.
              </p>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
