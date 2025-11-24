import os
import asyncio
import tempfile

from subdivx_dl import helper
from browserforge.fingerprints import Screen
from camoufox.async_api import AsyncCamoufox

class Browser:
    _instance = None
    _user_data_dir = os.path.join(tempfile.gettempdir(), 'subdivx-dl', 'user_data')

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(Browser, cls).__new__(cls)
            cls._instance.browser = None
        return cls._instance

    async def _get_browser(self):
        if self.browser is None:
            self.browser = AsyncCamoufox(
                headless=True,
                os=["macos"],
                screen=Screen(max_width=1920, max_height=1080),
                persistent_context=True,
                user_data_dir=Browser._user_data_dir
            )
            await self.browser.start()
            helper.logger.info('Started browser')
        return self.browser.browser

    # See: https://github.com/MaestroOfAutomation/turnstile_bypass
    async def _cloudflare_bypass(self, url: str):
        browser = await self._get_browser()
        page = await browser.new_page()
        await page.goto(url)

        for _ in range(15):
            await asyncio.sleep(1)

            for frame in page.frames:
                if frame.url.startswith('https://challenges.cloudflare.com'):
                    frame_element = await frame.frame_element()
                    bounding_box = await frame_element.bounding_box()
                    coord_x = bounding_box['x']
                    coord_y = bounding_box['y']

                    width = bounding_box['width']
                    height = bounding_box['height']

                    checkbox_x = coord_x + width / 9
                    checkbox_y = coord_y + height / 2

                    await page.mouse.click(x=checkbox_x, y=checkbox_y)

        helper.logger.info('Bypassed Cloudflare')
        return page

    async def open_page(self, url: str):
        if os.path.exists(Browser._user_data_dir) is False:
            page = await self._cloudflare_bypass(url)
            return page
        else:
            browser = await self._get_browser()
            page = await browser.new_page()
            await page.goto(url)
            return page

    async def close_browser(self):
        if self.browser is not None:
            await self.browser.browser.close()
            self.browser = None
