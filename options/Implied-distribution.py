import pandas as pd
import numpy as np 
import matplotlib.pyplot as plt 
import yfinance as yf 
from scipy.interpolate import make_smoothing_spline

# Get options data from yfinance
ticker = yf.Ticker("SPY")  # Replace with your desired ticker

# Get available expiration dates
expiration_dates = ticker.options

# Get options chain for a specific expiration date
opt_chain = ticker.option_chain(expiration_dates[0])

# Access calls and puts separately
calls = opt_chain.calls
puts = opt_chain.puts

cv = calls['impliedVolatility']
K  = calls['strike']
plt.plot(K,cv)

ss = make_smoothing_spline(K,cv)

# Now i can use the cov formula to back out the implied distribution
# Need to get the derivative of ss
derivative_ss = ss.derivative(nu= 2) #(this is just the function)
deriv_at_K = derivative_ss(K)