#
# DOCTEST.PY
#
# Test the ARNPDFScanner class by running it on a number of ARN document and validating its output.
#
# Execute from the "test" directory or the paths will not be correct.
#
import random
import unittest
import os
import site
site.addsitedir("..")
import arn_pdf_scanner



class TestSequenceFunctions(unittest.TestCase):
	DOC_DIR = "testdocs"
	
	def setUp(self):
		self.s = arn_pdf_scanner.ARNPDFScanner()

	def test_comp(self):
		# Get list of PDF files in testdocs
		keyfiles = [f for f in os.listdir(self.DOC_DIR)
			if os.path.isfile(os.path.join(self.DOC_DIR, f)) and ".key" in f]
		
		# Scan each PDF and compare it with the corresponding result file in DOC_DIR
		#
		# Improvement tip: 	Store results as serialized python objects.
		# 					Then use itertools.izip() to iterate over the two lists of tuples.
		for keyfile in keyfiles:
			res = self.s.scan(os.path.join(self.DOC_DIR, keyfile.strip(".key") + ".pdf"))
			
			with open(os.path.join(self.DOC_DIR, keyfile), 'r') as k:
				for r in res:
					line = k.readline()
					# The following will also fail if the file ends prior to the tuple list
					self.assertEqual(self.s.tuple2str(r), line.strip())
				# Assert there's nothing left in the file
				self.assertEqual(len(k.read()), 0)
				
if __name__ == '__main__':
    unittest.main()