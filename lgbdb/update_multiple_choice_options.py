from BeautifulSoup import BeautifulSoup
import urllib2
import re

# A lot of code duplication because different lists require custom parsing strategies




###############



# CPUS
wiki = "http://www.cpubenchmark.net/CPU_mega_page.html"
header = {'User-Agent': 'Mozilla/5.0'} #Needed to prevent 403 error on Wikipedia
req = urllib2.Request(wiki,headers=header)
page = urllib2.urlopen(req)
soup = BeautifulSoup(page)


tables = soup.findAll('a')

intel_cpus = []
amd_cpus = []
for table in tables:
    cpu = table.text    
                                                    
    if cpu.find("AMD")!= -1 and cpu.find("Mobile AMD") == -1:
        cpu = cpu.replace('&#160;',' ')
        cpu = re.sub("[\[].*?[\]]", "", cpu)                
        if cpu not in amd_cpus:
            amd_cpus += [cpu]                                       
    else:
        if cpu.find("Intel")!= -1 and cpu.find("Mobile Intel") == -1:
            cpu = cpu.replace('&#160;',' ')
            cpu = re.sub("@.*", "", cpu)
            if cpu not in intel_cpus:
                intel_cpus += [cpu]
                        
###############



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
            gpu = re.sub("\n", " ", gpu)
            
            if (gpu.find("GeForce") != -1) or (gpu.find("Quadro") != -1) and gpu not in nvidia_gpus:
                nvidia_gpus += ["NVidia " + gpu]
                
###############



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
            gpu = re.sub("\n", " ", gpu)
            
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
                    gpu = re.sub("\n", " ", gpu)
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
    ratio = str(tds[1].text).replace("~","")
    width = str(tds[2].text)
    height = str(tds[3].text)
    if width and height:
        res_string = width + "x" + height                   
        resolutions[ratio] = resolutions.get(ratio,[]) + [res_string]
            
###############






## Since some information lacks good sources to parse or are limited by the settings available for selection, was created a series of arrays and a matrix
systems = {}
systems["Windows"]=['Windows XP', 'Windows Vista', 'Windows 7', 'Windows 8', 'Windows 10', 'Windows-other']
systems["Linux"]=['Debian-based (Debian, Ubuntu, Mint, Elementary OS, SteamOS)','Arch-based (Arch, Manjaro)',
                    'Red Hat-based (RedHat, Fedora, CentOS)','Gentoo-based (Gentoo, Chromium, Funtoo)','SUSE-based',
                    'Slackware-based','Mandriva-based','Linux-other']
gameSettings=["Low","Medium","High","Very High","Ultra"]
dualGpu=["None","SLI", "Crossfire"]
antialias=["Antialias enable","Antialias disable"]

## Print out everything in a nice python dictionary format
info = 'GPU CHOICES = (\n'

for vendor, vendor_gpus in zip(["AMD", "Intel", "NVidia"],[amd_gpus, intel_gpus, nvidia_gpus]):

    info = info + "('"+vendor+"',\n\t(\n"
    
    for gpu in (vendor_gpus):
        info = info + "\t('" + gpu + "','" + gpu + "'), \n"        
        

    info = info + "\n\t)\n\t),\n"
info = info + '\n\t)\n'                         

info = info + 'CPU_CHOICES = ('

for vendor, vendor_cpus in zip(["AMD", "Intel"],[amd_cpus, intel_cpus]):

        info = info + "('"+vendor+"',\n\t(\n"
    
        for cpu in (vendor_cpus):
            info = info + "\t('" + cpu + "','" + cpu + "'), \n"
        
        info = info + "\n\t)\n\t),\n"
info = info + '\n\t)'    

info = info + '\t\nDRIVER_CHOICES = (\n\t("Opensource","Opensource"),\n\t("Proprietary","Proprietary"),\n\t)\n'                    
    
info = info + 'RESOLUTION_CHOICES = ('
i=0
for ratio in sorted(resolutions.keys()):
        
        if(i==2):
            info = info + "\n('21:9',\n\t(\n\t('2560x1080','2560x1080'),\n\t('3440x1440','3440x1440'),\n\t)\n\t),"
    
        info = info + "\n('"+ratio+"',\n\t(\n"        
        
        for res in sorted(resolutions[ratio]):
            info = info + "\t('" + res + "','" + res + "'), \n"
        
        info = info + '\t)\n\t),'
        i=i+1
info = info + ')\n),'
        
info = info + '\nOS_CHOICES = ('
for system in sorted(systems.keys()):
        
            
        info = info + "\n('"+system+"',\n\t(\n"        
        
        for sys in sorted(systems[system]):
            info = info + "\t('" + sys + "','" + sys + "'),\n"
        
        info = info + '\t)\n),'
info = info + '\n\t)'

info = info + '\nGAME_SETTINGS_CHOICES = (\n'

for quality in gameSettings:
    info = info + "\t('" + quality + "','" + quality + "'),\n"
    
info = info + '\n\t)'

info = info + '\nANTIALIAS_CHOICES = (\n'

for aa in antialias:
    info = info + "\t('" + aa + "','" + aa + "'),\n"
    
info = info + '\n\t)'

info = info + '\nDUAL_GPU_CHOICES = (\n'

i=0
for multigpu in dualGpu:
    if(i==0):
        extra=""
    if(i==1):
        extra=" (Nvidia)"    
    if(i==2):
        extra=" (AMD)"    
    i=i+1
    info = info + "\t('" + multigpu + "','" + multigpu+extra + "'),\n"
    
    
    
info = info + ' \n\t)'
        
            
info = info.encode('ascii', 'ignore')
info = str(info.decode('ascii'))           
with open("multiple_choice_options2.py", "w") as f:
    f.write(info)
    
