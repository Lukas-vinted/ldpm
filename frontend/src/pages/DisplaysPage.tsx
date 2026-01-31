import { Plus } from 'lucide-react';
import { DisplayCard } from '../components';
import { useDisplays, usePowerControl } from '../hooks/useApi';

export default function DisplaysPage() {
  const { data: displays, isLoading, error } = useDisplays();
  const powerMutation = usePowerControl();

  const handlePowerToggle = (id: number, state: 'on' | 'off') => {
    powerMutation.mutate({ id, state });
  };

  if (isLoading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="text-gray-500">Loading displays...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-4">
        <p className="text-red-800">Failed to load displays. Please try again.</p>
      </div>
    );
  }

  return (
    <div>
      <div className="flex justify-between items-center mb-6">
        <h2 className="text-2xl font-bold text-gray-900">Displays</h2>
        <button className="flex items-center space-x-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors">
          <Plus className="w-5 h-5" />
          <span>Add Display</span>
        </button>
      </div>

      {!displays || displays.length === 0 ? (
        <div className="bg-white rounded-lg shadow p-8 text-center">
          <p className="text-gray-600">No displays configured yet. Add displays to get started.</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {displays.map((display) => (
            <DisplayCard
              key={display.id}
              display={display}
              onPowerToggle={handlePowerToggle}
              isLoading={powerMutation.isPending}
            />
          ))}
        </div>
      )}
    </div>
  );
}
