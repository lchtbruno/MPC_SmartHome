def forecast(past,horizon):
	fc=[]
	for i in range(horizon):
		fc.append(past[-horizon+i])
	return fc