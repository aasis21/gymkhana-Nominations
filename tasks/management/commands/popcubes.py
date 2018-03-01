from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import User
from django.db.utils import IntegrityError
from core.models import *
from core.forms import *

users = {
    'sparrow': {
        'username': 'sparrow', 'email' : 'sparrow@iitk.ac.in', 'password' :'pass1234',
        'name': 'Jack Sparrow', 'roll' : 190123, 'program' : 'BT' , 'department' : 'CSE' ,
        'mobile' : 7318099999, 'hall' : '15', 'room' : 'B967'
        },
    'groot': {
        'username': 'groot', 'email' : 'groot@iitk.ac.in', 'password' :'pass1234',
        'name': 'Groot Tonga', 'roll' : 190167, 'program' : 'BT' , 'department' : 'CSE' ,
        'mobile' : 7318099999, 'hall' : '15', 'room' : 'B967'
        },
    'boyd': {
        'username': 'boyd', 'email' : 'boyd@iitk.ac.in', 'password' :'pass1234',
        'name': ' Ellis Boyd', 'roll' : 190110, 'program' : 'BT' , 'department' : 'CSE' ,
        'mobile' : 7318099999, 'hall' : '15', 'room' : 'B967'
        },
    'faizal': {
        'username': 'faizal', 'email' : 'faizal@iitk.ac.in', 'password' :'pass1234',
        'name': 'Faizal Khan', 'roll' : 190169, 'program' : 'BT' , 'department' : 'CE' ,
        'mobile' : 7318099999, 'hall' : '15', 'room' : 'B969'
        },
    'legolas': {
        'username': 'legolas', 'email' : 'legolas@iitk.ac.in', 'password' :'pass1234',
        'name': 'Legolas Kondrial', 'roll' : 190129, 'program' : 'BT' , 'department' : 'BSBE' ,
        'mobile' : 7318099999, 'hall' : '15', 'room' : 'B967'
        },
    'amy': {
        'username': 'amy', 'email' : 'amy@iitk.ac.in', 'password' :'pass1234',
        'name': 'Amy Dunne', 'roll' : 190160, 'program' : 'BT' , 'department' : 'CSE' ,
        'mobile' : 7318099998, 'hall' : '6', 'room' : 'B935'
        },
    }

clubs = [
    {'name': 'Student\'Senate' , 'parent': None },
    {'name': 'Presidential Council' , 'parent': 'Student\'Senate' },
    {'name': 'Cultural Council' , 'parent': 'Student\'Senate' },
    {'name': 'Games and sports Council' , 'parent': 'Student\'Senate' },
    {'name': 'Science and Technology Council' , 'parent': 'Student\'Senate' },
    {'name': 'Dance Club', 'parent' : 'Cultural Council'},
    {'name': 'Dramatics Club', 'parent' : 'Cultural Council'},
    {'name': 'ELS', 'parent' : 'Cultural Council'},
    {'name': 'HSS', 'parent' : 'Cultural Council'},
    {'name': 'Aeromodelling Club', 'parent' : 'Science and Technology Council' },
    {'name': 'Astronomy Club', 'parent' : 'Science and Technology Council' },
    {'name': 'Electronics Club', 'parent' : 'Science and Technology Council' },
    {'name': 'Programming Club', 'parent' : 'Science and Technology Council' },
    {'name': 'Robotics Club', 'parent' : 'Science and Technology Council' },
]

posts = [
    {'name' : 'ChairPerson, Student Gymkhana', 'club' : 'Student\'Senate', 'parent' : None,
        'tags' : ['Student\'Senate'], 'post_holders' : ['legolas'], 'perms' : 'can ratify the post'},
    {'name' : 'President', 'club' : 'Presidential Council', 'parent' : 'ChairPerson, Student Gymkhana',
        'tags' : ['Student\'Senate','Presidential Council'], 'post_holders' : ['amy'], 'perms' : 'can approve post and send nominations to users'},
    {'name' : 'Gen Sec, SNT', 'club' : 'Science and Technology Council', 'parent' : 'ChairPerson, Student Gymkhana',
        'tags' : ['Student\'Senate','Science and Technology Council'], 'post_holders' : ['boyd'], 'perms' : 'can approve post and send nominations to users'},
    {'name' : 'Cordinator, Pclub', 'club' : 'Programming Club', 'parent' : 'Gen Sec, SNT',
        'tags' : ['Student\'Senate','Science and Technology Council','Programming Club'], 'post_holders' : ['groot'], 'perms' : 'normal'},
    {'name' : 'Cordinator, Eclub', 'club' : 'Electronics Club', 'parent' : 'Gen Sec, SNT',
        'tags' : ['Student\'Senate','Science and Technology Council','Programming Club'], 'post_holders' : [], 'perms' : 'normal'},
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
