class House(object):
	def __init__(self,length,width,height,building_date):
		self.length=length
		self.width=width
		self.height=height
		self.building_date=building_date

		if self.building_date>=2021:
			self.transfer_coefficient=70
		elif self.building_date>=1995:
			self.transfer_coefficient=90
		elif self.building_date>=1984:
			self.transfer_coefficient=130
		else:
			self.transfer_coefficient=210

	def surface(self):
		return (self.height*self.width+self.width*self.length+self.length*self.height)*2

	def waermebedarf(self):
		#print(str(self.width*self.length*self.transfer_coefficient)+" kWh space heating p.a.")
		return round(self.width*self.length*self.transfer_coefficient/(365*24*10),4)

		
