import React, { useState } from 'react';
import { Monitor, Loader2 } from 'lucide-react';
import { Modal } from './Modal';
import { useCreateDisplay } from '../hooks/useApi';

interface AddDisplayModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export const AddDisplayModal: React.FC<AddDisplayModalProps> = ({ isOpen, onClose }) => {
  const createMutation = useCreateDisplay();
  const [formData, setFormData] = useState({
    name: '',
    ip_address: '',
    psk: '',
    location: '',
    tags: '',
  });
  const [errors, setErrors] = useState<Record<string, string>>({});

  const validateIP = (ip: string): boolean => {
    const ipPattern = /^(\d{1,3}\.){3}\d{1,3}$/;
    if (!ipPattern.test(ip)) return false;
    const parts = ip.split('.');
    return parts.every(part => parseInt(part) >= 0 && parseInt(part) <= 255);
  };

  const validate = (): boolean => {
    const newErrors: Record<string, string> = {};

    if (!formData.name.trim()) {
      newErrors.name = 'Display name is required';
    }

    if (!formData.ip_address.trim()) {
      newErrors.ip_address = 'IP address is required';
    } else if (!validateIP(formData.ip_address)) {
      newErrors.ip_address = 'Invalid IP address format';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!validate()) return;

    const payload = {
      name: formData.name.trim(),
      ip_address: formData.ip_address.trim(),
      psk: formData.psk.trim() || null,
      location: formData.location.trim() || '',
      tags: formData.tags.trim() 
        ? formData.tags.split(',').reduce((acc, tag) => {
            const trimmed = tag.trim();
            if (trimmed) acc[trimmed] = true;
            return acc;
          }, {} as Record<string, any>)
        : {},
      status: 'unknown' as const,
    };

    createMutation.mutate(payload, {
      onSuccess: () => {
        setFormData({ name: '', ip_address: '', psk: '', location: '', tags: '' });
        setErrors({});
        onClose();
      },
    });
  };

  const handleClose = () => {
    setFormData({ name: '', ip_address: '', psk: '', location: '', tags: '' });
    setErrors({});
    createMutation.reset();
    onClose();
  };

  return (
    <Modal isOpen={isOpen} onClose={handleClose} title="Add Display">
      <form onSubmit={handleSubmit} className="space-y-4">
        {/* Name */}
        <div>
          <label htmlFor="name" className="block text-sm font-medium text-slate-300 mb-1">
            Display Name <span className="text-red-400">*</span>
          </label>
          <input
            type="text"
            id="name"
            value={formData.name}
            onChange={(e) => setFormData({ ...formData, name: e.target.value })}
            className="w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded-lg text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            placeholder="Conference Room TV"
          />
          {errors.name && <p className="mt-1 text-sm text-red-400">{errors.name}</p>}
        </div>

        {/* IP Address */}
        <div>
          <label htmlFor="ip_address" className="block text-sm font-medium text-slate-300 mb-1">
            IP Address <span className="text-red-400">*</span>
          </label>
          <input
            type="text"
            id="ip_address"
            value={formData.ip_address}
            onChange={(e) => setFormData({ ...formData, ip_address: e.target.value })}
            className="w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded-lg text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            placeholder="192.168.1.100"
          />
          {errors.ip_address && <p className="mt-1 text-sm text-red-400">{errors.ip_address}</p>}
        </div>

        {/* PSK */}
        <div>
          <label htmlFor="psk" className="block text-sm font-medium text-slate-300 mb-1">
            Pre-Shared Key <span className="text-slate-500">(optional)</span>
          </label>
          <input
            type="password"
            id="psk"
            value={formData.psk}
            onChange={(e) => setFormData({ ...formData, psk: e.target.value })}
            className="w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded-lg text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            placeholder="0000"
          />
          {errors.psk && <p className="mt-1 text-sm text-red-400">{errors.psk}</p>}
          <p className="mt-1 text-xs text-slate-400">Leave empty for Simple IP Control (no authentication)</p>
        </div>

        {/* Location */}
        <div>
          <label htmlFor="location" className="block text-sm font-medium text-slate-300 mb-1">
            Location <span className="text-slate-500">(optional)</span>
          </label>
          <input
            type="text"
            id="location"
            value={formData.location}
            onChange={(e) => setFormData({ ...formData, location: e.target.value })}
            className="w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded-lg text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            placeholder="Building A, Floor 2"
          />
        </div>

        {/* Tags */}
        <div>
          <label htmlFor="tags" className="block text-sm font-medium text-slate-300 mb-1">
            Tags <span className="text-slate-500">(optional)</span>
          </label>
          <input
            type="text"
            id="tags"
            value={formData.tags}
            onChange={(e) => setFormData({ ...formData, tags: e.target.value })}
            className="w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded-lg text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            placeholder="meeting-room, main-display"
          />
          <p className="mt-1 text-xs text-slate-400">Comma-separated tags</p>
        </div>

        {/* Error Message */}
        {createMutation.isError && (
          <div className="p-3 bg-red-900/20 border border-red-500/50 rounded-lg">
            <p className="text-sm text-red-400">
              Failed to add display. Please try again.
            </p>
          </div>
        )}

        {/* Success Message */}
        {createMutation.isSuccess && (
          <div className="p-3 bg-green-900/20 border border-green-500/50 rounded-lg">
            <p className="text-sm text-green-400">
              Display added successfully!
            </p>
          </div>
        )}

        {/* Buttons */}
        <div className="flex space-x-3 pt-4">
          <button
            type="button"
            onClick={handleClose}
            disabled={createMutation.isPending}
            className="flex-1 px-4 py-2 bg-slate-700 text-white rounded-lg hover:bg-slate-600 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            Cancel
          </button>
          <button
            type="submit"
            disabled={createMutation.isPending}
            className="flex-1 px-4 py-2 bg-gradient-to-r from-blue-600 to-purple-600 text-white rounded-lg hover:from-blue-700 hover:to-purple-700 transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center space-x-2"
          >
            {createMutation.isPending ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                <span>Adding...</span>
              </>
            ) : (
              <>
                <Monitor className="w-4 h-4" />
                <span>Add Display</span>
              </>
            )}
          </button>
        </div>
      </form>
    </Modal>
  );
};
