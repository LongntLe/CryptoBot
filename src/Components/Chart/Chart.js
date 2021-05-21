import { useEffect, useState } from 'react';
import * as d3 from 'd3';
import './Chart.scss';

const Chart = () => {
	const [chartData, setChartData] = useState([]);

	const fetchChartData = () => {
		fetch('http://localhost:5000/api/crypto')
		.then(res => res.json())
		.then(cryptoData => {
			setChartData(cryptoData);
		});
	}

	useEffect(() => {
		fetchChartData();
	}, []);

	const buildChart = (financialMetric, timeMetric) => {
		let dimensions = {
			width: window.innerWidth * 0.9,
			height: 600,
			margins: {
				top: 15,
				right: 15,
				bottom: 45,
				left: 90
			}
		};

		dimensions.boundedWidth = dimensions.width
			- dimensions.margins.left
			- dimensions.margins.right;

		dimensions.boundedHeight = dimensions.height
			- dimensions.margins.top
			- dimensions.margins.bottom;

		const chartContainer = d3.select('#chart')
			.append('svg')
				.attr('width', dimensions.width)
				.attr('height', dimensions.height);

		const bounds = chartContainer.append('g')
			.style('transform', `translate(${
				dimensions.margins.left
			}px, ${
				dimensions.margins.top
			}px
			)`);

		// y Axis
		let yAccessor = data => data[financialMetric];
		let yDomain = d3.extent(chartData, yAccessor);

		if (financialMetric === 'amount'){
			yAccessor = data => (data[financialMetric] / 100000000);
			yDomain = d3.extent(chartData, yAccessor);
		}

		// y Scale
		const yScale = d3.scaleLinear()
			.domain(yDomain)
			.range([dimensions.boundedHeight, 0])
			.nice();

		// x Axis - format date from Mongo timestamp to JS timestamp
		const xAccessor = data => {
			const jsTimeStamp = parseInt(data[timeMetric].toString().substr(0,8), 16) * 1000;
			return jsTimeStamp;
		};
		// x Scale
		const xDomain = d3.extent(chartData, xAccessor);
		const xScale = d3.scaleTime()
			.domain(xDomain)
			.range([0, dimensions.boundedWidth])
			.nice();

		const lineGenerator = d3.line()
			.x(data => xScale(xAccessor(data)))
			.y(data => yScale(yAccessor(data)));

		const line = bounds.append('path')
			.attr('d', lineGenerator(chartData))
			.attr('fill', 'none')
			.attr('stroke', '#141CDE')

		// Draw Axes
		const yAxisGenerator = d3.axisLeft()
			.scale(yScale)
			.tickFormat(d3.format(9));

		const yAxis = bounds.append('g')
			.call(yAxisGenerator);
		// TODO: Make robust enough to handle any asset
		let yLabel = (financialMetric === 'amount') ? 'XBT in your account' : 'Unrealized PnL (XBT/1e8)';
		// Y Axis Label
		const yAxisLabel = yAxis.append('text')
			.attr('x', -dimensions.boundedHeight / 2)
			.attr('y', -dimensions.margins.left + 10)
			.style('transform', 'rotate(-90deg)')
			.style('text-anchor', 'middle')
			.attr('fill', '#000')
			.style('font-size', '1.4em')
			.text(yLabel);

		const xAxisGenerator = d3.axisBottom()
			.scale(xScale)

		const xAxis = bounds.append('g')
			.call(xAxisGenerator)
			.style('transform', `translateY(${
				dimensions.boundedHeight
			}px)`);

		// X Axis Label
		const xAxisLabel = xAxis.append('text')
			.attr('x', dimensions.boundedWidth / 2)
			.attr('y', dimensions.margins.bottom - 9)
			.attr('fill', '#000')
			.style('font-size', '1.4em')
			.text('Time Stamp');
	}

	useEffect(() => {
		if (chartData.length > 0) {
			buildChart('unrealisedPnl', 'timestamp');
			buildChart('amount', 'timestamp');
		}
	}, [chartData]);

	return (
		<div id="chart">

		</div>
	)
}

export default Chart;
