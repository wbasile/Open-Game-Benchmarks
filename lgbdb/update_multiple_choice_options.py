from BeautifulSoup import BeautifulSoup
import urllib2
import re
 


# A lot of coede duplication because different lists require custom parsing strategies


# NVIDIA GPUS
wiki = "https://en.wikipedia.org/wiki/List_of_Nvidia_graphics_processing_units"
header = {'User-Agent': 'Mozilla/5.0'} #Needed to prevent 403 error on Wikipedia
req = urllib2.Request(wiki,headers=header)
page = urllib2.urlopen(req)
soup = BeautifulSoup(page)
 
tables = soup.findAll("table", { "class" : "wikitable" })

nvidia_gpus = []

for table in tables:
    for row in table.findAll('tr'):
        if len(row.findAll('th')) == 1:
            gpu = row.find('th').text
            
            gpu = gpu.replace('&#160;',' ')
            gpu = re.sub("[\[].*?[\]]", "", gpu)
            
            if (gpu.find("GeForce") != -1) or (gpu.find("Quadro") != -1) and gpu not in nvidia_gpus:
                nvidia_gpus += ["NVidia " + gpu]
                
###############

#~ print "\n".join(nvidia_gpus)

#~ print "('"+"NVidia"+"',\n\t("
    #~ 
#~ for gpu in (nvidia_gpus):
    #~ print "\t('" + gpu + "','" + gpu + "'),"
    #~ 
#~ print "\t)\n),\n\n"
    #~ 
#~ exit()


# AMD GPUS
wiki = "https://en.wikipedia.org/wiki/List_of_AMD_graphics_processing_units"
header = {'User-Agent': 'Mozilla/5.0'} #Needed to prevent 403 error on Wikipedia
req = urllib2.Request(wiki,headers=header)
page = urllib2.urlopen(req)
soup = BeautifulSoup(page)
 
tables = soup.findAll("table", { "class" : "wikitable" })

amd_gpus = []

for table in tables:
    for row in table.findAll('tr'):
        if len(row.findAll('th')) == 1:
            gpu = row.find('th').text
            
            gpu = gpu.replace('&#160;',' ')
            gpu = re.sub("[\[].*?[\]]", "", gpu)
            
            if gpu.find("Radeon") != -1 and gpu not in amd_gpus:
                amd_gpus += ["AMD " + gpu]

###############


# INTEL GPUS
wiki = "https://en.wikipedia.org/wiki/List_of_Intel_graphics_processing_units"
header = {'User-Agent': 'Mozilla/5.0'} #Needed to prevent 403 error on Wikipedia
req = urllib2.Request(wiki,headers=header)
page = urllib2.urlopen(req)
soup = BeautifulSoup(page)
 
tables = soup.findAll("table", { "class" : "wikitable" })

intel_gpus = []
for table in tables:
    for row in table.findAll('tr'):
        if row.findAll('td'): 
            gpu = row.findAll('td')[0].text
            
            if gpu.find("GMA") != -1 or gpu.find("HD") != -1:
                if gpu.find(" ") != -1:
                    gpu = gpu.replace('&#160;',' ')
                    gpu = re.sub("[\[].*?[\]]", "", gpu)
                    if gpu not in intel_gpus:
                        intel_gpus += ["Intel " + gpu]
                        
###############



# RESOLUTIONS
wiki = "https://en.wikipedia.org/wiki/Display_resolution"
header = {'User-Agent': 'Mozilla/5.0'} #Needed to prevent 403 error on Wikipedia
req = urllib2.Request(wiki,headers=header)
page = urllib2.urlopen(req)
soup = BeautifulSoup(page)
 
table = soup.find("table", { "class" : "sortable wikitable" })

resolutions = {}

for row in  table.findAll("tr")[1:]:
    tds = row.findAll("td")
    if tds:
        
        ratio = str(tds[1].text).replace("~","")
        width = str(tds[2].text)
        height = str(tds[3].text)
        if width and height:
            res_string = width + "x" + height
            
            resolutions[ratio] = resolutions.get(ratio,[]) + [res_string]
            
###############




## Print out everything in a nice python dictionary format            

print 'GPU_CHOICES = ('

for vendor, vendor_gpus in zip(["AMD", "Intel", "NVidia"],[amd_gpus, intel_gpus, nvidia_gpus]):

    print "('"+vendor+"',\n\t("
    
    for gpu in (vendor_gpus):
        print "\t('" + gpu + "','" + gpu + "'),"
        
    print "\t)\n),\n\n"

print ')'    
print

    
print 'RESOLUTION_CHOICES = ('
            
for ratio in sorted(resolutions.keys()):
    
    print "('"+ratio+"',\n\t("
    
    for res in sorted(resolutions[ratio]):
        print "\t('" + res + "','" + res + "'),"
        
    print "\t)\n),\n\n"
    
print ')' 

