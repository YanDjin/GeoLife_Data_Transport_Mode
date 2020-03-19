import pandas as pd
import requests
import json
import os
import re
import datetime
from math import sin, cos, sqrt, atan2, radians
from copy import deepcopy

# root data
root_path_windows = 'C:\\Users\\Yan\\Documents\\Projects\\ETNA\\Mappy\\group-768539'
root_path_linux = '/home/yanis.bouzidi/ETNA-Projects/Mappy Geolife transport modal/group-768539'

# geolife data path
geolife_data_path_windows = 'C:\\Users\\Yan\\Documents\\Projects\\ETNA\\Mappy\\group-768539\\Data'
geolife_data_path_linux = '/home/yanis.bouzidi/ETNA-Projects/Mappy Geolife transport modal/group-768539/Data'

# pickles paths
pickles_path_windows = 'C:\\Users\\Yan\\Documents\\Projects\\ETNA\\Mappy\\group-768539\\Pickles'
pickles_path_linux = '/home/yanis.bouzidi/ETNA-Projects/Mappy Geolife transport modal/group-768539/Pickles'


# returns files paths in choosen path, retuns only files with choosen extensions
def files_paths(root_folder_path, files_extensions, files_paths_list_available=None):
    root_folder_path = os.path.abspath(root_folder_path)

    if isinstance(files_extensions, list) is False:
        files_extensions = [files_extensions]
        files_extensions_is_array = False
    else:
        files_extensions_is_array = True

    files_paths_list = {}
    files_extensions = files_extensions if isinstance(files_extensions, list) else [files_extensions]
    for index in range(len(files_extensions)):
        files_extensions[index] = "." + files_extensions[index] if files_extensions[index][0] != '.' else \
            files_extensions[index]
        files_paths_list[files_extensions[index]] = []
    for dirpath, subdirs, files in os.walk(root_folder_path):
        for file in files:
            for extension in files_extensions:
                if file.endswith(extension):
                    files_paths_list[extension].append(os.path.join(dirpath, file))
    if files_extensions_is_array is False:
        if files_paths_list_available is None:
            return files_paths_list[files_extensions[0]]
        else:
            files_paths_list_available.append(files_paths_list[files_extensions[0]])
    return files_paths_list


# two dates formats are present in the GeoLife files, returns the correct format by analysing the string
def date_format(date_string):
    if re.search('/', date_string):
        return '%Y/%m/%d %H:%M:%S'
    return '%Y-%m-%d %H:%M:%S'


# users are identified by folders in the GeoLife files, returns the user number in the path
def get_user_number(file_path, search_in_file=False):
    if search_in_file is False:
        search_linux = re.search('/\d{3}/', file_path)
        if search_linux:
            return search_linux.group(0)[1:-1]
        else:
            search_windows = re.search('\\\\\d{3}\\\\', file_path)
            if search_windows:
                return search_windows.group(0)[1:-1]
    else:
        search_linux = re.search('/\d{3}', file_path)
        if search_linux:
            return search_linux.group(0)[1:]
        else:
            search_windows = re.search('\\\\\d{3}', file_path)
            if search_windows:
                return search_windows.group(0)[1:]
    pass


def get_dir_path_from_label_path(label_path):
    replaced_path = label_path.replace('labels.txt', '')
    if replaced_path != label_path:
        return replaced_path
    pass


# loads csv and and adds user number and transport type
def load_from_plt(data_folder_path):
    labels_path_list = files_paths(data_folder_path, '.txt')
    labels_path_list_cleaned = {}
    for label_path in labels_path_list:
        user_number = get_user_number(label_path)
        label_path_cleaned = get_dir_path_from_label_path(label_path)
        if label_path_cleaned is not None and user_number is not None:
            labels_path_list_cleaned[user_number] = label_path_cleaned

    files_paths_list = {}
    for key__user_number in labels_path_list_cleaned:
        list_of_plt = files_paths(labels_path_list_cleaned[key__user_number], '.plt')
        list_of_plt.sort()
        files_paths_list[key__user_number] = list_of_plt

    data_frames = {}
    i = 0
    length_of_files_paths_list = len(files_paths_list)
    for key__user_number in files_paths_list:
        print(str(round((i / length_of_files_paths_list) * 100, 2)) + '%')
        data_frames[key__user_number] = []
        for file_path in files_paths_list[key__user_number]:
            data_frames[key__user_number].append(pd.read_csv(file_path, skiprows=6, header=None,
                                                             names=["latitude", "longitude", "other", "altitude",
                                                                    "timestamp", "date", "time"]))
        i = i + 1

    data_frames_labels = {}
    for key__user_number in labels_path_list_cleaned:
        data_frames_labels[key__user_number] = pd.read_csv(labels_path_list_cleaned[key__user_number] + 'labels.txt',
                                                           delimiter='	')
    print('100%')
    return {
        'data': data_frames,
        'labels': data_frames_labels
    }


def add_user_number_to_data_frame(data_frames):
    data_frames_copy = deepcopy(data_frames)
    for key__user_number in data_frames_copy:
        for x in range(len(data_frames_copy[key__user_number])):
            data_frames_copy[key__user_number][x]['user'] = key__user_number

    return data_frames_copy


def add_transport_modes_to_data_frame(data_frames, data_frames_labels):
    data_frames_copy = deepcopy(data_frames)
    length = number_of_data_frames_recursively(data_frames_copy) + 1
    # k variable is only for displaying % on process done
    k = 1
    for key__user_number in data_frames_labels:
        i = 0
        j = len(data_frames_labels[key__user_number].index)
        print(str(round((k / length) * 100, 2)) + '%')
        for x in range(len(data_frames_copy[key__user_number])):
            data_frames_copy[key__user_number][x]['transport'] = 'None'
            for index, row in data_frames_copy[key__user_number][x].iterrows():
                if k % 5000 == 0:
                    print(str(round((k / length) * 100, 2)) + '%')
                date_string_row = row['date'] + ' ' + row['time']
                while i < j:
                    date_string_label_start = data_frames_labels[key__user_number].iat[i, 0]
                    date_string_label_end = data_frames_labels[key__user_number].iat[i, 1]

                    row_date = datetime.datetime.strptime(date_string_row, date_format(date_string_row))
                    label_date_start = datetime.datetime.strptime(date_string_label_start,
                                                                  date_format(date_string_label_start))
                    label_date_end = datetime.datetime.strptime(date_string_label_end,
                                                                date_format(date_string_label_end))

                    if label_date_start <= row_date <= label_date_end:
                        data_frames_copy[key__user_number][x].at[index, 'transport'] = data_frames_labels[key__user_number].iat[i, 2]
                        break
                    elif label_date_end < row_date:
                        i = i + 1
                    else:
                        break
                k = k + 1
            k = k + 1
        k = k + 1
    print('100%')
    return data_frames_copy


def number_of_data_frames_recursively(data_frames, length=0):
    if isinstance(data_frames, list):
        length = length + len(data_frames)
        for x in range(len(data_frames)):
            length = number_of_data_frames_recursively(data_frames[x], length)
    elif isinstance(data_frames, dict):
        length = length + len(data_frames)
        for x in data_frames:
            length = number_of_data_frames_recursively(data_frames[x], length)
    elif isinstance(data_frames, pd.DataFrame):
        length = length + len(data_frames.index)
    return length


# saves data frames as pickles, separated in folders by user number
def save_data_frames_as_pickles(path_to_save_to, data_frames_=None, data_frames_labels_=None):
    if data_frames_ is not None:
        for key__user_number_ in data_frames_:
            for x_ in range(len(data_frames_[key__user_number_])):
                os.makedirs(os.path.join(path_to_save_to, "data_frames", key__user_number_), exist_ok=True)
                data_frames_[key__user_number_][x_].to_pickle(
                    os.path.join(path_to_save_to, "data_frames", key__user_number_, (str(x_) + ".pkl")))
    if data_frames_labels_ is not None:
        for key__user_number_ in data_frames_labels_:
            os.makedirs(os.path.join(path_to_save_to, "labels"), exist_ok=True)
            data_frames_labels_[key__user_number_].to_pickle(
                os.path.join(path_to_save_to, "labels", (key__user_number_ + ".pkl")))


# loads pickles created by function above
def load_all_pickles(pickles_folder_path):
    data_frames_ = {}
    data_frames_labels_ = {}
    data_frames_pickles_paths = files_paths(os.path.join(pickles_folder_path, "data_frames"), '.pkl')
    labels_data_frames_pickles_paths = files_paths(os.path.join(pickles_folder_path, 'labels'), '.pkl')
    for path in data_frames_pickles_paths:
        user_number_ = get_user_number(path)
        if user_number_ not in data_frames_:
            data_frames_[user_number_] = []
        data_frames_[user_number_].append(pd.read_pickle(path))
    for path in labels_data_frames_pickles_paths:
        user_number_ = get_user_number(path, True)
        data_frames_labels_[user_number_] = pd.read_pickle(path)
    return {
        "data_frames": data_frames_,
        'labels': data_frames_labels_
    }


# save data as csv for the ETL
def save_all_as_csv(path_to_save_to, data_frames_=None, data_frames_labels_=None):
    if data_frames_ is not None:
        for key__user_number_ in data_frames_:
            for x_ in range(len(data_frames_[key__user_number_])):
                os.makedirs(os.path.join(path_to_save_to, "data_frames", key__user_number_), exist_ok=True)
                data_frames_[key__user_number_][x_].to_csv(
                    os.path.join(path_to_save_to, "data_frames", key__user_number_, (str(x_) + ".csv")))
    if data_frames_labels_ is not None:
        os.makedirs(os.path.join(path_to_save_to, "labels"), exist_ok=True)
        for key__user_number_ in data_frames_labels_:
            data_frames_labels_[key__user_number_].to_csv(
                os.path.join(path_to_save_to, "labels", (key__user_number_ + ".csv")))


def save_decomposed(path_to_save_to, data_frames_):
    for key_ in range(len(data_frames_)):
        os.makedirs(os.path.join(path_to_save_to, "decomposed"), exist_ok=True)
        data_frames_[key_].to_pickle(
            os.path.join(path_to_save_to, "decomposed", (str(key_) + ".pkl")))


def load_decomposed(path_to_pickles):
    data_frames_paths = files_paths(os.path.join(path_to_pickles, "decomposed"), '.pkl')
    data_frames_paths_sorted = sorted(data_frames_paths, key=lambda i: int(os.path.splitext(os.path.basename(i))[0]))
    data_frames_ = []
    for key_ in range(len(data_frames_paths_sorted)):
        data_frames_.append(pd.read_pickle(data_frames_paths_sorted[key_]))
    return data_frames_


def merge_data_frames_one_level(data_frame):
    data_frames_copy = deepcopy(data_frame)
    if isinstance(data_frames_copy, dict):
        for key in data_frames_copy:
            if isinstance(data_frames_copy[key], list):
                data_frames_copy[key] = pd.concat(data_frames_copy[key]).reset_index(drop=True)
            else:
                data_frames_dict_to_array = list(data_frames_copy.values())
                return pd.concat(data_frames_dict_to_array).reset_index(drop=True)
    else:
        data_frames_copy = pd.concat(data_frames_copy).reset_index(drop=True)
    return data_frames_copy


# merge all data frames
def merge_all_data_frames_to_one(data_frames):
    data_frames_copy = deepcopy(data_frames)
    for key in data_frames_copy:
        if isinstance(data_frames_copy[key], list):
            data_frames_copy[key] = merge_data_frames_one_level(data_frames_copy[key])
    data_frames_copy = merge_data_frames_one_level(data_frames_copy)
    return data_frames_copy


# decomposed data_frame by travel number
def decompose_by_travel(data_frame):
    data_frame_decomposed = []
    first_index = 0
    length_of_data_frame = len(data_frame)  # for logs percent
    for index, row in data_frame.iterrows():

        if index % 5000 == 0:  # log percent
            print(str(round(((index / length_of_data_frame) * 100), 2)) + '%')

        if int(index) <= 0:
            continue
        date_one_string = data_frame.iat[int(index) - 1, 5] + ' ' + data_frame.iat[index - 1, 6]
        date_two_string = data_frame.iat[int(index), 5] + ' ' + data_frame.iat[index, 6]
        date_one = datetime.datetime.strptime(date_one_string, date_format(date_one_string))
        date_two = datetime.datetime.strptime(date_two_string, date_format(date_two_string))

        user_one = data_frame.iat[index - 1, 8]
        user_two = data_frame.iat[index, 8]
        if (date_two - date_one).total_seconds() > 600 or user_one != user_two:
            one_travel_data_frame = data_frame[first_index:index]
            first_index = index
            data_frame_decomposed.append(one_travel_data_frame)
    print('100%')
    return data_frame_decomposed


# adds travel number to data_frame
def add_travel_number(data_frames):
    data_frames_copy = deepcopy(data_frames)
    data_frames_copy['travel_number'] = "None"
    travel_index = 0
    length_of_data_frame = len(data_frames_copy)  # for logs percent
    for index, row in data_frames_copy.iterrows():
        if index % 5000 == 0:  # log percent
            print(str(round(((index / length_of_data_frame) * 100), 2)) + '%')
        if int(index) <= 0:
            data_frames_copy.at[index, 'travel_number'] = 0
            continue
        date_one_string = data_frames_copy.iat[int(index) - 1, 5] + ' ' + data_frames_copy.iat[index - 1, 6]
        date_two_string = data_frames_copy.iat[int(index), 5] + ' ' + data_frames_copy.iat[index, 6]
        date_one = datetime.datetime.strptime(date_one_string, date_format(date_one_string))
        date_two = datetime.datetime.strptime(date_two_string, date_format(date_two_string))

        user_one = data_frames_copy.at[index - 1, 'user']
        user_two = data_frames_copy.at[index, 'user']
        if (date_two - date_one).total_seconds() > 600 or user_one != user_two:
            travel_index = travel_index + 1
        data_frames_copy.at[index, 'travel_number'] = travel_index
    print('100%')
    return data_frames_copy


# loads data_frame from geoLife files
def load_and_concatenate(path_to_pickles, only_with_transports=False, with_labels=False):
    loaded_data_frames = load_all_pickles(path_to_pickles)
    data_frames = loaded_data_frames['data_frames']
    data_frames = merge_all_data_frames_to_one(data_frames)
    if only_with_transports is True:
        data_frames_temp = data_frames.loc[data_frames['transport'] != "None"].reset_index(drop=True)
        data_frames = data_frames_temp
    if with_labels is True:
        labels = loaded_data_frames['labels']
        labels = merge_all_data_frames_to_one(labels)
        return {
            'data_frames': data_frames,
            'labels': labels
        }
    return data_frames


def calculate_distance_between_two_coordinates(lat1, lon1, lat2, lon2):
    R = 6373.0

    lat1 = radians(lat1)
    lon1 = radians(lon1)
    lat2 = radians(lat2)
    lon2 = radians(lon2)

    dlon = lon2 - lon1
    dlat = lat2 - lat1

    a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    return R * c


def difference_two_dates_and_time(date_1_string, time_1_string, date_2_string, time_2_string):
    datetime_1_string = date_1_string + ' ' + time_1_string
    datetime_2_string = date_2_string + ' ' + time_2_string
    datetime_1 = datetime.datetime.strptime(datetime_1_string, date_format(datetime_1_string))
    datetime_2 = datetime.datetime.strptime(datetime_2_string, date_format(datetime_2_string))
    return abs((datetime_1 - datetime_2).total_seconds())


def calculate_speed_from_distance(distance, seconds):
    speed_on_seconds = distance / seconds
    speed = speed_on_seconds * 3600
    if speed < 0.1:
        return 0
    return speed


def calculate_speed_from_data_frame(data_frame, index):
    lat_1 = data_frame.iat[index - 1, 0]
    lon_1 = data_frame.iat[index - 1, 1]
    lat_2 = data_frame.iat[index, 0]
    lon_2 = data_frame.iat[index, 1]
    distance = calculate_distance_between_two_coordinates(lat_1, lon_1, lat_2, lon_2)

    date_1 = data_frame.iat[index - 1, 5]
    time_1 = data_frame.iat[index - 1, 6]
    date_2 = data_frame.iat[index, 5]
    time_2 = data_frame.iat[index, 6]
    seconds = difference_two_dates_and_time(date_1, time_1, date_2, time_2)

    if seconds == 0:
        return data_frame.iat[index - 1, 9]
    return calculate_speed_from_distance(distance, seconds)


# adds speed to data_frame
def add_speed_to_data_frame(data_frames):
    data_frames_copy = deepcopy(data_frames)
    data_frames_copy['speed'] = "0"
    length_of_data_frame = len(data_frames_copy)  # for logs percent
    for index, row in data_frames_copy.iterrows():
        if index % 5000 == 0:  # log percent
            print(str(round(((index / length_of_data_frame) * 100), 2)) + '%')

        if index == 0:
            continue
        if data_frames_copy.at[index - 1, 'user'] != data_frames_copy.at[index, 'user']:
            data_frames_copy.at[index, 'speed'] = 0
            continue
        data_frames_copy.at[index, 'speed'] = calculate_speed_from_data_frame(data_frames_copy, index)
    print('100%')
    return data_frames_copy


def drop_rows_without_transport_mode(data_frame):
    return data_frame.loc[data_frame['transport'] != "None"].reset_index(drop=True)


def save_merged_pickle(path_to_save_to, data_frames):
    os.makedirs(os.path.join(path_to_save_to, "Pickles"), exist_ok=True)
    os.makedirs(os.path.join(path_to_save_to, "Pickles", 'joined'), exist_ok=True)
    data_frames.to_pickle(
        os.path.join(path_to_save_to, "Pickles", 'joined', "merged.pkl"))


def load_merged_pickle(path_to_pickles):
    linux = False
    if re.search('/', path_to_pickles):
        linux = True
    decomposed = None
    if linux:
        decomposed = path_to_pickles.split('/')
    else:
        decomposed = path_to_pickles.split('\\\\')
        if len(decomposed) == 1:
            decomposed = path_to_pickles.split('\\')
    if len(decomposed[len(decomposed) - 1]) == 0:
        decomposed.pop(len(decomposed) - 1)
    if decomposed[len(decomposed) - 1] == "merged.pkl":
        return pd.read_pickle(path_to_pickles)
    elif decomposed[len(decomposed) - 1] == "joined":
        return pd.read_pickle(os.path.join(path_to_pickles, 'merged.pkl'))
    elif decomposed[len(decomposed) - 1] == "Pickles":
        return pd.read_pickle(os.path.join(path_to_pickles, 'joined', 'merged.pkl'))
    if decomposed[len(decomposed) - 1].find('.plk') != -1:
        return pd.read_pickle(path_to_pickles)
    return pd.read_pickle(os.path.join(path_to_pickles, 'Pickles', "joined", 'merged.pkl'))


def request_details_from_coordinates(lat, lon, only_class=False):
    response = requests.get("https://nominatim.openstreetmap.org/search.php?q=" + str(lat) + " " + str(lon) + "&format=json")
    print(response)
    if response.ok:
        content = json.loads(response.content)
        if len(content) > 0:
            if 'class' in content[0] and only_class:
                return content[0]['class']
            elif 'class' in content[0]:
                return content[0]
    return False


transports_taken_into_account = {
    'railway': {
        'default': {
            'train': {
                'min': 30,
                'max': 400,
                'ideal': 140
            },
            'airplane': {
                'min': 400,
                'max': 1100,
                'ideal': 800,
            }
        }
    },
    'highway': {
        'secondary': {
            'car': {
                'min': 20,
                'max': 120,
                'ideal': 70
            },
            'train': {
                'min': 30,
                'max': 400,
                'ideal': 140
            },
            'bike': {
                'min': 10,
                'max': 50,
                'ideal': 25
            },
            'subway': {
                'min': 25,
                'max': 70,
                'ideal': 45
            },
            'airplane': {
                'min': 400,
                'max': 1100,
                'ideal': 800,
            }
        },
        'residential': {
            'car': {
                'min': 15,
                'max': 40,
                'ideal': 20
            },
            'bike': {
                'min': 5,
                'max': 30,
                'ideal': 14
            },
            'walk': {
                'min': 0,
                'max': 8,
                'ideal': 4
            },
            'subway': {
                'min': 25,
                'max': 70,
                'ideal': 45
            },
            'airplane': {
                'min': 400,
                'max': 1100,
                'ideal': 800,
            }
        },
        'tertiary': {
            'car': {
                'min': 10,
                'max': 40,
                'ideal': 20
            },
            'train': {
                'min': 30,
                'max': 400,
                'ideal': 140
            },
            'bike': {
                'min': 10,
                'max': 50,
                'ideal': 25
            },
            'subway': {
                'min': 25,
                'max': 70,
                'ideal': 45
            },
            'airplane': {
                'min': 400,
                'max': 1100,
                'ideal': 800,
            }
        },
        'default': {
            'car': {
                'min': 20,
                'max': 60,
                'ideal': 40
            },
            'walk': {
                'min': 0,
                'max': 8,
                'ideal': 4
            },
            'airplane': {
                'min': 400,
                'max': 1100,
                'ideal': 800,
            },
            'train': {
                'min': 30,
                'max': 400,
                'ideal': 140
            },
            'bike': {
                'min': 10,
                'max': 50,
                'ideal': 25
            },
        }
    },
    'amenity': {
        'default': {
            'walk': {
                'min': 0,
                'max': 8,
                'ideal': 4
            },
            'subway': {
                'min': 25,
                'max': 70,
                'ideal': 45
            },
            'airplane': {
                'min': 400,
                'max': 1100,
                'ideal': 800,
            }
        }
    },
    'building': {
        'default': {
            'car': {
                'min': 20,
                'max': 60,
                'ideal': 40
            },
            'train': {
                'min': 30,
                'max': 280,
                'ideal': 100
            },
            'bike': {
                'min': 10,
                'max': 30,
                'ideal': 20
            },
            'walk': {
                'min': 0,
                'max': 8,
                'ideal': 4
            },
            'subway': {
                'min': 25,
                'max': 70,
                'ideal': 45
            },
            'airplane': {
                'min': 400,
                'max': 1100,
                'ideal': 800,
            }
        }
    },
    'default': {
        'default': {
            'car': {
                'min': 30,
                'max': 120,
                'ideal': 70
            },
            'train': {
                'min': 30,
                'max': 400,
                'ideal': 140
            },
            'bike': {
                'min': 10,
                'max': 50,
                'ideal': 25
            },
            'walk': {
                'min': 0,
                'max': 8,
                'ideal': 4
            },
            'subway': {
                'min': 25,
                'max': 70,
                'ideal': 45
            },
            'airplane': {
                'min': 400,
                'max': 1100,
                'ideal': 800,
            }
        }
    }
}


def find_transport_for_travel(data_frame):
    stations = {}
    results = {
        'car': 0,
        'train': 0,
        'bike': 0,
        'walk': 0,
        'subway': 0,
        'airplane': 0
    }
    stations = {
        'train': 0,
        'subway': 0,
        'airplane': 0
    }
    last_requests_results = []

    for index, row in data_frame.iterrows():
        lat = data_frame.iat[index, 0]
        lon = data_frame.iat[index, 1]
        speed = data_frame.at[index, 'speed']
        request_response = request_details_from_coordinates(lat, lon)
        if request_response is False:
            class_ = 'default'
            type_ = 'default'
        else:
            class_ = request_response['class']
            type_ = request_response['type']
        if type_ == 'station' and class_ in stations:
            stations[class_] = stations[class_] + 1
        results_new = get_score_per_request_and_speed(speed, class_, type_)
        print(results_new)
        if len(last_requests_results) >= 10:
            last_requests_results.pop(0)
        last_requests_results.append(get_greatest(results))
        for key in results_new:
            results[key] += results_new[key]
        additional_results = calculate_additional_from_last_results(last_requests_results, speed)
        if additional_results is not None:
            for key in results_new:
                results[key] += results_new[key]
        for key in stations:
            results[key] = results[key] + stations[key]

    return get_greatest(results)


def get_score_per_request_and_speed(speed, class_, type_):
    results = {
        'car': 0,
        'train': 0,
        'bike': 0,
        'walk': 0,
        'subway': 0,
        'airplane': 0
    }
    if class_ not in transports_taken_into_account:
        class_ = 'default'
    if type_ not in transports_taken_into_account[class_]:
        type_ = 'default'
    for key, value in transports_taken_into_account[class_][type_].items():
        results[key] = calculate_points_from_speed(speed, value['min'], value['max'], value['ideal'])
    return results


def calculate_points_from_speed(speed, min, max, ideal):
    print(speed, min, max, ideal)
    if int(speed) < int(min) or int(speed) > int(max):
        return 0
    if speed < ideal:
        return ((speed - min) / (ideal - min)) ** 2
    diff_max = max - ideal
    diff_speed = speed - ideal
    return ((diff_max - diff_speed) / diff_max) ** 2


def get_greatest(results):
    greatest = {
        'key': None,
        'value': 0
    }
    for key in results:
        if results[key] > greatest['value']:
            greatest['key'] = key
            greatest['value'] = results[key]
    return greatest['key']


transports_taken_into_account_for_last_results = {
    'train': {
        'min': 80,
        'max': 400,
        'ideal': 140,
    },
    'bike': {
        'min': 10,
        'max': 50,
        'ideal': 25,
    },
    'walk': {
        'min': 0,
        'max': 8,
        'ideal': 4,
    },
    'airplane': {
        'min': 400,
        'max': 1100,
        'ideal': 800,
    },
    'subway': {
        'min': 25,
        'max': 70,
        'ideal': 45
    }
}


def calculate_additional_from_last_results(last_requests_results, speed):
    results = {
        'train': 0,
        'bike': 0,
        'walk': 0,
        'subway': 0,
        'airplane': 0
    }
    length = len(last_requests_results)
    if length <= 0 or length == 1:
        return None
    if last_requests_results[length - 2] == last_requests_results[length - 1]:
        return None
    number_of_changes_in_chain = number_of_changes(last_requests_results)
    for key, value in transports_taken_into_account_for_last_results.items():
        results[key] = calculate_points_from_speed(speed, value['min'], value['max'], value['ideal'])
    greatest = get_greatest(results)
    returned_result = {}[greatest] = results[greatest] + ((10 - number_of_changes_in_chain) ** 2)
    return returned_result


def number_of_changes(last_requests_results):
    number = 0
    length = len(last_requests_results)
    for i in range(length):
        if i < length - 1:
            if last_requests_results[i] != last_requests_results[i + 1]:
                number = number + 1
    return number
