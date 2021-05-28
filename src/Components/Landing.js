import cryptoImage from '../static/img/crypto_moon.png';

export function Landing(){
	return(
		<div className="landing-container">
			<header>
				<h1 className="app-header">BitMex Trading Bot</h1>
				<h2>The Next Generation of Crypto Trading & Charting</h2>
				<h3>Advanced Trading Algorithm that makes you money*</h3>
				<div className="tooltip">
					Not financial advice 😉😏
				</div>
			</header>

			<img 
				className="crypto-img"
				src={ cryptoImage }
				alt="Crypto is Headed to the Moon"
			/>

			<h2>Join us on our journey to the moon!</h2>

			<a href="#chart" className="arrow-btn">
				<i className="fas fa-arrow-circle-down arrow-down"></i>
			</a>
		</div>
	)
}