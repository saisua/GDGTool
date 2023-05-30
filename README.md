# GDGTool

Data harvesting, also known as web scraping, is the process of collecting infor-
mation from websites automatically. Dynamic websites, which are characterized
by their ability to update content in real-time (AJAX), present unique challenges
for data harvesting.
The importance of this information for people, companies and researchers is
paramount, as it can be used for a variety of purposes such as business intelli-
gence, research and personal usage, and even for training Large Language Mod-
els (LLM).
We describe the architecture, design, and implementation of a modular, exten-
sible and open-source data harvesting tool that we have created using Python,
Cython and the library "Playwright", among many other NLP libraries, specifi-
cally made to address these challenges, and whose performance we will evaluate
through experiments and case studies.
As part of the reflection about this tool, we will conclude by discussing the po-
tential applications of data harvested from these dynamic websites and the future
trends in this field.

- Note: When you launch the project it may not allow the creation of new tabs. This can be disabled by clicking the 'Block open websites' option in the menu.

# Requirements
This project requires Docker to launch and prepare the tool

# First execution
The first execution will install the whole Docker environment and requirements. It will install the required NLP models and other dependencies by itself.

I have provided two files to run the tool in Linux:
- build.sh
- build_console.sh

Those files build only the changes made to the tool, so they can be reused to relaunch the tool, they are not installation scripts.

The difference is that build.sh will launch the tool and show its logs, and build_console.sh will launch it but open instead a ssh inside the docker container.

However, if there is some issue, these commands can also be run to build the docker directly in the terminal:
<code>
\# build.sh
docker-compose up --build

\# build_console.sh
docker-compose up --build -d # build & detach the process
docker exec -it scraper /bin/bash # connect to the ssh 
</code>

I would recommend to run the console version, as I will mention later

Once in the tool, you will get only a few options from the menu:
- Block open websites: Toggles the prohibition of allowing to open new tabs. This is useful to block spam
- Get website keywords: This will analyze the current page text and provide some keywords about the text in the whole website. It can take a few seconds in the worst case
- Open website test: This will open a test website I use for testing

This is not all possible menu options but I still have to add a few like crawling before processing the texts

# Behave

I recommended launching in the console version because I have implemented behave usecase testing.
This files can be found under Tests/features, and they are -easy to read, easy to modify- files that run tests on the functionalities of the tools.

For example, upon connecting to the ssh, one can do
<code>
cd Tests
behave
</code>

And the project will execute all tests available.
Be careful! It will launch many requests to different websites, as it is a tool meant to be performant.

# Folder Structure explanation
API: The API component provides a slow but safe interface for interacting with the tool. It includes type and value checking to ensure that the input data is valid and conforms to the expected format. This is the intended approach for users that want to extend the tool to his/her own needs but do not require a fast interaction with it.

Core: The core component contains the main bulk of the code and is responsible for the fast and efficient execution of the scraping process. It is compiled code that handles the web crawling, data extraction, and data storage.

EndScripts: The EndScripts component contains scripts that perform alterations and analysis on the data harvested by the tool after it has finished. These scripts can be used for tasks such as summarization of text data.

Extensions: The extensions component contains optional code that must be integrated to the core component manually. These extensions provide additional utilities such as rotating proxies, which can be enabled or disabled as needed.

Plugins: The plugins component contains optional code that can be added dynamically at different stages of the scraping process. These plugins are independent and run during the harvest, but are not integrated into the core component. An example of a plugin is the video harvesting.

Tests: The tests component contains a set of automated tests to ensure that the tool works correctly and that the different components are functioning as expected.
