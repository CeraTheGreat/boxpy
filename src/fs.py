class FileSystem:
    def __init__(self, name, folder_id):
        self.current_path = [(name,Folder(name,folder_id))]

    def path(self):
        return '/' + '/'.join([x[0] for x in self.current_path[1:]])

    def children(self):
        return [n for n in self.pwd().folders]  \
                + [n for n in self.pwd().files]

    def files(self):
        return [n for n in self.pwd().files]

    def folders(self):
        return [n for n in self.pwd().folders]

    def pwd(self):
        return self.head(self.current_path)

    def head(self, path):
        return path[-1][1]
    
    def traverse(self, path):
        temp_path = []
        if path.startswith('/'):
            temp_path = [self.current_path[0]]
        else:
            temp_path = self.current_path

        dirs = path.split('/')
        for directory in dirs:
            directory = ''.join(filter(lambda ch: ch not in '"', directory))
            if directory == ' ' or directory == '' or directory == '.':
                continue
            elif self.head(temp_path).contains_folder(directory):
                temp_path.append((directory,self.head(temp_path).folders[directory]))
            elif directory == '..':
                temp_path.pop()
            elif self.head(temp_path).contains_file(directory):
                raise Exception("{} in {} is not a directory".format(directory, path))
            elif not self.head(temp_path).contains_folder(directory):
                raise Exception("{} in {} does not exist".format(directory, path))
        self.current_path = temp_path
            
    def get_item(self, path):
        if '/' in path:
            old_path = self.current_path
            item,path = path.split('/')[-1],('/').join(path.split('/')[:-1])
            self.traverse(path)
            
            if self.pwd().contains_folder(item):
                item = self.pwd().folders[item]
                self.current_path = old_path
                return item
            elif self.pwd().contains_file(item):
                item = self.pwd().files[item]
                self.current_path = old_path
                return item
            else:
                self.current_path = old_path
                raise Exception('{} could not be found'.format(item))
        else:
            if self.pwd().contains_folder(path):
                return self.pwd().folders[path]
            elif self.pwd().contains_file(path):
                return self.pwd().files[path]
            else:
                raise Exception('{} could not be found'.format(item))

    def is_folder(self, name):
        return any([x for x in self.pwd().folders if x == name])
            
    def is_file(self, name):
        return any([x for x in self.pwd().files if x == name])

    def add_file(self, name, file_id):
        self.pwd().add_file(name, file_id)

    def add_folder(self, name, folder_id):
        self.pwd().add_folder(name, folder_id)


class Item:
    def __init__(self, name, item_id):
        self.name = name
        self.id = item_id


class Folder(Item):
    def __init__(self, name, folder_id):
        super().__init__(name, folder_id)
        self.folders = {}
        self.files = {}

    def add_folder(self, name, folder_id):
        self.folders[name] = Folder(name, folder_id)

    def add_file(self, name, file_id):
        self.files[name] = File(name, file_id)

    def del_folder(self, name):
        del self.folders[name]

    def del_file(self, name):
        del self.files[name]

    def add_folders(self, folders):
        for f in folders:
            self.add_folder(f)

    def add_files(self, files):
        for f in files:
            self.add_file(f)

    def contains(self, name):
        return contains_file(name) or contains_folder(name)

    def contains_file(self, name):
        return any([x for x in self.files if x == name])

    def contains_folder(self, name):
        return any([x for x in self.folders if x == name])


class File(Item):
    def __init__(self, name, file_id):
        super().__init__(name, file_id)
