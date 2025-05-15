import { useState, useEffect } from 'react';
import api from '../services/api';

export const useSystemStats = (isRealTimeOpen) => {
  const [systemStats, setSystemStats] = useState({ 
    cpu: {total_usage: 0, top_processes: [], last_hourly_avg: null, last_daily_avg: null, last_weekly_avg: null},
    mem: {total_usage: 0, top_processes: [], last_hourly_avg: null, last_daily_avg: null, last_weekly_avg: null}
  });

  useEffect(() => {
    const fetchData = async () => {
      try {
        const response = await api.get('/current-usages');
        setSystemStats({
          cpu: {
            total_usage: response.data.cpu_values.total_usage,
            top_processes: response.data.cpu_values.top_processes.map(proc => ({
              name: proc.name,
              value: proc.cpu_percent
            })),
            last_hourly_avg: response.data.cpu_values.last_hourly_avg,
            last_daily_avg: response.data.cpu_values.last_daily_avg,
            last_weekly_avg: response.data.cpu_values.last_weekly_avg
          },
          mem: {
            total_usage: response.data.mem_values.total_usage,
            top_processes: response.data.mem_values.top_processes.map(proc => ({
              name: proc.name,
              value: proc.memory_percent
            })),
            last_hourly_avg: response.data.mem_values.last_hourly_avg,
            last_daily_avg: response.data.mem_values.last_daily_avg,
            last_weekly_avg: response.data.mem_values.last_weekly_avg
          }
        });
        console.log('System stats:', {
            cpu: response.data.cpu_values,
            mem: response.data.mem_values
          });
      } catch (error) {
        console.error('Error fetching system stats:', error);
      }
    };

    let interval;
    if (isRealTimeOpen) {
      fetchData();
      interval = setInterval(fetchData, 2500);
    }
    return () => interval && clearInterval(interval);
  }, [isRealTimeOpen]);

  return systemStats;
};