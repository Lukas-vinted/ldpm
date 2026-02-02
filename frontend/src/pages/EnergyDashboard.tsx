import { useState, useMemo } from 'react';
import { Leaf, Euro, Clock, TreePine, Calendar, Zap } from 'lucide-react';

interface DisplaySavings {
  display_id: number;
  display_name: string;
  total_hours_off: number;
  energy_saved_kwh: number;
  cost_saved_eur: number;
  co2_reduced_kg: number;
}

interface EnergySavingsData {
  total_hours_off: number;
  energy_saved_kwh: number;
  cost_saved_eur: number;
  co2_reduced_kg: number;
  start_date: string | null;
  end_date: string | null;
  displays: DisplaySavings[];
}

type DateRange = 'today' | 'week' | 'month' | 'custom' | 'all';

function EnergyDashboard() {
  const [dateRange, setDateRange] = useState<DateRange>('all');
  const [customStartDate, setCustomStartDate] = useState('');
  const [customEndDate, setCustomEndDate] = useState('');
  const [energyData, setEnergyData] = useState<EnergySavingsData | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  // Calculate date range based on selection
  const { startDate, endDate } = useMemo(() => {
    const now = new Date();
    const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());
    
    switch (dateRange) {
      case 'today':
        return {
          startDate: today.toISOString().split('T')[0],
          endDate: now.toISOString().split('T')[0]
        };
      case 'week':
        const weekAgo = new Date(today);
        weekAgo.setDate(weekAgo.getDate() - 7);
        return {
          startDate: weekAgo.toISOString().split('T')[0],
          endDate: now.toISOString().split('T')[0]
        };
      case 'month':
        const monthAgo = new Date(today);
        monthAgo.setMonth(monthAgo.getMonth() - 1);
        return {
          startDate: monthAgo.toISOString().split('T')[0],
          endDate: now.toISOString().split('T')[0]
        };
      case 'custom':
        return {
          startDate: customStartDate,
          endDate: customEndDate
        };
      case 'all':
      default:
        return { startDate: '', endDate: '' };
    }
  }, [dateRange, customStartDate, customEndDate]);

  // Fetch energy savings data
  const fetchEnergySavings = async () => {
    setIsLoading(true);
    try {
      const params = new URLSearchParams();
      if (startDate) params.append('start_date', startDate);
      if (endDate) params.append('end_date', endDate);

      const auth = localStorage.getItem('auth');
      const response = await fetch(`http://localhost:8000/api/v1/energy/savings?${params}`, {
        headers: {
          'Authorization': `Basic ${auth}`
        }
      });

      if (response.ok) {
        const data = await response.json();
        setEnergyData(data);
      }
    } catch (error) {
      console.error('Failed to fetch energy savings:', error);
    } finally {
      setIsLoading(false);
    }
  };

  // Auto-fetch when date range changes (except custom until dates are entered)
  useState(() => {
    if (dateRange !== 'custom' || (customStartDate && customEndDate)) {
      fetchEnergySavings();
    }
  });

  return (
    <div className="min-h-screen bg-gradient-to-br from-emerald-50 via-teal-50 to-cyan-50 dark:from-gray-950 dark:via-emerald-950 dark:to-teal-950 px-6 py-8">
      {/* Header */}
      <div className="max-w-7xl mx-auto mb-12">
        <div className="flex items-center gap-4 mb-3">
          <div className="w-16 h-16 bg-gradient-to-br from-emerald-500 to-teal-600 rounded-2xl flex items-center justify-center shadow-lg shadow-emerald-500/20">
            <Zap className="w-8 h-8 text-white" />
          </div>
          <div>
            <h1 className="text-5xl font-black text-transparent bg-clip-text bg-gradient-to-r from-emerald-600 via-teal-600 to-cyan-600 dark:from-emerald-400 dark:via-teal-400 dark:to-cyan-400">
              Energy Savings
            </h1>
            <p className="text-lg text-gray-600 dark:text-gray-400 mt-1">
              Track your environmental impact and cost savings
            </p>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto">
        {/* Date Range Selector */}
        <div className="bg-white/80 dark:bg-gray-900/80 backdrop-blur-xl rounded-3xl shadow-2xl border border-emerald-100 dark:border-emerald-900/30 p-8 mb-8">
          <div className="flex items-center gap-3 mb-6">
            <Calendar className="w-6 h-6 text-emerald-600 dark:text-emerald-400" />
            <h2 className="text-2xl font-bold text-gray-900 dark:text-white">Time Period</h2>
          </div>

          <div className="flex flex-wrap gap-3 mb-6">
            {(['today', 'week', 'month', 'all', 'custom'] as DateRange[]).map((range) => (
              <button
                key={range}
                onClick={() => setDateRange(range)}
                className={`px-6 py-3 rounded-xl font-semibold transition-all duration-200 ${
                  dateRange === range
                    ? 'bg-gradient-to-r from-emerald-500 to-teal-600 text-white shadow-lg shadow-emerald-500/30 scale-105'
                    : 'bg-gray-100 dark:bg-gray-800 text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-700'
                }`}
              >
                {range === 'today' && 'Today'}
                {range === 'week' && 'This Week'}
                {range === 'month' && 'This Month'}
                {range === 'all' && 'All Time'}
                {range === 'custom' && 'Custom Range'}
              </button>
            ))}
          </div>

          {dateRange === 'custom' && (
            <div className="flex gap-4 items-end">
              <div className="flex-1">
                <label className="block text-sm font-semibold text-gray-700 dark:text-gray-300 mb-2">
                  Start Date
                </label>
                <input
                  type="date"
                  value={customStartDate}
                  onChange={(e) => setCustomStartDate(e.target.value)}
                  className="w-full px-4 py-3 rounded-xl border-2 border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:border-emerald-500 focus:ring-2 focus:ring-emerald-500/20 transition-all"
                />
              </div>
              <div className="flex-1">
                <label className="block text-sm font-semibold text-gray-700 dark:text-gray-300 mb-2">
                  End Date
                </label>
                <input
                  type="date"
                  value={customEndDate}
                  onChange={(e) => setCustomEndDate(e.target.value)}
                  className="w-full px-4 py-3 rounded-xl border-2 border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:border-emerald-500 focus:ring-2 focus:ring-emerald-500/20 transition-all"
                />
              </div>
              <button
                onClick={fetchEnergySavings}
                disabled={!customStartDate || !customEndDate}
                className="px-8 py-3 bg-gradient-to-r from-emerald-500 to-teal-600 text-white font-semibold rounded-xl shadow-lg shadow-emerald-500/30 hover:shadow-xl hover:scale-105 transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:scale-100"
              >
                Apply
              </button>
            </div>
          )}
        </div>

        {/* Loading State */}
        {isLoading && (
          <div className="flex items-center justify-center py-24">
            <div className="w-16 h-16 border-4 border-emerald-200 dark:border-emerald-800 border-t-emerald-600 dark:border-t-emerald-400 rounded-full animate-spin"></div>
          </div>
        )}

        {/* Energy Savings Cards */}
        {!isLoading && energyData && (
          <>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
              {/* Energy Saved Card */}
              <div className="group bg-gradient-to-br from-emerald-500 to-teal-600 rounded-3xl p-8 shadow-2xl shadow-emerald-500/20 hover:shadow-emerald-500/40 hover:scale-105 transition-all duration-300">
                <div className="flex items-center justify-between mb-6">
                  <div className="w-14 h-14 bg-white/20 backdrop-blur-sm rounded-2xl flex items-center justify-center group-hover:scale-110 transition-transform duration-300">
                    <Leaf className="w-7 h-7 text-white" />
                  </div>
                  <div className="text-right">
                    <p className="text-emerald-100 text-sm font-semibold uppercase tracking-wider">Energy Saved</p>
                  </div>
                </div>
                <div className="flex items-baseline gap-2">
                  <span className="text-5xl font-black text-white">{energyData.energy_saved_kwh.toFixed(1)}</span>
                  <span className="text-2xl font-bold text-emerald-100">kWh</span>
                </div>
                <div className="mt-4 pt-4 border-t border-white/20">
                  <p className="text-emerald-50 text-sm">
                    Equivalent to {Math.round(energyData.total_hours_off)} hours off-time
                  </p>
                </div>
              </div>

              {/* Money Saved Card */}
              <div className="group bg-gradient-to-br from-amber-500 to-orange-600 rounded-3xl p-8 shadow-2xl shadow-amber-500/20 hover:shadow-amber-500/40 hover:scale-105 transition-all duration-300">
                <div className="flex items-center justify-between mb-6">
                  <div className="w-14 h-14 bg-white/20 backdrop-blur-sm rounded-2xl flex items-center justify-center group-hover:scale-110 transition-transform duration-300">
                    <Euro className="w-7 h-7 text-white" />
                  </div>
                  <div className="text-right">
                    <p className="text-amber-100 text-sm font-semibold uppercase tracking-wider">Cost Saved</p>
                  </div>
                </div>
                <div className="flex items-baseline gap-2">
                  <span className="text-5xl font-black text-white">€{energyData.cost_saved_eur.toFixed(2)}</span>
                  <span className="text-2xl font-bold text-amber-100">EUR</span>
                </div>
                <div className="mt-4 pt-4 border-t border-white/20">
                  <p className="text-amber-50 text-sm">
                    Based on €0.12 per kWh rate
                  </p>
                </div>
              </div>

              {/* Hours Off Card */}
              <div className="group bg-gradient-to-br from-blue-500 to-indigo-600 rounded-3xl p-8 shadow-2xl shadow-blue-500/20 hover:shadow-blue-500/40 hover:scale-105 transition-all duration-300">
                <div className="flex items-center justify-between mb-6">
                  <div className="w-14 h-14 bg-white/20 backdrop-blur-sm rounded-2xl flex items-center justify-center group-hover:scale-110 transition-transform duration-300">
                    <Clock className="w-7 h-7 text-white" />
                  </div>
                  <div className="text-right">
                    <p className="text-blue-100 text-sm font-semibold uppercase tracking-wider">Time Off</p>
                  </div>
                </div>
                <div className="flex items-baseline gap-2">
                  <span className="text-5xl font-black text-white">{Math.round(energyData.total_hours_off)}</span>
                  <span className="text-2xl font-bold text-blue-100">hrs</span>
                </div>
                <div className="mt-4 pt-4 border-t border-white/20">
                  <p className="text-blue-50 text-sm">
                    {Math.round(energyData.total_hours_off / 24)} days total off-time
                  </p>
                </div>
              </div>

              {/* CO2 Reduced Card */}
              <div className="group bg-gradient-to-br from-green-500 to-emerald-600 rounded-3xl p-8 shadow-2xl shadow-green-500/20 hover:shadow-green-500/40 hover:scale-105 transition-all duration-300">
                <div className="flex items-center justify-between mb-6">
                  <div className="w-14 h-14 bg-white/20 backdrop-blur-sm rounded-2xl flex items-center justify-center group-hover:scale-110 transition-transform duration-300">
                    <TreePine className="w-7 h-7 text-white" />
                  </div>
                  <div className="text-right">
                    <p className="text-green-100 text-sm font-semibold uppercase tracking-wider">CO₂ Reduced</p>
                  </div>
                </div>
                <div className="flex items-baseline gap-2">
                  <span className="text-5xl font-black text-white">{energyData.co2_reduced_kg.toFixed(1)}</span>
                  <span className="text-2xl font-bold text-green-100">kg</span>
                </div>
                <div className="mt-4 pt-4 border-t border-white/20">
                  <p className="text-green-50 text-sm">
                    Carbon footprint reduction
                  </p>
                </div>
              </div>
            </div>

            {/* Display Breakdown */}
            {energyData.displays.length > 0 && (
              <div className="bg-white/80 dark:bg-gray-900/80 backdrop-blur-xl rounded-3xl shadow-2xl border border-emerald-100 dark:border-emerald-900/30 p-8">
                <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-6">Savings by Display</h2>
                <div className="space-y-4">
                  {energyData.displays.map((display) => (
                    <div
                      key={display.display_id}
                      className="flex items-center justify-between p-6 bg-gradient-to-r from-gray-50 to-emerald-50 dark:from-gray-800 dark:to-emerald-950/20 rounded-2xl border border-gray-200 dark:border-gray-700 hover:border-emerald-300 dark:hover:border-emerald-700 transition-all duration-200"
                    >
                      <div className="flex-1">
                        <h3 className="text-lg font-bold text-gray-900 dark:text-white">{display.display_name}</h3>
                        <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
                          {Math.round(display.total_hours_off)} hours off-time
                        </p>
                      </div>
                      <div className="flex gap-8 text-right">
                        <div>
                          <p className="text-2xl font-bold text-emerald-600 dark:text-emerald-400">
                            {display.energy_saved_kwh.toFixed(1)} kWh
                          </p>
                          <p className="text-xs text-gray-500 dark:text-gray-500 mt-1">Energy</p>
                        </div>
                        <div>
                          <p className="text-2xl font-bold text-amber-600 dark:text-amber-400">
                            €{display.cost_saved_eur.toFixed(2)}
                          </p>
                          <p className="text-xs text-gray-500 dark:text-gray-500 mt-1">Savings</p>
                        </div>
                        <div>
                          <p className="text-2xl font-bold text-green-600 dark:text-green-400">
                            {display.co2_reduced_kg.toFixed(1)} kg
                          </p>
                          <p className="text-xs text-gray-500 dark:text-gray-500 mt-1">CO₂</p>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* No Data State */}
            {energyData.displays.length === 0 && (
              <div className="bg-white/80 dark:bg-gray-900/80 backdrop-blur-xl rounded-3xl shadow-2xl border border-gray-200 dark:border-gray-700 p-12 text-center">
                <Leaf className="w-16 h-16 text-gray-400 dark:text-gray-600 mx-auto mb-4" />
                <h3 className="text-xl font-bold text-gray-700 dark:text-gray-300 mb-2">No Power Logs Found</h3>
                <p className="text-gray-600 dark:text-gray-400">
                  There are no power control events recorded for the selected time period.
                </p>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
}

export default EnergyDashboard;
