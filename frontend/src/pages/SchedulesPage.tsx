import { useState } from 'react';
import { Plus } from 'lucide-react';
import { ScheduleCard } from '../components/ScheduleCard';
import { CreateScheduleModal } from '../components/CreateScheduleModal';
import { ConfirmDeleteModal } from '../components/ConfirmDeleteModal';
import { useSchedules, useToggleSchedule, useDeleteSchedule } from '../hooks/useApi';

export default function SchedulesPage() {
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [deleteConfirm, setDeleteConfirm] = useState<{ id: number; name: string } | null>(null);
  const { data: schedules, isLoading, error } = useSchedules();
  const toggleMutation = useToggleSchedule();
  const deleteMutation = useDeleteSchedule();

  const handleToggle = (id: number, enabled: boolean) => {
    toggleMutation.mutate({ id, enabled });
  };

  const handleDeleteClick = (id: number) => {
    const schedule = schedules?.find(s => s.id === id);
    if (schedule) {
      setDeleteConfirm({ id, name: schedule.name });
    }
  };

  const handleDeleteConfirm = () => {
    if (deleteConfirm) {
      deleteMutation.mutate(deleteConfirm.id, {
        onSuccess: () => {
          setDeleteConfirm(null);
        },
      });
    }
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
          <span>Add Schedule</span>
        </button>
      </div>

      {!schedules || schedules.length === 0 ? (
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow dark:shadow-gray-900 p-8 text-center">
          <p className="text-gray-600 dark:text-gray-400">No schedules configured yet. Add schedules to automate power control.</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {schedules.map((schedule) => (
            <ScheduleCard
              key={schedule.id}
              schedule={schedule}
              onToggle={handleToggle}
              onDelete={handleDeleteClick}
              isLoading={toggleMutation.isPending}
            />
          ))}
        </div>
      )}

      <CreateScheduleModal 
        isOpen={isModalOpen} 
        onClose={() => setIsModalOpen(false)} 
      />

      <ConfirmDeleteModal
        isOpen={!!deleteConfirm}
        onClose={() => setDeleteConfirm(null)}
        onConfirm={handleDeleteConfirm}
        title="Delete Schedule"
        message="Are you sure you want to delete this schedule?"
        itemName={deleteConfirm?.name}
        isDeleting={deleteMutation.isPending}
      />
    </div>
  );
}
