import { useState } from 'react';
import { Plus } from 'lucide-react';
import { GroupCard } from '../components';
import { CreateGroupModal } from '../components/CreateGroupModal';
import { ConfirmDeleteModal } from '../components/ConfirmDeleteModal';
import { ManageGroupDisplaysModal } from '../components/ManageGroupDisplaysModal';
import { useGroups, useDeleteGroup } from '../hooks/useApi';
import { Group } from '../types';

export default function GroupsPage() {
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [deleteConfirm, setDeleteConfirm] = useState<{ id: number; name: string } | null>(null);
  const [manageGroup, setManageGroup] = useState<Group | null>(null);
  const { data: groups, isLoading, error } = useGroups();
  const deleteMutation = useDeleteGroup();

  const handleDeleteClick = (id: number) => {
    const group = groups?.find(g => g.id === id);
    if (group) {
      setDeleteConfirm({ id, name: group.name });
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

  const handleManageClick = (id: number) => {
    const group = groups?.find(g => g.id === id);
    if (group) {
      setManageGroup(group);
    }
  };

  if (isLoading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="text-gray-500 dark:text-gray-400">Loading groups...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 dark:bg-red-950 border border-red-200 dark:border-red-800 rounded-lg p-4">
        <p className="text-red-800 dark:text-red-300">Failed to load groups. Please try again.</p>
      </div>
    );
  }

  return (
    <div>
      <div className="flex justify-between items-center mb-6">
        <h2 className="text-2xl font-bold text-gray-900 dark:text-white">Groups</h2>
        <button 
          onClick={() => setIsModalOpen(true)}
          className="flex items-center space-x-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
        >
          <Plus className="w-5 h-5" />
          <span>Create Group</span>
        </button>
      </div>

      {!groups || groups.length === 0 ? (
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow dark:shadow-gray-900 p-8 text-center">
          <p className="text-gray-600 dark:text-gray-400">No groups created yet. Create groups to manage multiple displays.</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {groups.map((group) => (
            <GroupCard 
              key={group.id} 
              group={group}
              onDelete={handleDeleteClick}
              onManage={handleManageClick}
            />
          ))}
        </div>
      )}

      <CreateGroupModal 
        isOpen={isModalOpen} 
        onClose={() => setIsModalOpen(false)} 
      />

      <ConfirmDeleteModal
        isOpen={!!deleteConfirm}
        onClose={() => setDeleteConfirm(null)}
        onConfirm={handleDeleteConfirm}
        title="Delete Group"
        message="Are you sure you want to delete this group? This will not delete the displays in the group."
        itemName={deleteConfirm?.name}
        isDeleting={deleteMutation.isPending}
      />

      <ManageGroupDisplaysModal
        isOpen={!!manageGroup}
        onClose={() => setManageGroup(null)}
        group={manageGroup}
        currentDisplayIds={manageGroup?.display_ids || []}
      />
    </div>
  );
}
