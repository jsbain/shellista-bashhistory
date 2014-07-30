'''history:
Prints recent command history
usage: history
history substitution supported as 
	![event][:word]
	allowable event 
		!   last command
		N   execute line N
		-N  execute line N ago
		string execute line starting with string
		?string? execute line containing string
	word modifiers
		^ first argument,( not including command)
		$ last argument
		* all args (not including command)
		x  where x is number: argument x.  0 is cmd
		x-y args x through y. can omit x or y, default to 0,$ respectively. 
'''

alias=['history']

from collections import deque
from ... tools.toolbox import bash
import re
import sys


class BashHistory(deque):
	def __init__(self,HISTSIZE=500):
		self.HISTSIZE = HISTSIZE
		deque.__init__(self, maxlen=HISTSIZE)
		

	def history(self,N=15):
		"""show last N items"""
		for i,s in zip(range(len(list(self))),list(self))[-N:]:
			print i,':',' '.join(s)
		return ''
#       try:
#           i=int(raw_input(':'))
#       except ValueError:
#           i=-1
#       try:
#           print i, self[i]
#           return ' '.join(self[i].replace(' ',"' '"))
#       except:
#           return '\n'

	def history_popup(self,N=15):
		try:
			import ui
		except ImportError:
			return self.history(N)
		v=ui.TableView()
		v.data_source=ui.ListDataSource( [' '.join([s.replace(' ',"' '") for s in x]) for x in list(self)[-N:]])
		v.delegate=v.data_source
		v.height=v.row_height*N+10
		v.width=400
		v.data_source.autoresizing=True
		def _rowselected(sender):
			sender.tableview.close()
		v.delegate.action=  _rowselected
		v.present('popover')
		v.wait_modal()
		print v.selected_row[1]+len(self)-min(len(self),N), ':',v.data_source.items[v.selected_row[1]]
		try:
			return v.data_source.items[v.selected_row[1]]
		except:
			return ''

	def history_replace(self, line):
		"""expand each occurance of ![event][:word]

		===TODO not yet implemented===
		^STRING^string  replace STRING with string
		:p  print and add to history, but dont execute
		"""
		# match inital bang, then one event identifier,
		#   either !, [-]N, string, or ?string?

		linepat=(r'!((?P<linebang>!)'       #!
		            '|(?P<linenum>-?\d+)'   #N, or -N
		            '|(?P<stringstart>\w+)' #str
		            '|\?(?P<stringsearch>\w+)\?)')   #?str?
		# for word modifier, match starting :, then either special char, or range
		wordpat=('(:('
		             '(?P<wordchar>[\^\*%$])'  #   ^ or * or $
		            '|(?P<wordrange>\d*-?\d*)' # x-y, x , x-, or -y
		         '))?')

		pat=linepat+wordpat
		import pdb

		for m in re.finditer(pat,line):
			#pdb.set_trace()
			line=self._process_match(line,m)
		return line

	def _select_line(self,m):
		'''returns line number of selected history substitution'''
		g=m.groupdict()
		#print g
		if g.get('linebang'):
			histline=-1     # !! == !-1
		elif g.get('linenum'):
			histline=int(g['linenum'])  #!n, or !-n
		elif g.get('stringstart'):
			histline=[-i-1 for i,v in enumerate(reversed([' '.join(s) for s in list(self)]))    if v.startswith(g['stringstart'])][0]
		elif g.get('stringsearch'):
			histline=[-i-1 for i,v in enumerate(reversed([' '.join(s) for s in list(self)]))    if v.find(g['stringsearch'])][0]
		else:
			histline=None
		return histline

	def _select_args(self,histline, m):
		lineargs = self[histline]
		g=m.groupdict()
		if g['wordchar']:
			if g['wordchar'][0]==r'^':
				return [lineargs[1]]
			elif g['wordchar'][0]=='*':
				return [lineargs[1:]]
			elif g['wordchar'][0]=='$':
				return [lineargs[-1]]
		elif g['wordrange']: #x, x-y, x-, -y
			if g['wordrange'].find('-')>=0:
				start,end=g['wordrange'].split('-')
				if (start == ''):
					start=0
				if (end == ''):
					end=len(lineargs)
				if (end=='$'):
					end=len(lineargs)
				return lineargs[int(start):int(end)+1]
			else:
				return [lineargs[int(g['wordrange'])]]
		else: # no range specified.. entire line
			return lineargs


	def _process_match(self,line,m):
		"""replace each history expression in line with expanded form """
		# self contains parsed lists, i.e [cmd,arg1,arg2]

		if not any(m.groupdict().itervalues()):
			return line
		else:
			lineidx=self._select_line(m)
			if lineidx:
				lineargs=self._select_args(lineidx, m)
			try:
				hist=   lineargs
				return re.sub(re.escape(m.group(0)),' '.join(hist),line ) #replace portion of line with expansion
			except:
				return line

#TODO: consider storing history file, and loading previous history
_bashhistory=BashHistory()

def main(self, line):
	"""print history"""
	args = bash( line)
	print len(args)
	if args is None:
		return
	elif len(args)>0:
		_bashhistory.history()
	else:
		_bashhistory.history_popup()

#	intercept precmd, replace with hist subst

def precmd(self,line):
		line= _bashhistory.history_replace(line)
		return line
# store completed line after bashing.  
#   todo: consider doing this is precmd instead

def postcmd(self,stop,line):
	_bashhistory.append(bash(line))
	
precmdhook=[precmd]
postcmdhook=[postcmd]

