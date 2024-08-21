import json
import arcgis
from arcgis.gis import GIS
from arcgis.mapping import WebMap
from GlendaleTools import glendale_tools



# Update Descriptions
def update_desc(creds):
    gis = GIS(creds[0], creds[1], creds[2])
    ApplicationTypes = ['Dashboard', 'Web Mapping Application']
    dashboard_ids = []
    app_ids = []
    webmap_app_ids = []
    the_path = r'D:\COG_ADMIN\MISC_PROJECTS\agic-2024-automating-gis\scripts\templates\\'
    
    dashboard_items = gis.content.search(query='owner:*', item_type="Dashboard", max_items=9999)
    app_items = gis.content.search(query='owner:*', item_type="Application", max_items=9999)
    webmap_app_items = gis.content.search(query='owner:*', item_type="Web Mapping Application", max_items=9999)
    
    for item in dashboard_items:
        dashboard_ids.append(item.id)
    for item in app_items:
        app_ids.append(item.id)
    for item in webmap_app_items:
        webmap_app_ids.append(item.id)
    
    app_type_dict = {'Dashboard': dashboard_ids, 'Web Mapping Application': webmap_app_ids}
    
    for app_type in ApplicationTypes:
        id_list = app_type_dict[app_type]
        
        for content_id in id_list:
            content_search = gis.content.get(content_id)
            
            try:
                print(content_search.get_data()['widgets'])
            except:
                pass
            
            print(f"CONTENT: {content_search.type}")
            
            # Process Dashboards
            if content_search.type == "Dashboard":
                update_dashboard(content_search, the_path, gis)
            
            # Process Web Mapping Applications
            elif content_search.type == "Web Mapping Application":
                update_web_mapping_app(content_search, the_path, gis)

def update_dashboard(content_search, the_path, gis):
    try:
        old_title = content_search.title
        title = old_title if ' (DASHBOARD)' in old_title else f"{old_title} (DASHBOARD)"
        
        for widget in content_search.get_data()['widgets']:
            if widget['type'] == "mapWidget":
                webmap_id = widget['itemId']
                print(f'The webmap id: {webmap_id}')
                mappy = gis.content.get(webmap_id)
                wm = WebMap(mappy)
                html_list = generate_html_list(wm)
                
                with open(the_path + "app-description.txt", "w") as f:
                    f.write(str(html_list))
                
                with open(the_path + "app-description.txt", "r") as f:
                    beedle = generate_beedle_html(mappy, wm, f.read())
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
    """
    Remove any occurrence of '(App)' from the title and append a single '(App)'.

    Args:
    title (str): The title of the application.

    Returns:
    str: The normalized title with a single '(App)' appended.
    """
    app_tag = '(App)'
    # Remove all occurrences of '(App)' and strip any leading/trailing whitespace
    clean_title = title.replace(app_tag, '')
    # Append a single '(App)' to the cleaned title
    return f"{clean_title} {app_tag}"

def update_web_mapping_app(content_search, the_path, gis):
    try:
        old_title = content_search.title
        title = normalize_app_title(old_title)
        
        try:
            webmap_id = content_search.get_data()['values']['webmap']
        except:
            try:
                val_getter = content_search.get_data(try_json=True)
                val_list = list(val_getter.values())
                item_dict = dict(val_list[11])
                webmap_id = item_dict['itemId']
            except:
                print('No web map found using default map')
                return
        
        print(f'The web map for this app: {webmap_id}')
        mappy = gis.content.get(webmap_id)
        wm = WebMap(mappy)
        html_list = generate_html_list(wm)
        
        with open(the_path + "app-description.txt", "w") as f:
            f.write(str(html_list))
        
        with open(the_path + "app-description.txt", "r") as f:
            beedle = generate_beedle_html(mappy, wm, f.read())
            props = {
                "title": title,
                "thumbnailurl": "https://gismaps.glendaleaz.com/gisportal/sharing/rest/content/items/9ab3b6e31c3749419467975c8e1e5c97/data",
                "description": beedle,
                "overwrite": True
            }
            content_search.update(item_properties=props)
        
    except Exception as e:
        print(f'Failed to update web mapping application: {e}')



def generate_html_list(wm):
    html_list = []
    lyr_url = []
    lyrs = [lyr.title for lyr in wm.layers]
    
    for i, lyr in enumerate(wm.layers):
        lyr_url.append(lyr.url)
        for a, lyr_title in enumerate(lyrs):
            stringy_url = f"<li><a href='{lyr_url[a]}' target='_blank'>{lyr_title}</li></a>"
            if stringy_url not in html_list:
                html_list.append(stringy_url)
    
    return html_list

def generate_beedle_html(mappy, wm, description):
    clean_description = description.replace('["', '').replace('"]', '').replace('",', '').replace('"', '')
    return (
        f"<font size='4'><b><font color='#ff0000' style='background-color:rgb(255, 255, 255);'><i>The Web Map Name Is:</i></font></b><br>"
        f"<ul><li><a href='https://gismaps.glendaleaz.com/gisportal//home/webmap/viewer.html?webmap={mappy.id}' target='_blank'>"
        f"<font size='4'><i>{wm.item.title}</i></font></a></li></ul><br>"
        f"<font size='3'>The Layers in this app are:<br><ul>{clean_description}</ul></font>"
    )

# Find Maps With Layer
def find_maps_with_layer(lyr_to_find, search_layer, map_item_query='1=1'):
    header_txt = ("<font size='4'><b><font color='#ff0000' style='background-color:rgb(255, 255, 255);'>"
                  "<i>This layer is found in the following WebMap's:</i></font></b>")
    web_map_items = gis.content.search(query=map_item_query, item_type="Web Map", max_items=10000)
    lyr_update = gis.content.search(query=lyr_to_find, item_type=search_layer, max_items=10000)
    
    print(f"Searching {len(web_map_items)} web maps")
    print(f"Searching for {lyr_to_find} in the maps")
    
    maps_with_layer = []
    maps_without_layer = []
    
    for item in web_map_items:
        found_it = False
        wm = WebMap(item)
        lyrs = wm.layers
        
        for lyr in lyrs:
            if 'url' in lyr and not found_it:
                found_it = lyr_to_find.lower() in lyr.url.lower()
            elif 'layerType' in lyr and lyr.layerType == "GroupLayer":
                for sublyr in lyr.layers:
                    if 'url' in sublyr and not found_it:
                        found_it = lyr_to_find.lower() in sublyr.url.lower()
        
        if found_it:
            print(f'{item.id} contains the layer')
            maps_with_layer.append(item)
        else:
            maps_without_layer.append(item)
    
    print(f"Found {len(maps_with_layer)} maps which contain the layer")
    print(f"Found {len(maps_without_layer)} maps which do not contain the layer")
    
    if len(lyr_update) == 0:
        print('No layer update found')
        return maps_with_layer, maps_without_layer
    
    describe = lyr_update[0]
    element_list = []
    the_path = r'D:\COG_ADMIN\MISC_PROJECTS\update-app-map\middle-man\\'
    
    for map_item in maps_with_layer:
        element_list.append(f"<ul><li><a href='https://gismaps.glendaleaz.com/gisportal//home/webmap/viewer.html?webmap="
                            f"{map_item.id}' target='_blank'><font size='4'><i>{map_item.title}</i></li></ul></font></a>")
    
    with open(the_path + "feature-layer-description.txt", "r+") as f:
        try:
            f.truncate(0)
            f.seek(0)
            f.write(header_txt + str(element_list).replace('["', '').replace('"]', '').replace('",', '').replace('"', ''))
        except:
            pass
    
    with open(the_path + "feature-layer-description.txt", "r") as f:
        description = f.read()
    
    updater = gis.content.get(describe.id)
    props = {
        "title": lyr_to_find.title,
        "thumbnailurl": "https://gismaps.glendaleaz.com/gisportal/sharing/rest/content/items/c0ed4fb77f1b441595ea1b6f31c5b46a/data",
        "description": description,
        "overwrite": True
    }
    if not element_list:
        props['tags'] = 'orphan'
    
    try:
        updater.update(item_properties=props)
    except:
        pass
    
    return maps_with_layer, maps_without_layer

if __name__ == "__main__":
    tools = glendale_tools()
    agol_login = tools.agol_creds()
    portal_creds = tools.portal_creds()
    creds = [agol_login, portal_creds]
    for i in range(len(creds)):
        update_desc(creds[i])