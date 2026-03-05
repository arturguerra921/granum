with open('src/view/view.py', 'r') as f:
    lines = f.readlines()

with open('src/view/view.py', 'w') as f:
    for line in lines:
        if "dcc.Download(id='download-model-log')," in line:
            pass # Remove this line
        else:
            f.write(line)

print("Duplicate ID removed from view.py")
