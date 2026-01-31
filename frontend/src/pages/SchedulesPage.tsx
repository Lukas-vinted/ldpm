import { Plus } from 'lucide-react';
import { ScheduleCard } from '../components';
import { useSchedules, useToggleSchedule } from '../hooks/useApi';

export default function SchedulesPage() {
  const { data: schedules, isLoading, error } = useSchedules();
  const toggleMutation = useToggleSchedule();

  const handleToggleEnabled = (id: number, enabled: boolean) => {
    toggleMutation.mutate({ id, enabled });
  };

  if (isLoading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="text-gray-500">Loading schedules...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-4">
        <p className="text-red-800">Failed to load schedules. Please try again.</p>
      </div>
    );
  }

  return (
    <div>
      <div className="flex justify-between items-center mb-6">
        <h2 className="text-2xl font-bold text-gray-900">Schedules</h2>
        <button className="flex items-center space-x-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors">
          <Plus className="w-5 h-5" />
          <span>Create Schedule</span>
        </button>
      </div>

      {!schedules || schedules.length === 0 ? (
        <div className="bg-white rounded-lg shadow p-8 text-center">
          <p className="text-gray-600">No schedules defined yet. Create schedules to automate power control.</p>
        </div>
      ) : (
        <div className="space-y-4">
          {schedules.map((schedule) => (
            <ScheduleCard
              key={schedule.id}
              schedule={schedule}
              onToggleEnabled={handleToggleEnabled}
              isLoading={toggleMutation.isPending}
            />
          ))}
        </div>
      )}
    </div>
  );
}
