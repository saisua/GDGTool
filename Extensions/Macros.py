import os, asyncio

class Firefox:
    @staticmethod
    async def set_ddg_search(context):
        page = await context.new_page()
        await page.goto("about:preferences#search", wait_until="domcontentloaded")
        await page.keyboard.press("Tab")
        await page.keyboard.press("Tab")
        await page.keyboard.press("ArrowDown")
        await page.keyboard.press("ArrowDown")
        await page.keyboard.press("ArrowDown")
        await page.close()

    @staticmethod
    async def set_ddg_extension(context):
        if(not os.path.isdir("Settings")):
            return
        if(not os.path.isdir("Settings/Addons")):
            return
        
        extensions = [os.path.abspath(f"Settings/Addons/{file}") for file in os.listdir("Settings/Addons") if file.endswith(".xpi")]
        if(not len(extensions)):
            return

        c1 = "const { AddonManager } = require('resource://gre/modules/AddonManager.jsm');"
        c2 = "const { FileUtils } = require('resource://gre/modules/FileUtils.jsm');"
        c3 = "AddonManager.installTemporaryAddon(new FileUtils.File('{}'));"

        page = await context.new_page()
        await page.goto("about:debugging#/runtime/this-firefox", wait_until="domcontentloaded")
        page2 = await context.new_page()
        await page2.goto("about:devtools-toolbox?id=9&type=tab", wait_until="domcontentloaded")
        await asyncio.sleep(1)
        await page2.keyboard.press("Tab")
        await page2.keyboard.down("Shift")
        await page2.keyboard.press("Tab")
        await page2.keyboard.press("Tab")
        await page2.keyboard.up("Shift")
        await page2.keyboard.press("ArrowRight")
        await page2.keyboard.press("Enter")

        await page2.keyboard.type(f"{' '*10}{c1}{c2}")
        await page2.keyboard.press("Enter")

        for extension in extensions:
            print(f"Adding extension: {extension}")
            await asyncio.sleep(0.2)

            await page2.keyboard.type(f"{' '*10}{c3.format(extension)}")
            await page2.keyboard.press("Enter")
            #await asyncio.sleep(0.2)
            await page2.bring_to_front()

            # const { AddonManager } = require("resource://gre/modules/AddonManager.jsm");
            # const {FileUtils} = require("resource://gre/modules/FileUtils.jsm");
            # AddonManager.installTemporaryAddon(new FileUtils.File(absolutePath));

        await context.close()

firefox = Firefox