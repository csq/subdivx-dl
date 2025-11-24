import random
import asyncio

async def human_like_typing(locator, text, min_delay=0.03, max_delay=0.12, mistake_rate=0.03):
    should_paste_text = random.choice([True, False])
    if should_paste_text:
        await locator.page.fill('#buscar', text)
        return

    for char in text:
        delay = random.uniform(min_delay, max_delay)
        await locator.type(char, delay=delay)
        if random.random() < 0.08:
            await asyncio.sleep(random.uniform(0.1, 0.5))
        if random.random() < mistake_rate:
            wrong_char = chr(random.randint(97,122))
            await locator.type(wrong_char, delay=random.uniform(min_delay, max_delay))
            await asyncio.sleep(random.uniform(0.05,0.2))
            await locator.press('Backspace')
