from fc import *
import csv,pulp
import pandas as pd
from gurobipy import *
import matplotlib.pyplot as plt
########################################################################################
########################################################################################
'IMPORT DATA'

df=pd.read_csv('profiles.csv')
df=df.round(decimals=3)
orig_Q_DHW = df['DHW'].tolist()

tank_volume=150

q_loss = (14.33 + 7.13 * (tank_volume) ** 0.4) / ((65 - 20) * 1000)  # kW/K	

resolution=5 			#minutes
simulation_duration= 7	#days
total_duration=int(1440/resolution *simulation_duration)
step_size=int(1440/resolution)
opti_size=int(step_size*1.5)
# initializing LP

Q_DHW=[]
for i in range(len(orig_Q_DHW)):
	Q_DHW.append(sum(orig_Q_DHW[i:i+resolution])/resolution)

P_max=1

s_T=[]
s_P=[]
r_T=[40.05]
r_P=[0]

for i in range(int(total_duration/step_size)):

	if i==0:
		_Q_DHW_fc=forecast(Q_DHW[total_duration:int(total_duration+step_size*1.5)],int(step_size*1.5))
	else:
		_Q_DHW_fc=forecast(Q_DHW[i*step_size:int((i+1.5)*step_size)],int(step_size*1.5))

	Q_DHW_fc=Q_DHW[:i*step_size]+_Q_DHW_fc

	LP = pulp.LpProblem('LP',pulp.LpMinimize)  
	T_tank = pulp.LpVariable.dicts("T_tank", range(opti_size), cat=pulp.LpContinuous, lowBound=40, upBound=85)
	P_waterheater = pulp.LpVariable.dicts("P_waterheater", range(opti_size), cat=pulp.LpContinuous, upBound=P_max, lowBound=0)

	for t in range(opti_size):

		if t==0:
			LP += T_tank[t] == r_T[-1]
			#LP += P_waterheater[t] == r_P[-1]
		else:
			LP += T_tank[t] == T_tank[t-1] + (P_waterheater[t]-Q_DHW_fc[t]-(T_tank[t-1]-23)* q_loss)  * resolution / (tank_volume * 4.1813)

	LP += pulp.lpSum(P_waterheater[t] for t in range(opti_size)) 
	status = LP.solve(pulp.GUROBI(mip=True, msg=False, timeLimit=15,epgap=None))
	print('Status: ' + pulp.LpStatus[status])


	for t in range(step_size):
		
		if r_T[-1]<=40 or r_T[-1]<T_tank[t].value():
			r_P.append(P_max)
		else: 
			r_P.append(0)

		dT=(r_P[-1]-Q_DHW[t+i*step_size]-(r_T[-1]-23)* q_loss)  * resolution / (tank_volume * 4.1813)

		r_T.append(r_T[-1] + dT)
##########################################
##########################################
##########################################
fig, ax1 = plt.subplots()

ax2 = ax1.twinx()
ax1.plot(r_T[:total_duration], 'g-', label='T')
ax2.plot(r_P[:total_duration], 'r-', label='P')
ax2.plot(Q_DHW[:total_duration], 'b-', label='Q')

ax1.legend(loc="upper left")
ax2.legend(loc="lower left")

plt.show()
