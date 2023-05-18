import PySimpleGUI as sg
import os.path

import asyncio

from datetime import datetime

# First the window layout in 2 columns

button_menu = [
]

def generate_layout(button_menu, texts_menu):
    file_list_column = [
        [
            sg.Text("Scraper controls"),
        ],
        [
            sg.HSeparator(),
        ],
        *([btn] for btn in button_menu)
    ]

    text_viewer_column = [
        texts_menu
    ]

    return [
        [
            sg.Column(file_list_column),
            sg.VSeperator(),
            sg.Column(text_viewer_column),
        ]
    ]


class Control_GUI:
    async def loop(self, control_buttons: dict={}, texts: dict={}, *, window_name=None):
        button_menu = [
            sg.Button(btn_name, key=btn_name) for btn_name in control_buttons.keys()
        ]
        texts_menu = [
            sg.Text(text, key=text_key) for text_key, text in texts.items()
        ]

        if(window_name is None):
            window_name = f"Scraper controller {datetime.today().strftime('%Y-%m-%d %H:%M:%S')}"

        window = sg.Window(window_name, generate_layout(button_menu, texts_menu))

        try:
            # Run the Event Loop
            while True:
                await asyncio.sleep(0.25)

                event, _ = window.read()
                if event == sg.WIN_CLOSED or event == "Exit":
                    break

                btn_call = control_buttons.get(event)
                if(btn_call is not None):
                    print(f"Running {btn_call.__name__}")
                    await btn_call(event, window, self)
        except KeyboardInterrupt:
            pass
        finally:
            window.close()