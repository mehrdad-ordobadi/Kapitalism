import React, { useEffect, useState } from 'react'
import '../App.css';

export default function AppStats() {
    const [isLoaded, setIsLoaded] = useState(false);
    const [stats, setStats] = useState({});
    const [error, setError] = useState(null);
    const [currentTime, setCurrentTime] = useState(new Date().toLocaleString());
     // eslint-disable-next-line
    useEffect(() => {
        const getStats = () => {
            fetch(`/processing/stats`)
                .then(res => res.json())
                .then((result)=>{
                    console.log("Received Stats")
                    setStats(result);
                    setIsLoaded(true);
                    setCurrentTime(new Date().toLocaleString());
                },(error) =>{
                    setError(error)
                    setIsLoaded(true);
                })
        }

        const interval = setInterval(() => getStats(), 2000);
        return() => clearInterval(interval);
    }, []);

    if (error){
        return (<div className={"error"}>Error found when fetching from API</div>)
    } else if (isLoaded === false){
        return(<div>Loading...</div>)
    } else if (isLoaded === true){
        return(
            <div>
                <h1>Latest Stats</h1>
                <table className={"StatsTable"}>
					<tbody>
						<tr>
							<th>Number of Products</th>
							<th>Number of Reviews</th>
						</tr>
						<tr>
							<td># Products: {stats['num_products']}</td>
							<td># Reviews: {stats['num_reviews']}</td>
						</tr>
						<tr>
							<td colspan="2">Most Expensive Product: {stats['max_product_price']}</td>
						</tr>
						<tr>
							<td colspan="2">Top Rated Product: {stats['top_avg_review_rating']}</td>
						</tr>
					</tbody>
                </table>
                <h3>Last Updated: {currentTime}</h3>

            </div>
        )
    }
}
