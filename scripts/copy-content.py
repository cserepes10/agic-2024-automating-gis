import arcpy, requests, json, sys
from arcgis.gis import GIS
from arcgis.gis import User

# Variables
sourcePortal = arcpy.GetParameterAsText(0)
source_username = arcpy.GetParameterAsText(1)
source_password = arcpy.GetParameterAsText(2)

targetPortal = arcpy.GetParameterAsText(3)
target_username = arcpy.GetParameterAsText(4)
target_password = arcpy.GetParameterAsText(5)

selectUser = arcpy.GetParameterAsText(6)

source = GIS(sourcePortal, source_username, source_password)
target = GIS(targetPortal, target_username, target_password)

content = arcpy.GetParameterAsText(7)
targetOwner = arcpy.GetParameterAsText(8)
targetFolder = arcpy.GetParameterAsText(9)


# Function to copy Map/Feature Services
def copyMapFeatureServices(item):
    ITEM_COPY_PROPERTIES = ['title', 'type', 'typeKeywords', 'description', 'tags',
    'snippet', 'extent', 'spatialReference', 'name',
    'accessInformation', 'licenseInfo', 'culture', 'url']

    # Get Item Properties
    item_properties = {}
    for property_name in ITEM_COPY_PROPERTIES:
        item_properties[property_name] = item[property_name]

    if mapServiceURL != '':
        url = item.url
        http = url.split('/')[0]
        serverName = url.split('/')[2]
        webAdaptorName = url.split('/')[3]
        newUrl = url.replace(http + "//" + serverName + "/" + webAdaptorName, mapServiceURL)
        item_properties['url'] = newUrl

    arcpy.AddMessage(item_properties['url'])

    # Get thumbnail and metadata
    thumbnail_file = item.download_thumbnail(arcpy.env.scratchFolder)
    metadata_file = item.download_metadata(arcpy.env.scratchFolder)

    # Add map service
    target_item = target.content.add(item_properties=item_properties, thumbnail=thumbnail_file,
                                     metadata=metadata_file, owner=targetOwner, folder=targetFolder)
    arcpy.AddMessage("Successfully copied: {}".format(target_item))


# Function to share item with Groups
def shareItemWithGroup(item, targetOwner, groupDict):
    searchResult = target.content.search("title:" + item.title + " AND owner:" + targetOwner, item_type = item.type)
    targetItem = searchResult[0]

    for group in groupDict:
        try:
            if group != 'everyone' and group != 'org':
                target_group = target.groups.search('title:{0}'.format(group))
                targetItem.share(groups=target_group[0].id)
        except:
            pass

    targetItem.share(everyone=groupDict['everyone'], org=groupDict['org'])
    arcpy.AddMessage("Successfully shared item with Groups")


# Update Web Map with new layer's ID
def updateWebMaps(item, user, folderId, layerID, newTargetItem):
    arcpy.AddMessage("--Updating with new ID".format(item.title))

    # Get WebMap's JSON for data
    if target.properties["portalHostname"] == 'www.arcgis.com':
        webmapURL = '{0}/arcgis/sharing/rest/content/items/{1}/data'.format(targetPortal, item.id)
    else:
        webmapURL = 'https://{0}:7443/arcgis/sharing/rest/content/items/{1}/data'.format(fqdn, item.id)
    params = {'f': 'pjson', 'token': token}
    r = requests.post(webmapURL, data = params, verify=False)
    response = json.loads(r.content)

    dict = {}
    x = 0
    for opLayer in response["operationalLayers"]:
        if opLayer['itemId'] == layerID:
            dict[x] = newTargetItem.id
            x += 1
        else:
            x += 1

    for val in dict:
        response["operationalLayers"][val]['itemId'] = dict[val]

    # Update WebMap's JSON for data
    if folderId == '':
        if target.properties["portalHostname"] == 'www.arcgis.com':
            updateURL = '{0}/arcgis/sharing/rest/content/users/{1}/{2}/items/{3}/update'.format(targetPortal, item.id)
        else:
            updateURL = 'https://{0}:7443/arcgis/sharing/rest/content/users/{1}/{2}/items/{3}/update'.format(fqdn, user.username, folderId, item.id)
    else:
        if target.properties["portalHostname"] == 'www.arcgis.com':
            updateURL = '{0}/arcgis/sharing/rest/content/users/{1}/items/{2}/update'.format(targetPortal, user.username, item.id)
        else:
            updateURL = 'https://{0}:7443/arcgis/sharing/rest/content/users/{1}/items/{2}/update'.format(fqdn, user.username, item.id)
    params = {'f': 'pjson', 'token': token, 'text': json.dumps(response)}
    r = requests.post(updateURL, data = params, verify=False)
    if r.status_code == 200:
        arcpy.AddMessage("---Successfully updated web map")
    else:
        arcpy.AddError("---Unable to update web map")



# Check Web Maps to see if overwritten service existed
def checkWebMaps(item, user, newTargetItem, folderId=''):
    for dependency in item.dependent_upon()['list']:
        try:
            for layerID in oldIDnewIDdict:
                if layerID == dependency['id']:
                    arcpy.AddMessage("\tLayer found in {0} owned by {1}".format(item.title, user.username))
                    updateWebMaps(item, user, folderId, layerID, newTargetItem)
        except:
            pass


# Function to process item
def processItem(item):
    try:
        # Get Groups item shared with
        groupDict = {}
        for group in item.shared_with.get('groups'):
            try:
                groupDict[group.title] = group.id
            except:
                pass

        groupDict['everyone'] = item.shared_with.get('everyone')
        groupDict['org'] = item.shared_with.get('org')

        # Copy Hosted Feature Services
        if 'Hosted Service' in str(item.typeKeywords):
            arcpy.AddMessage("------------------\nProcessing item: {}".format(item.title))

            # Check if item exists in Target Portal
            searchResult = target.content.search("title:" + item.title + " AND owner:" + targetOwner, item_type = item.type)
            try:
                targetItem = searchResult[0]
                arcpy.AddMessage("{0} found in target portal-----Deleting".format(item.title))
                targetItem.delete()
            except:
                pass

            # Clone Item
            cloneItem = source.content.get(item.id)
            if targetFolder == 'ROOT':
                target.content.clone_items([cloneItem], owner=targetOwner)
            else:
                target.content.clone_items([cloneItem], folder=targetFolder, owner=targetOwner)
            arcpy.AddMessage("Succcessfully copied {}".format(item.title))

            # Share Item
            if item.access == 'shared' or item.access == 'public' or item.access == 'org':
               shareItemWithGroup(item, targetOwner, groupDict)

            # Get new ID of Item and update all web maps that referenced previous ID
            if len(searchResult) > 0:
                newTargetItem = searchResult[0]
                oldIDnewIDdict[targetItem.id] = newTargetItem.id

                target_users = target.users.search('!esri & !system_publisher', max_users=10000)

                for user in target_users:
                    try:
                        if user.user_types()['name'] not in ('Viewer', 'Editor', 'Field Worker'):
                            # Get all web maps these users own
                            for item in user.items():
                                if item.type == 'Web Map':
                                    checkWebMaps(item, user, newTargetItem)
                            folders = user.folders
                            for folder in folders:
                                for item in user.items(folder=folder['title']):
                                    if item.type == 'Web Map':
                                        checkWebMaps(item, user, newTargetItem, folder['id'])
                    except:
                        if user.level == '2':
                           # Get all web maps these users own
                            for item in user.items():
                                if item.type == 'Web Map':
                                    checkWebMaps(item, user, newTargetItem)
                            folders = user.folders
                            for folder in folders:
                                for item in user.items(folder=folder['title']):
                                    if item.type == 'Web Map':
                                        checkWebMaps(item, user, newTargetItem, folder['id'])

    except Exception as e:
        if 'An existing connection was forcibly closed by the remote host' in str(e):
            arcpy.AddMessage("------------------\n\nError processing item: {0}".format(item.title))
            arcpy.AddMessage("Error: {0}".format(e))
            arcpy.AddMessage("Trying again in 10 seconds\n\n")
            time.sleep(10)
            processItem(item)
        else:
            arcpy.AddWarning("------------------\n\nError occurred processing item {0}".format(item.title))
            arcpy.AddWarning("Error: {0}".format(e))
            pass



# Main
if __name__ == "__main__":
    # Get Token
    token = target._con.token

    if target.properties["portalHostname"] == 'www.arcgis.com':
       fqdn = ''
    else:
        # Test if Windows Authentication is enabled
        try:
            targetURL = target.url.split('/')[2] + '/' + target.url.split('/')[3]
            webAppURL = 'https://{0}/sharing/rest/portals/self'.format(targetURL)
            params = {'f': 'pjson', 'token': token}
            r = requests.post(webAppURL, data = params, verify=False)
            if r.status_code == 200:
               fqdn = targetURL
        except Exception as e:
            # Get Target Portal's Fully Qualified Domain Name
            wa = target.admin.system.web_adaptors
            fqdn = wa.properties["webAdaptors"][0]["machineName"] + ':7443/arcgis'

    # Create dictionary for old and new Web Map Ids:
    oldIDnewIDdict = {}

    # Copy map/feature services
    source_users = source.users.search('!esri & !system_publisher', max_users=10000)
    for user in source_users:
        if user.username == selectUser:
            user_content = user.items()
            folders = user.folders
            for folder in folders:
                for item in user.items(folder=folder['title']):
                    user_content.append(item)
            for val in content.split(';'):
                contentData = (val.split(' - ')[0][1:])
                try:
                    for item in user_content:
                        if str(item.title) == contentData and 'Service' in str(item.typeKeywords):
                            processItem(item)
                except Exception as e:
                    if 'An existing connection was forcibly closed by the remote host' in str(e):
                        arcpy.AddMessage("------------------\n\nLost connection: {0}".format(e))
                        arcpy.AddMessage("Trying to reconnect in 10 seconds")
                        time.sleep(10)
                    else:
                        ##arcpy.AddWarning("------------------\n\nError occurred accessing item {0}".format(item.title))
                        arcpy.AddWarning("Error: {0}".format(e))
                        pass

    # Close connections
    arcpy.AddMessage("Deleting Connections")
    del target, source, source_users