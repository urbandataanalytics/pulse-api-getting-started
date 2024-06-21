from utils.common import Endpoint, session
from utils.settings import env

import pandas as pd
from pprint import pprint

import geopandas as gpd

from shapely import wkt

import warnings
warnings.filterwarnings('ignore')

def coordinates_to_wkt(coordinates):
    ''' 
    Function to convert coordinates to WKT
    '''
    try:
        wkt_polygon = "POLYGON (("
        wkt_polygon += ", ".join([f"{coord[0]} {coord[1]}" for coord in coordinates])
        wkt_polygon += "))"
        return wkt.loads(wkt_polygon)
    except: pass


class Indicators(Endpoint):

    url: str = f"{env.PROXY}/api/integration/super/indicators/advanced"
    center_x: float = None
    center_y: float = None

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def request(self, **params):

        if 'page_num' not in params:
            params['page_num'] = self.cur_page

        if self.verbose: pprint(params)

        response = session.get(self.url, params=params)

        if response.status_code>300:
            pprint(response)
            return

        if self.verbose: 
            pprint(response.json())

        if results:=response.json().get('results'):
            df = pd.DataFrame(results)
            if features:=response.json().get('features'):
                sorted_cols = [f for f in features if f in df.columns]
                df = df.reindex(sorted_cols, axis=1)
            df.set_index(['period_code'], inplace=True)
            if 'geometry' in df.columns:
                df['geometry'] = df['geometry'].apply(coordinates_to_wkt)
                projected_crs = 'EPSG:4326'
                df = gpd.GeoDataFrame(df, geometry='geometry', crs=projected_crs)
                df = df.to_crs(projected_crs)
                df['centroid'] = df.geometry.centroid
                df['lat'], df['lon'] = df.centroid.x, df.centroid.y
                df = df.drop(columns=['centroid'])
                self.center_x, self.center_y = df.lat.mean(), df.lon.mean()
            self.df = df 
            return self

        raise Exception('No results')

    def get_mercator(self):
        df_wm = self.df.to_crs(epsg=3857)
        df_wm['lat'], df_wm['lon'] = df_wm.geometry.centroid.x, df_wm.geometry.centroid.y
        df_wm['centroid'] = df_wm.apply(lambda x: [x.lat, x.lon], axis=1)
        return df_wm