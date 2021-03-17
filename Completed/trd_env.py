import gym
from gym import spaces
import pandas as pd
import numpy as np
import random
class trading_env(gym.Env):
    """Single Stock Trading Environment"""
    def __init__(self,df, init_capital=10000):
        #instance attributes
        self.df = df
        self.initial_capital = init_capital
        self.current_step = None
        #Porfolio Information
        self.no_stocks_bought = None
        self.no_stocks_sold = None
        self.portfolio_value = None
        self.current_stocks_held = None
        self.current_capital = None
        self.avg_cost = None
        self.returns = None
        self.max_steps = None
    
        #Values for normalising data
        self.max_stock_price = max(self.df["Close"])
        self.max_volume = max(self.df["Volume_(BTC)"])
        self.max_capital = 1000000
        self.max_no_shares = 10000
    
    
        #state/observation space
        self.action_space = spaces.Box(low=np.array([0,0]),high=np.array([3,1]),dtype=np.float16)
        #Consider Volumne, Close, Return, MACD,RSI, EMA, Porfolio(current_capital,portfolio_value,returns, no_stocks_owned,avg_cost,no_stocks_sold )
        self.observation_space = spaces.Box(low=0.0,high= 1.0,shape=(7,6))
    
    
    def observation(self):
        #-6 the predefined lookback window 
#         env_observations = np.array([self.df.loc[self.current_step-5:self.current_step,"Close"].values/self.max_stock_price,
#                                     self.df.loc[self.current_step-5:self.current_step,"Volume_(BTC)"].values/self.max_volume,
#                                     self.df.loc[self.current_step-5:self.current_step,"MACD_status"].values,
#                                     self.df.loc[self.current_step-5:self.current_step,"RSI_status"].values,
#                                     self.df.loc[self.current_step-5:self.current_step,"EMA_status"].values,
#                                     self.df.loc[self.current_step-5:self.current_step,"3D_return_norm"].values]
#                                    ) #Not required for Q-learning, only using 2 variables, combined_indicators & return_norm
        
#         obs = np.append(env_observations,[[
#             self.current_capital/self.max_capital,
#             self.portfolio_value/self.max_capital,
#             self.returns/self.initial_capital, # not sure how to normalise returns since it can be a negative value
#             self.no_stocks_bought/self.max_no_shares,
#             self.no_stocks_sold/self.max_no_shares,
#             self.avg_cost/self.max_stock_price
#         ]],axis = 0)
        obs = np.array([self.df.loc[self.current_step,"3D_return_norm"], self.df.loc[self.current_step,"MACD_status"],self.df.loc[self.current_step,"RSI_status"],self.df.loc[self.current_step,"EMA_status"]])
        
        return obs
    
    def step(self,a):
        self.action(a)
        self.current_step += 1
        
        if self.current_step > len(self.df.loc[:,"Open"].values) + 6:
            self.current_step = 0 # Sanity check ensuring that current step isn't greater than 6 steps ahead
        
        delay = self.current_step/self.max_steps
        
        reward = self.returns * delay
        
        if self.current_step == len(self.df):
            self.done = True
        elif self.portfolio_value == 0:
            self.done = True
        
        obs = self.observation()
        
        return obs,reward, self.done
        
    def action(self,a):
        self.amount = 0
        current_price = random.uniform(self.df.loc[self.current_step,"Open"],self.df.loc[self.current_step,"Close"])
        #Buy at the low and sell high
        if self.df.loc[self.current_step,"3D_return"] < -0.19:
            self.amount = random.uniform(0.3,0.5)
        elif (self.df.loc[self.current_step,"3D_return"] > -0.19) & (self.df.loc[self.current_step,"3D_return"]<-0.02):
            self.amount = random.uniform(0.1,0.3)
        elif self.df.loc[self.current_step,"3D_return"] > 0.3:
            self.amount = random.uniform(0.3,0.5)
        elif (self.df.loc[self.current_step,"3D_return"] >0.1) & (self.df.loc[self.current_step,"3D_return"]<0.3):
            self.amount = random.uniform(0.1,0.3)
        
        
        action_taken = a

        
        if action_taken == 2: # Buy
            total_possible = self.current_capital/current_price
            amount_stocks_bought = total_possible * self.amount
            current_cost = amount_stocks_bought * current_price
            prior_cost = self.avg_cost * self.no_stocks_bought 
            
            self.no_stocks_bought += amount_stocks_bought
            self.current_stocks_held += amount_stocks_bought
            self.avg_cost = (prior_cost+current_cost)/self.no_stocks_bought
            self.current_capital -= current_cost
            
        elif action_taken == 0: #Sell
            shares_sell = self.current_stocks_held * self.amount
            profit = shares_sell * current_price
            
            self.no_stocks_sold += shares_sell
            self.current_stocks_held -= shares_sell
            self.current_capital += profit
            self.returns = profit - (shares_sell * self.avg_cost)
            
            
        elif action_taken == 1:
            None
            
        if self.current_capital > self.max_capital:
            self.max_capital = self.current_capital
        if self.current_stocks_held <= 0:
            self.avg_cost == 0 
            
    def reset(self):
        self.no_stocks_bought = 0
        self.no_stocks_sold = 0
        self.current_stocks_held = 0
        self.portfolio_value = self.initial_capital
        self.current_capital = self.initial_capital
        self.avg_cost = 0
        self.returns = 0 
        self.max_steps = 10000
        self.current_step = 0
        self.done = False
        
        return self.observation()
        
    def render(self):
        current_price = random.uniform(self.df.loc[self.current_step, "Open"],self.df.loc[self.current_step,"Close"])
        self.portfolio_value = self.current_capital + (self.current_stocks_held*current_price)
        
        print(f"Current Porfolio Value:{self.portfolio_value}; Available Capital: {self.current_capital}; Current Stocks Held: {self.current_stocks_held}")
        print(f"No. Stocks Bought:{self.no_stocks_bought}; No. Stocks Sold:{self.no_stocks_sold}; Average Cost:{self.avg_cost} ")
        print(f"Return:{self.portfolio_value - self.initial_capital}")
        print(f"{self.current_step}")