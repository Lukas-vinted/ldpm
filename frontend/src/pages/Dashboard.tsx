import { Monitor, Users, Clock, Power } from 'lucide-react';
import { useDisplays, useGroups, useSchedules } from '../hooks/useApi';

export default function Dashboard() {
  const { data: displays } = useDisplays();
  const { data: groups } = useGroups();
  const { data: schedules } = useSchedules();

  const activeDisplays = displays?.filter(d => d.status === 'active').length || 0;
  const standbyDisplays = displays?.filter(d => d.status === 'standby').length || 0;
  const offlineDisplays = displays?.filter(d => d.status === 'offline').length || 0;
  const enabledSchedules = schedules?.filter(s => s.enabled).length || 0;

  const stats = [
    {
      name: 'Active Displays',
      value: activeDisplays,
      total: displays?.length || 0,
      icon: Monitor,
      color: 'text-green-600',
      bg: 'bg-green-100',
    },
    {
      name: 'Standby Displays',
      value: standbyDisplays,
      total: displays?.length || 0,
      icon: Power,
      color: 'text-yellow-600',
      bg: 'bg-yellow-100',
    },
    {
      name: 'Offline Displays',
      value: offlineDisplays,
      total: displays?.length || 0,
      icon: Monitor,
      color: 'text-red-600',
      bg: 'bg-red-100',
    },
    {
      name: 'Total Groups',
      value: groups?.length || 0,
      icon: Users,
      color: 'text-blue-600',
      bg: 'bg-blue-100',
    },
    {
      name: 'Active Schedules',
      value: enabledSchedules,
      total: schedules?.length || 0,
      icon: Clock,
      color: 'text-purple-600',
      bg: 'bg-purple-100',
    },
  ];

  return (
    <div>
      <div className="mb-6">
        <h2 className="text-2xl font-bold text-gray-900 dark:text-white">Dashboard</h2>
        <p className="text-gray-600 dark:text-gray-400 mt-1">Welcome to LDPM - Linux Display Power Management</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {stats.map((stat) => (
          <div key={stat.name} className="bg-white dark:bg-gray-800 rounded-lg shadow dark:shadow-gray-900 p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600 dark:text-gray-400">{stat.name}</p>
                <p className="text-3xl font-bold text-gray-900 dark:text-white mt-2">
                  {stat.value}
                  {(stat.total ?? 0) > 0 && stat.name !== 'Total Groups' && (
                    <span className="text-lg text-gray-500 dark:text-gray-400"> / {stat.total}</span>
                  )}
                </p>
              </div>
              <div className={`p-3 rounded-lg ${stat.bg} dark:bg-opacity-20`}>
                <stat.icon className={`w-8 h-8 ${stat.color} dark:opacity-80`} />
              </div>
            </div>
          </div>
        ))}
      </div>

      <div className="mt-8 bg-blue-50 dark:bg-blue-950 border border-blue-200 dark:border-blue-900 rounded-lg p-6">
        <h3 className="text-lg font-semibold text-blue-900 dark:text-blue-100 mb-2">Quick Start</h3>
        <ul className="text-blue-800 dark:text-blue-200 space-y-1">
          <li>• Add displays from the Displays page</li>
          <li>• Create groups to manage multiple displays together</li>
          <li>• Set up schedules to automate power control</li>
        </ul>
      </div>
    </div>
  );
}
