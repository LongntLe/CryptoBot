import ReactDOM from 'react-dom';

import './sass/app.scss';

import { Landing } from './Components/Landing';
import ChartContainer from './Components/Chart/ChartContainer';
import DashBoard from './Components/DashBoard/DashBoard';
import { TeamMembers } from './Components/TeamMembers/TeamMembers';

const App = () => {
	return(
		<div className="app-container">
			<Landing />
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
