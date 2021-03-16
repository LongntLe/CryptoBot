import ReactDOM from 'react-dom';

import './App.scss';

import Chart from './Components/Chart/Chart';
import DashBoard from './Components/DashBoard/DashBoard';

const App = () => {
	return(
		<div className="app-container">
			<h1 className="app-header">BitMex Trading Bot</h1>
			<Chart />
			<DashBoard />
		</div>
	)
};

ReactDOM.render(
	<App />,
	document.getElementById("root")
);
