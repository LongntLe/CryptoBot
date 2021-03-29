import ReactDOM from 'react-dom';

import './App.scss';

import Chart from './Components/Chart/Chart';
import DashBoard from './Components/DashBoard/DashBoard';
import { TeamMembers } from './Components/TeamMembers/TeamMembers';

const App = () => {
	return(
		<div className="app-container">
			<h1 className="app-header">BitMex Trading Bot</h1>
			<Chart />
			<DashBoard />
			<TeamMembers />
		</div>
	)
};

ReactDOM.render(
	<App />,
	document.getElementById("root")
);
