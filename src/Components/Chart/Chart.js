import { useEffect, useState } from 'react';
import { Tooltip } from './Tooltip';
import * as d3 from 'd3';

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

	// Example Timestamp - 2021-04-18T05:31:00.894Z
	// More Info on D3 time conversion: https://github.com/d3/d3-time-format
	const dateParser = d3.utcParse('%Y-%m-%dT%H:%M:%S.%LZ');
	const formatDate = d3.timeFormat('%B %d, %Y');

	const buildChart = (financialMetric, timeMetric) => {
		let dimensions = {
			width: window.innerWidth * 0.9,
			height: 600,
			margins: {
				top: 15,
				right: 15,
				bottom: 105,
				left: 90
			}
		};

		dimensions.boundedWidth = dimensions.width
			- dimensions.margins.left
			- dimensions.margins.right;

		dimensions.boundedHeight = dimensions.height
			- dimensions.margins.top
			- dimensions.margins.bottom;

		const chartContainer = d3.select('#charts')
			.append('svg')
				.attr('class', 'chart')
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
			const date = data[timeMetric];
			return dateParser(date);
		};

		// x Scale
		const xDomain = d3.extent(chartData, xAccessor);
		const xScale = d3.scaleTime()
			.domain(xDomain)
			.range([0, dimensions.boundedWidth]);

		const lineGenerator = d3.line()
			.x(data => xScale(xAccessor(data)))
			.y(data => yScale(yAccessor(data)));

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
			.attr('y', -dimensions.margins.left + 12)
			.style('transform', 'rotate(-90deg)')
			.style('text-anchor', 'middle')
			.attr('fill', '#000')
			.style('font-size', '1.4em')
			.text(yLabel);

		// Y Grid
		const yAxisGridGenerator = d3.axisLeft(yScale)
			.tickSize(-dimensions.boundedWidth)
			.tickFormat('')
			.ticks(12);

		const yAxisGrid = yAxis.append('g')
			.call(yAxisGridGenerator)
			.attr('class', 'y axis-grid');

		const xAxisGenerator = d3.axisBottom()
			.scale(xScale)
			.tickFormat(formatDate);

		const xAxis = bounds.append('g')
			.call(xAxisGenerator)
			.style('transform', `translateY(${
				dimensions.boundedHeight
			}px)`);

		xAxis.selectAll('text')
			.attr('y', 0)
			.attr('x', 12)
			.attr('dy', '0.3em')
			.attr('transform', 'rotate(90)')
			.style('text-anchor', 'start');

		// X Axis Label
		const xAxisLabel = xAxis.append('text')
			.attr('x', dimensions.boundedWidth / 2)
			.attr('y', dimensions.margins.bottom - 12)
			.attr('fill', '#000')
			.style('font-size', '1.4em')
			.text('Time Stamp');

		// X Grid
		const xAxisGridGenerator = d3.axisBottom(xScale)
			.tickSize(-dimensions.boundedHeight)
			.tickFormat('')
			.ticks(12);

		const xAxisGrid = xAxis.append('g')
			.call(xAxisGridGenerator)
			.attr('class', 'x axis-grid');

		const line = bounds.append('path')
			.data(chartData)
			.attr('d', lineGenerator(chartData))
			.attr('fill', 'none')
			.style('stroke', '#141CDE')
			.style('stroke-width', '0.5px');

		const listenerRect = bounds.append('rect')
			.attr('class', 'listener-rect')
			.attr('width', dimensions.boundedWidth)
			.attr('height', dimensions.boundedHeight)
			.on('mousemove', handleMouseMove)
			.on('mouseleave', handleMouseLeave);

		const tooltip = d3.select('#tooltip');

		const tooltipCircle = bounds.append('circle')
			.attr('class', 'tooltip-circle')
			.attr('r', 4.5);

		const bisectDate = d3.bisector(function(dataPoint){
			if (dataPoint && dataPoint.timestamp) return new Date(dataPoint.timestamp);
		}).left;

		function handleMouseMove(event){
			const mousePosition = d3.pointer(event);
			const hoveredPoint = new Date(xScale.invert(mousePosition[0]));
			const currentIndex = bisectDate(chartData, hoveredPoint, 1);
			const prevPoint = chartData[currentIndex - 1];
			const currentPoint = chartData[currentIndex];
			const closestDataPoint = hoveredPoint - prevPoint.timestamp > currentPoint.timestamp - hoveredPoint ? currentPoint : prevPoint;

			tooltip.style('opacity', 1);
			tooltip.select('#value')
				.html(`<span class="bold-text">${ yLabel }</span>: ${ closestDataPoint.unrealisedPnl }`);
			tooltip.select('#timestamp')
				.text(closestDataPoint.timestamp);

			const x = xScale(xAccessor(closestDataPoint) - dimensions.margins.left);
			const y = yScale(yAccessor(closestDataPoint) + dimensions.margins.top);
			tooltip.style('transform', `translate(
				${ x }px,
				${ y }px
			)`);

			tooltipCircle
				.attr('cx', x)
				.attr('cy', yScale(closestDataPoint.unrealisedPnl))
				.style('opacity', 1);
		}

		function handleMouseLeave(){
			tooltip.style('opacity', 0);
			tooltipCircle.style('opacity', 0);
		}
	}

	useEffect(() => {
		if (chartData.length > 0) {
			buildChart('unrealisedPnl', 'timestamp');
			buildChart('amount', 'timestamp');
		}
	}, [chartData]);

	return (
		<div id="chart">
			<h2>Your Crypto Assets</h2>

			<Tooltip />
		</div>
	)
}

export default Chart;
