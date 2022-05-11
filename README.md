# sayit-online
This is a web app that enables it's users to play this real nice card game called sayit (or dixit if you translate it to latin).

### The Tech Stack (or rather the lack of it)
The project uses ```django``` for everything but the socket connections and ```redis``` for the socket connections.
The django version used is the latest one as of the year AD 2020. 

### Problems
There are quite a few problems with this project, the primary one being the person who wrote it.
For example, even though there is a database running, some parts of the code don't use it but instead substitute the filesystem as the database, which is not good.
There are other things that are not good. However, the app is working. 

### Maintenance
The project is unfortunately no longer maintained but you can use it if you want.

### Setup
The setup steps are described in the ```django_setup.txt``` file and are applicable on the linux platform. It is my belief however that these very steps could be quite effortlessly transcribed to other platforms such as ```Windows``` or ```MacOS```.



