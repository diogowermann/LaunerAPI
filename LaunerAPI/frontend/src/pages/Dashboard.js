import React from 'react';
import { PieChart, Pie, Cell, ResponsiveContainer, Legend,
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip
} from 'recharts';
import { useSystemStats } from '../hooks/useSystemStats';
import { useTotalData } from '../hooks/useLastHourData';
import { usePerProcessData } from '../hooks/useLastHourData';
import { useServicesData } from '../hooks/useLastHourData';

const Dashboard = () => {
  const [isRealTimeOpen, setIsRealTimeOpen] = React.useState(false);
  const systemStats = useSystemStats(isRealTimeOpen);
  const { totalData } = useTotalData();
  const { cpuData, memoryData } = usePerProcessData();
  const { servicesCpuData, servicesMemoryData } = useServicesData();

  React.useEffect(() => {
    const collapseElement = document.getElementById('realTimeDataCollapse');
    
    const handleShow = () => setIsRealTimeOpen(true);
    const handleHide = () => setIsRealTimeOpen(false);
    
    collapseElement.addEventListener('show.bs.collapse', handleShow);
    collapseElement.addEventListener('hide.bs.collapse', handleHide);
    
    return () => {
      collapseElement.removeEventListener('show.bs.collapse', handleShow);
      collapseElement.removeEventListener('hide.bs.collapse', handleHide);
    };
  }, []);

  const totalDataLastHour = totalData.map(point => ({
    time: point.time,
    cpu: point.cpu,
    memory: point.memory
  }))

  const currentCpuData = [
    { name: 'Em Uso', value: systemStats.cpu.total_usage },
    { name: 'Livre', value: 100 - systemStats.cpu.total_usage }
  ];
  const cpuPerProcessData = systemStats.cpu.top_processes.map(process => ({
    name: process.name,
    value: process.value
  }));

  const currentMemData = [
    { name: 'Em Uso', value: systemStats.mem.total_usage },
    { name: 'Livre', value: 100 - systemStats.mem.total_usage }
  ];
  const memPerProcessData = systemStats.mem.top_processes.map(process => ({
    name: process.name,
    value: process.value
  }));

  const cpuLastHour = systemStats.cpu.last_hourly_avg?.uso ?? 0;
  const cpuLastDay = systemStats.cpu.last_daily_avg?.uso ?? 0;
  const cpuLastWeek = systemStats.cpu.last_weekly_avg?.uso ?? 0;
  const memLastHour = systemStats.mem.last_hourly_avg?.uso ?? 0;
  const memLastDay = systemStats.mem.last_daily_avg?.uso ?? 0;
  const memLastWeek = systemStats.mem.last_weekly_avg?.uso ?? 0;

  const COLORS = ['#08960C', '#525452'];

  // Prepare per-process data for recharts: [{time, proc1: val, proc2: val, ...}]
  const cpuProcessNames = cpuData.length > 0
    ? Object.keys(cpuData[0]).filter(key => key !== 'time')
    : [];
  
  const memoryProcessNames = memoryData.length > 0
    ? Object.keys(memoryData[0]).filter(key => key !== 'time')
    : [];

  const cpuServicesProcessNames = servicesCpuData.length > 0
    ? Object.keys(servicesCpuData[0]).filter(key => key !== 'time')
    : [];
  
  const memoryServicesProcessNames = servicesMemoryData.length > 0
    ? Object.keys(servicesMemoryData[0]).filter(key => key !== 'time')
    : [];

  const CustomLegend = ({payload}) => {
    return (
      <ul style={{listStyleType: 'none', padding: 0}}>
        {payload.map((entry, index) => (
          <li key={`item-${index}`} style={{color: entry.color}}>
            {entry.value}: {entry.payload.value.toFixed(2)}%
          </li>
        ))}
      </ul>
    );
  };
  return (
    <div className='container text-center'>
      
      <div className='container' style={{ marginTop: "25px", marginBottom: "50px"}}>
        <h1>Painel</h1>
      </div>

      <div className='container text-center'>
          <button className='btn btn-info' type='button' data-bs-toggle='collapse' data-bs-target='#realTimeDataCollapse'>
            Mostrar Dados em Tempo Real
          </button>
      </div>

      <div className='containert text-center collapse' id='realTimeDataCollapse'>      
        <div className='row'>
          <div className='col'>
            <h2>Uso do Processador</h2>
            <div style={{ width: '100%', height: 200 }}>
              <ResponsiveContainer>
                <PieChart>
                  <Pie
                    data={currentCpuData}
                    cx="50%"
                    cy="50%"
                    innerRadius={60}
                    outerRadius={80}
                    paddingAngle={5}
                    dataKey="value"
                  >
                    {currentCpuData.map((entry, index) =>
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                    )}
                  </Pie>
                  <Legend />
                  <text x="50%" y="50%" textAnchor="middle" dominantBaseline="middle">
                    {systemStats.cpu.total_usage}%
                  </text>
                </PieChart>
              </ResponsiveContainer>
            </div>
          </div>
          
          <div className='col'>
            <h2>Uso da Memória</h2>
            <div style={{ width: '100%', height: 200, minWidth: '250px', minHeight: '200px' }}>
            <ResponsiveContainer width="100%" height="100%">
            <PieChart>
                  <Pie
                    data={currentMemData}
                    cx="50%"
                    cy="50%"
                    innerRadius={60}
                    outerRadius={80}
                    paddingAngle={5}
                    dataKey="value"
                  >
                    {currentMemData.map((entry, index) =>
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                    )}
                  </Pie>
                  <Legend />
                  <text x="50%" y="50%" textAnchor="middle" dominantBaseline="middle">
                    {systemStats.mem.total_usage}%
                  </text>
                </PieChart>
              </ResponsiveContainer>
            </div>
          </div>
        </div>
        <div className='row'>
          <div className='col'>
            <h2>Uso por Processo</h2>
            <div style={{ width: '100%', height: 400 }}>
              <ResponsiveContainer>
                <PieChart>
                  <Pie
                    data={cpuPerProcessData}
                    cx="50%"
                    cy="50%"
                    innerRadius={60}
                    outerRadius={80}
                    paddingAngle={5}
                    dataKey="value"
                  >
                    {cpuPerProcessData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={`hsl(${(index * 60) % 360}, 70%, 40%)`} />
                    ))}
                  </Pie>
                  <Legend content={<CustomLegend/>} />
                </PieChart>
              </ResponsiveContainer>
            </div>
          </div>
          
          <div className='col'>
            <h2>Uso por Processo</h2>
            <div style={{ width: '100%', height: 400 }}>
              <ResponsiveContainer>
                <PieChart>
                  <Pie
                    data={memPerProcessData}
                    cx="50%"
                    cy="50%"
                    innerRadius={60}
                    outerRadius={80}
                    paddingAngle={5}
                    dataKey="value"
                  >
                    {memPerProcessData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={`hsl(${(index * 60) % 360}, 70%, 40%)`} />
                    ))}
                  </Pie>
                  <Legend content={<CustomLegend/>} />
                </PieChart>
              </ResponsiveContainer>
            </div>
          </div>
        </div>
        <div className='container row'>
          <div className='col'>
            <h5>Última Hora</h5>
            <h3>{cpuLastHour.toFixed(2)}%</h3>
          </div>
          <div className='col'>
            <h5>Último Dia</h5>
            <h3>{cpuLastDay.toFixed(2)}%</h3>
          </div>
          <div className='col'>
            <h5>Última Semana</h5>
            <h3>{cpuLastWeek.toFixed(2)}%</h3>
          </div>
          <div className='col'>
            <h5>Última Hora</h5>
            <h3>{memLastHour.toFixed(2)}%</h3>
          </div>
          <div className='col'>
            <h5>Último Dia</h5>
            <h3>{memLastDay.toFixed(2)}%</h3>
          </div>
          <div className='col'>
            <h5>Última Semana</h5>
            <h3>{memLastWeek.toFixed(2)}%</h3>
          </div>
        </div>
      </div>
      <div className='container mt-5'>
        <div className='container row text-center'>
          <button className='btn btn-primary col' type='button' data-bs-toggle='collapse' data-bs-target='#totalCollapse'  style={{ maxWidth: '28%', margin: 'auto', marginLeft: '5%' }}>
          Registros do <strong>Total</strong> da Última Hora
          </button>
          <button className='btn btn-primary col' type='button' data-bs-toggle='collapse' data-bs-target='#cpuCollapse'  style={{ maxWidth: '28%', margin: 'auto' }}>
          Registros do <strong>CPU</strong> da Última Hora
          </button>
          <button className='btn btn-primary col' type='button' data-bs-toggle='collapse' data-bs-target='#memoryCollapse'  style={{ maxWidth: '28%', margin: 'auto' }}>
          Registros da <strong>Memória</strong> da Última Hora
          </button>
        </div>
        <div className='collapse row' id='totalCollapse'>
          <div className='container text-center'>
            <h2>Registro de Uso da Última Hora</h2>
            <div style={{ width: '100%', height: 300 }}>
              <ResponsiveContainer>
                <LineChart data={totalDataLastHour}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="time" />
                  <YAxis domain={[0, 100]} />
                  <Tooltip />
                  <Legend />
                  <Line 
                    type="monotone" 
                    dataKey="cpu" 
                    name="CPU"
                    stroke="#e35f00" 
                    dot={false} 
                    activeDot={{ r: 4 }} 
                  />
                  <Line 
                    type="monotone" 
                    dataKey="memory" 
                    name="Memória"
                    stroke="#2228bf" 
                    dot={false} 
                    activeDot={{ r: 4 }} 
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </div>
        </div>
        <div className='collapse row' id='cpuCollapse'>
          <div className='container text-center col' style={{ height: 300 }}>
            <h2>Registros Gerais</h2>
            <ResponsiveContainer>
              <LineChart data={cpuData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="time" />
                <YAxis domain={[0, 100]} />
                <Tooltip />
                <Legend />
                {cpuProcessNames.map((name, idx) => (
                  <Line
                    key={name}
                    type="monotone"
                    dataKey={name}
                    name={name}
                    stroke={`hsl(${(idx * 60) % 360}, 70%, 40%)`}
                    dot={false}
                    activeDot={{ r: 4 }}
                  />
                ))}
              </LineChart>
            </ResponsiveContainer>
          </div>
          <div className='container text-center col' style={{ height: '300px' }}>
            <h2>Serviços do Protheus</h2>
            <ResponsiveContainer>
              <LineChart data={servicesCpuData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="time" />
                <YAxis domain={[0, 100]} />
                <Tooltip />
                <Legend />
                {cpuServicesProcessNames.map((name, idx) => (
                  <Line
                    key={name}
                    type="monotone"
                    dataKey={name}
                    name={name}
                    stroke={`hsl(${(idx * 60) % 360}, 70%, 40%)`}
                    dot={false}
                    activeDot={{ r: 4 }}
                  />
                ))}
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>
        <div className='collapse row' id='memoryCollapse'>
          <div className='container text-center col' style={{ height: '300px' }}>
            <h3>Registros Gerais</h3>
            <ResponsiveContainer>
              <LineChart data={memoryData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="time" />
                <YAxis domain={[0, 100]} />
                <Tooltip />
                <Legend />
                {memoryProcessNames.map((name, idx) => (
                  <Line
                    key={name}
                    type="monotone"
                    dataKey={name}
                    name={name}
                    stroke={`hsl(${(idx * 60) % 360}, 70%, 40%)`}
                    dot={false}
                    activeDot={{ r: 4 }}
                  />
                ))}
              </LineChart>
              </ResponsiveContainer>
          </div>
          <div className='container text-center col' style={{ height: '300px' }}>
            <ResponsiveContainer>
              <h3>Serviços do Protheus</h3>
              <LineChart data={servicesMemoryData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="time" />
                <YAxis domain={[0, 100]} />
                <Tooltip />
                <Legend />
                {memoryServicesProcessNames.map((name, idx) => (
                  <Line
                    key={name}
                    type="monotone"
                    dataKey={name}
                    name={name}
                    stroke={`hsl(${(idx * 60) % 360}, 70%, 40%)`}
                    dot={false}
                    activeDot={{ r: 4 }}
                  />
                ))}
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>
    </div>
  );
}

export default Dashboard;