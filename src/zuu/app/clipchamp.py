import os

# source : https://www.reddit.com/r/ClipChamp/comments/vvsaf4/where_are_the_clipchamp_windows_11_projects_stored/?rdt=54261
projects_path_template = r"C:\\Users\\{username}\\AppData\\Local\\Packages\\Clipchamp.Clipchamp_yxz26nhyzhsrt\\LocalState\\EBWebView\\Default\\indexeddb"
projects_path = projects_path_template.format(username=os.getlogin())
