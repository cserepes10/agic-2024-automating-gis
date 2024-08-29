from arcgis.gis import GIS
from arcgis.mapping import WebMap
from GlendaleTools import glendale_tools
from arcgis.apps.expbuilder import WebExperience



# Update Descriptions
def update_desc(creds):
    gis = GIS(creds[0], creds[1], creds[2])
    if 'gismaps.gelndaleaz.com' in creds[0]:
        portal = True
    else:
        portal = False
    ApplicationTypes = ['Dashboard', 'Web Mapping Application','Web Experience']
    dashboard_ids = []
    app_ids = []
    exp_ids = []
    webmap_app_ids = []
    the_path = r'D:\COG_ADMIN\MISC_PROJECTS\agic-2024-automating-gis\scripts\templates\\'
    
    dashboard_items = gis.content.search(query='owner:BCserepes@GLENDALEAZ.COM_COG_GIS', item_type="Dashboard", max_items=9999)
    app_items = gis.content.search(query='owner:BCserepes@GLENDALEAZ.COM_COG_GIS', item_type="Application", max_items=9999)
    webmap_app_items = gis.content.search(query='owner:BCserepes@GLENDALEAZ.COM_COG_GIS', item_type="Web Mapping Application", max_items=9999)
    webexp_app_items = gis.content.search(query='owner:BCserepes@GLENDALEAZ.COM_COG_GIS', item_type="Web Experience", max_items=9999)
    
    
    for item in dashboard_items:
        dashboard_ids.append(item.id)
    for item in app_items:
        app_ids.append(item.id)
    for item in webmap_app_items:
        webmap_app_ids.append(item.id)
    for item in webexp_app_items:
        exp_ids.append(item.id)
    print(len(exp_ids))
    
    app_type_dict = {'Dashboard': dashboard_ids, 'Web Mapping Application': webmap_app_ids, 'Web Experience': exp_ids}
    
    for app_type in ApplicationTypes:
        id_list = app_type_dict[app_type]
        
        for content_id in id_list:
            content_search = gis.content.get(content_id)
            
            #print(f"CONTENT: {content_search.type}")
            
            # Process Dashboards
            if content_search.type == "Dashboard":
                
                update_dashboard(content_search, the_path, gis, portal)
            
            # Process Web Mapping Applications
            if content_search.type == "Web Mapping Application":
                update_web_mapping_app(content_search, the_path, gis, portal)
            # Process Web Experiences
            if content_search.type == "Web Experience":
                update_web_mapping_app(content_search, the_path, gis, portal)

def update_dashboard(content_search, the_path, gis, portal):
    try:
        old_title = content_search.title
        title = old_title if ' (DASHBOARD)' in old_title else f"{old_title} (DASHBOARD)"
        
        for widget in content_search.get_data()['widgets']:
            if widget['type'] == "mapWidget":
                webmap_id = widget['itemId']
                #print(f'The webmap id: {webmap_id}')
                mappy = gis.content.get(webmap_id)
                selected_web_map = WebMap(mappy)
                html_list = generate_html_list(selected_web_map, gis, portal=portal)
                
                with open(the_path + "app-description.txt", "w") as f:
                    f.write(str(html_list))
                
                with open(the_path + "app-description.txt", "r") as f:
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
def deal_with_exp_builder(content_search, gis):
    print(content_search.id)
    experience_builder = WebExperience(content_search.id, gis = gis)
    print(experience_builder.datasources)
    keys_list = []
    for key in experience_builder.datasources.keys():
        keys_list.append(key)
    print(keys_list)
    for i in keys_list:
        if experience_builder.datasources[i]['type'] == 'WEB_MAP':
            print(f'web map waha: {experience_builder.datasources[i]["itemId"]}')
            webmap_id = experience_builder.datasources[i]["itemId"]
    return webmap_id
def update_web_mapping_app(content_search, the_path, gis, portal):
    try:
        old_title = content_search.title
        title = normalize_app_title(old_title)
        
        try:
            webmap_id = content_search.get_data()['values']['webmap']
        except:
            try:
                val_getter = content_search.get_data(try_json=True)
                val_list = list(val_getter.values())
                #print(val_list)
                item_dict = dict(val_list[11])
                webmap_id = item_dict['itemId']
            except:
                print('No web map trying experience builders')
        try:
            webmap_id = deal_with_exp_builder(content_search, gis)
        except:
            print('not an experience builder')
            pass
        
        print(f'The web map for this app: {webmap_id}')
        mappy = gis.content.get(webmap_id)
        print(mappy.title)
        selected_web_map = WebMap(mappy)
        html_list = generate_html_list(selected_web_map, gis, portal=portal)
        print(html_list)
        with open(the_path + "app-description.txt", "w") as f:
            f.write(str(html_list))
        
        with open(the_path + "app-description.txt", "r") as f:
            beedle = generate_beedle_html(mappy, selected_web_map, f.read(), portal)
            props = {
                "title": title,
                "thumbnailurl": "https://gismaps.glendaleaz.com/gisportal/sharing/rest/content/items/9ab3b6e31c3749419467975c8e1e5c97/data",
                "description": beedle,
                "overwrite": True
            }
            content_search.update(item_properties=props)
        
    except Exception as e:
        print(f'Failed to update web mapping application: {e}')



def generate_html_list(selected_web_map, gis, portal):
    html_list = []
    lyr_url = []
    lyr_type = []
    try:
        for lyr in selected_web_map.layers:
            lyr_url.append(lyr.url)
            lyr_type.append(lyr.get('layerType', 'Unknown'))
            stringy_url = f"<li><a href='{lyr.url}' target='_blank'>{lyr.title}</li></a>"
            if stringy_url not in html_list:
                html_list.append(stringy_url)
        try:
            for k in range(len(lyr_url)):
                find_maps_with_layer(lyr_url[k], lyr_type[k], gis=gis, portal=portal)
        except:
            print('couldnt get the layers description updated')
    except:
        html_list = "Couldn't get the list"
    
    return html_list

def generate_beedle_html(mappy, selected_web_map, description, portal):
    clean_description = description.replace('["', '').replace('"]', '').replace('",', '').replace('"', '')
    if portal == True:
        url = 'https://gismaps.glendaleaz.com/gisportal/apps/mapviewer/index.html?webmap='
    else:
        url = 'https://cog-gis.maps.arcgis.com/apps/mapviewer/index.html?webmap='
    return (
        f"<font size='4'><b><font color='#ff0000' style='background-color:rgb(255, 255, 255);'><i>The Web Map Name Is:</i></font></b><br>"
        f"<ul><li><a href='{url}{mappy.id}' target='_blank'>"
        f"<font size='4'><i>{selected_web_map.item.title}</i></font></a></li></ul><br>"
        f"<font size='3'>The Layers in this app are:<br><ul>{clean_description}</ul></font>"
    )


def find_maps_with_layer(lyr_to_find, search_layer,  gis='', portal=''):
    new_description = ("<font size='4'><b><font color='#ff0000' style='background-color:rgb(255, 255, 255);'>"
                  "<i>This layer is found in the following Web Map's:</i></font></b>")
    
    # Search for web maps and the specific layer
    web_map_items = gis.content.search(query='*', item_type="Web Map", max_items=200)
    lyr_to_find = lyr_to_find.split('FeatureServer')[0]+'FeatureServer'
    lyr_update = gis.content.search(query=lyr_to_find,item_type="Feature Layer Collection", max_items=1)

    print(lyr_update)
    if portal == True:
        url = 'https://gismaps.glendaleaz.com/gisportal/apps/mapviewer/index.html?webmap='
    else:
        url = 'https://cog-gis.maps.arcgis.com/apps/mapviewer/index.html?webmap='
    maps_with_layer = []
    maps_without_layer = []
    
    # Iterate over each web map
    for item in web_map_items:
        found_it = False
        selected_web_map = WebMap(item)
        lyrs = selected_web_map.layers
        
        for lyr in lyrs:
            if 'url' in lyr and lyr_to_find.lower() in lyr.url.lower():
                found_it = True
                break
            elif 'layerType' in lyr and lyr.layerType == "GroupLayer":
                for sublyr in lyr.layers:
                    if 'url' in sublyr and lyr_to_find.lower() in sublyr.url.lower():
                        found_it = True
                        break
        
        if found_it:
            print(f'{item.id} contains the layer')
            maps_with_layer.append(item)
        else:
            maps_without_layer.append(item)
    
    if not lyr_update:
        print('No layer update found')
        return 
    
    # Update the description of the first matching layer
    describe = lyr_update[0]
    element_list = []
    the_path = r'D:\COG_ADMIN\MISC_PROJECTS\agic-2024-automating-gis\scripts\templates\\'
    
    for map_item in maps_with_layer:
        new_description += (
            f"<ul><li><a href='{url}"
            f"{map_item.id}' target='_blank'><font size='4'><i>{map_item.title}</i></font></a></li></ul>"
        )
    print(new_description)
    try:
        
        print("THE TITLE IS :" + describe.title)
        props = {
            "title": describe.title,
            "thumbnailurl": "https://gismaps.glendaleaz.com/gisportal/sharing/rest/content/items/c0ed4fb77f1b441595ea1b6f31c5b46a/data",
            "description": new_description,
            "overwrite": True
            }
        if not element_list:
            props['tags'] = 'orphan'
            
        describe.update(item_properties=props)
    
    except Exception as e:
        print(f"Failed to update feature layer description: {e}")
    
    return maps_with_layer, maps_without_layer


if __name__ == "__main__":
    tools = glendale_tools()
    agol_login = tools.agol_creds()
    portal_creds = tools.portal_creds()
    creds = [agol_login, portal_creds]
    for i in range(len(creds)):
        update_desc(creds[i])