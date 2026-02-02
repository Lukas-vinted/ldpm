import { useState, useEffect } from 'react';
import { Modal } from './Modal';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { Loader2 } from 'lucide-react';

interface EnergyChartModalProps {
  isOpen: boolean;
  onClose: () => void;
  metric: 'energy' | 'cost' | 'time' | 'co2';
  days?: number;
}

interface ChartDataPoint {
  date: string;
  value: number;
}

const metricConfig = {
  energy: {
    title: 'Energy Saved Over Time',
    unit: 'kWh',
    color: '#10b981',
    gradientFrom: '#10b981',
    gradientTo: '#14b8a6',
  },
  cost: {
    title: 'Cost Savings Over Time',
    unit: '€',
    color: '#f59e0b',
    gradientFrom: '#f59e0b',
    gradientTo: '#f97316',
  },
  time: {
    title: 'Time Off Over Time',
    unit: 'hrs',
    color: '#3b82f6',
    gradientTo: '#6366f1',
    gradientFrom: '#3b82f6',
  },
  co2: {
    title: 'CO₂ Reduction Over Time',
    unit: 'kg',
    color: '#10b981',
    gradientFrom: '#22c55e',
    gradientTo: '#10b981',
  },
};

export const EnergyChartModal: React.FC<EnergyChartModalProps> = ({
  isOpen,
  onClose,
  metric,
  days = 30,
}) => {
  const [data, setData] = useState<ChartDataPoint[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const config = metricConfig[metric];

  useEffect(() => {
    if (!isOpen) return;

    const fetchData = async () => {
      setIsLoading(true);
      try {
        const auth = localStorage.getItem('auth');
        const response = await fetch(
          `http://localhost:8000/api/v1/energy/history?days=${days}&metric=${metric}`,
          {
            headers: {
              Authorization: `Basic ${auth}`,
            },
          }
        );

        if (response.ok) {
          const result = await response.json();
          setData(result.data || []);
        }
      } catch (error) {
        console.error('Failed to fetch energy history:', error);
      } finally {
        setIsLoading(false);
      }
    };

    fetchData();
  }, [isOpen, metric, days]);

  const formatDate = (dateStr: string) => {
    const date = new Date(dateStr);
    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
  };

  return (
    <Modal isOpen={isOpen} onClose={onClose} title={config.title}>
      <div className="h-96">
        {isLoading ? (
          <div className="flex items-center justify-center h-full">
            <Loader2 className="w-8 h-8 text-emerald-500 animate-spin" />
          </div>
        ) : data.length === 0 ? (
          <div className="flex items-center justify-center h-full text-gray-400">
            <p>No data available for this period</p>
          </div>
        ) : (
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={data} margin={{ top: 20, right: 30, left: 0, bottom: 20 }}>
              <defs>
                <linearGradient id={`gradient-${metric}`} x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor={config.gradientFrom} stopOpacity={0.8} />
                  <stop offset="100%" stopColor={config.gradientTo} stopOpacity={0.1} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="#374151" opacity={0.3} />
              <XAxis
                dataKey="date"
                tickFormatter={formatDate}
                stroke="#9ca3af"
                style={{ fontSize: '12px' }}
              />
              <YAxis
                stroke="#9ca3af"
                style={{ fontSize: '12px' }}
                label={{ value: config.unit, angle: -90, position: 'insideLeft', fill: '#9ca3af' }}
              />
              <Tooltip
                contentStyle={{
                  backgroundColor: '#1f2937',
                  border: '1px solid #374151',
                  borderRadius: '8px',
                  color: '#fff',
                }}
                labelFormatter={(label) => formatDate(label as string)}
                formatter={(value: number | undefined) => 
                  value !== undefined ? [`${value.toFixed(2)} ${config.unit}`, config.title] : ['', '']
                }
              />
              <Line
                type="monotone"
                dataKey="value"
                stroke={config.color}
                strokeWidth={3}
                fill={`url(#gradient-${metric})`}
                dot={{ fill: config.color, strokeWidth: 2, r: 4 }}
                activeDot={{ r: 6, fill: config.color }}
              />
            </LineChart>
          </ResponsiveContainer>
        )}
      </div>
      <div className="mt-6 pt-4 border-t border-gray-700">
        <p className="text-sm text-gray-400 text-center">
          Showing data for the last {days} days
        </p>
      </div>
    </Modal>
  );
};
