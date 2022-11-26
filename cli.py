# distutils: language=c++

import cython
from API.Live import Live_browser

@cython.cfunc
def main():
    br: object
    i: str

    with Live_browser(remove_old_data=True, headless=False, browser_name="firefox") as br:
        br.open_websites(websites=['https://duckduckgo.com'], run_mode="agen")

        print(br.slave_local_results.get())

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
    main()