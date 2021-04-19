import ReactDOM from 'react-dom';

import './App.scss';

import ChartContainer from './Components/Chart/ChartContainer';
import DashBoard from './Components/DashBoard/DashBoard';
import { TeamMembers } from './Components/TeamMembers/TeamMembers';

const App = () => {
	return(
		<div className="app-container">
			<h1 className="app-header">BitMex Trading Bot</h1>
			<ChartContainer />
			<DashBoard />
			<TeamMembers />
		</div>
	)
};

ReactDOM.render(
	<App />,
	document.getElementById("root")
);
