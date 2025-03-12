import React, { useEffect, useState } from 'react'
import '../App.css';
import config from '../config';

export default function AnomalyDisplay() {
    const [isLoaded, setIsLoaded] = useState(false);
    const [anomalies, setAnomalies] = useState({});
    const [error, setError] = useState(null);
    const [currentTime, setCurrentTime] = useState(new Date().toLocaleString());

    const getAnomalies = () => {
        const types = ['PriceTooHigh', 'StockTooLow'];
        const promises = types.map(type => 
            fetch(config.endpoints.anomalies(type))
                .then(res => res.json())
                .then(data => ({ type, data }))
        );

        Promise.all(promises)
            .then(results => {
                const anomalyData = {};
                results.forEach(({ type, data }) => {
                    anomalyData[type] = data.length > 0 ? data[0] : null;
                });
                setAnomalies(anomalyData);
                setIsLoaded(true);
                setCurrentTime(new Date().toLocaleString());
            })
            .catch(error => {
                setError(error);
                setIsLoaded(true);
            });
    };

    useEffect(() => {
        const interval = setInterval(() => getAnomalies(), 2000);
        return() => clearInterval(interval);
    }, []);

    if (error){
        return (<div className={"error"}>Error found when fetching from API</div>)
    } else if (isLoaded === false){
        return(<div>Loading...</div>)
    } else if (isLoaded === true){
        return(
            <div className="anomaly-display">
                <h1>Latest Anomalies</h1>
                
                <div className="anomaly-section">
                    <p><strong>Price Latest Anomaly UUID</strong>:</p>
                    {anomalies.PriceTooHigh ? (
                        <>
                            <p>{anomalies.PriceTooHigh.event_id}</p>
                            <p>{anomalies.PriceTooHigh.description}</p>
                            <p>Detected on {anomalies.PriceTooHigh.timestamp}</p>
                        </>
                    ) : (
                        <p>No price anomalies detected</p>
                    )}
                </div>

                <div className="anomaly-section">
                    <p><strong>Stock Latest Anomaly UUID</strong>:</p>
                    {anomalies.StockTooLow ? (
                        <>
                            <p>{anomalies.StockTooLow.event_id}</p>
                            <p>{anomalies.StockTooLow.description}</p>
                            <p>Detected on {anomalies.StockTooLow.timestamp}</p>
                        </>
                    ) : (
                        <p>No stock anomalies detected</p>
                    )}
                </div>

                <h3>Last Updated: {currentTime}</h3>
            </div>
        )
    }
}