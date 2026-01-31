import { useState } from 'react';
import { Plus } from 'lucide-react';
import { ScheduleCard } from '../components';
import { CreateScheduleModal } from '../components/CreateScheduleModal';
import { useSchedules, useToggleSchedule } from '../hooks/useApi';

export default function SchedulesPage() {
  const [isModalOpen, setIsModalOpen] = useState(false);
  const { data: schedules, isLoading, error } = useSchedules();
  const toggleMutation = useToggleSchedule();

  const handleToggleEnabled = (id: number, enabled: boolean) => {
    toggleMutation.mutate({ id, enabled });
  };

  if (isLoading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="text-gray-500 dark:text-gray-400">Loading schedules...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 dark:bg-red-950 border border-red-200 dark:border-red-800 rounded-lg p-4">
        <p className="text-red-800 dark:text-red-300">Failed to load schedules. Please try again.</p>
      </div>
    );
  }

  return (
    <div>
      <div className="flex justify-between items-center mb-6">
        <h2 className="text-2xl font-bold text-gray-900 dark:text-white">Schedules</h2>
        <button 
          onClick={() => setIsModalOpen(true)}
          className="flex items-center space-x-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
        >
          <Plus className="w-5 h-5" />
          <span>Create Schedule</span>
        </button>
      </div>

      {!schedules || schedules.length === 0 ? (
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow dark:shadow-gray-900 p-8 text-center">
          <p className="text-gray-600 dark:text-gray-400">No schedules defined yet. Create schedules to automate power control.</p>
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

      <CreateScheduleModal 
        isOpen={isModalOpen} 
        onClose={() => setIsModalOpen(false)} 
      />
    </div>
  );
}
