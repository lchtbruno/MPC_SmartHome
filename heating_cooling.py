from heating_requirements import *
from fc import *
import csv,pulp
import pandas as pd
from gurobipy import *
import matplotlib.pyplot as plt

df=pd.read_csv('profiles.csv')
df=df.round(decimals=3)
T_OUT_orig = df['T_OUT'].tolist()

T_OUT=[]
for i in range(len(T_OUT_orig)):
	T_OUT.append(sum(T_OUT_orig[i:i+5])/5)

q_loss = (14.33 + 7.13 * (150) ** 0.4) / ((65 - 20) * 1000)  # kW/K	

house_length=12.15
house_width=10.6
house_height=6
House1=House(length=house_length,width=house_width,height=house_height,building_date=1970)

house_thermal_mass=house_height*house_width*house_length*1.2 	# kJ/K

q_loss=House1.waermebedarf()

resolution=5 #minutes
step_size=int(60*24/resolution)
opt_size=int(step_size*2)
total_duration=int(2*60/resolution*24*7)



P_max_HP=100000
P_max_AC=100000
COP_AC=5
COP_HP=5

T_max=25
T_min=20

s_T_house=[]
s_P_HP=[]
s_P_AC=[]

r_T_house=[21]
r_P_HP=[]
r_P_AC=[]

for i in range(int(total_duration/step_size)):

	if i==0:
		_T_OUT_fc=forecast(T_OUT[total_duration:total_duration+step_size*3],step_size*3)
	else:
		_T_OUT_fc=forecast(T_OUT[i*step_size:(i+3)*step_size],step_size*3)

	T_OUT_fc=T_OUT[:i*step_size]+_T_OUT_fc


	LP = pulp.LpProblem('LP',pulp.LpMinimize)  
	T_house = pulp.LpVariable.dicts("T_house", range(opt_size), cat=pulp.LpContinuous, lowBound=T_min, upBound=T_max)
	P_HP = pulp.LpVariable.dicts("P_HP", range(opt_size), cat=pulp.LpContinuous, upBound=P_max_HP, lowBound=0)
	P_AC = pulp.LpVariable.dicts("P_AC", range(opt_size), cat=pulp.LpContinuous, upBound=P_max_AC, lowBound=0)

	for t in range(opt_size):

		if t==0:
			LP += T_house[t] == r_T_house[-1] 
			
		else:
			LP += T_house[t] == T_house[t-1] + (P_HP[t]*COP_HP-P_AC[t]*COP_AC-q_loss*(T_house[t-1]-T_OUT_fc[t]))*60*resolution/house_thermal_mass

		LP += P_HP[t] + P_AC[t]

	LP += pulp.lpSum(P_HP[t] + P_AC[t] for t in range(opt_size)) 

	status = LP.solve(pulp.GUROBI(mip=True, msg=False, timeLimit=15,epgap=None))
	print('Status: ' + pulp.LpStatus[status])

	for t in range(step_size):
		s_P_AC.append(P_AC[t].value())
		s_P_HP.append(P_HP[t].value())
		s_T_house.append(T_house[t].value())


		"""SIMULATION"""

	for t in range(step_size):

		if r_T_house[-1]>T_OUT[t+i*step_size]:

			if r_T_house[-1]>s_T_house[t+i*step_size]:

				if r_T_house[-1] > T_max:
					r_P_AC.append(1)
					r_P_HP.append(0)

				else:
					r_P_AC.append(0)
					r_P_HP.append(0)

			else:
				r_P_AC.append(0)
				r_P_HP.append(1)

		else:
			if r_T_house[-1]<s_T_house[t+i*step_size]:

				if r_T_house[-1]<T_min:
					r_P_AC.append(0)
					r_P_HP.append(1)

				else:
					r_P_AC.append(0)
					r_P_HP.append(0)

			else:
				r_P_AC.append(1)
				r_P_HP.append(0)


		r_T_house.append(r_T_house[-1]+(r_P_HP[-1]*COP_HP-r_P_AC[-1]*COP_AC-q_loss*(r_T_house[-1]-T_OUT[t+i*step_size]))*60*resolution/house_thermal_mass)


##########################################


fig, ax1 = plt.subplots()

ax2 = ax1.twinx()
ax1.plot(r_T_house,label="T_house",color='y')
ax1.plot(T_OUT[:total_duration],label="T_OUT",color='g')
ax2.plot(r_P_HP,label="P_HP",color='r')
#ax2.plot(r_P_AC,label="P_AC",color='b')

ax1.legend(loc="upper left")
ax2.legend(loc="lower left")
plt.show()





