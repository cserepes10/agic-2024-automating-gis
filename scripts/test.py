import json
import arcgis
from arcgis.gis import GIS
from arcgis.mapping import WebMap
from GlendaleTools import glendale_tools
from arcgis.apps.expbuilder import WebExperience
from concurrent.futures import ThreadPoolExecutor

# Define the path for file operations
THE_PATH = r'D:\COG_ADMIN\MISC_PROJECTS\agic-2024-automating-gis\scripts\templates\\'

def update_desc(creds):
    gis = GIS(creds[0], creds[1], creds[2])
    portal = 'gismaps.gelndaleaz.com' in creds[0]
    app_types = {
        'Dashboard': 'Dashboard',
        'Web Mapping Application': 'Web Mapping Application',
        'Web Experience': 'Web Experience'
    }

    item_ids = {key: [] for key in app_types.keys()}
    
    for key, item_type in app_types.items():
        items = gis.content.search(query='owner:BCserepes@GLENDALEAZ.COM_COG_GIS', item_type=item_type, max_items=9999)
        item_ids[key].extend(item.id for item in items)
    
    print(len(item_ids['Web Experience']))
    
    with ThreadPoolExecutor() as executor:
        futures = []
        for app_type, ids in item_ids.items():
            for content_id in ids:
                futures.append(executor.submit(process_content, content_id, app_type, gis, THE_PATH, portal))
        for future in futures:
            future.result()

def process_content(content_id, app_type, gis, the_path, portal):
    try:
        content_search = gis.content.get(content_id)
        if app_type == "Dashboard":
            update_dashboard(content_search, the_path, gis, portal)
        elif app_type == "Web Mapping Application":
            update_web_mapping_app(content_search, the_path, gis, portal)
        elif app_type == "Web Experience":
            update_web_mapping_app(content_search, the_path, gis, portal)
    except Exception as e:
        print(f'Failed to update {app_type}: {e}')

def update_dashboard(content_search, the_path, gis, portal):
    try:
        old_title = content_search.title
        title = f"{old_title} (DASHBOARD)" if ' (DASHBOARD)' not in old_title else old_title

        widgets = content_search.get_data().get('widgets', [])
        for widget in widgets:
            if widget.get('type') == "mapWidget":
                webmap_id = widget['itemId']
                mappy = gis.content.get(webmap_id)
                selected_web_map = WebMap(mappy)
                html_list = generate_html_list(selected_web_map, gis)

                description_file = the_path + "app-description.txt"
                with open(description_file, "w") as f:
                    f.write(str(html_list))

                with open(description_file, "r") as f:
                    beedle = generate_beedle_html(mappy, selected_web_map, f.read(), portal)
                    props = {
                        "title": title,
                        "thumbnailurl": "https://gismaps.glendaleaz.com/gisportal/sharing/rest/content/items/8dbff04007044f75b818b2f33607fcb5/data",
                        "description": beedle,
                        "overwrite": True
                    }
                    content_search.update(item_properties=props)
    except Exception as e:
        print(f'Failed to update dashboard: {e}')

def normalize_app_title(title):
    app_tag = '(App)'
    clean_title = title.replace(app_tag, '').strip()
    return f"{clean_title} {app_tag}"

def deal_with_exp_builder(content_search, gis):
    print(content_search.id)
    experience_builder = WebExperience(content_search.id, gis=gis)
    print(experience_builder.datasources)
    webmap_ids = [exp['itemId'] for exp in experience_builder.datasources.values() if exp['type'] == 'WEB_MAP']
    return webmap_ids[0] if webmap_ids else None

def update_web_mapping_app(content_search, the_path, gis, portal):
    try:
        old_title = content_search.title
        title = normalize_app_title(old_title)

        try:
            webmap_id = content_search.get_data().get('values', {}).get('webmap')
            if not webmap_id:
                webmap_id = deal_with_exp_builder(content_search, gis)
        except:
            print('Failed to get web map ID')
            webmap_id = None
        
        if webmap_id:
            print(f'The web map for this app: {webmap_id}')
            mappy = gis.content.get(webmap_id)
            print(mappy.title)
            selected_web_map = WebMap(mappy)
            html_list = generate_html_list(selected_web_map, gis)
            print(html_list)

            description_file = the_path + "app-description.txt"
            with open(description_file, "w") as f:
                f.write(str(html_list))

            with open(description_file, "r") as f:
                beedle = generate_beedle_html(mappy, selected_web_map, f.read(), portal)
                props = {
                    "title": title,
                    "thumbnailurl": "https://gismaps.glendaleaz.com/gisportal/sharing/rest/content/items/9ab3b6e31c3749419467975c8e1e5c97/data",
                    "description": beedle,
                    "overwrite": True
                }
                content_search.update(item_properties=props)
        else:
            print(f'No web map found for {content_search.id}')
    except Exception as e:
        print(f'Failed to update web mapping application: {e}')

def generate_html_list(selected_web_map, gis):
    html_list = []
    try:
        for lyr in selected_web_map.layers:
            lyr_url = lyr.url
            lyr_type = lyr.get('layerType', 'Unknown')
            stringy_url = f"<li><a href='{lyr_url}' target='_blank'>{lyr.title}</li></a>"
            if stringy_url not in html_list:
                html_list.append(stringy_url)

        for lyr in selected_web_map.layers:
            find_maps_with_layer(lyr.url, lyr.get('layerType', 'Unknown'), gis)
    except:
        html_list = "Couldn't get the list"

    return html_list

def generate_beedle_html(mappy, selected_web_map, description, portal):
    clean_description = description.replace('["', '').replace('"]', '').replace('",', '').replace('"', '')
    url = 'https://gismaps.glendaleaz.com/gisportal/apps/mapviewer/index.html?webmap=' if portal else 'https://cog-gis.maps.arcgis.com/apps/mapviewer/index.html?webmap='
    return (
        f"<font size='4'><b><font color='#ff0000' style='background-color:rgb(255, 255, 255);'><i>The Web Map Name Is:</i></font></b><br>"
        f"<ul><li><a href='{url}{mappy.id}' target='_blank'><font size='4'><i>{selected_web_map.item.title}</i></font></a></li></ul><br>"
        f"<font size='3'>The Layers in this app are:<br><ul>{clean_description}</ul></font>"
    )

def find_maps_with_layer(lyr_to_find, search_layer, gis=''):
    header_txt = ("<font size='4'><b><font color='#ff0000' style='background-color:rgb(255, 255, 255);'>"
                  "<i>This layer is found in the following Web Map's:</i></font></b>")

    web_map_items = gis.content.search(query='*', item_type="Web Map", max_items=10000)
    lyr_update = gis.content.search(query=lyr_to_find, max_items=10000)

    print(f"Searching {len(web_map_items)} web maps")
    print(f"Searching for {lyr_to_find} in the maps")

    maps_with_layer = []
    maps_without_layer = []

    for item in web_map_items:
        found_it = False
        selected_web_map = WebMap(item)
        for lyr in selected_web_map.layers:
            if 'url' in lyr and lyr_to_find.lower() in lyr.url.lower():
                found_it = True
                break
            elif 'layerType' in lyr and lyr.layerType == "GroupLayer":
                if any('url' in sublyr and lyr_to_find.lower() in sublyr.url.lower() for sublyr in lyr.layers):
                    found_it = True
                    break

        if found_it:
            maps_with_layer.append(item)
        else:
            maps_without_layer.append(item)

    print(f"Found {len(maps_with_layer)} maps which contain the layer")
    print(f"Found {len(maps_without_layer)} maps which do not contain the layer")

    if lyr_update:
        element_list = [
            f"<ul><li><a href='https://gismaps.glendaleaz.com/gisportal//home/webmap/viewer.html?webmap={map_item.id}' target='_blank'><font size='4'><i>{map_item.title}</i></font></a></li></ul>"
            for map_item in maps_with_layer
        ]
        try:
            description_file = THE_PATH + "feature-layer-description.txt"
            with open(description_file, "w") as f:
                f.write(header_txt + ''.join(element_list))

            with open(description_file, "r") as f:
                description = f.read()

            for updater in lyr_update:
                print(updater)
                props = {
                    "title": updater.title,
                    "thumbnailurl": "https://gismaps.glendaleaz.com/gisportal/sharing/rest/content/items/c0ed4fb77f1b441595ea1b6f31c5b46a/data",
                    "description": description,
                    "overwrite": True
                }
                if not element_list:
                    props['tags'] = 'orphan'
                updater.update(item_properties=props)
        except Exception as e:
            print(f"Failed to update feature layer description: {e}")

    

if __name__ == "__main__":
    tools = glendale_tools()
    agol_login = tools.agol_creds()
    portal_creds = tools.portal_creds()
    creds = [agol_login, portal_creds]
    for i in range(len(creds)):
        update_desc(creds[i])
