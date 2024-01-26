
import json
import os 
import pytest

def check_json_consistency(data):
    # get app ID
    app_id = data.get("app_info", {}).get("App ID", "Unknown ID")

    # check if 'compact_dict' exists
    if "compact_dict" not in data:
        return (app_id, f"'compact_dict' not found")

    # if 'Data Not Collected' or 'No Details Provided' is a key in compact_dict, other dictionaries should be empty
    if "Data Not Collected" in data["compact_dict"] or "No Details Provided" in data["compact_dict"]:
        for key in ['data_linked', 'data_not_linked', 'data_track']:
            if data[key]:
                return (app_id, f"'{key}' should be empty when 'Data Not Collected' or 'No Details Provided' is present")

        # if these conditions are met, return without checking the keys in the other dictionaries
        return None

    # check if 'data_linked', 'data_not_linked', and 'data_track' exist
    for key in ['data_linked', 'data_not_linked', 'data_track']:
        if key not in data:
            return (app_id, f"'{key}' not found")

    if "Data Linked to You" in data["compact_dict"]:
        if not data.get('data_linked', {}):
            return (app_id, "'data_linked' should not be empty when 'Data Linked to You' is present")

    if "Data Not Linked to You" in data["compact_dict"]:
        if not data.get('data_not_linked', {}):
            return (app_id, "'data_not_linked' should not be empty when 'Data Not Linked to You' is present")

    if "Data Used to Track You" in data["compact_dict"]:
        if not data.get('data_track', {}):
            return (app_id, "'data_track' should not be empty when 'Data Used to Track You' is present")

    return None


def test_check_json_consistency():
    # Test case 1: 'Data Linked to You' is present but 'data_linked' is empty
    data = {
        "app_info": {"App ID": 1234},
        "compact_dict": {"Data Linked to You": None},
        "data_linked": {},
        "data_not_linked": {},
        "data_track": {}
    }
    result = check_json_consistency(data)
    assert result is not None, "Expected inconsistency but found none"

    # Test case 2: 'Data Linked to You' is present and 'data_linked' has data
    data = {
        "app_info": {"App ID": 1234},
        "compact_dict": {"Data Linked to You": None},
        "data_linked": {"Some Data": None},
        "data_not_linked": {},
        "data_track": {}
    }
    result = check_json_consistency(data)
    assert result is None, "Expected no inconsistency but found one"
    
    # Test case 3: 'Data Not Collected' is present but other dictionaries have data
    data = {
        "app_info": {"App ID": "1234"},
        "compact_dict": {"Data Not Collected": None},
        "data_linked": {"Some Data": None},
        "data_not_linked": {"Some Data": None},
        "data_track": {"Some Data": None}
    }
    result = check_json_consistency(data)
    assert result is not None, "Expected inconsistency but found none"
    
    # Test case 4: 'Data Not Collected' is present and other dictionaries are empty
    data = {
        "app_info": {"App ID": "1234"},
        "compact_dict": {"Data Not Collected": None},
        "data_linked": {},
        "data_not_linked": {},
        "data_track": {}
    }
    result = check_json_consistency(data)
    assert result is None, "Expected no inconsistency but found one"


def main():
    # initialize an empty list
    inconsistent_apps = []

    # directory_path = 'ios_scraper/json_files-06-21'
    directory_path = '/Users/earnsmacbookair/Downloads/ios_files'
    json_files = os.listdir(directory_path)

    # assuming json_files is a list of all your json file paths
    for json_file in json_files:
        full_path = os.path.join(directory_path, json_file) # create the full path to the file
        with open(full_path, 'r') as f: 
            data = json.load(f)
            inconsistency = check_json_consistency(data)
            if inconsistency is not None:
                inconsistent_apps.append(inconsistency)
            

    # print the inconsistent apps
    for app_id, reason in inconsistent_apps:
        print(f"App ID: {app_id}, Reason: {reason}")
        
    if not inconsistent_apps:
        print      
        
if __name__ == "__main__":
    main()
