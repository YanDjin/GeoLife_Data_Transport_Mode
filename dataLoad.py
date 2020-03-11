import pandas as pd
import os
import re


def files_paths(root_folder_path, files_extensions, files_paths_list = None):
    root_folder_path = os.path.abspath(root_folder_path)
    if files_paths_list is None:
        files_paths_list = {}
    files_extensions = files_extensions if isinstance(files_extensions, list) else [files_extensions]
    for index in range(len(files_extensions)):
        files_extensions[index] = "." + files_extensions[index] if files_extensions[index][0] != '.' else files_extensions[index]
        files_paths_list[files_extensions[index]] = []
    for dirpath, subdirs, files in os.walk(root_folder_path):
        for file in files:
            for extension in files_extensions:
                if file.endswith(extension):
                    files_paths_list[extension].append(os.path.join(dirpath, file))
    return files_paths_list


def date_format(date_string):
    if re.search(date_string, '/'):
        return '%Y/%m/%d %H:%M:%S'
    return '%Y-%m-%d %H:%M:%S'


def identify_folders


def get_user(file_path):
    return re.search(file_path, '/ddd/')[0][1:-1]


files_paths_list = files_paths('Data/056', ['.plt', '.txt'])

data_frames = []
for file_path in files_paths_list:
    data_frames.append(pd.read_csv(file_path, skiprows=6, header=None,
                                   names=["latitude", "longitude", "other", "altitude", "timestamp", "date", "time"]))
