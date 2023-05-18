# distutils: language=c++

import os, sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from API.Browser import Live_browser

def open_live_browser_test():
    with Live_browser(remove_old_data=True, headless=False, browser_name="firefox") as br:
        br.open_websites(websites=['https://duckduckgo.com'], run_mode="agen")

        try:
            while True:
                i = input("> ")
                
                if(i == "exit"):
                    break
                elif(not i.startswith('br')):
                    continue
                else:
                    exec(i)
        except KeyboardInterrupt:
            pass

if(__name__ == "__main__"):
    open_live_browser_test()