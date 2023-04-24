import os
import numpy as np
import plotly.graph_objects as go
from io import BytesIO
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
from requests import get
from typing import List

def __get_text_content(url: str) -> str:
    return get(url).content.decode('utf-8')

def __get_json_content(url: str) -> List:
    content = __get_text_content(url) \
        .replace("null", "None").replace("true", "True").replace("false", "False")
    try:
        return eval(content)
    except:
        exit(f'Invalid content for {url}')

def __get_profile(url: str) -> Image:
    if 'icon' in url:
        return Image.open('default_photo.png').resize((80,80))
    
    profile = Image.open(get(url.replace("\\",""), stream=True).raw)

    h,w = profile.size
    
    # creating luminous image
    lum_img = Image.new('L',[h,w] ,0) 
    draw = ImageDraw.Draw(lum_img)
    draw.pieslice([(0,0),(h,w)],0,360,fill=255)
    img_arr = np.array(profile)
    lum_img_arr = np.array(lum_img)
    final_img_arr = np.dstack((img_arr, lum_img_arr))
    return Image.fromarray(final_img_arr).resize((80,80))

def __get_equity_curve(strategy, width=1200, height=400) -> Image:
    # Add line
    fig = go.Figure()
   
    x, y = [],[]
    statistics = strategy.get('statistics')
    if statistics:
        for point in statistics.get('sparkline',[]):
            x.append(point['time'])
            y.append(point['value'])

    fig.add_trace(go.Scatter(x=x, y=y, line=dict(color='#0096FF', width=3)))

    fig.update_layout(
        autosize=False,
        width=width,
        height=height,
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        margin=dict(l=0, r=0, t=0, b=0),
        xaxis=dict(visible=False),
        yaxis=dict(visible=False)
    )

    fig_bytes = fig.to_image(format="png")
    return Image.open(BytesIO(fig_bytes))

def __create_landscape(template, strategy, profile) -> Image:
    # Create a copy of the template to add elements
    copy = template.copy()

    # Add profile picture
    copy.paste(profile, (681, 120),mask=profile)

    # Add texts
    I1 = ImageDraw.Draw(copy)
    name = strategy.get('name')
    author_name = strategy.get('authorName')
    category = strategy.get('category')
    if not category: category = ''
    category = category.upper()

    width = name_font.getlength(name)
    if width < 530:
        I1.text((105,120), name, font=name_font, fill='#313131')
    else:
        parts = name.split(' ')
        for i in reversed(range(len(parts))):
            if name_font.getlength(' '.join(parts[:i])) <= 530:
                break
        I1.text((105,120), ' '.join(parts[:i]), font=name_font, fill='#313131')
        I1.text((105,155), ' '.join(parts[i:]), font=name_font, fill='#313131')
        
    width = author_font.getlength(author_name)
    if width < 250:
        I1.text((775,157), author_name, font=author_font, fill='#313131')
    else:
        parts = author_name.split(' ')
        for i in reversed(range(len(parts))):
            if author_font.getlength(' '.join(parts[:i])) <= 250:
                break
        if i == 0:
            while author_font.getlength(author_name) > 250:
                author_name = author_name[:-1]
            I1.text((775,157), f'{author_name}...', font=author_font, fill='#313131')
        else:
            I1.text((775,157), ' '.join(parts[:i]), font=author_font, fill='#313131')
            I1.text((775,182), ' '.join(parts[i:]), font=author_font, fill='#313131')

    I1.text((105,200), category, font=category_font,
        fill=colors_by_category.get(category, '#313131'))

    fig = __get_equity_curve(strategy)
    copy.paste(fig, (0, 210),mask=fig)
    return copy

def __create_square(template, strategy, profile) -> Image:
    # Create a copy of the template to add elements
    copy = template.copy()

    # Add profile picture
    copy.paste(profile, (550, 225),mask=profile)

    # Add texts
    I1 = ImageDraw.Draw(copy)
    name = strategy.get('name')
    author_name = strategy.get('authorName')
    category = strategy.get('category')
    if not category: category = ''
    category = category.upper()

    width = name_font.getlength(name)
    if width < 450:
        I1.text((42,220), name, font=name_font, fill='#313131')
    else:
        parts = name.split(' ')
        for i in reversed(range(len(parts))):
            if name_font.getlength(' '.join(parts[:i])) <= 450:
                break
        I1.text((42,220), ' '.join(parts[:i]), font=name_font, fill='#313131')
        I1.text((42,255), ' '.join(parts[i:]), font=name_font, fill='#313131')
        
    width = author_font.getlength(author_name)
    if width < 200:
        I1.text((640,265), author_name, font=author_font, fill='#313131')
    else:
        parts = author_name.split(' ')
        for i in reversed(range(len(parts))):
            if author_font.getlength(' '.join(parts[:i])) <= 200:
                break
        if i == 0:
            while author_font.getlength(author_name) > 200:
                author_name = author_name[:-1]
            I1.text((640,265), f'{author_name}...', font=author_font, fill='#313131')
        else:
            I1.text((640,265), ' '.join(parts[:i]), font=author_font, fill='#313131')
            I1.text((640,290), ' '.join(parts[i:]), font=author_font, fill='#313131')

    I1.text((42,300), category, font=category_font,
        fill=colors_by_category.get(category, '#313131'))

    fig = __get_equity_curve(strategy, 860, 285)
    copy.paste(fig, (0, 440),mask=fig)
    return copy

colors_by_category = {
    'CRYPTO': '#C39E78',
    'EQUITIES': '#BF7C7C',
    'US EQUITIES': '#9A74BF',
    'ETF': '#B44444',
    'FOREX': '#5FB26F',
    'FUTURES': '#5D6586'
}

if __name__ == '__main__':

    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    destination_folder = Path('thumbnails')
    destination_folder.mkdir(parents=True, exist_ok=True)

    template_landscape = Image.open('template_landscape.png')
    template_square = Image.open('template_square.png')
    name_font = ImageFont.FreeTypeFont('Inter font/static/Inter-SemiBold.ttf', 35)
    category_font = ImageFont.FreeTypeFont('Inter font/static/Inter-Regular.ttf', 20)
    author_font = ImageFont.FreeTypeFont('Inter font/static/Inter-Regular.ttf', 24)

    content = __get_json_content('https://www.quantconnect.com/api/v2/sharing/strategies/list/')
    strategies = content.get('strategies', [])

    for strategy in strategies:
        id = strategy.get('projectId')
        if not id:
            print(f'No project Id for {strategy}')
            continue
                    
        profile_picture = __get_profile(strategy['authorProfile'])

        landscape = __create_landscape(template_landscape, strategy, profile_picture)
        landscape.save(f"thumbnails/{id}.png")

        square = __create_square(template_square, strategy, profile_picture)
        square.save(f"thumbnails/{id}_square.png")