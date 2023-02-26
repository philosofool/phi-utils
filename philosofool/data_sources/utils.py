import yaml

def read_yml(path, loader=yaml.CLoader):
    with open(path, 'r') as f:
        return yaml.load(f, Loader=loader)

if __name__ == "__main__":
    path = r'C:\Users\lenha\Repos\fantasy-baseball-draft\local\config.yml'
    print(read_yml(path))


