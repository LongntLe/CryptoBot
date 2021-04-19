import Chart from './Chart';

import './Chart.scss';

const ChartContainer = () => {
	return (
		<div className="chart-container">
			<h2>View your Bitcoin holdings</h2>
			<Chart />
		</div>
	)
}

export default ChartContainer;
