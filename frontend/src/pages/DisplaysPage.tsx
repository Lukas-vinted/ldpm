import { useState } from 'react';
import { Plus, Upload } from 'lucide-react';
import { DisplayCard } from '../components';
import { AddDisplayModal } from '../components/AddDisplayModal';
import { ImportCSVModal } from '../components/ImportCSVModal';
import { ConfirmDeleteModal } from '../components/ConfirmDeleteModal';
import { useDisplays, usePowerControl, useDeleteDisplay } from '../hooks/useApi';

export default function DisplaysPage() {
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [isImportModalOpen, setIsImportModalOpen] = useState(false);
  const [deleteConfirm, setDeleteConfirm] = useState<{ id: number; name: string } | null>(null);
  const { data: displays, isLoading, error } = useDisplays();
  const powerMutation = usePowerControl();
  const deleteMutation = useDeleteDisplay();

  const handlePowerToggle = (id: number, state: 'on' | 'off') => {
    powerMutation.mutate({ id, state });
  };

  const handleDeleteClick = (id: number) => {
    const display = displays?.find(d => d.id === id);
    if (display) {
      setDeleteConfirm({ id, name: display.name });
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
        <div className="text-gray-500 dark:text-gray-400">Loading displays...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 dark:bg-red-950 border border-red-200 dark:border-red-800 rounded-lg p-4">
        <p className="text-red-800 dark:text-red-300">Failed to load displays. Please try again.</p>
      </div>
    );
  }

  return (
    <div>
      <div className="flex justify-between items-center mb-6">
        <h2 className="text-2xl font-bold text-gray-900 dark:text-white">Displays</h2>
        <div className="flex space-x-3">
          <button 
            onClick={() => setIsImportModalOpen(true)}
            className="flex items-center space-x-2 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors"
          >
            <Upload className="w-5 h-5" />
            <span>Import CSV</span>
          </button>
          <button 
            onClick={() => setIsModalOpen(true)}
            className="flex items-center space-x-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
          >
            <Plus className="w-5 h-5" />
            <span>Add Display</span>
          </button>
        </div>
      </div>

      {!displays || displays.length === 0 ? (
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow dark:shadow-gray-900 p-8 text-center">
          <p className="text-gray-600 dark:text-gray-400">No displays configured yet. Add displays to get started.</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {displays.map((display) => (
            <DisplayCard
              key={display.id}
              display={display}
              onPowerToggle={handlePowerToggle}
              onDelete={handleDeleteClick}
              isLoading={powerMutation.isPending}
            />
          ))}
        </div>
      )}

      <AddDisplayModal 
        isOpen={isModalOpen} 
        onClose={() => setIsModalOpen(false)} 
      />

      <ImportCSVModal 
        isOpen={isImportModalOpen} 
        onClose={() => setIsImportModalOpen(false)} 
      />

      <ConfirmDeleteModal
        isOpen={!!deleteConfirm}
        onClose={() => setDeleteConfirm(null)}
        onConfirm={handleDeleteConfirm}
        title="Delete Display"
        message="Are you sure you want to delete this display?"
        itemName={deleteConfirm?.name}
        isDeleting={deleteMutation.isPending}
      />
    </div>
  );
}
