# Gymkhana Nomination Portal
 A scalable web application using Django for releasing and managing nominations for various posts in Student’s Gymkhana. The Portal keeps track of each and every process the application goes through i.e release, submission, interview, review, approval and final selection. Created by [Ashish](https://github.com/aasis21) and [Aniket](https://github.com/aniketp41) during summer camp 2017.

 ## Webpage
Live project is available [here](https://gymkhana.pythonanywhere.com).

## Local Development
Here is a step by step plan on how to setup the Portal. It will get you to a point of having a local running instance.

Create a virtual environment somewhere on your disk, then activate it:
```
virtualenv gym
cd gym
source bin/activate
```
Create a folder in here, and clone the repository:
```
mkdir checkouts
cd checkouts
git clone https://github.com/aasis21/gymkhana-Nominations
```
Next, install the dependencies using  `pip`  (included inside of  [virtualenv](http://pypi.python.org/pypi/virtualenv)):
```
cd gymkhana-Nominations
pip install -r requirements.txt
```
Build your database:
```
python manage.py migrate
```
Then please create a superuser account for Django:
```
python manage.py createsuperuser
```
Run this custom command to create some dummy users and post for testing.
```
python manage.py popcubes
```
Finally, you’re ready to start the webserver:
```
python manage.py runserver
```
Visit  [http://127.0.0.1:8000/](http://127.0.0.1:8000/)  in your browser to see how it looks; you can use the admin interface via  [http://127.0.0.1:8000/admin](http://127.0.0.1:8000/admin)  (logging in with the superuser account you just created).

## Docker Image
You can also build and run the project using docker.
```
git clone https://github.com/aasis21/gymkhana-Nominations
cd gymkhana-Nominations
docker build -t gym  .
docker run -it  --net=host gym
```
The web-app will be available at  `0.0.0.0:8000`  on your browser.

## Some Selected Features
### Dynamic Post Heirarchy
This is one of the most important aspect of the portal. It would very tedious if we would hardcode all the posts in Student Gymkhana,so we made it dynamic. So if we consider all post as node,then its parent in the tree is itself a post. So what are its pros:
-  Ones the top level post is created, then all the required post can be created by the users with post (have power to create child posts).
- It provides infinite levels of post heirarchy as post can create its child post,provides flexibilty as the post heirarchy can be changed at any point of time.

```python

class Post(model.Models):
    post_name = models.CharField(max_length=500)
    club = models.ForeignKey(Club)
    parent = model.ForeignKey(self)
    post_holders = models.ManyToManyField(User, related_name='posts')

```

Many other features of the portal revolves around this dynamic heirarchy. We have same heirarchy for entities like club and council but we use these entities as tags to post for simplification. Modules for ratification or deratification of post holders also work around this.


### Dynamic Approval System
Most of the stuff that happens in gymkhana needs an approval from higher authority. Mostly by the Gen-Secs or the Chairperson. While creating a Post or a Nomination You need a final approval from the concerned authority.

To accomplish it, we needed to create a ladder like functionality so that an approval request can climb up the ranks and after getting a heads-up from a level. So, we created a separate field in Post and Nomination models:

```python
class Post(model.Models):
    ...
    post_approvals = models.ManyToManyField('self')

class Nomination(model.Models):
    ...
    result_approvals = models.ManyToManyField(Post)
    nomi_approvals = models.ManyToManyField(Post)

```
You would observe there are three different approval fields post_approvals, result_approvals, nomi_approvals. These columns contain the list of all the Posts, above the post for which the nomination was released. Once it passes through a certain level, the very next level gets added to the approvals list. So our Nomination knows where to go next for approval. This continues till it reaches the highest authority, on whose approval, the nomination is released for public.

Same can be said for Posts, although it is highly unlikely that any additional posts would be created. But, to make it more dynamic, we allowed separate posts to be created, just in case..

### Post-Holders Search
The Portal provides a search engine powered with year, club and post filter to search and find details of the post holders in Student's Gymkhana. All past years post post details are also maintained dynamically by the portal and can be reached by changing gymkhana year in search filter. To archive this we have added a Post History model to the portal models.

```python

class PostHistory(models.Model):
    post = models.ForeignKey(Post)
    user = models.ForeignKey(User)
    start_date = models.DateField(auto_now_add=True)
    end_date = models.DateField(null=True, blank=True, editable=True)
    post_session = models.ForeignKey(Session)

```

Apart form these the Search has some other awesome features also which aimed to serve for administrative purpose :
- copy institute mail address of all relevent search results.
- generate csv file containing all relevent data of the search results.


### Form Module
- Every Nomination is linked to a Form. This Form module has almost all the features of Google Form in additions to features of our needed.  
- It is used for generating questionnaires consisting various questions during runtime. One can specify the question type like CharField, TextFied, ChoiceField, MultipleChoiceField, etc.
-  Requirement can also be mentioned whether the question is compulsary or not.
- Interviewers can add comment and provide feedback on the filled response.
-  This module is also released separately as a reusable Django package named [diafo](https://github.com/aasis21/diafo).

### User Dashboard
This Dashboard provides various features to a general user. These are:
- Updation of user profile like profile picture, mobile number, room number, etc. On the other side there are certain fields that are not allowed to change.
- Provides details and status of nominations filled by them, interview schedules, tentative results, etc.
- Lists all their saved nomination, allow them to edit nomination form (will discuss later) and either submit or resave the nomination until the deadline. After deadline, Nomination is submitted automatically.
- Provides details regarding the current and past posts of the user in Students Gymkhana.

### Popcubes
This is our custom test-data generator. This creates few user, clubs and posts so that you can make nominations and do testing and development easily. This also assigns some post to dummy users.

```
python manage.py popcubes
```

All the dummy user have password `pass1234`. Dummy users are `groot`, `boyd`, `sparrow`,`legolas` and `amy`.

If you want to flush the database and return each table to an empty state, run this
```
python manage.py flush  
```

*All rights reserved. Copyright © 2017,   [Ashish](https://github.com/aasis21) and [Aniket](https://github.com/aniketp41)*
