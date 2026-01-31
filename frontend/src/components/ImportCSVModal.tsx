import React, { useState, useRef } from 'react';
import { Upload, Download, FileText, CheckCircle, XCircle, Loader2 } from 'lucide-react';
import { Modal } from './Modal';
import { useImportCSV } from '../hooks/useApi';

interface ImportCSVModalProps {
  isOpen: boolean;
  onClose: () => void;
}

interface ImportResult {
  created_count: number;
  updated_count: number;
  failed_count: number;
  total_processed: number;
  failed_rows?: Array<{
    row_number: number;
    data: Record<string, string>;
    error: string;
  }>;
}

export const ImportCSVModal: React.FC<ImportCSVModalProps> = ({ isOpen, onClose }) => {
  const importMutation = useImportCSV();
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [result, setResult] = useState<ImportResult | null>(null);

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      setSelectedFile(file);
      setResult(null);
      importMutation.reset();
    }
  };

  const handleImport = async () => {
    if (!selectedFile) return;

    importMutation.mutate(selectedFile, {
      onSuccess: (data: ImportResult) => {
        setResult(data);
        setSelectedFile(null);
        if (fileInputRef.current) {
          fileInputRef.current.value = '';
        }
      },
    });
  };

  const downloadTemplate = () => {
    const csv = 'ip_address,name,location\n192.168.1.100,Conference Room TV,Building A Floor 2\n192.168.1.101,Lobby Display,Main Entrance';
    const blob = new Blob([csv], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'displays_template.csv';
    a.click();
    URL.revokeObjectURL(url);
  };

  const handleClose = () => {
    setSelectedFile(null);
    setResult(null);
    importMutation.reset();
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
    onClose();
  };

  return (
    <Modal isOpen={isOpen} onClose={handleClose} title="Import Displays from CSV">
      <div className="space-y-4">
        <div className="bg-blue-900/20 border border-blue-500/50 rounded-lg p-3">
          <p className="text-sm text-blue-300 mb-2">
            <strong>CSV Format:</strong> ip_address, name, location
          </p>
          <p className="text-xs text-blue-400">
            • Existing displays (same IP) will be updated<br />
            • New IPs will be added as new displays
          </p>
        </div>

        <div>
          <button
            type="button"
            onClick={downloadTemplate}
            className="flex items-center space-x-2 text-sm text-blue-400 hover:text-blue-300 transition-colors"
          >
            <Download className="w-4 h-4" />
            <span>Download CSV Template</span>
          </button>
        </div>

        <div>
          <label className="block text-sm font-medium text-slate-300 mb-2">
            Select CSV File
          </label>
          <div className="flex items-center space-x-3">
            <input
              ref={fileInputRef}
              type="file"
              accept=".csv"
              onChange={handleFileSelect}
              className="hidden"
              id="csv-upload"
            />
            <label
              htmlFor="csv-upload"
              className="flex-1 px-4 py-2 bg-slate-900 border border-slate-700 rounded-lg text-slate-400 cursor-pointer hover:border-slate-600 transition-colors flex items-center space-x-2"
            >
              <FileText className="w-4 h-4" />
              <span className="text-sm">
                {selectedFile ? selectedFile.name : 'Choose file...'}
              </span>
            </label>
          </div>
        </div>

        {result && (
          <div className="space-y-3">
            <div className="bg-slate-900 border border-slate-700 rounded-lg p-4 space-y-2">
              <div className="flex items-center justify-between text-sm">
                <span className="text-slate-400">Total Processed:</span>
                <span className="text-white font-semibold">{result.total_processed}</span>
              </div>
              {result.created_count > 0 && (
                <div className="flex items-center justify-between text-sm">
                  <span className="text-green-400 flex items-center space-x-1">
                    <CheckCircle className="w-4 h-4" />
                    <span>Created:</span>
                  </span>
                  <span className="text-green-400 font-semibold">{result.created_count}</span>
                </div>
              )}
              {result.updated_count > 0 && (
                <div className="flex items-center justify-between text-sm">
                  <span className="text-blue-400 flex items-center space-x-1">
                    <CheckCircle className="w-4 h-4" />
                    <span>Updated:</span>
                  </span>
                  <span className="text-blue-400 font-semibold">{result.updated_count}</span>
                </div>
              )}
              {result.failed_count > 0 && (
                <div className="flex items-center justify-between text-sm">
                  <span className="text-red-400 flex items-center space-x-1">
                    <XCircle className="w-4 h-4" />
                    <span>Failed:</span>
                  </span>
                  <span className="text-red-400 font-semibold">{result.failed_count}</span>
                </div>
              )}
            </div>

            {result.failed_rows && result.failed_rows.length > 0 && (
              <div className="bg-red-900/20 border border-red-500/50 rounded-lg p-3 max-h-48 overflow-y-auto">
                <p className="text-sm text-red-400 font-medium mb-2">Failed Rows:</p>
                <div className="space-y-2">
                  {result.failed_rows.map((row, idx) => (
                    <div key={idx} className="text-xs text-red-300">
                      <span className="font-semibold">Row {row.row_number}:</span> {row.error}
                      <div className="text-red-400 ml-2">
                        {JSON.stringify(row.data)}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}

        {importMutation.isError && (
          <div className="p-3 bg-red-900/20 border border-red-500/50 rounded-lg">
            <p className="text-sm text-red-400">
              Failed to import CSV. Please check the file format and try again.
            </p>
          </div>
        )}

        <div className="flex space-x-3 pt-4">
          <button
            type="button"
            onClick={handleClose}
            disabled={importMutation.isPending}
            className="flex-1 px-4 py-2 bg-slate-700 text-white rounded-lg hover:bg-slate-600 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {result ? 'Close' : 'Cancel'}
          </button>
          <button
            type="button"
            onClick={handleImport}
            disabled={!selectedFile || importMutation.isPending}
            className="flex-1 px-4 py-2 bg-gradient-to-r from-blue-600 to-purple-600 text-white rounded-lg hover:from-blue-700 hover:to-purple-700 transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center space-x-2"
          >
            {importMutation.isPending ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                <span>Importing...</span>
              </>
            ) : (
              <>
                <Upload className="w-4 h-4" />
                <span>Import</span>
              </>
            )}
          </button>
        </div>
      </div>
    </Modal>
  );
};
