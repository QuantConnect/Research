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
    destination_folder = Path('images')
    destination_folder.mkdir(parents=True, exist_ok=True)

    template = Image.open('template.png')
    name_font = ImageFont.FreeTypeFont('Inter font/static/Inter-SemiBold.ttf', 35)
    category_font = ImageFont.FreeTypeFont('Inter font/static/Inter-Regular.ttf', 20)
    author_font = ImageFont.FreeTypeFont('Inter font/static/Inter-Regular.ttf', 24)

    content = __get_json_content('https://beta.quantconnect.com/api/v2/sharing/strategies/list/')
    strategies = content.get('strategies', [])

    for strategy in strategies:
        id = strategy.get('projectId')
        if not id:
            print(f'No project Id for {strategy}')
            continue

        # Create a copy of the template to add elements
        copy = template.copy()

        # Add profile picture        
        profile = __get_profile(strategy['authorProfile'])
        copy.paste(profile, (681, 120),mask=profile)

        # Add texts
        I1 = ImageDraw.Draw(copy)
        name = strategy.get('name')
        author_name = strategy.get('authorName')
        category = strategy.get('category')
        if not category: category = ''
        category = category.upper()

        width = name_font.getlength(name)
        if width < 600:
            I1.text((105,120), name, font=name_font, fill='#313131')
        else:
            parts = name.split(' ')
            for i in reversed(range(len(parts))):
                if name_font.getlength(' '.join(parts[:i])) <= 600:
                    break
            I1.text((105,120), ' '.join(parts[:i-1]), font=name_font, fill='#313131')
            I1.text((105,155), ' '.join(parts[i-1:]), font=name_font, fill='#313131')
        
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
            width=1200,
            height=400,
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            margin=dict(l=0, r=0, t=0, b=0),
            xaxis=dict(visible=False),
            yaxis=dict(visible=False)
        )

        fig_bytes = fig.to_image(format="png")        
        fig = Image.open(BytesIO(fig_bytes))
        copy.paste(fig, (0, 210),mask=fig)
        copy.save(f"images/{id}.png")