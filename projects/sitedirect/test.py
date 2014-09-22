import httplib, urllib
import base64
import pdb

host = "siren.sitedirect.se"
url = "/sitedirect/_custom/int_textualrelations/create_article.php"

key = "d87bfcba8283989d19e2f86470f16d6c"	# Magic string used for authentication
xml = "<notis>testtest</notis>"  			# Sane XML data goes here
file = ""									# The PDF document goes here as one big string
# It might have to be base 64 encoded. If that's suspected, uncomment the line below.
# file =  base64.b64encode(file)

# Configure
params = urllib.urlencode({'xml': xml, 'file': file, 'key': key})
headers = {"Content-type": "application/x-www-form-urlencoded",
           "Accept": "text/plain"}

# Establish the TCP connection...
conn = httplib.HTTPConnection(host)

# ...and make the HTTP POST request
conn.request("POST", url, params, headers)

# Read out the response
response = conn.getresponse()
print "Response status:", response.status
print "Response reason:", response.reason
data = response.read()
#pdb.set_trace()

# When the sitedirect's server is happy with your request, you'll get a serialized object in reply.
# It's in the JSON format (check wikipedia). The current reply, "Array", is not of valid JSON syntax.
print "Response data:", data