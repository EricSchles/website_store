# website_store
a tool for storing websites.

This tool will download a website, with any depth you like to store a website simply do the following:

m = Mapper()

links = m.mapper([website specific url],[base url],depth,[])
m.storing(links)

specific example:

m = Mapper()

links = m.mapper("https://www.google.com","https://www.google.com",1,[])
m.storing(links)
