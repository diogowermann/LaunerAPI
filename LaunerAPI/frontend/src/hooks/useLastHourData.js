import { useState, useEffect } from 'react';
import api from '../services/api';

export const useTotalData = () => {
    const [totalData, setTotalData] = useState([]);

    useEffect(() => {
        const fetchData = async () => {
            try {
                const response = await api.get('/last-60-minutes');
                const total = response.data.total_data;

                setTotalData(total);
            } catch (error) {
                console.error('Error fetching hourly data:', error);
            }
        };

        fetchData();
        const interval = setInterval(fetchData, 60000);

        return () => clearInterval(interval);
    }, []);

    return {
        totalData
    };
};

export const useServicesData =() => {
    const [servicesCpuData, setServicesCpuData] = useState([]);;
    const [servicesMemoryData, setServicesMemoryData] = useState([]);
    
    useEffect(() => {
        const fetchData = async () => {
            try {
                const response = await api.get('/last-60-minutes-services');
                const cpu = response.data.cpu
                const memory = response.data.memory
                console.log(cpu);

                const cpuServicesForChart = cpu.map(([time, obj]) => ({ time, ...obj}));
                const memoryServicesForChart = memory.map(([time, obj]) => ({ time, ...obj}));
                setServicesCpuData(cpuServicesForChart);
                setServicesMemoryData(memoryServicesForChart);
            } catch (error) {
                console.error('Error fetching per process data:', error);
            }
        };

        fetchData();
        const interval = setInterval(fetchData, 60000);

        return () => clearInterval(interval);
    }, []);

    return {
        servicesCpuData,
        servicesMemoryData
    };
}

export const usePerProcessData = () => {
    const [cpuData, setCpuData] = useState([]);
    const [memoryData, setMemoryData] = useState([]);

    useEffect(() => {
        const fetchData = async () => {
            try {
                const response = await api.get('/last-60-minutes');
                const cpu = response.data.cpu_data
                const memory = response.data.memory_data

                const cpuForChart = cpu.map(([time, obj]) => ({ time, ...obj}));
                const memoryForChart = memory.map(([time, obj]) => ({ time, ...obj}));
                setCpuData(cpuForChart);
                setMemoryData(memoryForChart);
            } catch (error) {
                console.error('Error fetching per process data:', error);
            }
        };

        fetchData();
        const interval = setInterval(fetchData, 60000);

        return () => clearInterval(interval);
    }, []);

    return {
        cpuData,
        memoryData
    };
};