import urllib2
from HTMLParser import HTMLParser
from urlparse import urlparse
import requests

# These are just the types of tags/attributes that I am accepting
validLinks = {
	"a":"href",
	"img":"src",
	"link":"href",
	"script":"src"
}

# To avoid anchors
ignoredSchemes = ["javascript"]

# Gets HTML of URL
def webinfo (url):
	try:
		response = urllib2.urlopen(url)
		html = response.read()
		return html
	# In the event of an error accessing the site (ex: 404 error)
	except Exception,e:
		print "Invalid url: %s"%url
		print str(e)
		return None

# Function merges the baseURL and it's path. This is mainly for links such as "/faq" and turns them into links like "http://ruscheduler.com/faq"
def mergeURL(baseURL, path):
	link = urlparse(path)
	if not link.netloc and link.path and link.scheme not in ignoredSchemes:
		# print link
		if link.geturl()[0] != "/" and baseURL[-1] != "/":
			return "%s/%s"%(baseURL, link.geturl())
		elif link.geturl()[0] == "/" and baseURL[-1] == "/":
			return "%s%s"%(baseURL[:-1], link.geturl())
		else:
			return "%s%s"%(baseURL, link.geturl())
	elif (not link.netloc and not link.path) or link.scheme in ignoredSchemes:
		return None
	else:
		return link.geturl()



# Subclass to have our own special HTML Parsing magic
class MyHTMLParser(HTMLParser):
	# Where links are stored
	links = []
	visited = []
	badLinks = []
	# For base URL
	url = ""
	
	# Our own special feed for HTML so we can control a few things
	def feedURL(self, url):
		if url in self.visited or url in self.badLinks:
			return
		self.url = url
		html = webinfo(url)
		if webinfo(url):
			self.visited.append(url)
			if url not in self.links:
				self.links.append(url)
			self.feed(html)
		else:
			print "Invalid URL"
			self.badLinks.append(url)

	# Takes the tags that match up with validLinks and adds their links if they are valid
	def handle_starttag(self, tag, attrs):
		if tag.lower() in validLinks:
			for attr in attrs:
				if attr[0].lower() == validLinks[tag.lower()]:
					link = mergeURL(self.url, attr[1])
					if not link or link in self.badLinks:
						continue
					elif link not in self.links:
						# self.links.append(link)
						# Validate the link before appending it
						try:
							if requests.head(link).status_code < 400:
								self.links.append(link)
							else:
								self.badLinks.append(link)
						except:
							self.badLinks.append(link)

# Checks for the same domain
def sameDomain(url, subURL):
	return urlparse(url).netloc == urlparse(subURL).netloc


def getLinks(url, levels = 5):
	# Validates entered URL
	try:
		if not requests.head(url).status_code < 400:
			print "Invalid URL: %s"%url
			return
	except:
		print "Invalid URL: %s"%url
		return
	
	# Time to build the parser and feed it the HTML
	parser = MyHTMLParser()
	parser.feedURL(url)

	# Need to setup our break conditions, if we go past 5 levels (or whatever is specified) or if no new urls are added to links after an iteration
	linkLength = 0
	level = 0
	while linkLength != len(parser.links) and level < levels:
		level+=1
		linkLength = len(parser.links)
		# Run all URLs in links through the parser again
		for subURL in parser.links:
			if subURL not in parser.visited and sameDomain(url, subURL):
				parser.feedURL(subURL)
	parser.links.sort()


	print
	print "Sitemap:"
	for link in parser.links:
		print link

if __name__ == "__main__":
	# getLinks("http://ruscheduler.com")
	url = raw_input("Enter URL of website to be crawled through (Try to avoid larger sites for better performance)\n")
	layers = raw_input("How many layers do you want to go through? (Please pick a small number such as 1-5 for better performance)\n")
	getLinks(url, layers)
