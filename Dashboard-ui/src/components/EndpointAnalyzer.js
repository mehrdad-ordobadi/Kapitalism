import React, { useEffect, useState } from 'react'
import '../App.css';
import config from '../config';

export default function EndpointAnalyzer(props) {
    const [isLoaded, setIsLoaded] = useState(false);
    const [log, setLog] = useState(null);
    const [error, setError] = useState(null);
    const [index, setIndex] = useState(null);  // New state for tracking the index

    const getAnalyzer = () => {
        const rand_val = Math.floor(Math.random() * 100); // Move random value generation inside getAnalyzer
        
        fetch(config.endpoints.analyzer(props.endpoint, rand_val))
            .then(res => res.json())
            .then((result)=>{
                console.log("Received Analyzer Results for " + props.endpoint)
                setLog(result);
                setIndex(rand_val);  // Set the index that corresponds to this data
                setIsLoaded(true);
            },(error) =>{
                setError(error)
                setIsLoaded(true);
            })
    }

    useEffect(() => {
        const interval = setInterval(() => getAnalyzer(), 4000); // Update every 4 seconds
        return() => clearInterval(interval);
    }, []); // Remove getAnalyzer from dependencies since it's defined within component

    if (error){
        return (<div className={"error"}>Error found when fetching from API</div>)
    } else if (isLoaded === false){
        return(<div>Loading...</div>)
    } else if (isLoaded === true){
        return (
            <div>
                <h3>{props.endpoint}-{index}</h3>
                {JSON.stringify(log)}
            </div>
        )
    }
}