#!/usr/bin/python
# -*- coding: utf8 -*-

from __future__ import unicode_literals

import numpy as np
import scipy as sp
import pandas as pd
from scipy.stats import norm

import matplotlib.pyplot as plt
import matplotlib.mlab as mlab

import sys, urllib
import bs4 as bs
import re
from datetime import datetime,timedelta
import time
import getopt
import os.path
import unicodedata, string

from collections import Counter, OrderedDict

def convertChrono(s):
	""" Convert a string under the format of hours:minutes:seconds into a timedelta object """
	strp = s.strip().split(':')
	return timedelta(hours=int(strp[0]),minutes=int(strp[1]),seconds=int(strp[2]))

class TRICLAIRModele(object):
	def get_data_triathlon(self,link,name='',format='',year=datetime.today().year-1):
		table = self.__get_soup_webpage(u'http://www.triclair.com' + link).findAll('table')[-1]

		entete = map(lambda x: x.text,table.find_all('tr')[0].find_all('th'))
		useful = [u'Place',u'Nom',u'Club',u'Cat.',u'Sexe',u'Temps scratch',u'Nat.',u'V\xe9lo',u'C\xe0p']
		translation = dict({u'Place':u'Place',u'Nom':u'Nom',u'Club':u'Club',u'Cat.':u'Categorie',u'Sexe':u'Sexe',
							u'Temps scratch':u'Scratch',u'Nat.':u'Natation',u'V\xe9lo':u'Velo',u'C\xe0p':u'Cap'})
		sections     = list(set(entete).intersection(set(useful)))
		not_sections = list(set(useful).difference(set(entete)))

		columns = OrderedDict()
		re_search = re.compile('[0-1]?[0-9]:[0-9]+:[0-9]+')
		re_search2 = re.compile('[0-9]+:[0-9]+')
		for col in useful:
			columns.setdefault(translation[col],[])

		for row in table.find_all('tr')[1:]:
			col = row.find_all('td')
			for sec in sections:
				data = col[entete.index(sec)].text.strip()
				if sec == u'Nom':
					data = data.upper()
					if u'Pr\xe9nom' in entete:
						data = u' '. join((data,col[entete.index(u'Pr\xe9nom')].text.upper().strip()))
				elif sec ==u'Place':
					data = int(data)
				elif sec == u'Club':
					data = 	'NON LICENCIE' if data == '' else data.upper()
				elif sec == u'Sexe':
					data = u'M' if data in ['M','m','H','h'] else (u'F' if data in ['F','f','W','w'] else u'NaN')
				elif sec == u'Cat.':
					pass
				elif sec in [u'Temps scratch',u'Nat.',u'V\xe9lo',u'C\xe0p']:
					if col[entete.index(u'Temps scratch')].text.strip() in ['DNF','DSQ','DNS']:
						data = float('nan')
					else:	
						data = convertChrono(re_search.findall(data)[0]) if re_search.match(data) else (convertChrono('00:' + re_search2.findall(data)[0]) if re_search2.match(data) else float('nan'))                 			
				
				columns[translation[sec]].append(data)
			for sec in not_sections:
				data = float('nan')
				columns[translation[sec]].append(data)	

		return pd.DataFrame(columns)

	def __get_soup_webpage(self,link):
		return bs.BeautifulSoup(urllib.urlopen(link).read())

def plot_bourgdata(N1,N2):
	A=TRICLAIRModele()
	Tb15 = A.get_data_triathlon(link='/triathlon-bourg-resultats-1996.htm',year=2015)
	Tb14 = A.get_data_triathlon(link='/triathlon-bourg-resultats-1715.htm',year=2014)	
	S15_ = map(lambda x: x.total_seconds()/60,Tb15['Scratch'].dropna())
	S14_ = map(lambda x: x.total_seconds()/60,Tb14['Scratch'].dropna())
	
	S15 = S15_[N1:N2]
	S14 = S14_[N1:N2]

	(mu14, sigma14) = norm.fit(S14)
	(mu15, sigma15) = norm.fit(S15)

	N_BINS = 50
	n, bins, patches = plt.hist(S14, N_BINS, normed=1, facecolor='red', alpha=0.5,label=r'$\mathrm{2014:}\ \mu=%.3f,\ \sigma=%.3f$' %(mu14, sigma14))
	y = mlab.normpdf( bins, mu14, sigma14)
	l = plt.plot(bins, y, 'r-', linewidth=3)
	n, bins, patches = plt.hist(S15, N_BINS, normed=1, facecolor='green', alpha=0.5,label=r'$\mathrm{ 2015:}\ \mu=%.3f,\ \sigma=%.3f$' %(mu15, sigma15))
	y = mlab.normpdf( bins, mu15, sigma15)
	l = plt.plot(bins, y, 'g-', linewidth=3)

	plt.xlabel('Scratch Time (minutes)')
	plt.ylabel('Number of athletes per scratch time (normalized)')

	plt.legend(loc='best', fancybox=True, framealpha=0.5)
	plt.title(r'$\mathrm{Athletes\ from\ rank\ } %d \mathrm{\ to\ } %d$' %(N1, N2))

	plt.show()
	