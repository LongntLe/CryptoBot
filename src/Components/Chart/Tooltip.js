export function Tooltip(){
	return(
		<div id="tooltip" className="tooltip">
			<div className="tooltip-range">
				<span id="value"></span>
			</div>
			<div className="tooltip-timestamp">
				<span id="timestamp"></span>
			</div>
		</div>
	)
}