import React, { useEffect, useState } from 'react';

import './TeamMembers.scss';

export function TeamMembers(){
	const [teamMembers, setTeamMembers] = useState([]);

	const fetchTeamData = () => {
		fetch('http://localhost:5000/api/teammembers')
		.then(res => res.json())
		.then(teamMembers => {
			setTeamMembers(teamMembers);
		});
	}

	useEffect(() => {
		fetchTeamData();
	}, []);

	return (
		<div className="team-members-container">
			<h2>Team Members</h2>
			<ul>Built By:
				{
					teamMembers.map( ( teammember ) => 
						<li 
							className="team-member"
							key={ teammember.id }
						>
							{ teammember.name } - { teammember.contribution }
						</li>
					)
				}
			</ul>
		</div>
	);
}