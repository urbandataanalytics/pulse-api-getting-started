from dataclasses import dataclass, field
from pandas import DataFrame

import folium 
import requests
import pandas as pd

from pprint import pprint

from settings import env

@dataclass
class Endpoint:
    params: dict
    response: dict = None
    
@dataclass
class Search(Endpoint):
    
    url: str = f"{env.PROXY}/api/integration/v2/comparables/search/advanced"
    df: DataFrame = None
    cur_page:int = 1

    def __init__(self, **params):
        self.params = params

    def clear(self):
        self.params = {}
        self.cur_page = 1
        return self

    def request(self, verbose=False, **params):
        self.params = dict(self.params,**params)
        if 'page_num' not in self.params:
            self.params['page_num'] = self.cur_page
        if verbose: pprint(self.params)
        self.response = requests.get(self.url, headers={'Authorization': env.API_KEY}, params=self.params)
        self.df = self._df()
        return self

    def _df(self):
        if self.response.status_code > 300:
            raise Exception(self.response.content)
        response_json = self.response.json()
        if pagination:= response_json.get('pagination'):
            total_count = pagination.get('total_count')
            page_num = pagination.get('page_current')
            page_count = pagination.get('page_count')
            print(f'Total: {total_count} - Page: {page_num}/{page_count}')
        df = pd.DataFrame(response_json.get('results'))
        self.df = pd.concat([df.drop(columns='score'),  pd.json_normalize(df['score'])], axis=1)
        return self.df

    def score(self):
        df = self.df.copy()
        score_fields = ['_id'] + [c for c in df.columns if 'score' in c] + ['similarity', 'distance']
        return df[score_fields].style.background_gradient(cmap='Blues', vmin=0, vmax=100)

    def map(self, fields=['_id'] ):

        df = self.df.copy()
        df['lat'] = df.location.map(lambda x: x['coordinates'][1])
        df['lon'] = df.location.map(lambda x: x['coordinates'][0])
        x, y = df.lat.mean(), df.lon.mean()
        map = folium.Map(location=[x, y], zoom_start=17, )
        for idx,point in df.iterrows():
            folium.Marker((point.lat, point.lon), popup=html(point), lazy=True).add_to(map)
        return map

    def show(self, columns = []):
        return show_images(self.df, columns)

def show_images(df, columns = []):

    df = df.copy(deep=False)

    def get_img(x,i):
        try:
            return x[i].get('url')
        except: pass
    
    df['img1'] = df.images_list.map(lambda x: get_img(x,0))
    df['img2'] = df.images_list.map(lambda x: get_img(x,1))
    df['img3'] = df.images_list.map(lambda x: get_img(x,2))
    
    df.drop(['images_list'], axis=1, inplace=True)

    idx = ['_id', 'title', 'url', 'img1', 'img2', 'img3']

    cols = list(set(columns) & set(df.columns))

    df = df[idx + cols]

    return df.style.format({
                    'url': make_clickable, 
                    'img1': make_image,
                    'img2': make_image,
                    'img3': make_image
                   }
                  )

def make_clickable(val):
    return '<a target="_blank" href="{}">{} . {}</a>'.format(val, val[:20], val[-10:])
    
def make_image(val):
    return '<img width="200px" src="{}"></a>'.format(val)

def html(x):
    images = x.get('images_list', [])
    title = x.get('title')
    url = x.get('url')

    img_tags = []
    
    for image in images[:10]:
        img_url = image.get('url', '')
        if img_url:
            img_tags.append(f"<img width=100px src='{img_url}'></img>")
    
    img_html = "".join(img_tags)
    return f"""
    <html>
        <head>
            <style>
                .grid-container {{
                    display: grid;
                    grid-template-columns: repeat(3, 1fr);
                    gap: 10px;
                }}
                .grid-item {{
                    width: 100px;
                }}
            </style>
        </head>
        <body>
            <p style="font-size:20px" >{title}</p>
            <a target=_blank style="font-size:15px" href={url}>listing url</a>
            <div class="grid-container">
                {img_html}
            </div>
        </body>
    </html>
    """