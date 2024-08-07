from dataclasses import dataclass

from utils.common import Endpoint, session
from utils.settings import env

import folium 
import pandas as pd

from pprint import pprint
    
@dataclass
class Search(Endpoint):
    
    url: str = f"{env.PROXY}/api/integration/v2/comparables/search/advanced"
    location: list = None
    df: object = None

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def request(self, **params):

        if 'page_num' not in params:
            params['page_num'] = self.cur_page

        if self.verbose: pprint(params)

        self.response = session.get(self.url, params=params)

        if query:=self.response.json().get('query_params'):
            self.location = [query.get('lat'), query.get('lon')]
        else:
            self.location = None

        self.build_df()

        if len(self.df)==0: 
            raise Exception('No results')

        return self

    def build_df(self):
        self.df = None
        if self.response.status_code > 300:
            raise Exception(self.response.content)
        response_json = self.response.json()
        if pagination:= response_json.get('pagination'):
            total_count = pagination.get('total_count')
            page_num = pagination.get('page_current')
            page_count = pagination.get('page_count')
            print(f'Total: {total_count} - Page: {page_num}/{page_count}')
        if results:= response_json.get('results'):
            self.df = pd.DataFrame(results)
        else: return None
        if 'score' in self.df.columns:
            self.df = pd.concat([self.df.drop(columns='score'),  pd.json_normalize(self.df['score'])], axis=1)
        return self.df

    def score(self):
        df = self.df.copy()
        score_fields = ['_id'] + [c for c in df.columns if 'score' in c] + ['similarity', 'distance']
        return df[score_fields].style.background_gradient(cmap='Blues', vmin=0, vmax=100)

    def map(self, distance=None):

        if not distance: 
            try: distance = self.response.json().get('query_params', {}).get('distance')
            except: pass

        df = self.df.copy()

        x, y = df.lat.mean(), df.lon.mean()

        map = folium.Map(location=[x, y], zoom_start=17, )

        for idx,point in df.iterrows():
            folium.Marker((point.lat, point.lon), popup=html(point), lazy=True).add_to(map)

        if self.location:

            folium.Circle(
                location=self.location,
                radius=10,
                color="white",
                weight=3,
                fill_opacity=1,
                opacity=1,
                fill_color="red",
                fill=False,  # gets overridden by fill_color
                popup="Center",
            ).add_to(map)

            if distance:
                folium.Circle(
                    location=self.location,
                    radius=distance,
                    color="blue",
                    weight=1,
                    fill_opacity=0.3,
                    opacity=1,
                    fill_color="lightgray",
                    fill=False,  # gets overridden by fill_color
                    popup="{} meters".format(distance),
                ).add_to(map)

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
    if val:
        return '<a target="_blank" href="{}">{} . {}</a>'.format(val, val[:20], val[-10:])
    return ''
    
def make_image(val):
    return '<img width="200px" src="{}"></a>'.format(val)

def html(x):
    images = x.get('images_list', [])
    title = x.get('title')
    url = x.get('url')

    img_tags = []
    
    if len(images):
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