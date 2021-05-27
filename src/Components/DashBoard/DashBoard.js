import { useState } from 'react';
import './DashBoard.scss';

const DashBoard = () => {
	const [profit, setProfit] = useState('');
	const [stopLoss, setStopLoss] = useState('');

	const data = { take_profit: parseFloat(profit), stop_loss: parseFloat(stopLoss) }

	const options = {
		method: 'POST',
		headers: {
			'Content-Type': 'application/json'
		},
		body: JSON.stringify({ data })
	};
	
	const handleFormSubmit = (event) => {
		event.preventDefault();
		fetch('http://localhost:5000/api/formsubmit', options)
		.then(res => console.log(res))
		.catch(error => console.log('Form submit error', error))
	}

	return (
		<div className="dashboard-container">
			<h2>Dash</h2>
			<div className="form-container">
				<form
					className="contact-form"
					onSubmit={ handleFormSubmit }
				>
					<div className="input-container">
						<label
							className="form-label"
							htmlFor="profit"
						>
							Take Profit
							<span className="required-symbol">*</span>
						</label>
						<input
							type="number"
							id="profit"
							className="form-control"
							name="profit"
							placeholder="Your take profit value"
							value={ profit }
							onChange={ event => setProfit( event.target.value ) }
							required
						/>
					</div>
					<div className="input-container">
						<label
							className="form-label"
							htmlFor="stop-loss"
						>
							Stop Loss 
							<span className="required-symbol">*</span>
						</label>
						<input
							type="number"
							id="stop-loss"
							className="form-control"
							name="stop-loss"
							placeholder="Your company name..."
							value={ stopLoss }
							onChange={ event => setStopLoss( event.target.value ) }
							required
						/>
					</div>
					<input type="submit"
						value="Start Bot Trader"
					/>
				</form>
			</div>
		</div>
	)
}

export default DashBoard;
