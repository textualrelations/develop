#
# Scans PDFs from ARN and outputs checkbox and radio button data in key-value pairs.
#
# PDF tree traversing code fetched from https://github.com/dpapathanasiou/pdfminer-layout-scanner/blob/master/layout_scanner.py
#
# Vilhelm Jutvik 2014 for Textual Relations: First version
#


import sys
import os
import pdb
from binascii import b2a_hex
import math

from pdfminer.pdfparser import PDFParser
from pdfminer.pdfdocument import PDFDocument, PDFNoOutlines
from pdfminer.pdfpage import PDFPage
from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.converter import PDFPageAggregator
from pdfminer.layout import LAParams, LTTextBox, LTTextLine, LTFigure, LTImage, LTChar, LTLine, LTRect, LTCurve

class ARNPDFScanner:
		
	###
	### pdf-miner requirements
	###
		
	def _with_pdf (self, pdf_doc, fn, pdf_pwd, *args):
		"""Open the pdf document, and apply the function, returning the results"""
		result = None
		try:
			# open the pdf file
			fp = open(pdf_doc, 'rb')
			# create a parser object associated with the file object
			parser = PDFParser(fp)
			# create a PDFDocument object that stores the document structure
			doc = PDFDocument(parser)
			# connect the parser and document objects
			parser.set_document(doc)
			# supply the password for initialization
				#        doc.initialize(pdf_pwd)
		
			#if doc.is_extractable:
			# apply the function and return the result
			result = fn(doc, *args)
	
			# close the pdf file
			fp.close()
		except IOError:
			# the file doesn't exist or similar problem
			pass
		return result
	
	
	def _get_line_ycoord(self, lt_obj, lines):
		return lt_obj.y0 - i * (lt_obj.height / len(lines))
	
	def _parse_lt_objs (self, lt_objs, chkboxes = [], chkmarks = [], radiobtns = [], pressedbtns = [], txtlines = []):
		"""Iterate through the list of LT* objects and capture the text or image data contained in each"""
		chkboxes = []
		chkmarks = []
		radiobtns = []
		pressedbtns = []
		txtlines = []
	
	#	page_text = {} # k=(x0, x1) of the bbox, v=list of text strings within that bbox width (physical column)
		for lt_obj in lt_objs:
	#		print str(type(lt_obj)) + " at (x0, y0) (" + str(lt_obj.x0) + ", " + str(lt_obj.y0) + ")"
			
			if isinstance(lt_obj, LTTextBox) or isinstance(lt_obj, LTTextLine):
				# text, so arrange is logically based on its column width
				#cpy = str(page_text)
				
				lines = lt_obj.get_text().strip('\n').split('\n')
				y = lt_obj.y0 + lt_obj.height
				for i, line in enumerate(lines):
					# Coordinate of the text line
	
	#				print "lt_obj index " + str(lt_obj.index)
					txtlines.append((lt_obj.x0, y - (i + 0.5) * (lt_obj.height / len(lines)), line, lt_obj.index))
		#			pdb.set_trace()
	#			print "txtlines is now " + str(txtlines)
			elif isinstance(lt_obj, LTCurve):
	#			print " with " + str(len(lt_obj.pts)) + " points and with dim " + str(lt_obj.width) + " x " + str(lt_obj.height)
	
				if int(lt_obj.width) == int(lt_obj.height):
					if len(lt_obj.pts) == 5:
						# Checkbox
						chkboxes.append(lt_obj)
					elif len(lt_obj.pts) == 2:
						# Checkmark
	#					print "Checkmark " + str(lt_obj.pts)
						if (lt_obj.pts[0][1] < lt_obj.pts[1][1]):
							chkmarks.append(lt_obj)
	                
					elif len(lt_obj.pts) == 13 and int(lt_obj.width) == 7:
						radiobtns.append(lt_obj)
	#					print "radiobtn"
					elif len(lt_obj.pts) == 13 and int(lt_obj.width) == 3:
						pressedbtns.append(lt_obj)
	#					print "radiobtn pressed"
						
	#		elif isinstance(lt_obj, LTFigure):
	#			print "Entering LTFigure"
	#			(chkboxes, chkmarks, radiobtns, pressedbtns, txtlines) = parse_lt_objs(lt_obj, chkboxes, chkmarks, radiobtns, pressedbtns, txtlines)
			
				
	#			page_text = update_page_text_hash(page_text, lt_obj)
				#print "New text " + page_text[len(cpy):len(page_text)]
			# elif isinstance(lt_obj, LTImage):
			#         # an image, so save it to the designated folder, and note its place in the text 
			#     	saved_file = save_image(lt_obj, page_number, images_folder)
			#     	if saved_file:
			#             # use html style <img /> tag to mark the position of the image within the text
			#             text_content.append('<img src="'+os.path.join(images_folder, saved_file)+'" />')
			#         else:
			#             print >> sys.stderr, "error saving image on page", page_number, lt_obj.__repr__
	#		elif isinstance(lt_obj, LTFigure):
	#			# LTFigure objects are containers for other LT* objects, so recurse through the children
			
		# for k, v in sorted([(key,value) for (key,value) in	 page_text.items()]):
		# 	# sort the page_text hash by the keys (x0,x1 values of the bbox),
		# 	# which produces a top-down, left-to-right sequence of related columns
		# 	text_content.append(''.join(v))
	
		return (chkboxes, chkmarks, radiobtns, pressedbtns, txtlines) #'\n'.join(text_content)
	
	def _rect2str(self, lt_rect):
		return "(x, y) = (" + str(lt_rect.x0) + ", " + str(lt_rect.y0) + ") width " + str(lt_rect.width) + " height " + str(lt_rect.height)
	
	###
	### Processing Pages
	###
	
	def _pt2str(self, x, y, xref, yref):
		return "(" + str(x) + ", " + str(y) + ") #(" + str(abs(x - xref)) + ", " + str(abs(y - yref)) + ")"
	
	# Returns the tuple (pageno, key, value) as a human readable string
	def tuple2str(self, t):
		return str(t)
	
	# Returns a list of tuples with the following format:
	# (selected box och button as a dict object, selection such as radio button or pressed dito as a dict object, associated line of text)
	def _match_objs(self, selectors, choices, txtlines, pageno):
		retlst = []
		choices.sort(key=lambda x:x.y0, reverse=True)
		txtlines.sort(key=lambda x: x[1])
		for choice in choices:
			# Calculate center of choice
			choice_center_x = choice.x0 + choice.width / 2
			choice_center_y = choice.y0 + choice.height / 2
			
			choice_text = group_text = None
			for selector in selectors:
				if choice_text and group_text: break
				
				# Calculate center of selector
				selector_center_x = selector.x0 + selector.width / 2
				selector_center_y = selector.y0 + selector.height / 2
	
				if math.hypot(selector_center_x - choice_center_x, selector_center_y - choice_center_y) < 5:
					# The choice has found its selector. Find the matching text.
	
					choice_text_box_id = None
					# Find the choice's text. Iterate over the text lines, starting from the bottom of the page
					for line in txtlines:
	
						# Choice text
						if choice_text is None and abs(choice_center_x - line[0]) < 30 and abs(choice_center_y - line[1]) < 5:
	
							# Found a matching text.
							choice_text = line[2]
							choice_text_box_id = line[3]
							#print "MATCH: Choice " + _pt2str(choice_center_x, choice_center_y, choice_center_x, choice_center_y) + " Selector " + _pt2str(selector_center_x, selector_center_y, choice_center_x, choice_center_y) + " Text " + _pt2str(line[0], line[1], choice_center_x, choice_center_y)
							# print "With TEXT " + line[2]
	#					else:
	#						print "NOMATCH: Choice " + _pt2str(choice_center_x, choice_center_y, choice_center_x, choice_center_y) + " Selector " + _pt2str(selector_center_x, selector_center_y, choice_center_x, choice_center_y) + " Text " + _pt2str(coord[0], coord[1], choice_center_x, choice_center_y)
	#						print "With TEXT " + v
	
						if choice_text is not None:
							break;
					
					
					# Find the choice's header (group text). Iterate over the text lines, starting from the bottom of the page
					for line in txtlines:
	
	#					print "Choice center y " + str(choice_center_y) + " text y " + str(k[1])
						#textmiddle = text.y0 + text.height / 2
	#					if abs(choice_center_x - textmiddle) < 5:
	
						# Group text
						if choice_text_box_id is not line[3] and line[0] < choice_center_x and choice_center_y + 5 < line[1]:
							# print "MATCHGROUP: Choice " + _pt2str(choice_center_x, choice_center_y, choice_center_x, choice_center_y) + " Selector " + _pt2str(selector_center_x, selector_center_y, choice_center_x, choice_center_y) + " Text " + _pt2str(line[0], line[1], choice_center_x, choice_center_y)
							# print "	With GROUPTEXT " + line[2]						
							group_text = line[2]
	#					else:
						 	# print "#NOMATCHGROUP: Choice " + _pt2str(choice_center_x, choice_center_y, choice_center_x, choice_center_y) + " Selector " + _pt2str(selector_center_x, selector_center_y, choice_center_x, choice_center_y) + " Text " + _pt2str(line[0], line[1], choice_center_x, choice_center_y)
						 	# print "	With GROUPTEXT " + line[2]						
	
						if group_text is not None:
							break;
	
					break # Process next choice
			
			if group_text is None or choice_text is None:
				raise Exception("Didn't find matching selector or text for a choice")
			# print group_text + "=" + choice_text
			retlst.append((pageno, group_text, choice_text))
			
		return retlst
					
	
	def _parse_pages (self, doc):
		"""With an open PDFDocument object, get the pages and parse each one
		[this is a higher-order function to be passed to _with_pdf()]"""
		rsrcmgr = PDFResourceManager()
		laparams = LAParams()
		device = PDFPageAggregator(rsrcmgr, laparams=laparams)
		interpreter = PDFPageInterpreter(rsrcmgr, device)
		
		result = []
		for i, page in enumerate(PDFPage.create_pages(doc)):
			pageno = i + 1
			#print "PAGE #" + str(pageno)
			interpreter.process_page(page)
			# receive the LTPage object for this page
			layout = device.get_result()
			# layout is an LTPage object which may contain child objects like LTTextBox, LTFigure, LTImage, etc.
			#chkboxes = chkmarks = radiobtns = pressedbtns = txtlines = []
			(chkboxes, chkmarks, radiobtns, pressedbtns, txtlines) = self._parse_lt_objs(layout)
	#		text_content.append(_parse_lt_objs(layout, (i + 1), images_folder, lt_rects, chkboxes, chkmarks, radiobtns, pressedbtns, txtlines))
	#		pdb.set_trace()
		
			# Match radiobtns and pressedbtns
	#		print "SCAN DONE"
			matches = self._match_objs(chkboxes + radiobtns, chkmarks + pressedbtns, txtlines, pageno)
			result = result + matches
		
	#	print "FOUND FOLLOWING RECTS AT PAGE #" + str(i + 1) + ":"
	#	for rect in lt_rects:
	#		print "Rectangle (" + str(rect.width) + ", " + str(rect.height) + ")"
		
	#	for rect1 in lt_rects:
	#		for rect2 in lt_rects:
	#			pdb.set_trace()
	#			if rect1 != rect2 and int(rect1.x0) == int(rect2.x0) and int(rect1.y0) == int(rect2.y0):
	#				print "Rectangles match:"
	#				print "#1: " + _rect2str(rect1) + "\n#2: " + _rect2str(rect2)
	
		return result
	
	#
	# Scans the ARN PDF whose path is given by filename, using password pdf_pwd, if any.
	# Returns a list of tuples: The first element is the page number; the second and third
	# constitutes the key value pair of the checkbox / radio button selection. The list is ordered by
	# page number, then from page top to page bottom.
	#
	# Only checked / pressed checkboxes / radio buttons are returned.
	#
	# pdf_doc: Filename
	# pdf_pwd: PDF password, if any
	#
	def scan(self, pdf_doc, pdf_pwd=''):
	    """Process each of the pages in this pdf file and return a list of strings representing the text found in each page"""
	    return self._with_pdf(pdf_doc, self._parse_pages, pdf_pwd)

if __name__ == '__main__':
	print "Scanning " + sys.argv[1]
	s = ARNPDFScanner()
	result = s.scan(sys.argv[1])
	for t in result:
		print s.tuple2str(t)