
<h1>Open Game Benchmarks</h1>

An open-source project with the aim of collecting and analysing game performance data in both Linux and Windows
<br>
<a href="www.opengamebenchmarks.org" target="new">www.opengamebenchmarks.org</a>


<h2>Goals</h2>
<p>
<ul>
Possible usages:
<li>a person wants to buy game X, and wants to know how that game would run with a system similar to his</li>
<li>compare how a set of graphics cards perform on a specific game</li>
<li>compare performances in Linux and Windows on a specific game</li>
<li>determine which factor(s) are the most important for performance on a given game/platform</li>
</ul>
</p>

<p>In the last few years, there has been a remarkable increase of video games available for Linux; small and big, indies and AAA companies are showing more interest in this Operating System evey day, and today we can enjoy games such as The Witcher 2, XCOM: Enemy Unknown, Civilization V on Linux. More and more developers are launching their games on Windows and Linux simultaneously.</p>
<p>Gaming on Linux has always been present, but the interest that Valve showed in this platform is surely playing an important role in the current rising trend. As of today (January 2016), more than 1500 titles are available on Steam that support Linux. With this in mind, the Open Game Benchmarks database was created, with the goals of having a comprehensive resource of game performances on Linux, and providing comparison information between Linux and Windows, as a tool to push developers and porters to provide a comparable performance on the two systems.</p>


<h2>How does it work?</h2>
<p>A few tools exist that can record the frame timings for OpenGL applications, such as <a href="https://github.com/ValveSoftware/voglperf" target="new">Voglperf</a> and <a href="https://glxosd.nickguletskii.com/" target="new">GLXOSD</a> on Linux and <a href="http://www.fraps.com/" target="new">FRAPS</a> on Windows. The user can upload this data to Open Game Benchmarks, where they are parsed and recorded, and a number of statistical measures (median, quartiles, average, standard deviation) are calculated. Together with the frame timings data, the use uploads a set of hardware+software settings.</p>
 
<p>A single benchmark is displayed in a detail page, with a graph and all its variables. In addition, the user can select an arbitrary number of benchmarks to compare: these can be seen as a table or a bar graph.</p>



<h2>How to contribute</h2>
<p>In several ways: do some benchmark of your favourite games and upload them; pick one of the opened <a href="https://github.com/wbasile/Open-Game-Benchmarks/issues">GitHub issues</a> and work on that; implement a feature or correct a bug and do a pull request; <a href="mailto:admin@opengamebenchmarks.org">email me</a> about a bug, missing feature, typo that you found.
</p>

<h2>Technical details</h2>
<p>
<ul>
<li>The supported games are only Steam games available for Linux + Windows</li>
<li>developed using <a href="https://www.djangoproject.com/" target="new">Django 1.9</a></li>
<li>graphs are create using the app <a href="https://github.com/agiliq/django-graphos" target="new">django-graphos</a>, with the Flot API</li>
<li>currently hosted on <a href="https://www.heroku.com/" target="new">Heroku</a></li>
</ul>
</p>
