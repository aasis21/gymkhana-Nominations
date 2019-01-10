from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import User
from django.db.utils import IntegrityError
from core.models import *
from core.forms import *

users = {
    'supervoter': {
        'username': 'supervoter', 'email' : 'ec_sg@iitk.ac.in', 'password' :'supervoter',
        'name': 'Mayank Chauhan', 'roll' : 111111, 'program' : 'BT' , 'department' : 'aaa' ,
        'mobile' : 8085822338, 'hall' : '1', 'room' : 'E316'
        },
    }

clubs = [
    {'name': 'Election Commission' , 'parent': None },
]

posts = [
    {'name' : 'Chief Election Officer', 'club' : 'Election Commission', 'parent' : None,
        'tags' : ['Election Commission'], 'post_holders' : ['supervoter'], 'perms' : 'can ratify the post'},
]

class Command(BaseCommand):
    help = 'Create Dummy Data for the Platform'

    def add_users(self,users):
        for userId, user in users.items():
            try:
                u = User.objects.create_user(user['username'], user['email'], user['password'])
            except IntegrityError:
                u = User.objects.get(username=user['username'])

            p , created = UserProfile.objects.get_or_create(user = u,name = user['name'],roll_no = user['roll'],
                                       programme = user["program"],department = user['department'],
                                       contact = user['mobile'], room_no = user['room'],hall = user['hall'])

            if created:
                print("Successfully created:", userId)
            else:
                print("Successfully updated:", userId)

    def add_club_and_posts(self, clubs, posts):
        for club in clubs:
            if club['parent']:
                club['parent'] = Club.objects.get(club_name = club['parent'])
            c, created = Club.objects.get_or_create(club_name = club['name'],club_parent = club['parent'])
            print("Club:" ,club['name'])

        for post in posts:
            name = post['name']
            club = Club.objects.filter(club_name = post['club']).first()
            parent = Post.objects.filter(post_name = post['parent']).first()
            # #tags = [Club.objects.get_or_create(club_name = each)[0] for each in post['tags']]
            # #post_holder = [User.objects.get(username=userId) for userId in post['post_holders']]
            perm = post['perms']
            p = Post.objects.create(post_name=name,
                                elder_brother=parent, club=club, parent=parent,
                                perms=perm, status='Post approved')
            try:
                for each in post['post_holders']:
                    u = User.objects.get(username = each )
                    p.post_holders.add(u)

                    session = Session.objects.filter(start_year=2018).first()
                    if session is None:
                        session = Session.objects.create(start_year=2018)

                    previous_history = PostHistory.objects.filter(post = p).filter(user = u).filter(post_session = session)

                    if not previous_history:
                        PostHistory.objects.create(post=p, user=u, post_session=session,
                                                 end=session_end_date(session.start_year))

            except:
                pass

            print("Post:", post['name'])



    def handle(self, *args, **kwargs):
        self.add_users(users)
        self.add_club_and_posts(clubs, posts)

        self.stdout.write("Task Successful")
