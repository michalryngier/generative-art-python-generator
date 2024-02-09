import os
import shutil

src_dir = "/Users/michalryngier/studia/projekt_inzynierski/cron-generator/public/image-ready"
dest_dir = "/Users/michalryngier/studia/praca-magisterska/art/ratings/random-tries"

counter = 1
for root, dirs, files in os.walk(src_dir):
    if len(files) == 2:
        for filename in files:
            if filename.endswith((".png", ".json")):
                file_path = os.path.join(root, filename)
                extension = filename.split(".")[-1]
                new_name = os.path.join(dest_dir, f"{counter}.{extension}")
                print(new_name)
                shutil.copy(file_path, new_name)
        counter += 1
