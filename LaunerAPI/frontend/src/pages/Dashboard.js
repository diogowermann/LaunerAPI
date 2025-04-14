import React from 'react';
import api from '../services/api';

const Dashboard = () => {
  const [systemStats, setSystemStats] = React.useState({ 
    cpu: {total_cpu_usage : 0, top_processes: [], last_hourly: null, last_daily: null, last_weekly: null },
    memory: {total_memory_usage : 0, top_processes: [], last_hourly: null, last_daily: null, last_weekly: null }
  });

  React.useEffect(() => {
    const fetchData = async () => {
      try {
        const [cpuResponse, memoryResponse] = await Promise.all([
          api.get('/cpu-usage'),
          api.get('/memory-usage')
        ]);
        
        setSystemStats({cpu: cpuResponse.data, memory: memoryResponse.data});
      } catch (error) {
        console.error('Error fetching system stats:', error);
      }
    };

    const interval = setInterval(fetchData, 3000);
    return () => clearInterval(interval);
  }, []);
  
  return (
    <div>
      <h1>Dashboard</h1>
      <p>Welcome to the dashboard!</p>
      <h2>CPU Usage</h2>
      <p>{systemStats.cpu.total_cpu_usage}%</p>
      <h3>Top Processes</h3>
      <ul>
        {systemStats.cpu.top_processes.map((process, index) => (
          <li key={process.pid}>
            {index + 1}. {process.name} (PID: {process.pid}) - {process.cpu_percent.toFixed(2)}%
          </li>
        ))}
      </ul>
      <h3>Last Hourly Usage</h3>
      <p>{systemStats.cpu.last_hourly ? systemStats.cpu.last_hourly.toFixed(2) : 'No data available'}</p>
      <h3>Last Daily Usage</h3>
      <p>{systemStats.cpu.last_daily ? systemStats.cpu.last_daily.toFixed(2) : 'No data available'}</p>
      <h3>Last Weekly Usage</h3>
      <p>{systemStats.cpu.last_weekly ? systemStats.cpu.last_weekly.toFixed(2) : 'No data available'}</p>
      <h2>Memory Usage</h2>
      <p>{systemStats.memory.total_memory_usage}%</p>
      <h3>Top Processes</h3>
      <ul>
        {systemStats.memory.top_processes.map((process, index) => (
          <li key={process.pid}>
            {index + 1}. {process.name} (PID: {process.pid}) - {process.memory_percent.toFixed(2)}%
          </li>
        ))}
      </ul>
      <h3>Last Hourly Usage</h3>
      <p>{systemStats.memory.last_hourly ? systemStats.memory.last_hourly.toFixed(2) : 'No data available'}</p>
      <h3>Last Daily Usage</h3>
      <p>{systemStats.memory.last_daily ? systemStats.memory.last_daily.toFixed(2) : 'No data available'}</p>
      <h3>Last Weekly Usage</h3>
      <p>{systemStats.memory.last_weekly ? systemStats.memory.last_weekly.toFixed(2) : 'No data available'}</p>
    </div>
  );
}

export default Dashboard;